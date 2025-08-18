import os
import json
import datetime
import pandas as pd
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# --- V2 SDK Imports ---
from chs_sdk.core.host import AgentKernel
from chs_sdk.agents.message import Message
from chs_sdk.agents.body_agents import TankAgent, GateAgent
from chs_sdk.agents.disturbance_agents import InflowAgent
from chs_sdk.agents.management_agents import DataCaptureAgent
import threading
from rule_based_agent import RuleBasedAgent

# --- V2 SDK Imports ---
from flask import send_from_directory
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from gym_wrapper import create_chs_env
import datetime
import mlflow
import mlflow.pytorch
import optuna
import shutil
import uuid
import requests

from flask_socketio import SocketIO, Namespace, join_room

# --- Flask App Initialization ---
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Determine the absolute path for the instance folder
instance_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'instance'))
os.makedirs(instance_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(instance_path, "projects.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MLFLOW_TRACKING_URI'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mlruns')
mlflow.set_tracking_uri(app.config['MLFLOW_TRACKING_URI'])


db = SQLAlchemy(app)
migrate = Migrate(app, db)

with app.app_context():
    db.create_all()

# --- Database Models ---
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    scenario_json = db.Column(db.Text, nullable=False)
    simulation_runs = db.relationship('SimulationRun', backref='project', lazy=True, cascade="all, delete-orphan")
    models = db.relationship('TrainedModel', backref='project', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "scenario": json.loads(self.scenario_json)
        }

class SimulationRun(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    run_timestamp = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    results_json = db.Column(db.Text, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "run_timestamp": self.run_timestamp.isoformat(),
            "results": json.loads(self.results_json)
        }

class TrainedModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    algorithm = db.Column(db.String(50), nullable=False)
    total_timesteps = db.Column(db.Integer, nullable=False)
    model_path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "algorithm": self.algorithm,
            "total_timesteps": self.total_timesteps,
            "created_at": self.created_at.isoformat()
        }

# --- Model Storage Setup ---
MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

# --- API Endpoints ---

@app.route('/api/projects', methods=['POST'])
def create_project():
    data = request.get_json()
    if not data or 'name' not in data or 'scenario' not in data:
        return jsonify({"status": "error", "message": "Invalid project data"}), 400

    project = Project(
        name=data['name'],
        scenario_json=json.dumps(data['scenario'])
    )
    db.session.add(project)
    db.session.commit()

    return jsonify({"status": "success", "project": project.to_dict()}), 201

class MLflowCallback(BaseCallback):
    """
    A custom callback for logging metrics to MLflow.
    """
    def __init__(self, verbose=0):
        super(MLflowCallback, self).__init__(verbose)
        self.rollout_count = 0

    def _on_rollout_end(self) -> None:
        """
        This event is triggered after a rollout.
        """
        self.rollout_count += 1
        # Metrics are logged manually, e.g., using self.logger
        # Here we can log the mean reward
        if "rollout/ep_rew_mean" in self.model.logger.name_to_value:
            mean_reward = self.model.logger.name_to_value["rollout/ep_rew_mean"]
            mlflow.log_metric("rollout_ep_rew_mean", mean_reward, step=self.rollout_count)

    def _on_step(self) -> bool:
        """
        This method will be called by the model after each call to `env.step()`.
        """
        # Log training loss
        if 'train/loss' in self.model.logger.name_to_value:
            loss = self.model.logger.name_to_value['train/loss']
            mlflow.log_metric("loss", loss, step=self.num_timesteps)
        return True

@app.route('/api/projects/<int:project_id>/train', methods=['POST'])
def train_project_model(project_id):
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid request body"}), 400

    params = {
        'algorithm': data.get('algorithm', 'PPO'),
        'total_timesteps': data.get('total_timesteps', 10000),
        'learning_rate': data.get('learning_rate', 0.0003) # Example of a new hyperparameter
    }

    if params['algorithm'] != 'PPO':
        return jsonify({"status": "error", "message": f"Algorithm {params['algorithm']} not supported"}), 400

    mlflow.set_experiment(project.name)

    try:
        with mlflow.start_run() as run:
            # Log parameters
            mlflow.log_params(params)
            app.logger.info(f"Starting training for project {project_id} with MLflow run ID: {run.info.run_id}")

            # 1. Create the Gym environment
            env = create_chs_env(project.scenario_json)

            # 2. Initialize the SB3 model
            model = PPO('MlpPolicy', env, verbose=1, learning_rate=params['learning_rate'])

            # 3. Train the model with MLflow callback
            mlflow_callback = MLflowCallback()
            model.learn(total_timesteps=params['total_timesteps'], callback=mlflow_callback)

            # 4. Save the trained model
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            model_filename = f"project_{project_id}_{run.info.run_id[:8]}_{timestamp}.zip"
            model_save_path = os.path.join(MODELS_DIR, model_filename)
            model.save(model_save_path)

            # Log model as an artifact
            mlflow.log_artifact(model_save_path, artifact_path="model")

            # 5. Save model metadata to the database
            trained_model = TrainedModel(
                project_id=project.id,
                algorithm=params['algorithm'],
                total_timesteps=params['total_timesteps'],
                model_path=model_filename # Store relative path
            )
            db.session.add(trained_model)
            db.session.commit()

            return jsonify({
                "status": "success",
                "message": "Training complete",
                "model": trained_model.to_dict(),
                "mlflow_run_id": run.info.run_id
            })

    except Exception as e:
        app.logger.error(f"An error occurred during training for project {project_id}: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/projects/<int:project_id>/optimize', methods=['POST'])
def optimize_project_model(project_id):
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid request body"}), 400

    n_trials = data.get('n_trials', 20)
    total_timesteps_per_trial = data.get('total_timesteps_per_trial', 5000)
    # The hyperparameter space can be passed from the frontend
    # For now, we define a default one.
    default_space = {
        "learning_rate": {"type": "loguniform", "low": 1e-5, "high": 1e-1}
    }
    hyperparameter_space = data.get('hyperparameter_space', default_space)

    # Create a temporary directory for this optimization run
    opt_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'optuna_runs', str(uuid.uuid4()))
    os.makedirs(opt_dir, exist_ok=True)

    def objective(trial: optuna.Trial) -> float:
        try:
            trial_params = {}
            # Suggest hyperparameters based on the space definition
            for name, space in hyperparameter_space.items():
                if space['type'] == 'loguniform':
                    trial_params[name] = trial.suggest_loguniform(name, space['low'], space['high'])
                elif space['type'] == 'uniform':
                    trial_params[name] = trial.suggest_uniform(name, space['low'], space['high'])
                elif space['type'] == 'categorical':
                    trial_params[name] = trial.suggest_categorical(name, space['choices'])
                # Add more types as needed

            # Create a unique directory for this trial's logs
            trial_log_dir = os.path.join(opt_dir, f"trial_{trial.number}")
            os.makedirs(trial_log_dir, exist_ok=True)

            # 1. Create environment and wrap it with a Monitor
            env = create_chs_env(project.scenario_json, log_dir=trial_log_dir)

            # 2. Create the model
            model = PPO('MlpPolicy', env, verbose=0, **trial_params)

            # 3. Train the model
            model.learn(total_timesteps=total_timesteps_per_trial)

            # 4. Save the model
            model_path = os.path.join(trial_log_dir, "model.zip")
            model.save(model_path)
            trial.set_user_attr("model_path", model_path) # Store path in trial

            # 5. Evaluate the model by reading the monitor file
            monitor_files = [f for f in os.listdir(trial_log_dir) if f.endswith(".monitor.csv")]
            if not monitor_files:
                app.logger.warning(f"No monitor file found for trial {trial.number}")
                return -float('inf') # Return a very bad score

            monitor_df = pd.read_csv(os.path.join(trial_log_dir, monitor_files[0]), skiprows=1)
            # The last episode's mean reward
            final_reward = monitor_df['r'].iloc[-10:].mean() if not monitor_df.empty else -float('inf')

            return final_reward

        except Exception as e:
            app.logger.error(f"Exception in Optuna trial {trial.number}: {e}", exc_info=True)
            # If a trial fails, Optuna will prune it.
            # We can return a very low value to signal failure.
            return -float('inf')


    try:
        # We want to maximize the reward
        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=n_trials)

        best_trial = study.best_trial
        best_params = best_trial.params
        best_model_path = best_trial.user_attrs.get("model_path")

        if not best_model_path or not os.path.exists(best_model_path):
             return jsonify({"status": "error", "message": "Could not find the best model file."}), 500

        # Copy the best model to the permanent models directory
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        final_model_filename = f"project_{project_id}_opt_{timestamp}.zip"
        final_model_path = os.path.join(MODELS_DIR, final_model_filename)
        shutil.copy(best_model_path, final_model_path)

        # Save model metadata to the database
        trained_model = TrainedModel(
            project_id=project.id,
            algorithm="PPO_Optuna", # Indicate that this was an optimized model
            total_timesteps=total_timesteps_per_trial * n_trials, # Approximate total
            model_path=final_model_filename
        )
        db.session.add(trained_model)
        db.session.commit()

        # Clean up the temporary optimization directory
        shutil.rmtree(opt_dir)

        return jsonify({
            "status": "success",
            "message": "Optimization complete.",
            "best_trial": {
                "number": best_trial.number,
                "value": best_trial.value,
                "params": best_params
            },
            "model": trained_model.to_dict()
        })

    except Exception as e:
        # Clean up in case of failure
        if os.path.exists(opt_dir):
            shutil.rmtree(opt_dir)
        app.logger.error(f"An error occurred during optimization for project {project_id}: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/projects/<int:project_id>/models', methods=['GET'])
def get_project_models(project_id):
    project = Project.query.get_or_404(project_id)
    models = TrainedModel.query.filter_by(project_id=project.id).order_by(TrainedModel.created_at.desc()).all()
    return jsonify([m.to_dict() for m in models])


@app.route('/api/models/<int:model_id>', methods=['GET'])
def download_model(model_id):
    model_record = TrainedModel.query.get_or_404(model_id)
    return send_from_directory(MODELS_DIR, model_record.model_path, as_attachment=True)

# --- Deployment Endpoint ---
CHS_SCADA_DISPATCH_URL = os.environ.get("CHS_SCADA_DISPATCH_URL", "http://chs-scada-dispatch:8080/api/v1")

@app.route('/api/agents/<int:agent_model_id>/deploy', methods=['POST'])
def deploy_agent(agent_model_id):
    model_record = TrainedModel.query.get_or_404(agent_model_id)
    data = request.get_json()
    if not data or 'target_device_id' not in data:
        return jsonify({"status": "error", "message": "Missing 'target_device_id' in request body"}), 400

    target_device_id = data['target_device_id']
    model_path = os.path.join(MODELS_DIR, model_record.model_path)

    if not os.path.exists(model_path):
        return jsonify({"status": "error", "message": "Model file not found on server"}), 404

    try:
        with open(model_path, 'rb') as f:
            files = {'agent_package': (model_record.model_path, f, 'application/zip')}
            deploy_url = f"{CHS_SCADA_DISPATCH_URL}/devices/{target_device_id}/deploy_agent"

            app.logger.info(f"Deploying agent {agent_model_id} to device {target_device_id} at {deploy_url}")

            response = requests.post(deploy_url, files=files, timeout=30) # 30-second timeout
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

            return jsonify({
                "status": "success",
                "message": f"Agent {agent_model_id} successfully deployed to device {target_device_id}.",
                "dispatch_response": response.json()
            }), response.status_code

    except requests.exceptions.RequestException as e:
        app.logger.error(f"Failed to deploy agent to dispatch service: {e}")
        return jsonify({"status": "error", "message": f"Failed to connect to dispatch service: {str(e)}"}), 503
    except Exception as e:
        app.logger.error(f"An unexpected error occurred during deployment: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/projects', methods=['GET'])
def get_projects():
    projects = Project.query.all()
    return jsonify([p.to_dict() for p in projects])

@app.route('/api/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    project = Project.query.get_or_404(project_id)
    return jsonify(project.to_dict())


@app.route('/api/projects/<int:project_id>/topology', methods=['GET'])
def get_project_topology(project_id):
    """
    Returns the topology data (components and connections) for a project.
    """
    project = Project.query.get_or_404(project_id)
    scenario = json.loads(project.scenario_json)

    # The frontend needs the components and connections to draw the topology
    topology_data = {
        "components": scenario.get("components", {}),
        "connections": scenario.get("connections", [])
    }

    return jsonify(topology_data)

# --- Simulation Constants ---
TIME_STEP = 1.0     # seconds
DISCHARGE_COEFF = 0.6
INFLOW_RATE = 50.0 # m^3/s

# --- V2 SDK Imports ---
# Corrected to use the new SimulationBuilder and SimulationManager
from water_system_sdk.src.chs_sdk.simulation_manager import SimulationManager
from water_system_sdk.src.chs_sdk.simulation_builder import SimulationBuilder


@app.route('/api/projects/<int:project_id>/runs', methods=['GET'])
def get_project_runs(project_id):
    project = Project.query.get_or_404(project_id)
    runs = SimulationRun.query.filter_by(project_id=project.id).order_by(SimulationRun.run_timestamp.desc()).all()
    return jsonify([run.to_dict() for run in runs])


# --- Live Simulation Namespace ---
active_simulations = {}

class LiveSimulationNamespace(Namespace):
    def on_connect(self):
        app.logger.info(f"SocketIO client connected: {request.sid}")

    def on_disconnect(self):
        app.logger.info(f"SocketIO client disconnected: {request.sid}")

    def on_join_simulation_room(self, data):
        sim_id = data.get('simulation_id')
        if sim_id and sim_id in active_simulations:
            app.logger.info(f"Client {request.sid} joining room for simulation {sim_id}")
            join_room(sim_id)
        else:
            app.logger.warning(f"Client {request.sid} tried to join invalid or expired room: {sim_id}")

socketio.on_namespace(LiveSimulationNamespace('/live'))

def _run_simulation_background(app, sim_id, scenario_json):
    """The background task that runs the simulation and emits updates."""
    with app.app_context():
        sim_manager = None
        try:
            builder = SimulationBuilder()
            scenario_config = json.loads(scenario_json)

            builder.set_simulation_params(**scenario_config.get('simulation_params', {}))
            for name, comp in scenario_config.get('components', {}).items():
                builder.add_component(name, comp.get('type'), comp.get('params', {}))
            for conn in scenario_config.get('connections', []):
                builder.add_connection(conn.get('source'), conn.get('target'))
            builder.set_execution_order(scenario_config.get('execution_order', []))
            builder.configure_logger(scenario_config.get('logger_config', []))

            sdk_config = builder.build()
            sim_manager = SimulationManager(config=sdk_config)
            active_simulations[sim_id] = sim_manager

            while sim_manager.is_running():
                sim_manager.run_step({})
                socketio.emit('simulation_update', sim_manager.current_results, room=sim_id, namespace='/live')
                socketio.sleep(sim_manager.dt)

            final_results_df = sim_manager.get_results()
            # TODO: Persist final results to the database. This requires passing project_id.

            socketio.emit('simulation_end', {'results': final_results_df.to_dict(orient='records')}, room=sim_id, namespace='/live')

        except Exception as e:
            app.logger.error(f"Error in background simulation {sim_id}: {e}", exc_info=True)
            socketio.emit('simulation_error', {'error': str(e)}, room=sim_id, namespace='/live')
        finally:
            if sim_id in active_simulations:
                del active_simulations[sim_id]
            app.logger.info(f"Simulation {sim_id} finished and cleaned up.")


@app.route('/api/projects/<int:project_id>/run_live', methods=['POST'])
def run_live_simulation(project_id):
    """
    Starts a simulation in the background and returns a simulation ID
    for clients to subscribe to real-time updates via WebSocket.
    """
    project = Project.query.get_or_404(project_id)
    sim_id = f"sim_{project_id}_{uuid.uuid4()}"

    socketio.start_background_task(
        target=_run_simulation_background,
        app=app,
        sim_id=sim_id,
        scenario_json=project.scenario_json
    )

    return jsonify({"status": "success", "simulation_id": sim_id})

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5001, allow_unsafe_werkzeug=True)
