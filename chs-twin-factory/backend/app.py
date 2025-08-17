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

# --- Flask App Initialization ---
app = Flask(__name__)
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

# --- Simulation Constants ---
TIME_STEP = 1.0     # seconds
DISCHARGE_COEFF = 0.6
INFLOW_RATE = 50.0 # m^3/s

@app.route('/api/projects/<int:project_id>/run', methods=['POST'])
def run_project_simulation(project_id):
    project = Project.query.get_or_404(project_id)
    sim_config = json.loads(project.scenario_json)

    try:
        results_data = execute_simulation(sim_config)

        simulation_run = SimulationRun(
            project_id=project.id,
            results_json=json.dumps(results_data)
        )
        db.session.add(simulation_run)
        db.session.commit()

        return jsonify({"status": "success", "data": results_data})
    except Exception as e:
        app.logger.error(f"An error occurred during simulation for project {project_id}: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/projects/<int:project_id>/runs', methods=['GET'])
def get_project_runs(project_id):
    project = Project.query.get_or_404(project_id)
    runs = SimulationRun.query.filter_by(project_id=project.id).order_by(SimulationRun.run_timestamp.desc()).all()
    return jsonify([run.to_dict() for run in runs])


def execute_simulation(sim_config):
    """
    Core simulation logic, refactored to be reusable.
    """
    # 1. Extract parameters from the config
    components = sim_config.get('components', {})
    reservoir_params = components.get('reservoir', {})
    sluice_gate_params = components.get('sluice_gate', {})
    controller_params = sim_config.get('controller', {})
    simulation_params = sim_config.get('simulation_params', {})

    initial_level = reservoir_params.get('initial_level', 10.0)
    reservoir_area = reservoir_params.get('area_storage_curve_coeff', 1000.0)
    gate_width = sluice_gate_params.get('width', 5.0)
    target_level = controller_params.get('target_level', 12.0)
    duration_hours = simulation_params.get('duration_hours', 0.055)
    sim_duration_seconds = duration_hours * 3600

    # 2. Initialize Agent Kernel
    kernel = AgentKernel()

    # 3. Define Topics
    topic_inflow = "data.inflow.constant"
    topic_level = "state.reservoir.level"
    topic_gate_control = "control.gate.opening"
    topic_gate_flow = "state.gate.flow"

    # 4. Add Agents
    kernel.add_agent(
        agent_class=InflowAgent,
        agent_id="inflow_provider",
        topic=topic_inflow,
        rainfall_pattern=[INFLOW_RATE]
    )
    kernel.add_agent(
        agent_class=TankAgent,
        agent_id="main_reservoir",
        area=reservoir_area,
        initial_level=initial_level,
        inflow_topic=topic_inflow,
        release_outflow_topic=topic_gate_flow,
        state_topic=topic_level
    )
    kernel.add_agent(
        agent_class=GateAgent,
        agent_id="main_gate",
        num_gates=1,
        gate_width=gate_width,
        discharge_coeff=DISCHARGE_COEFF,
        upstream_topic=topic_level,
        downstream_topic="data.boundary.downstream_level",
        opening_topic=topic_gate_control,
        state_topic=topic_gate_flow
    )
    kernel.add_agent(
        agent_class=RuleBasedAgent,
        agent_id="rule_controller",
        level_topic=topic_level,
        gate_topic=topic_gate_control,
        set_point=target_level
    )
    kernel.add_agent(
        agent_class=DataCaptureAgent,
        agent_id="data_logger",
        topics_to_log=["#"]
    )
    kernel.add_agent(
        agent_class=InflowAgent,
        agent_id="downstream_level_provider",
        topic="data.boundary.downstream_level",
        rainfall_pattern=[0.0]
    )
    # 5. Run Simulation
    sim_thread = threading.Thread(target=kernel.run, kwargs={'duration': sim_duration_seconds, 'time_step': TIME_STEP})
    sim_thread.start()
    sim_thread.join() # Wait for the simulation to complete

    # 6. Process and Return Results
    data_logger = kernel._agents["data_logger"]
    captured_data = data_logger.get_data()
    df = pd.DataFrame(captured_data)

    def extract_payload(payload, key):
        if hasattr(payload, 'dict'):
            payload = payload.dict()
        return payload.get(key) if isinstance(payload, dict) else None

    level_series = df[df['topic'] == topic_level].set_index('time')['payload'].apply(lambda p: extract_payload(p, 'level')).rename('level')
    inflow_series = df[df['topic'] == topic_inflow].set_index('time')['payload'].apply(lambda p: extract_payload(p, 'value')).rename('inflow')
    outflow_series = df[df['topic'] == topic_gate_flow].set_index('time')['payload'].apply(lambda p: extract_payload(p, 'flow')).rename('outflow')

    results_df = pd.concat([level_series, inflow_series, outflow_series], axis=1).ffill().bfill().reset_index()
    results_df = results_df.rename(columns={'index': 'time'})
    results_df = results_df.astype({'time': 'float', 'level': 'float', 'inflow': 'float', 'outflow': 'float'}).fillna(0)

    return {
        "time": results_df['time'].round(1).tolist(),
        "level": results_df['level'].round(2).tolist(),
        "inflow": results_df['inflow'].round(2).tolist(),
        "outflow": results_df['outflow'].round(2).tolist()
    }

@app.route('/api/run_simulation', methods=['POST'])
def run_simulation():
    """
    Legacy endpoint to run a simulation without creating a project.
    """
    sim_config = request.get_json()
    if not sim_config:
        return jsonify({"status": "error", "message": "Invalid JSON payload"}), 400
    try:
        results_data = execute_simulation(sim_config)
        return jsonify({"status": "success", "data": results_data})
    except Exception as e:
        app.logger.error(f"An error occurred during simulation: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
