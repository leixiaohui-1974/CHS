import gymnasium as gym
from gymnasium import spaces
import numpy as np
import json

# Assuming CHS_SDK can be imported this way.
# The actual path might need adjustment during integration.
from water_system_sdk.src.chs_sdk.main import CHS_SDK


class ChsEnv(gym.Env):
    """Custom Environment for CHS-SDK that follows the gymnasium interface."""
    metadata = {'render_modes': ['human']}

    def __init__(self, scenario_json: str):
        super().__init__()

        self.scenario_config = json.loads(scenario_json)
        self.sdk = CHS_SDK(self.scenario_config)

        # --- Define action and observation space ---
        # The spaces are defined dynamically based on the scenario config.
        # This is a simplified example assuming specific keys in the config.

        # Example Action Space: Control the outflow of the first controllable component.
        # In a real implementation, you would parse config['control']
        action_low = np.array([0.0], dtype=np.float32)
        action_high = np.array([100.0], dtype=np.float32) # Assuming a max_flow of 100
        self.action_space = spaces.Box(low=action_low, high=action_high, dtype=np.float32)

        # Example Observation Space: Observe the level of the first reservoir.
        # In a real implementation, you would parse config['components']
        obs_low = np.array([80.0], dtype=np.float32) # Assuming min_level
        obs_high = np.array([100.0], dtype=np.float32) # Assuming max_level
        self.observation_space = spaces.Box(low=obs_low, high=obs_high, dtype=np.float32)

        self.target_level = 95.0 # Example target level for reward

    def _get_obs(self):
        """Helper function to get the current observation from the SDK."""
        state = self.sdk.get_current_state()
        # This is highly dependent on the scenario's component IDs.
        # This should be made more robust.
        # Assuming the first component is the reservoir we want to observe.
        first_component_id = list(state.keys())[0]
        level = state[first_component_id].get('level', self.target_level)
        return np.array([level], dtype=np.float32)

    def _get_info(self):
        """Helper function to get diagnostic information."""
        return {}

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        # Re-initialize the SDK to reset the simulation state
        self.sdk = CHS_SDK(self.scenario_config)

        observation = self._get_obs()
        info = self._get_info()

        return observation, info

    def step(self, action):
        # --- Map action to SDK's expected format ---
        # This is also dependent on the scenario config.
        # Assuming the action controls the outflow of the first controllable component.
        control_config = self.scenario_config.get('control', [])
        if not control_config:
            raise ValueError("No control defined in the scenario config.")

        target_component_id = control_config[0]['component_id']
        target_variable = control_config[0]['variable']

        sdk_action = {
            target_component_id: {
                target_variable: float(action[0])
            }
        }

        # --- Run one timestep in the simulation ---
        self.sdk.run_step(sdk_action)

        # --- Get the new state (observation) ---
        observation = self._get_obs()

        # --- Calculate reward ---
        # Reward is higher the closer the level is to the target level.
        level = observation[0]
        reward = -np.abs(level - self.target_level)

        # --- Check for termination ---
        # For simplicity, we don't terminate the episode here.
        # In a real scenario, this could be based on reaching a critical level.
        terminated = False
        truncated = False # For when the episode is ended by a time limit

        info = self._get_info()

        return observation, reward, terminated, truncated, info

    def render(self, mode='human'):
        # For now, we'll just print the current state
        if mode == 'human':
            obs = self._get_obs()
            print(f"Current Level: {obs[0]}")

    def close(self):
        pass


from stable_baselines3.common.monitor import Monitor


def create_chs_env(scenario_json: str, log_dir: str = None) -> gym.Env:
    """
    Factory function to create an instance of the ChsEnv.
    """
    env = ChsEnv(scenario_json)
    # Wrap the environment with a Monitor to log statistics
    env = Monitor(env, filename=log_dir)
    return env
