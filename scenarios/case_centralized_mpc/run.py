# scenarios/case_centralized_mpc/run.py
import sys
import os
import yaml
import argparse

# 将项目根目录添加到Python路径以允许绝对导入
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
src_path = os.path.join(project_root, 'water_system_sdk', 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_path)

from chs_sdk.core.launcher import Launcher

def main():
    # 为启动器设置配置文件参数
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')

    parser = argparse.ArgumentParser(description="运行集中式MPC场景")
    parser.add_argument('--config', type=str, default=config_path, help='场景配置文件的路径')
    args = parser.parse_args()

    print(f"--- 运行集中式MPC系统集成测试 ---")
    print(f"使用配置文件: {args.config}")

    with open(args.config, 'r') as f:
        scenario_config = yaml.safe_load(f)

    launcher = Launcher()
    launcher.run(scenario_config)

    print("--- 集中式MPC系统集成测试完成 ---")

if __name__ == "__main__":
    main()
