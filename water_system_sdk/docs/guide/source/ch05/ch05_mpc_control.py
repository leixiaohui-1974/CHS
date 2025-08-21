import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
import pandas as pd
import copy
import numpy as np

from chs_sdk.agents.base import BaseAgent
from chs_sdk.agents.message import Message
from chs_sdk.core.host import AgentKernel as Host
from chs_sdk.modules.modeling.storage_models import FirstOrderInertiaModel
from chs_sdk.modules.control.mpc_controller import MPCController
from water_system_sdk.docs.guide.source.project_utils import EulerMethod, ModelAgent


# ++++++++++++++ 1. 定义一个修正版的模型，解决 deepcopy 陷阱 ++++++++++++++
class FixedFirstOrderInertiaModel(FirstOrderInertiaModel):

    def __init__(self, initial_storage, time_constant, solver_class, dt, **kwargs):
        # 调用父类的 __init__，但我们不使用它创建的 solver
        super().__init__(initial_storage, time_constant, solver_class, dt, **kwargs)

        # ★★★ 关键修正 ★★★
        # 创建一个新的 solver，并把 self.ode_function (一个真正的类方法) 传给它
        self.solver = solver_class(f=self.ode_function, dt=dt)

    def ode_function(self, t, y):
        """
        这是一个真正的类方法，而不是闭包。
        这里的 'self' 将永远指向正确的实例（无论是原始的还是克隆的）。
        """
        outflow = y / self.time_constant if self.time_constant > 0 else 0
        total_inflow = self.input.inflow + self.input.control_inflow
        return total_inflow - outflow


# ++++++++++++++ 2. 定义我们之前完善好的、合规的 ControllerAgent ++++++++++++++
class ControllerAgent(BaseAgent):
    def __init__(self, agent_id, kernel, **config):
        super().__init__(agent_id, kernel, **config)
        self.model = None;
        self.current_state = None;
        self.last_control_action = 0.0

    def setup(self):
        model_class = self.config.pop('model_class');
        self.model = model_class(**self.config)

    def subscribe(self, topic: str):
        self.kernel.message_bus.subscribe(self, topic)

    def on_message(self, message: Message):
        self.current_state = message.payload

    def on_execute(self, current_time: float, time_step: float):
        if self.model is None: return
        if self.current_state is not None:
            self.last_control_action = self.model.step(current_state=self.current_state)
        self._publish(topic=f"{self.agent_id}/output", payload=self.last_control_action)


# ++++++++++++++ 3. 运行主程序 ++++++++++++++
def run_simulation():
    host = Host()

    # ★★★ 使用我们修正后的模型类 ★★★
    host.add_agent(
        agent_class=ModelAgent, agent_id='MyReservoir',
        model_class=FixedFirstOrderInertiaModel,  # <--- 使用修正后的模型
        initial_storage=10.0,
        time_constant=5.0, solver_class=EulerMethod, dt=1.0
    )

    # ★★★ 预测模型也必须使用修正后的版本 ★★★
    prediction_model_for_mpc = FixedFirstOrderInertiaModel(
        initial_storage=10.0, time_constant=5.0, solver_class=EulerMethod, dt=1.0
    )

    host.add_agent(
        agent_class=ControllerAgent, agent_id='MyMPCController',
        model_class=MPCController,
        prediction_model=prediction_model_for_mpc, prediction_horizon=10,
        control_horizon=3, set_point=15.0, q_weight=1.0, r_weight=0.1,
        u_min=0.0, u_max=20.0
    )

    reservoir_agent = host._agents['MyReservoir']
    mpc_agent = host._agents['MyMPCController']

    mpc_agent.subscribe(topic=f"{reservoir_agent.agent_id}/storage")

    # ★★★ 确保连接到正确的 control_inflow 端口 ★★★
    reservoir_agent.subscribe(topic=f"{mpc_agent.agent_id}/output", port_name='control_inflow')

    num_steps = 50;
    dt = 1.0;
    results = []
    host.start(time_step=dt)
    for i in range(num_steps):
        host.tick()
        results.append({
            'time': host.current_time,
            'reservoir_storage': reservoir_agent.model.state.storage,
            'mpc_output': mpc_agent.last_control_action
        })

    results_df = pd.DataFrame(results)
    print("仿真结果:");
    print(results_df.head())

    plt.figure(figsize=(12, 8));
    plt.subplot(2, 1, 1)
    plt.plot(results_df['time'], results_df['reservoir_storage'], label='水库蓄水量')
    plt.axhline(y=15.0, color='r', linestyle='--', label='设定值 (15.0)')
    plt.title('水库蓄水水位 (MPC控制)');
    plt.ylabel('蓄水量 (单位)');
    plt.legend();
    plt.grid(True)
    plt.subplot(2, 1, 2)
    plt.plot(results_df['time'], results_df['mpc_output'], label='MPC 输出 (入流量)')
    plt.title('控制器输出');
    plt.ylabel('流量 (单位)');
    plt.xlabel('时间 (小时)');
    plt.legend();
    plt.grid(True)
    plt.tight_layout();
    plt.show()


if __name__ == "__main__":
    run_simulation()