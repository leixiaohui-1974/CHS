import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
import pandas as pd
import sys
import os

# 自动添加必要的Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
chs_sdk_path = os.path.join(current_dir, '..', '..', 'src')
project_utils_path = os.path.join(current_dir, '..')

# 添加到Python路径
if chs_sdk_path not in sys.path:
    sys.path.insert(0, chs_sdk_path)
if project_utils_path not in sys.path:
    sys.path.insert(0, project_utils_path)

print(f"🔧 已添加路径: {chs_sdk_path}")
print(f"🔧 已添加路径: {project_utils_path}")

def run_simulation():
    """
    This script demonstrates how to use a PID controller to modulate a
    valve's opening to achieve a target flow rate in a pressurized pipe system.
    """
    print("🚀 开始阀门控制仿真...")
    
    try:
        # 导入chs_sdk模块
        from chs_sdk.core.host import AgentKernel as Host
        from chs_sdk.modules.modeling.storage_models import LinearTank
        from chs_sdk.modules.control.pid_controller import PIDController
        from chs_sdk.modules.modeling.valve_models import ButterflyValve
        from project_utils import ModelAgent
        
        print("✅ 成功导入chs_sdk模块！")
        
        # 创建Host实例
        host = Host()
        
        # 1. 创建组件
        print("📦 创建仿真组件...")
        host.add_agent(
            agent_class=ModelAgent,
            agent_id='DownstreamReservoir',
            model_class=LinearTank,
            area=500,
            initial_level=10.0)
        host.add_agent(
            agent_class=ModelAgent,
            agent_id='ControlValve',
            model_class=ButterflyValve,
            cv_max=10.0,
            slew_rate=5.0/60.0)
        host.add_agent(
            agent_class=ModelAgent,
            agent_id='FlowPID',
            model_class=PIDController,
            Kp=0.04,    # 稍微增加比例增益，提高响应
            Ki=0.0015,   # 大幅降低积分增益，防止积分饱和
            Kd=0.003,    # 增加微分增益，增强阻尼
            set_point=2.5,
            output_min=0.0,
            output_max=0.5)

        # 2. 建立连接
        print("🔗 建立组件连接...")
        downstream_reservoir_agent = host._agents['DownstreamReservoir']
        valve_agent = host._agents['ControlValve']
        pid_agent = host._agents['FlowPID']

        # 建立订阅关系
        pid_agent.subscribe(f"{valve_agent.agent_id}/inflow", 'error_source')  # PID从阀门接收流量反馈
        valve_agent.subscribe(f"{pid_agent.agent_id}/output", 'command')       # 阀门从PID接收控制指令
        downstream_reservoir_agent.subscribe(f"{valve_agent.agent_id}/inflow", 'inflow')  # 水库接收流量

        # 3. 运行仿真
        print("⚡ 开始仿真运行...")
        num_steps = 600
        dt = 1.0
        results = []
        host.start(time_step=dt)
        
        for i in range(num_steps):
            # 在每一步手动设置阀门的上下游压力（用水位代替）
            valve_agent.input_values['upstream_pressure'] = 17.0  # 增加上游压力，增大压差
            valve_agent.input_values['downstream_pressure'] = downstream_reservoir_agent.model.output

            # 执行仿真步长
            host.tick()
            
            # 记录结果
            results.append({
                'time': host.current_time,
                'ControlValve.value': valve_agent.model.output,
                'FlowPID.output': pid_agent.model.output,
                'ControlValve.actual_position': valve_agent.model.get_current_position()
            })
            
            # 每100步打印一次状态
            if i % 100 == 0:
                print(f"⏱️  时间: {host.current_time:.1f}s, "
                      f"流量: {valve_agent.model.output:.3f} m³/s, "
                      f"PID输出: {pid_agent.model.output:.3f}, "
                      f"阀门开度: {valve_agent.model.get_current_position():.3f}")

        # 4. 绘图
        print("📊 生成仿真结果图表...")
        results_df = pd.DataFrame(results)
        print("\n仿真结果 (前5行):")
        print(results_df.head())
        print("\n仿真结果 (后5行):")
        print(results_df.tail())

        # 创建2x2的子图布局，参考ch07的设计
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('第八章: PID阀门流量控制仿真', fontsize=16)

        # 左上：流量控制效果
        ax1.plot(results_df['time'], results_df['ControlValve.value'], 'b-', label='实际流量', linewidth=2)
        ax1.axhline(y=2.5, color='r', linestyle='--', label='目标流量 (2.5 m^3/s)', linewidth=2)
        ax1.set_ylabel('流量 (m^3/s)', fontsize=12)
        ax1.set_title('流量控制效果', fontsize=14)
        ax1.legend(fontsize=10)
        ax1.grid(True, alpha=0.3)

        # 右上：阀门开度控制
        ax2.plot(results_df['time'], results_df['FlowPID.output'], 'g--', label='PID指令 (目标开度)', linewidth=2)
        ax2.plot(results_df['time'], results_df['ControlValve.actual_position'], 'm-', label='阀门实际开度', linewidth=2)
        ax2.set_ylabel('阀门开度 (0-1)', fontsize=12)
        ax2.set_title('阀门开度控制', fontsize=14)
        ax2.legend(fontsize=10)
        ax2.grid(True, alpha=0.3)

        # 左下：PID控制器输出
        ax3.plot(results_df['time'], results_df['FlowPID.output'], 'c-', linewidth=2, label='PID控制器输出')
        ax3.set_ylabel('PID输出', fontsize=12)
        ax3.set_xlabel('时间 (秒)', fontsize=12)
        ax3.set_title('PID控制器响应', fontsize=14)
        ax3.legend(fontsize=10)
        ax3.grid(True, alpha=0.3)

        # 右下：阀门位置响应
        ax4.plot(results_df['time'], results_df['ControlValve.actual_position'], 'orange', linewidth=2, label='阀门实际位置')
        ax4.set_ylabel('阀门位置', fontsize=12)
        ax4.set_xlabel('时间 (秒)', fontsize=12)
        ax4.set_title('阀门执行器响应', fontsize=14)
        ax4.legend(fontsize=10)
        ax4.grid(True, alpha=0.3)

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.show()
        
        # 5. 分析结果
        print("\n=== 仿真结果分析 ===")
        final_flow = results_df['ControlValve.value'].iloc[-1]
        target_flow = 2.5
        flow_error = abs(final_flow - target_flow)
        flow_error_percent = (flow_error / target_flow) * 100
        
        print(f"目标流量: {target_flow} m³/s")
        print(f"最终流量: {final_flow:.3f} m³/s")
        print(f"流量误差: {flow_error:.3f} m³/s ({flow_error_percent:.1f}%)")
        
        if flow_error_percent < 5:
            print("✅ 流量控制效果良好！误差小于5%")
        elif flow_error_percent < 10:
            print("⚠️  流量控制效果一般，误差在5-10%之间")
        else:
            print("❌ 流量控制效果较差，误差大于10%")
        
        # 检查阀门开度响应
        valve_response_time = 0
        for i, row in results_df.iterrows():
            if abs(row['ControlValve.actual_position'] - row['FlowPID.output']) < 0.01:
                valve_response_time = row['time']
                break
        
        print(f"\n阀门响应时间: {valve_response_time:.1f} 秒")
        if valve_response_time < 30:
            print("✅ 阀门响应速度良好！")
        else:
            print("⚠️  阀门响应较慢，可能需要调整slew_rate参数")
            
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("💡 请确保chs_sdk已正确安装")
        print("🔧 可以尝试运行: pip install -e ../../..")
        
    except Exception as e:
        print(f"❌ 运行时错误: {e}")
        print("💡 这可能是chs_sdk模块功能不完整导致的")
        print("🔧 我们需要检查并补充缺失的功能")

if __name__ == "__main__":
    run_simulation()
