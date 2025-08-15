# scenarios/case_kernel_fault_tolerance/run.py
import sys
import os
import yaml
import argparse

# 确保 chs_sdk 和 scenarios 目录在 Python 路径中
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from scenarios.launcher import Launcher

def main():
    parser = argparse.ArgumentParser(description="Run Kernel Fault Tolerance Scenario")
    parser.add_argument('--config', type=str, default='scenarios/case_kernel_fault_tolerance/config.yaml', help='Path to the scenario config file')
    args = parser.parse_args()

    print(f"Loading scenario from: {args.config}")
    with open(args.config, 'r') as f:
        scenario_config = yaml.safe_load(f)

    launcher = Launcher()
    launcher.run(scenario_config)
    print("Scenario finished.")

if __name__ == "__main__":
    main()
