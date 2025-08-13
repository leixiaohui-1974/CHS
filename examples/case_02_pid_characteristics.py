import matplotlib.pyplot as plt
import pandas as pd
import copy
from water_system_simulator.simulation_manager import SimulationManager

def get_base_config():
    """Returns the base configuration for the PID characteristic tests."""
    return {
        "simulation_params": {
            "total_time": 50,
            "dt": 0.1
        },
        "components": {
            "process_var_signal": {
                "type": "Disturbance",
                "params": {
                    "signal_type": "constant",
                    "value": 0.0
                }
            },
            "pid": {
                "type": "PIDController",
                "params": {
                    "Kp": 1.0, "Ki": 0.0, "Kd": 0.0,
                    "set_point": 1.0, # This creates a constant error of 1.0
                    "output_min": None,
                    "output_max": None
                }
            }
        },
        "connections": [
            {
                "source": "process_var_signal.output",
                "target": "pid.input.error_source"
            }
        ],
        "execution_order": ["process_var_signal", "pid"],
        "logger_config": [
            "pid.state.output",
            "pid.state.integral"
        ]
    }

def run_pid_test(kp, ki, kd, output_min=None, output_max=None):
    """Runs a single PID test with the given parameters."""
    config = get_base_config()

    # Adjust PID parameters for the specific test run
    pid_params = config["components"]["pid"]["params"]
    pid_params["Kp"] = kp
    pid_params["Ki"] = ki
    pid_params["Kd"] = kd
    pid_params["output_min"] = output_min
    pid_params["output_max"] = output_max

    manager = SimulationManager()
    return manager.run(config)

def plot_pid_characteristics():
    """Plots the output of P, PI, and PID controllers for a step error."""
    # Run simulations for each controller type
    p_results = run_pid_test(kp=2.0, ki=0.0, kd=0.0)
    pi_results = run_pid_test(kp=2.0, ki=1.5, kd=0.0)
    pid_results = run_pid_test(kp=2.0, ki=1.5, kd=0.8)

    # Plot the controller outputs for comparison
    plt.figure(figsize=(12, 7))
    plt.plot(p_results['time'], p_results['pid.state.output'], label='P-Only (Kp=2.0)')
    plt.plot(pi_results['time'], pi_results['pid.state.output'], label='PI (Kp=2.0, Ki=1.5)')
    plt.plot(pid_results['time'], pid_results['pid.state.output'], label='PID (Kp=2.0, Ki=1.5, Kd=0.8)')

    plt.title('PID Controller Characteristics (Response to Unit Step Error)')
    plt.xlabel('Time (s)')
    plt.ylabel('Controller Output')
    plt.grid(True)
    plt.legend()

    import os
    os.makedirs("results", exist_ok=True)
    output_filename = "results/case_02_pid_characteristics.png"
    plt.savefig(output_filename)
    print(f"PID characteristics plot saved to {output_filename}")

def plot_anti_windup_test():
    """Runs and plots a test to demonstrate the anti-windup mechanism."""
    # A PI controller with a high integral gain to show saturation effect
    kp, ki, kd = 1.0, 2.0, 0.0

    # Run simulation without output limits
    unlimited_results = run_pid_test(kp, ki, kd)

    # Run simulation with an output limit
    limited_results = run_pid_test(kp, ki, kd, output_max=5.0)

    # Create plots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

    # Plot 1: Controller Output Comparison
    ax1.plot(unlimited_results['time'], unlimited_results['pid.state.output'], 'r--', label='Output (Unlimited)')
    ax1.plot(limited_results['time'], limited_results['pid.state.output'], 'b-', label='Output (Limited to 5.0)')
    ax1.axhline(y=5.0, color='k', linestyle=':', label='Output Limit')
    ax1.set_title('Anti-Windup Test: Controller Output')
    ax1.set_ylabel('Output')
    ax1.legend()
    ax1.grid(True)

    # Plot 2: Internal Integral State Comparison
    ax2.plot(unlimited_results['time'], unlimited_results['pid.state.integral'], 'r--', label='Integral Term (Unlimited)')
    ax2.plot(limited_results['time'], limited_results['pid.state.integral'], 'b-', label='Integral Term (with Anti-Windup)')
    ax2.set_title('Anti-Windup Test: Internal Integral State')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Integral Value')
    ax2.legend()
    ax2.grid(True)

    import os
    os.makedirs("results", exist_ok=True)
    output_filename = "results/case_02_anti_windup_test.png"
    plt.savefig(output_filename)
    print(f"Anti-windup test plot saved to {output_filename}")

if __name__ == "__main__":
    plot_pid_characteristics()
    plot_anti_windup_test()
