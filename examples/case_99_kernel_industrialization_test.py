import time
import pprint
from chs_sdk.core.host import AgentKernel
from chs_sdk.agents.base_agent import BaseAgent
from chs_sdk.agents.message import Message
from chs_sdk.agents.management_agents import (
    LifecycleManagerAgent,
    MonitoringAgent,
    TOPIC_CMD_LIFECYCLE_RESTART,
    TOPIC_SYS_MONITORING_PERFORMANCE,
)
from chs_sdk.utils.logger import log


# --- Agent Definitions for Testing ---

class StableAgent(BaseAgent):
    """A simple agent that runs without errors."""
    def execute(self, current_time: float):
        log.info(f"'{self.agent_id}' executing at {current_time:.2f}s.")
        time.sleep(0.01) # Simulate some work
        self._publish("system.test.topic", {"data": "some value"})

    def on_message(self, message: Message):
        log.info(f"'{self.agent_id}' received message on topic '{message.topic}'.")

class FaultyAgent(BaseAgent):
    """An agent designed to fail after a few executions."""
    def __init__(self, agent_id: str, kernel: 'AgentKernel', **config):
        super().__init__(agent_id, kernel, **config)
        self.fail_at_time = config.get("fail_at_time", 5.0)
        self.execution_count = 0

    def execute(self, current_time: float):
        self.execution_count += 1
        if current_time >= self.fail_at_time:
            log.warning(f"'{self.agent_id}' is about to fail intentionally.")
            raise RuntimeError(f"Intentional failure in {self.agent_id} at time {current_time}!")

        log.info(f"'{self.agent_id}' executing (run #{self.execution_count}) at {current_time:.2f}s. Will fail at t>={self.fail_at_time}s.")
        time.sleep(0.02) # Simulate more work

    def on_message(self, message: Message):
        pass

class PerformanceMonitorLogger(BaseAgent):
    """Subscribes to the performance monitoring topic and logs the results."""
    def setup(self):
        self.kernel.message_bus.subscribe(self, TOPIC_SYS_MONITORING_PERFORMANCE)

    def execute(self, current_time: float):
        pass # Purely reactive

    def on_message(self, message: Message):
        log.info("--- Performance Report Received ---")
        pprint.pprint(message.payload)
        log.info("------------------------------------")


# --- Main Test Runner ---

def run_industrial_kernel_test():
    """
    Demonstrates the features of the industrialized AgentKernel V2.
    """
    log.info("--- Starting AgentKernel V2 Demonstration ---")

    # 1. Initialize Kernel
    kernel = AgentKernel()

    # 2. Register Management Agents
    kernel.add_agent(LifecycleManagerAgent, "lifecycle_manager")
    kernel.add_agent(MonitoringAgent, "perf_monitor", publish_interval=3.0)

    # 3. Register Application Agents
    kernel.add_agent(StableAgent, "stable_agent_1")
    kernel.add_agent(FaultyAgent, "faulty_agent_1", fail_at_time=4.0)
    kernel.add_agent(PerformanceMonitorLogger, "perf_logger")

    # 4. Start the kernel for tick-based execution
    kernel.start(time_step=1.0)

    # 5. Run ticks until the agent fails
    log.info("\n>>> Running simulation tick-by-tick until agent fails.\n")
    fault_detected_time = -1
    for i in range(5): # Run for 5 ticks, failure should be at tick 4
        log.info(f"--- Tick {i} (Current Time: {kernel.current_time:.2f}s) ---")
        kernel.tick()
        if kernel._agents["faulty_agent_1"].status.name == 'FAULT':
            fault_detected_time = kernel.current_time
            log.info(f"Agent 'faulty_agent_1' has failed as expected at time {fault_detected_time:.2f}s.")
            break

    # 6. Verify agent status after failure
    log.info("\n--- Agent Statuses After Failure ---")
    faulty_agent_status = kernel._agents["faulty_agent_1"].status
    for agent_id, agent in kernel._agents.items():
        log.info(f"Agent '{agent_id}' status: {agent.status.name}")
    log.info("------------------------------------")
    assert faulty_agent_status.name == 'FAULT', f"Expected FAULT, got {faulty_agent_status.name}"
    log.info("Assertion successful: faulty_agent_1 is in FAULT state.")

    # 7. Issue a restart command for the faulty agent
    log.info("\n>>> Publishing restart command for 'faulty_agent_1'.\n")
    restart_msg = Message(
        topic=TOPIC_CMD_LIFECYCLE_RESTART,
        sender_id="system_admin",
        payload={"agent_id": "faulty_agent_1"}
    )
    kernel.message_bus.publish(restart_msg)
    kernel.tick() # Tick once more to process the restart message

    # 8. Verify the agent is running again
    log.info("\n--- Agent Statuses After Restart ---")
    restarted_agent_status = kernel._agents["faulty_agent_1"].status
    for agent_id, agent in kernel._agents.items():
        log.info(f"Agent '{agent_id}' status: {agent.status.name}")
    log.info("------------------------------------")
    assert restarted_agent_status.name == 'RUNNING', f"Expected RUNNING, got {restarted_agent_status.name}"
    log.info("Assertion successful: faulty_agent_1 is RUNNING again.")

    # 9. Run a few more ticks to see the restarted agent in action
    log.info("\n>>> Running a few more ticks...\n")
    for i in range(3):
        kernel.tick()

    # 10. Final shutdown
    kernel.stop()
    log.info("\n--- Kernel V2 Demonstration Finished Successfully! ---")


if __name__ == "__main__":
    run_industrial_kernel_test()
