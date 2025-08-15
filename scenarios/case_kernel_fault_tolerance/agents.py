# scenarios/case_kernel_fault_tolerance/agents.py
import time
from chs_sdk.agents.base_agent import BaseAgent

class DummyAgent(BaseAgent):
    """一个行为正常的智能体，用于验证系统在其他智能体故障时仍能继续运行。"""
    def execute(self, current_time: float):
        print(f"[{current_time:.2f}s] DummyAgent ({self.agent_id}): I am running normally.")

class FaultyAgent(BaseAgent):
    """一个会故意失败的智能体，用于测试内核的容错能力。"""
    def __init__(self, agent_id, kernel, **config):
        super().__init__(agent_id, kernel, **config)
        self.fail_at_tick = self.config.get("fail_at_tick", 3)
        self._tick_count = 0

    def execute(self, current_time: float):
        self._tick_count += 1
        if self._tick_count >= self.fail_at_tick:
            raise ValueError(f"This is an intentional failure from FaultyAgent ({self.agent_id})!")

        print(f"[{current_time:.2f}s] FaultyAgent ({self.agent_id}): I am about to fail in {self.fail_at_tick - self._tick_count} steps...")
