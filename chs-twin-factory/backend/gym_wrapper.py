import gymnasium as gym
from gymnasium import spaces
import numpy as np
import json
from collections import OrderedDict

# Correctly import the SDK components I created and refactored
from chs_sdk.simulation_manager import SimulationManager
from chs_sdk.simulation_builder import SimulationBuilder


class ChsEnv(gym.Env):
    """
    A dynamically configurable Gymnasium Environment for the CHS-SDK.

    This environment parses a `scenario_json` to configure its observation
    space, action space, and reward function, allowing it to adapt to
    various simulation scenarios without code changes.
    """
    metadata = {'render_modes': ['human']}

    def __init__(self, scenario_json: str, log_dir: str = None):
        super().__init__()

        self.scenario_config = json.loads(scenario_json)
        self._parse_config()

        # Create a reusable builder instance
        self.builder = SimulationBuilder()
        self.sim_manager = None  # Will be initialized in reset()

    def _parse_config(self):
        """Parses the scenario config to define spaces and reward."""
        if 'rl_config' not in self.scenario_config:
            raise ValueError("Scenario config must contain 'rl_config' section.")

        rl_config = self.scenario_config['rl_config']

        # --- Observation Space ---
        self.observation_keys = OrderedDict(rl_config['observation_space'])
        obs_low = np.array([v['low'] for v in self.observation_keys.values()], dtype=np.float32)
        obs_high = np.array([v['high'] for v in self.observation_keys.values()], dtype=np.float32)
        self.observation_space = spaces.Box(low=obs_low, high=obs_high, dtype=np.float32)

        # --- Action Space ---
        self.action_keys = OrderedDict(rl_config['action_space'])
        action_low = np.array([v['low'] for v in self.action_keys.values()], dtype=np.float32)
        action_high = np.array([v['high'] for v in self.action_keys.values()], dtype=np.float32)
        self.action_space = spaces.Box(low=action_low, high=action_high, dtype=np.float32)

        # --- Reward Function ---
        self.reward_config = rl_config['reward']

        # --- Truncation ---
        self.max_steps = rl_config.get('max_steps_per_episode', 1000)
        self.current_step = 0

    def _get_obs(self):
        """Extracts the observation vector from the full simulation state."""
        if not self.sim_manager or not self.sim_manager.current_results:
            return np.zeros(self.observation_space.shape, dtype=np.float32)

        latest_results = self.sim_manager.current_results
        obs_vector = np.array(
            [latest_results.get(key, 0.0) for key in self.observation_keys.keys()],
            dtype=np.float32
        )
        return obs_vector

    def _calculate_reward(self, observation_vector: np.ndarray) -> float:
        """Calculates the reward based on the configured logic."""
        obs_dict = {name: observation_vector[i] for i, name in enumerate(self.observation_keys.keys())}

        total_reward = 0.0
        for reward_part in self.reward_config:
            if reward_part['type'] == 'distance_to_target':
                target_val = reward_part['target']
                actual_val = obs_dict.get(reward_part['variable'])
                if actual_val is not None:
                    # Use a negative quadratic to encourage being close to target
                    error = (target_val - actual_val) * reward_part.get('scale', 1.0)
                    total_reward -= error**2 * reward_part['weight']
            # Add other reward types here (e.g., 'energy_cost')

        return total_reward

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step = 0

        # Build the simulation config from the scenario using the builder
        # This part assumes the scenario_config has the right structure for the builder
        sdk_config = self.builder.set_simulation_params(**self.scenario_config['simulation_params'])
        for name, comp in self.scenario_config['components'].items():
            self.builder.add_component(name, comp['type'], comp['params'])
        for conn in self.scenario_config['connections']:
            self.builder.add_connection(conn['source'], conn['target'])
        self.builder.set_execution_order(self.scenario_config['execution_order'])
        self.builder.configure_logger(self.scenario_config['logger_config'])

        # Initialize the simulation manager
        self.sim_manager = SimulationManager(config=self.builder.build())

        # Run one step to get initial state
        self.sim_manager.run_step({})

        observation = self._get_obs()
        info = {} # No extra info on reset

        return observation, info

    def step(self, action):
        self.current_step += 1

        # Map the agent's action vector to the SDK's expected input format
        sdk_action = {key: float(action[i]) for i, key in enumerate(self.action_keys.keys())}

        # Run one timestep in the simulation
        self.sim_manager.run_step(sdk_action)

        # Get results
        observation = self._get_obs()
        reward = self._calculate_reward(observation)

        # Check for termination and truncation
        terminated = False # Termination logic (e.g., critical failure) can be added here
        truncated = self.current_step >= self.max_steps

        info = {}

        return observation, reward, terminated, truncated, info

    def render(self, mode='human'):
        if mode == 'human':
            obs = self._get_obs()
            print(f"Step: {self.current_step}, Observation: {obs}")

    def close(self):
        self.sim_manager = None


from stable_baselines3.common.monitor import Monitor

def create_chs_env(scenario_json: str, log_dir: str = None) -> gym.Env:
    """
    Factory function to create and wrap an instance of the ChsEnv.
    """
    env = ChsEnv(scenario_json, log_dir)
    if log_dir:
        env = Monitor(env, filename=log_dir)
    return env
