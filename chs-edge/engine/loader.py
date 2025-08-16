from chs_sdk.agents.control import PIDControlAgent
from chs_sdk.modules.control import PIDController

def load_agent(model_path: str):
    # 打印路径以模拟加载
    print(f"Loading agent from: {model_path}")
    # MVP: 返回一个硬编码的PID智能体
    pid_module = PIDController(setpoint=20.0, kp=0.5, ki=0.1, kd=0.05)
    return PIDControlAgent(agent_id='pid_edge_1', pid_instance=pid_module)
