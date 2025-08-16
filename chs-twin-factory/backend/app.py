import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'water_system_sdk', 'src')))

import pandas as pd
from flask import Flask, jsonify, send_from_directory

from chs_sdk.core.host import AgentKernel
from chs_sdk.core.message import Message
from chs_sdk.modules.modeling.storage_models import LinearTank
from chs_sdk.modules.modeling.control_structure_models import SluiceGate
from chs_sdk.agents.disturbance_agents import DisturbanceAgent
from chs_sdk.agents.management_agents import DataCaptureAgent
from rule_based_agent import RuleBasedAgent

# Point to the built React app
app = Flask(__name__, static_folder='../../chs-hmi/build', static_url_path='/')

# --- Simulation setup constants ---
SIM_DURATION = 200  # seconds
TIME_STEP = 1.0     # seconds
RESERVOIR_AREA = 1000.0 # m^2
INITIAL_LEVEL = 10.0 # m
GATE_WIDTH = 5.0 # m
DISCHARGE_COEFF = 0.6
SET_POINT = 12.0 # Target water level for the agent

# --- Topic Names ---
TOPIC_INFLOW = "disturbance.inflow"
TOPIC_LEVEL = "sensor.reservoir.level"
TOPIC_GATE_CONTROL = "control.gate.opening"
TOPIC_GATE_FLOW = "sensor.gate.flow"

@app.route('/api/run_simulation', methods=['POST'])
def run_simulation():
    """
    This endpoint runs a hardcoded CHS-SDK simulation and returns the results.
    """
    try:
        # 1. Initialize Agent Kernel
        kernel = AgentKernel(time_step=TIME_STEP)

        # 2. Define Physical Components
        reservoir = LinearTank(
            area=RESERVOIR_AREA,
            initial_level=INITIAL_LEVEL,
            name="main_reservoir"
        )
        gate = SluiceGate(
            gate_width=GATE_WIDTH,
            discharge_coeff=DISCHARGE_COEFF,
            name="main_gate"
        )

        # 3. Define Agents
        # This agent provides a constant inflow disturbance
        inflow_agent = DisturbanceAgent(
            agent_id="inflow_provider",
            kernel=kernel,
            topic_to_publish=TOPIC_INFLOW,
            value_to_publish={"value": 50.0} # Constant inflow of 50 m^3/s
        )

        # The rule-based agent to control the gate
        control_agent = RuleBasedAgent(
            agent_id="rule_controller",
            kernel=kernel,
            level_topic=TOPIC_LEVEL,
            gate_topic=TOPIC_GATE_CONTROL,
            set_point=SET_POINT
        )

        # This agent will capture all data for later analysis
        data_logger = DataCaptureAgent(
            agent_id="data_logger",
            kernel=kernel,
            topics_to_log=["#"] # Log all topics
        )

        # 4. Register Agents with the Kernel
        kernel.add_agent(inflow_agent)
        kernel.add_agent(control_agent)
        kernel.add_agent(data_logger)

        # 5. Main Simulation Loop
        kernel.start(time_step=TIME_STEP)
        while kernel.current_time < SIM_DURATION:
            # Get messages from the bus
            inflow_msg = kernel.message_bus.get_message(TOPIC_INFLOW)
            gate_cmd_msg = kernel.message_bus.get_message(TOPIC_GATE_CONTROL)

            # Update gate opening based on agent command
            if gate_cmd_msg:
                gate.set_opening(gate_cmd_msg.payload.get("value", 0.0))

            # Update reservoir level
            inflow_value = inflow_msg.payload.get("value", 0.0) if inflow_msg else 0.0
            reservoir.input.inflow = inflow_value
            reservoir.input.release_outflow = gate.output # Outflow from previous step
            reservoir.step(dt=TIME_STEP)

            # Update gate flow for the next step
            # Downstream level is assumed to be 0 for simplicity
            gate.step(upstream_level=reservoir.output, downstream_level=0, dt=TIME_STEP)

            # Publish sensor and state data
            kernel.message_bus.publish(Message(sender_id="system", topic=TOPIC_LEVEL, payload={"level": reservoir.output}))
            kernel.message_bus.publish(Message(sender_id="system", topic=TOPIC_GATE_FLOW, payload={"flow": gate.output}))

            kernel.tick()

        kernel.stop()

        # 6. Process and Return Results
        captured_data = data_logger.get_data()
        df = pd.DataFrame(captured_data)

        # Helper to extract payload values safely
        def extract_payload(payload, key):
            return payload.get(key) if isinstance(payload, dict) else None

        # Pivot the data to get one row per timestamp
        level_series = df[df['topic'] == TOPIC_LEVEL].set_index('time')['payload'].apply(lambda p: extract_payload(p, 'level')).rename('level')
        inflow_series = df[df['topic'] == TOPIC_INFLOW].set_index('time')['payload'].apply(lambda p: extract_payload(p, 'value')).rename('inflow')
        outflow_series = df[df['topic'] == TOPIC_GATE_FLOW].set_index('time')['payload'].apply(lambda p: extract_payload(p, 'flow')).rename('outflow')

        # Combine the series into a single DataFrame
        results_df = pd.concat([level_series, inflow_series, outflow_series], axis=1).ffill().bfill().reset_index()
        results_df = results_df.rename(columns={'index': 'time'})

        # Ensure correct data types and fill NaNs
        results_df = results_df.astype({'time': 'int', 'level': 'float', 'inflow': 'float', 'outflow': 'float'}).fillna(0)

        # Format for JSON response
        response_data = {
            "time": results_df['time'].tolist(),
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
    app.run(debug=True, port=5001)
