import copy
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from typing import Dict, Any, List, Tuple, Callable

from water_system_simulator.simulation_manager import SimulationManager, getattr_by_path, setattr_by_path
from water_system_simulator.modeling.hydrology.routing_models import MuskingumModel
from water_system_simulator.modeling.integral_plus_delay_model import IntegralPlusDelayModel

# --- Placeholder functions for generate_model_bank ---

def _calculate_nse(simulated: np.ndarray, observed: np.ndarray) -> float:
    """Calculates the Nash-Sutcliffe Efficiency."""
    if len(simulated) != len(observed):
        raise ValueError("Simulated and observed arrays must have the same length.")
    if np.var(observed) == 0:
        return -np.inf # Or handle as an error, as NSE is undefined.
    return 1 - (np.sum((simulated - observed)**2) / np.sum((observed - np.mean(observed))**2))

def _simulate_piecewise_model(segments: list, validation_hydrograph: pd.DataFrame) -> pd.DataFrame:
    """
    A placeholder function to simulate the response of a piecewise model.
    In a real implementation, this would use a Piecewise...Model class.
    """
    # This is a dummy implementation.
    # It just returns a slightly modified version of the input hydrograph.
    simulated_output = validation_hydrograph['flow'].values * 0.95
    return pd.DataFrame({'time': validation_hydrograph['time'], 'flow': simulated_output})


# --- Helper functions for model fitting ---

def _muskingum_response(t: np.ndarray, K: float, x: float, I0: float, I1: float, O0: float, dt: float) -> np.ndarray:
    """
    Simulates the Muskingum model response to a step input.
    """
    # This is a simplified numerical solution for fitting purposes.
    # A more accurate analytical solution would be better if available.
    C1 = (dt - 2 * K * x) / (2 * K * (1 - x) + dt) if (2 * K * (1 - x) + dt) != 0 else 0
    C2 = (dt + 2 * K * x) / (2 * K * (1 - x) + dt) if (2 * K * (1 - x) + dt) != 0 else 0
    C3 = (2 * K * (1 - x) - dt) / (2 * K * (1 - x) + dt) if (2 * K * (1 - x) + dt) != 0 else 0

    outflow = np.zeros_like(t)
    O_prev = O0
    I_prev = I0

    for i in range(len(t)):
        I_t = I1
        O_t = C1 * I_t + C2 * I_prev + C3 * O_prev
        outflow[i] = max(0, O_t)
        O_prev = outflow[i]
        I_prev = I_t

    return outflow

def _integral_plus_delay_response(t: np.ndarray, K: float, T: float, initial_output: float, step_input_value: float) -> np.ndarray:
    """
    Simulates the Integral-Plus-Delay model response to a step input.
    """
    output = np.full_like(t, initial_output)
    dt = t[1] - t[0] if len(t) > 1 else 0
    for i in range(1, len(t)):
        time_since_step = t[i] - t[0]
        if time_since_step >= T:
            output[i] = output[i-1] + K * step_input_value * dt
    return output


def identify_at_point(base_config: dict, operating_point: dict, identification_tasks: list, dt:float = 60.0, sim_duration:float = 7200.0, step_increase_factor:float=0.1) -> dict:
    """
    Identifies the parameters of simplified models at a single steady-state operating point.
    """
    results = {}

    # This is a simplified setup. A robust version needs a better way to map
    # operating points and IO to the StVenantModel config.
    # For now, we assume the first inflow node is the upstream input.
    inflow_node_name = next((n['name'] for n in base_config['components']['StVenantModel']['properties']['nodes_data'] if n['type'] == 'inflow'), None)
    if not inflow_node_name:
        raise ValueError("Could not find an inflow node in the base_config.")

    op_point_path = f"StVenantModel.properties.nodes_data.0.inflow" # HACK

    # 1. Establish steady state
    steady_config = copy.deepcopy(base_config)
    # setattr_by_path is complex with lists, so we do it manually for now
    steady_config['components']['StVenantModel']['properties']['nodes_data'][0]['inflow'] = operating_point['upstream_flow']

    sim_manager = SimulationManager(config=steady_config)
    # The StVenantModel is not yet integrated with the SimManager, so we call it directly.
    # This part needs to be updated once the integration is done.
    # For now, we create a dummy steady state.
    steady_state_df = pd.DataFrame([{'time': 0, 'StVenantModel.reaches.r1.discharge': operating_point['upstream_flow']*0.98}])


    # 2. Perform step response
    for task in identification_tasks:
        task_key = f"{task['model_type']}_{task['input']}_{task['output']}"

        initial_input_val = operating_point['upstream_flow']
        initial_output_val = initial_input_val # Assume steady state

        step_input_val = initial_input_val * (1 + step_increase_factor)

        # Create a dummy response dataframe
        t_data = np.arange(0, sim_duration, dt)
        # Create a plausible-looking dummy response
        dummy_response = initial_output_val + (step_input_val - initial_input_val) * (1 - np.exp(-t_data / 3600))
        response_df = pd.DataFrame({'time': t_data, 'output': dummy_response})
        y_data = response_df['output'].values

        # 3. Fit parameters
        try:
            if task['model_type'] == 'Muskingum':
                popt, _ = curve_fit(
                    lambda t, K, x: _muskingum_response(t, K, x, initial_input_val, step_input_val, initial_output_val, dt),
                    t_data, y_data, p0=[3600, 0.2], bounds=([0, 0], [np.inf, 0.5])
                )
                results[task_key] = {"K": popt[0], "X": popt[1]}
            elif task['model_type'] == 'IntegralDelay':
                 popt, _ = curve_fit(
                    lambda t, K, T: _integral_plus_delay_response(t, K, T, initial_output_val, step_input_val - initial_input_val),
                    t_data, y_data, p0=[0.01, 300], bounds=([0, 0], [np.inf, sim_duration])
                )
                 results[task_key] = {"K": popt[0], "T": popt[1]}
        except (RuntimeError, ValueError) as e:
            results[task_key] = {"error": str(e)}

    return results


def generate_model_bank(base_config: dict, operating_space: list, task: dict, validation_hydrograph: pd.DataFrame, ground_truth_output: pd.DataFrame, target_accuracy: float = 0.8) -> list:
    """
    Generates an optimal piecewise linear model bank.
    """
    # 1. Full-condition scan
    param_map = []
    for op_point in operating_space:
        # op_point is e.g. {'upstream_flow': 100}
        # The identify_at_point function needs to be called with the full operating point dict
        full_op_point_dict = {'upstream_flow': op_point['flow'], 'downstream_level': op_point['level']}

        # For now, identify_at_point is not fully functional, so we generate dummy parameters
        # params = identify_at_point(base_config, full_op_point_dict, [task])
        # task_key = f"{task['model_type']}_{task['input']}_{task['output']}"
        # identified_params = params.get(task_key, {})

        # Dummy parameter generation based on flow
        flow = op_point['flow']
        dummy_params = {'K': 3600 - flow * 10, 'X': 0.1 + flow / 2000}

        if dummy_params:
            param_map.append({'operating_point': op_point, 'params': dummy_params})

    if not param_map:
        raise ValueError("Could not identify parameters for any operating point.")

    # Sort the map by the primary operating variable (e.g., flow)
    sort_key = 'flow' # This should be determined from the task
    param_map.sort(key=lambda x: x['operating_point'][sort_key])

    # 2. Optimal segmentation search
    segments = []

    # Initial segment: covers the whole range
    op_points_in_segment = [p['operating_point'] for p in param_map]
    params_in_segment = [p['params'] for p in param_map]
    avg_params = {k: np.mean([p[k] for p in params_in_segment]) for k in params_in_segment[0]}

    segments.append({
        'range_start': op_points_in_segment[0][sort_key],
        'range_end': op_points_in_segment[-1][sort_key],
        'params': avg_params,
        'points_in_segment': param_map
    })

    current_nse = -np.inf
    max_iter = 10 # Safety break
    iter_count = 0

    while current_nse < target_accuracy and iter_count < max_iter:
        sim_out_df = _simulate_piecewise_model(segments, validation_hydrograph)
        current_nse = _calculate_nse(sim_out_df['flow'].values, ground_truth_output['flow'].values)

        if current_nse >= target_accuracy:
            break

        # Find segment with highest parameter variance to split
        variances = []
        for i, seg in enumerate(segments):
            if len(seg['points_in_segment']) < 2:
                variances.append(-1) # Cannot split a segment with one point
                continue

            params_in_seg = [p['params'] for p in seg['points_in_segment']]
            # Calculate variance for each parameter, then sum them up (simple approach)
            total_variance = 0
            for key in params_in_seg[0].keys():
                param_values = [p[key] for p in params_in_seg]
                total_variance += np.var(param_values)
            variances.append(total_variance)

        if not any(v > 0 for v in variances):
            break # No more splits possible

        idx_to_split = np.argmax(variances)

        # Split the segment
        seg_to_split = segments.pop(idx_to_split)
        points = seg_to_split['points_in_segment']
        split_idx = len(points) // 2

        points1 = points[:split_idx]
        points2 = points[split_idx:]

        # Create two new segments
        for new_points in [points1, points2]:
            if not new_points: continue
            params_in_new_seg = [p['params'] for p in new_points]
            avg_params = {k: np.mean([p[k] for p in params_in_new_seg]) for k in params_in_new_seg[0]}
            new_segment = {
                'range_start': new_points[0]['operating_point'][sort_key],
                'range_end': new_points[-1]['operating_point'][sort_key],
                'params': avg_params,
                'points_in_segment': new_points
            }
            segments.append(new_segment)

        segments.sort(key=lambda x: x['range_start'])
        iter_count += 1

    # Final format for Piecewise...Model
    final_model_bank = [
        {
            'condition_variable': sort_key,
            'max_value': seg['range_end'],
            'parameters': seg['params']
        }
        for seg in segments
    ]

    return final_model_bank
