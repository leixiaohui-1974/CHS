import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from water_system_simulator.engine import Simulator

def _calculate_metrics(df: pd.DataFrame, level_col: str, setpoint: float):
    """Calculates control performance metrics."""
    try:
        y = df[level_col]
        t = df['time']

        # Steady-state error
        ss_error = abs(y.iloc[-1] - setpoint)

        # Overshoot
        peak = y.max()
        overshoot = ((peak - setpoint) / setpoint) * 100 if setpoint != 0 else 0
        overshoot = max(0, overshoot) # Only positive overshoot

        # Rise time (10% to 90% of the steady-state value)
        ten_percent = y.iloc[0] + 0.1 * (y.iloc[-1] - y.iloc[0])
        ninety_percent = y.iloc[0] + 0.9 * (y.iloc[-1] - y.iloc[0])

        t10 = t[y >= ten_percent].iloc[0] if not t[y >= ten_percent].empty else 0
        t90 = t[y >= ninety_percent].iloc[0] if not t[y >= ninety_percent].empty else 0
        rise_time = t90 - t10

        return {
            "Steady-State Error": f"{ss_error:.3f}",
            "Overshoot (%)": f"{overshoot:.2f}",
            "Rise Time (s)": f"{rise_time:.2f}"
        }
    except Exception:
        return {"Error": "Could not calculate metrics."}

def generate_report(case_path: str):
    """
    Runs a simulation and generates a detailed analysis report.
    """
    case_name = os.path.basename(os.path.normpath(case_path))
    print(f"\n--- Generating Report for: {case_name} ---")

    if not os.path.isdir(case_path):
        print(f"Error: Case path not found.")
        return

    # 1. Run Simulation
    try:
        sim = Simulator(case_path)
        duration = 250
        dt = 1.0
        log_file = f"{case_name}_log.csv"
        sim.run(duration=duration, dt=dt, log_file_prefix=case_name)
        log_file_path = os.path.join('results', log_file)
        df = pd.read_csv(log_file_path)
    except Exception as e:
        print(f"Failed to run simulation for {case_name}: {e}")
        return

    # 2. Generate Plot
    print("Generating plot...")
    plot_path = os.path.join('results', f"{case_name}_results.png")

    # Generic plotting logic (can be improved)
    plt.figure(figsize=(12, 7))
    level_cols = [col for col in df.columns if 'level' in col.lower() or 'storage' in col.lower() or 'channel.output' in col]
    for col in level_cols:
        plt.plot(df['time'], df[col], label=col)

    # Try to find a setpoint to plot
    if sim.control_params:
        for params in sim.control_params.values():
            if 'setpoint' in params:
                sp = params['setpoint']
                # Handle list or scalar setpoint
                sp_val = sp[-1] if isinstance(sp, list) else sp
                plt.axhline(y=sp_val, color='r', linestyle='--', label=f'Setpoint ({sp_val})')
                break # Plot first setpoint found

    plt.title(f'Simulation Results for {case_name}')
    plt.xlabel('Time (s)')
    plt.ylabel('State Value')
    plt.legend()
    plt.grid(True)
    plt.savefig(plot_path)
    plt.close()
    print(f"Plot saved to {plot_path}")

    # 3. Calculate Metrics
    metrics = {}
    if level_cols and 'setpoint' in locals():
        metrics = _calculate_metrics(df, level_cols[0], sp_val)

    # 4. Assemble Markdown Report
    print("Generating markdown report...")
    report = f"# Analysis Report: {case_name}\n\n"
    report += "## 1. Problem Description\n"
    report += f"This report details the simulation results for the '{case_name}' scenario.\n\n"
    report += "## 2. Inputs\n"
    report += f"- **Topology File:** `{os.path.join(case_path, 'topology.yml')}`\n"
    report += f"- **Disturbances File:** `{os.path.join(case_path, 'disturbances.csv')}`\n"
    report += f"- **Control Parameters File:** `{os.path.join(case_path, 'control_parameters.yaml')}`\n\n"
    report += "## 3. Results\n\n"
    report += f"![Simulation Results]({plot_path})\n\n"
    report += "### 3.1. Performance Metrics\n"
    if metrics:
        for key, value in metrics.items():
            report += f"- **{key}:** {value}\n"
    else:
        report += "Performance metrics could not be calculated for this case.\n"
    report += "\n"
    report += "### 3.2. Raw Data Sample\n"
    report += df.head().to_markdown(index=False) + "\n"
    report += "\n## 4. Analysis and Discussion\n"
    if metrics.get("Overshoot (%)", "0") != "0.00":
        report += "- The controller exhibited an overshoot, suggesting the proportional or integral gain might be too high.\n"
    if metrics.get("Steady-State Error", "0") != "0.000":
        report += "- A non-zero steady-state error was observed, which could indicate a need for integral action or adjustment of the 'I' gain.\n"
    report += "- The system's response to disturbances can be seen in the plot, showing how the controller adapts to changes in inflow or demand.\n"

    report_file_path = os.path.join('results', f"report_{case_name}.md")
    with open(report_file_path, 'w') as f:
        f.write(report)

    print(f"Report saved to {report_file_path}")

if __name__ == '__main__':
    if not os.path.exists('results'):
        os.makedirs('results')

    case_dirs = [
        'examples/2_single_reservoir_case/',
        'examples/3_double_reservoir_case/',
        'examples/4_one_gate_one_channel_case/',
        # Case 5 has multiple topologies, this will run the default 'topology.yml'
        'examples/5_one_gate_two_channels_case/',
        'examples/6_complex_tunnel_pipeline_case/',
    ]

    for case in case_dirs:
        generate_report(case)
