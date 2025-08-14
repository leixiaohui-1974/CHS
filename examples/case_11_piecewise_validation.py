import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# --- Dummy Model Implementations for Demonstration ---

class DummyStVenantModel:
    """A dummy model to generate a 'ground truth' hydrograph."""
    def run(self, hydrograph: pd.DataFrame) -> pd.DataFrame:
        # Simulate a realistic delay and attenuation
        flow = hydrograph['flow'].values
        flow_out = np.convolve(flow, np.array([0.1, 0.3, 0.4, 0.15, 0.05]), 'same')
        return pd.DataFrame({'time': hydrograph['time'], 'flow': flow_out})

class DummyMuskingumModel:
    """A dummy Muskingum model for a single segment."""
    def __init__(self, K, X):
        self.K = K
        self.X = X
        self.dt = 3600 # Assume hourly steps

    def run(self, hydrograph: pd.DataFrame) -> pd.DataFrame:
        I = hydrograph['flow'].values
        O = np.zeros_like(I)
        O[0] = I[0]
        I_prev = I[0]

        C1 = (self.dt - 2 * self.K * self.X) / (2 * self.K * (1 - self.X) + self.dt)
        C2 = (self.dt + 2 * self.K * self.X) / (2 * self.K * (1 - self.X) + self.dt)
        C3 = (2 * self.K * (1 - self.X) - self.dt) / (2 * self.K * (1 - self.X) + self.dt)

        for i in range(1, len(I)):
            O[i] = C1 * I[i] + C2 * I_prev + C3 * O[i-1]
            I_prev = I[i]

        return pd.DataFrame({'time': hydrograph['time'], 'flow': np.maximum(0, O)})

class DummyPiecewiseMuskingumModel:
    """A dummy piecewise model that uses a model bank."""
    def __init__(self, model_bank: list):
        self.model_bank = model_bank

    def run(self, hydrograph: pd.DataFrame) -> pd.DataFrame:
        I = hydrograph['flow'].values
        O = np.zeros_like(I)
        O[0] = I[0]
        I_prev = I[0]

        for i in range(1, len(I)):
            # Find the correct parameters for the current flow
            current_inflow = I[i]
            params = self.model_bank[-1]['parameters'] # Default to last segment
            for segment in self.model_bank:
                if current_inflow <= segment['max_value']:
                    params = segment['parameters']
                    break

            K, X, dt = params['K'], params['X'], 3600

            C1 = (dt - 2 * K * X) / (2 * K * (1 - X) + dt)
            C2 = (dt + 2 * K * X) / (2 * K * (1 - X) + dt)
            C3 = (2 * K * (1 - X) - dt) / (2 * K * (1 - X) + dt)

            O[i] = C1 * I[i] + C2 * I_prev + C3 * O[i-1]
            I_prev = I[i]

        return pd.DataFrame({'time': hydrograph['time'], 'flow': np.maximum(0, O)})

def calculate_nse(simulated: np.ndarray, observed: np.ndarray) -> float:
    """Calculates the Nash-Sutcliffe Efficiency."""
    return 1 - (np.sum((simulated - observed)**2) / np.sum((observed - np.mean(observed))**2))


def run_piecewise_validation():
    """
    Validates the performance of a generated model bank against a baseline
    and a single-segment model.
    """
    print("--- Setting up Validation Scenario ---")

    # 1. Load or define the model bank (dummy version from case_10)
    # This would typically be the output from generate_model_bank
    model_bank = [
        {'condition_variable': 'flow', 'max_value': 150.0, 'parameters': {'K': 2600.0, 'X': 0.15}},
        {'condition_variable': 'flow', 'max_value': 300.0, 'parameters': {'K': 1800.0, 'X': 0.22}}
    ]
    print("Using dummy model bank:")
    pprint.pprint(model_bank)

    # 2. Define a new validation hydrograph (different from the one used for generation)
    time = np.arange(0, 172800, 3600) # 48 hours
    peak_time = 36 * 3600
    flow = 50 + 200 * np.exp(-((time - peak_time)**2) / (2 * (12*3600)**2))
    validation_hydrograph = pd.DataFrame({'time': time, 'flow': flow})

    # 3. Run the three simulations
    print("\n--- Running Simulations ---")

    # i. Ground Truth (from a 'real' high-fidelity model)
    ground_truth_model = DummyStVenantModel()
    truth_output = ground_truth_model.run(validation_hydrograph)
    print("Generated ground truth data.")

    # ii. Single-Segment Model (using average parameters)
    avg_params = {
        'K': np.mean([s['parameters']['K'] for s in model_bank]),
        'X': np.mean([s['parameters']['X'] for s in model_bank])
    }
    single_segment_model = DummyMuskingumModel(**avg_params)
    single_seg_output = single_segment_model.run(validation_hydrograph)
    print(f"Ran single-segment simulation with avg params: K={avg_params['K']:.2f}, X={avg_params['X']:.2f}")

    # iii. Piecewise Model
    piecewise_model = DummyPiecewiseMuskingumModel(model_bank)
    piecewise_output = piecewise_model.run(validation_hydrograph)
    print("Ran piecewise simulation.")

    # 4. Compare results
    print("\n--- Analyzing Results ---")

    # i. Calculate NSE
    nse_single = calculate_nse(single_seg_output['flow'].values, truth_output['flow'].values)
    nse_piecewise = calculate_nse(piecewise_output['flow'].values, truth_output['flow'].values)

    print(f"NSE (Single-Segment Model): {nse_single:.4f}")
    print(f"NSE (Piecewise Model):      {nse_piecewise:.4f}")

    # ii. Plot hydrographs
    plt.figure(figsize=(12, 7))
    plt.plot(truth_output['time']/3600, truth_output['flow'], 'k-', label='Ground Truth (St. Venant)', linewidth=2.5)
    plt.plot(validation_hydrograph['time']/3600, validation_hydrograph['flow'], 'k--', label='Inflow Hydrograph', alpha=0.4)
    plt.plot(single_seg_output['time']/3600, single_seg_output['flow'], 'b:', label=f'Single-Segment (NSE={nse_single:.3f})')
    plt.plot(piecewise_output['time']/3600, piecewise_output['flow'], 'r-', label=f'Piecewise Model (NSE={nse_piecewise:.3f})')

    plt.title('Validation of Piecewise Model vs. Single-Segment Model')
    plt.xlabel('Time (hours)')
    plt.ylabel('Flow (m^3/s)')
    plt.legend()
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.savefig('piecewise_validation.png')
    print("\nSaved validation plot to 'piecewise_validation.png'")
    plt.close()

    # iii. Assertion for automated testing
    target_nse = 0.80
    print(f"\n--- Automated Test Assertion (is NSE >= {target_nse}?) ---")
    assert nse_piecewise >= target_nse, f"Piecewise model failed to meet target NSE of {target_nse}. Got {nse_piecewise:.4f}"
    print(f"PASSED: Piecewise model NSE ({nse_piecewise:.4f}) is greater than or equal to target ({target_nse}).")


if __name__ == "__main__":
    run_piecewise_validation()
