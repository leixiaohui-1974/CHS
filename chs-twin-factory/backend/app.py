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

# --- Flask App Initialization ---
app = Flask(__name__)
# Determine the absolute path for the instance folder
instance_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'instance'))
os.makedirs(instance_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(instance_path, "projects.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


# --- Database Models ---
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    scenario_json = db.Column(db.Text, nullable=False)
    simulation_runs = db.relationship('SimulationRun', backref='project', lazy=True, cascade="all, delete-orphan")

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
