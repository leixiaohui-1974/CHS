import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Adjust the path to import the toolkit from the SDK source
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../water_system_sdk/src')))

from water_system_simulator.tools.identification_toolkit import IdentificationToolkit
from water_system_simulator.modeling.hydrology.routing_models import MuskingumModel

# --- 1. Data Generation ---
def generate_ground_truth(inflow: np.ndarray, dt: float) -> (np.ndarray, np.ndarray, pd.DataFrame):
    """
    Generates a 'ground truth' outflow using a Muskingum model with time-varying parameters.
    K changes based on the inflow magnitude.
    """
    true_outflow = np.zeros_like(inflow)
    true_outflow[0] = inflow[0]
    X_true = 0.2

    params_history = []

    for i in range(1, len(inflow)):
        # K varies with the current inflow, creating a non-linear system
        K_true = 30 * 3600 if inflow[i] < 70 else 20 * 3600
        params_history.append({'time': i * dt, 'K_true': K_true, 'X_true': X_true})

        model = MuskingumModel() # This model is stateless, params are passed to methods
        # Manually calculate coefficients as the SDK model class is structured for a different use case
        denominator = 2 * K_true * (1 - X_true) + dt
        C1 = (dt - 2 * K_true * X_true) / denominator
        C2 = (dt + 2 * K_true * X_true) / denominator
        C3 = (2 * K_true * (1 - X_true) - dt) / denominator

        # O_t = C1*I_t + C2*I_{t-1} + C3*O_{t-1}
        outflow_val = C1 * inflow[i] + C2 * inflow[i-1] + true_outflow[i-1] * C3
        true_outflow[i] = max(0, outflow_val)

    # Add measurement noise to create a realistic 'observed' signal
    noise = np.random.normal(0, 1.0, len(true_outflow))
    observed_outflow = true_outflow + noise

    return true_outflow, observed_outflow, pd.DataFrame(params_history)

def simulate_single_model(inflow: np.ndarray, params: dict, dt: float, initial_outflow: float) -> np.ndarray:
    """Helper to simulate the response of a single Muskingum model."""
    sim_outflow = np.zeros_like(inflow)
    sim_outflow[0] = initial_outflow
    K, X = params['K'], params['X']

    denominator = 2 * K * (1 - X) + dt
    C1 = (dt - 2 * K * X) / denominator
    C2 = (dt + 2 * K * X) / denominator
    C3 = (2 * K * (1 - X) - dt) / denominator

    for i in range(1, len(inflow)):
        outflow_val = C1 * inflow[i] + C2 * inflow[i-1] + sim_outflow[i-1] * C3
        sim_outflow[i] = max(0, outflow_val)
    return sim_outflow


print("--- CHS Identification Toolkit Showcase ---")
# Generate a synthetic hydrograph
dt = 3600  # seconds (1 hour)
time_hours = np.arange(0, 240) # 10 days
time_seconds = time_hours * dt
inflow_hydrograph = 50 + 50 * np.sin(2 * np.pi * time_hours / 80) + 30 * np.sin(2 * np.pi * time_hours / 25)
inflow_hydrograph[inflow_hydrograph < 20] = 20

# Generate the ground truth and observed data
true_outflow, observed_outflow, true_params_df = generate_ground_truth(inflow_hydrograph, dt)

# Instantiate the toolkit
toolkit = IdentificationToolkit()

# --- 2. Run Toolkit Methods ---

# a) Offline Identification (single model for the whole period)
print("\n[1] Running Offline Identification...")
try:
    offline_results = toolkit.identify_offline(
        model_type='Muskingum',
        inflow=inflow_hydrograph,
        outflow=observed_outflow,
        dt=dt,
        initial_guess=[25*3600, 0.25],
        bounds=([10*3600, 0.01], [40*3600, 0.49])
    )
    print(f"  > Offline Results: K={offline_results['params']['K']:.2f}, X={offline_results['params']['X']:.3f}, RMSE={offline_results['rmse']:.3f}")
    sim_outflow_offline = simulate_single_model(inflow_hydrograph, offline_results['params'], dt, observed_outflow[0])
except Exception as e:
    print(f"  > FAILED: {e}")
    offline_results = None
    sim_outflow_offline = np.zeros_like(inflow_hydrograph)


# b) Piecewise Identification
print("\n[2] Running Piecewise Identification...")
try:
    # Generate data for identifying parameters at different operating points
    op_points = [40, 90]
    op_inflows = [
        np.full(100, 40.0) + np.random.randn(100) * 5, # Low flow
        np.full(100, 90.0) + np.random.randn(100) * 10 # High flow
    ]
    op_outflows = [generate_ground_truth(inf, dt)[1] for inf in op_inflows]

    piecewise_model_bank = toolkit.identify_piecewise(
        model_type='Muskingum',
        operating_inflows=op_inflows,
        operating_outflows=op_outflows,
        operating_points=op_points,
        dt=dt,
        initial_guess=[25*3600, 0.25],
    bounds=([10*3600, 0.01], [40*3600, 0.49]),
        validation_inflow=inflow_hydrograph,
        validation_outflow=observed_outflow,
        target_nse=0.95
    )
    print(f"  > Piecewise Model Bank generated with {len(piecewise_model_bank)} segments.")
    # Use the toolkit's internal helper to run the simulation for plotting
    sim_outflow_piecewise = toolkit._run_piecewise_model(inflow_hydrograph, piecewise_model_bank, 'Muskingum', dt, observed_outflow[0])
except Exception as e:
    print(f"  > FAILED: {e}")
    piecewise_model_bank = None
    sim_outflow_piecewise = np.zeros_like(inflow_hydrograph)


# c) Online RLS Tracking
print("\n[3] Running Online RLS Tracking...")
try:
    rls_results_df = toolkit.track_online_rls(
        model_type='Muskingum',
        inflow=inflow_hydrograph,
        outflow=observed_outflow,
        dt=dt,
        initial_guess={'K': 25*3600, 'X': 0.2},
        forgetting_factor=0.985,
        initial_covariance=100
    )
    print("  > RLS tracking complete.")
except Exception as e:
    print(f"  > FAILED: {e}")
    rls_results_df = pd.DataFrame()


# d) Online KF Tracking
print("\n[4] Running Online KF Tracking...")
try:
    kf_results_df = toolkit.track_online_kf(
        model_type='Muskingum',
        inflow=inflow_hydrograph,
        outflow=observed_outflow,
        dt=dt,
        initial_guess={'K': 25*3600, 'X': 0.2},
        process_noise=1e-8,
        measurement_noise=1.0**2,
        initial_covariance=100
    )
    print("  > KF tracking complete.")
except Exception as e:
    print(f"  > FAILED: {e}")
    kf_results_df = pd.DataFrame()


# --- 3. Visualization ---
print("\n[5] Generating plots...")
fig, axes = plt.subplots(2, 1, figsize=(15, 12), gridspec_kw={'height_ratios': [2, 1]})
fig.suptitle('CHS Identification Toolkit Showcase: Comparing Methods', fontsize=16)

# Plot 1: Hydrographs
ax1 = axes[0]
ax1.plot(time_hours, inflow_hydrograph, 'k--', label='Inflow Hydrograph', alpha=0.6)
ax1.plot(time_hours, observed_outflow, 'o', color='skyblue', markersize=3, alpha=0.5, label='Observed Outflow')
ax1.plot(time_hours, true_outflow, 'b-', label='True Outflow (Unseen)', linewidth=2)
if offline_results:
    ax1.plot(time_hours, sim_outflow_offline, 'g-', label=f'Offline Model (K={offline_results["params"]["K"]:.0f})', linewidth=2)
if piecewise_model_bank:
    ax1.plot(time_hours, sim_outflow_piecewise, 'r-', label=f'Piecewise Model ({len(piecewise_model_bank)} segments)', linewidth=2)
ax1.set_xlabel('Time (hours)')
ax1.set_ylabel('Flow (m³/s)')
ax1.set_title('Hydrograph Comparison')
ax1.legend()
ax1.grid(True, which='both', linestyle='--', linewidth=0.5)


# Plot 2: Parameter Tracking
ax2 = axes[1]
ax2.plot(true_params_df['time'] / 3600, true_params_df['K_true'], 'b-', label='True K Value', linewidth=2)
if offline_results:
    ax2.axhline(y=offline_results['params']['K'], color='g', linestyle='--', label='Offline K')
if piecewise_model_bank:
    # Plot piecewise K values as horizontal lines over their active ranges
    for i, seg in enumerate(piecewise_model_bank):
        start_val = piecewise_model_bank[i-1]['max_value'] if i > 0 else 0
        ax2.hlines(seg['parameters']['K'], xmin=start_val, xmax=seg['max_value'], color='r', linestyle='--', label=f"Piecewise K (Seg {i+1})")
if not rls_results_df.empty:
    ax2.plot(rls_results_df['time'] / 3600, rls_results_df['K'], 'm-', label='RLS Estimated K', alpha=0.8)
if not kf_results_df.empty:
    ax2.plot(kf_results_df['time'] / 3600, kf_results_df['K'], 'c-', label='KF Estimated K', alpha=0.8)

ax2.set_xlabel('Time (hours)')
ax2.set_ylabel('Parameter K (seconds)')
ax2.set_title('Online Parameter Tracking Comparison (K)')
ax2.legend()
ax2.grid(True, which='both', linestyle='--', linewidth=0.5)

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
output_path = os.path.join(os.path.dirname(__file__), '..', 'results', 'case_21_toolkit_showcase.png')
os.makedirs(os.path.dirname(output_path), exist_ok=True)
plt.savefig(output_path)
print(f"\nPlots saved to {output_path}")

plt.show()
