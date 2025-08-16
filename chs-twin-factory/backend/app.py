import pandas as pd
from flask import Flask, jsonify, request, send_from_directory

# --- V2 SDK Imports ---
# Core
from chs_sdk.core.host import AgentKernel
from chs_sdk.agents.message import Message

# Agent Classes
from chs_sdk.agents.body_agents import TankAgent, GateAgent
from chs_sdk.agents.disturbance_agents import InflowAgent
from chs_sdk.agents.management_agents import DataCaptureAgent
from rule_based_agent import RuleBasedAgent # Local custom agent

# Point to the built React app
app = Flask(__name__, static_folder='../../chs-hmi/build', static_url_path='/')

# --- Simulation Constants ---
TIME_STEP = 1.0     # seconds
DISCHARGE_COEFF = 0.6
INFLOW_RATE = 50.0 # m^3/s

@app.route('/api/run_simulation', methods=['POST'])
def run_simulation():
    """
    This endpoint runs a CHS-SDK v2.0 simulation based on dynamic parameters
    provided in a JSON payload.
    """
    try:
        # 1. Get parameters from the request body
        sim_config = request.get_json()
        if not sim_config:
            return jsonify({"status": "error", "message": "Invalid JSON payload"}), 400

        # Extract parameters with defaults
        components = sim_config.get('components', {})
        reservoir_params = components.get('reservoir', {})
        sluice_gate_params = components.get('sluice_gate', {})
        controller_params = sim_config.get('controller', {})
        simulation_params = sim_config.get('simulation_params', {})

        initial_level = reservoir_params.get('initial_level', 10.0)
        reservoir_area = reservoir_params.get('area_storage_curve_coeff', 1000.0)
        gate_width = sluice_gate_params.get('width', 5.0)
        target_level = controller_params.get('target_level', 12.0)
        duration_hours = simulation_params.get('duration_hours', 0.055) # Default to ~200 seconds

        sim_duration_seconds = duration_hours * 3600

        # 2. Initialize Agent Kernel (V2)
        kernel = AgentKernel()

        # 3. Define Topics for Agent Communication
        topic_inflow = "data.inflow.constant"
        topic_level = "state.reservoir.level"
        topic_gate_control = "control.gate.opening"
        topic_gate_flow = "state.gate.flow"

        # 4. Add Agents to Kernel using the V2 pattern
        kernel.add_agent(
            agent_class=InflowAgent,
            agent_id="inflow_provider",
            topic=topic_inflow,
            rainfall_pattern=[INFLOW_RATE] # Use a constant pattern
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
            downstream_topic="data.boundary.downstream_level", # Assume constant downstream level
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

        # This agent will capture all data for later analysis
        kernel.add_agent(
            agent_class=DataCaptureAgent,
            agent_id="data_logger",
            topics_to_log=["#"] # Log all topics
        )

        # Add a dummy agent to provide the downstream level for the gate
        kernel.add_agent(
            agent_class=InflowAgent,
            agent_id="downstream_level_provider",
            topic="data.boundary.downstream_level",
            rainfall_pattern=[0.0] # Constant 0 level
        )


        # 5. Run the simulation via the Kernel
        kernel.run(duration=sim_duration_seconds, time_step=TIME_STEP)

        # 6. Process and Return Results
        data_logger = kernel._agents["data_logger"] # Get the agent instance from the kernel
        captured_data = data_logger.get_data()
        df = pd.DataFrame(captured_data)

        # --- DEBUG ---
        app.logger.info("--- DEBUG ---")
        app.logger.info(f"Captured Data Sample: {captured_data[:5]}")
        app.logger.info(f"DataFrame Columns: {df.columns}")
        app.logger.info("--- END DEBUG ---")
        # --- END DEBUG ---

        # Helper to extract payload values safely
        def extract_payload(payload, key):
            # The new SDK wraps payloads in a Pydantic model, so we need to handle that
            if hasattr(payload, 'dict'):
                payload = payload.dict()
            return payload.get(key) if isinstance(payload, dict) else None

        # Pivot the data to get one row per timestamp
        level_series = df[df['topic'] == topic_level].set_index('time')['payload'].apply(lambda p: extract_payload(p, 'level')).rename('level')
        inflow_series = df[df['topic'] == topic_inflow].set_index('time')['payload'].apply(lambda p: extract_payload(p, 'value')).rename('inflow')
        outflow_series = df[df['topic'] == topic_gate_flow].set_index('time')['payload'].apply(lambda p: extract_payload(p, 'flow')).rename('outflow')

        # Combine the series into a single DataFrame
        results_df = pd.concat([level_series, inflow_series, outflow_series], axis=1).ffill().bfill().reset_index()
        results_df = results_df.rename(columns={'index': 'time'})

        # Ensure correct data types and fill NaNs
        results_df = results_df.astype({'time': 'float', 'level': 'float', 'inflow': 'float', 'outflow': 'float'}).fillna(0)

        # Format for JSON response
        response_data = {
            "time": results_df['time'].round(1).tolist(),
            "level": results_df['level'].round(2).tolist(),
            "inflow": results_df['inflow'].round(2).tolist(),
            "outflow": results_df['outflow'].round(2).tolist()
        }

        return jsonify({"status": "success", "data": response_data})

    except Exception as e:
        # Log the exception for debugging
        app.logger.error(f"An error occurred during simulation: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.errorhandler(404)
def not_found(e):
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=False, port=5001)
