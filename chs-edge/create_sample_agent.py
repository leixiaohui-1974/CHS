import pickle
import json
import zipfile
import os
from chs_sdk.agents.control import PIDControlAgent
from chs_sdk.modules.control import PIDController

def create_sample_agent():
    """
    Creates a sample .agent file for testing purposes.
    """
    # 1. Create a sample agent instance
    pid_module = PIDController(setpoint=100.0, kp=0.5, ki=0.1, kd=0.05)
    agent = PIDControlAgent(agent_id='sample_pid_agent_01', pid_instance=pid_module)

    # 2. Define the agent configuration
    config = {
        "agent_class": "PIDControlAgent",
        "model_file": "model.pkl",
        "description": "A sample PID control agent."
    }

    # 3. Save the agent and config to files
    with open("model.pkl", "wb") as f:
        pickle.dump(agent, f)

    with open("config.json", "w") as f:
        json.dump(config, f, indent=4)

    # 4. Create the .agent zip archive
    with zipfile.ZipFile("sample_agent.agent", 'w') as zipf:
        zipf.write("model.pkl")
        zipf.write("config.json")

    print("Created sample_agent.agent successfully.")

    # Clean up the individual files
    os.remove("model.pkl")
    os.remove("config.json")

if __name__ == "__main__":
    create_sample_agent()
