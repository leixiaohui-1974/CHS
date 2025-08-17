from chs_sdk.agents.base import BaseAgent
from chs_sdk.utils.logger import log

class DebugAgent(BaseAgent):
    def setup(self):
        log.info(f"DebugAgent '{self.agent_id}' setup.")

    def execute(self, current_time: float):
        log.info(f"DebugAgent '{self.agent_id}' executing at time {current_time}.")
