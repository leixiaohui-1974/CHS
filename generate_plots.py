import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# This script is based on the self-contained example from advanced_mpc.md
# It has been adapted to generate plots for the mocked interactive tutorial.

# Mock Agent and Model from the tutorial
class MPControlAgent:
    def __init__(self, agent_id, **kwargs):
        self.agent_id = agent_id
        self.params = kwargs
        self.target = None
        print(f"MPControlAgent '{self.agent_id}' created.")

    def set_target(self, target):
        self.target = target
        print(f"Target set to: {self.target}")

    def compute_action(self, current_state):
        if self.target is None:
            return np.zeros(self.params['action_dim'])
        error = self.target - current_state
        action = error * 0.5
        action_bounds = self.params['action_bounds']
        action = np.clip(action, action_bounds[:, 0], action_bounds[:, 1])
        return action

def reservoir_model(state, action, params):
    dt = params.get('dt', 1.0)
    area = params.get('area', 100.0)
    current_level = state[0]
    inflow_rate = action[0]
    level_change = (inflow_rate * dt) / area
    next_level = current_level + level_change
    return np.array([next_level])

def generate_plot_for_setpoint(setpoint_val, filename):
    print(f"\n--- Generating plot for setpoint {setpoint_val} ---")

    mpc_params = {
        'prediction_horizon': 10, 'control_horizon': 3, 'state_dim': 1, 'action_dim': 1,
        'model_function': reservoir_model, 'model_params': {'dt': 1, 'area': 100},
        'state_bounds': np.array([[90, 115]]), # Increased upper bound for level 21
        'action_bounds': np.array([[-10, 10]]),
        'Q': np.diag([10.0]), 'R': np.diag([1.0]),
    }

    mpc_agent = MPControlAgent(agent_id="reservoir_mpc_agent", **mpc_params)
    setpoint = np.array([setpoint_val])
    mpc_agent.set_target(setpoint)

    current_state = np.array([95.0])
    history = [{'time': 0, 'level': current_state[0], 'action': 0}]

    for t in range(48): # Longer simulation to show stabilization
        action = mpc_agent.compute_action(current_state)
        next_state = reservoir_model(current_state, action, mpc_params['model_params'])
        state_bounds = mpc_params['state_bounds']
        next_state = np.clip(next_state, state_bounds[:, 0], state_bounds[:, 1])
        current_state = next_state
        history.append({'time': t + 1, 'level': current_state[0], 'action': action[0]})

    df = pd.DataFrame(history)

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df['time'], df['level'], 'b-', label='Simulated Water Level')
    ax.axhline(setpoint_val, color='r', linestyle='--', label=f'Target Level ({setpoint_val}m)')
    ax.set_xlabel('Time Step (hours)')
    ax.set_ylabel('Water Level (m)')
    ax.set_title(f'Reservoir Water Level Control (Target: {setpoint_val}m)')
    ax.legend()
    ax.grid(True)

    plt.tight_layout()
    fig.savefig(filename)
    print(f"Plot saved to {filename}")
    plt.close(fig)

if __name__ == "__main__":
    # Ensure the target directory exists
    import os
    output_dir = "chs-knowledge-hub/docs/assets/images"
    os.makedirs(output_dir, exist_ok=True)

    # Generate the two required plots
    generate_plot_for_setpoint(20.0, os.path.join(output_dir, "result_default.png"))
    generate_plot_for_setpoint(21.0, os.path.join(output_dir, "result_level_21.png"))
    print("\nAll plots generated successfully.")
