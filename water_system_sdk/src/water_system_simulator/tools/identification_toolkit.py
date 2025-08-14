import copy
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from typing import Dict, Any, List, Tuple, Callable

from water_system_simulator.simulation_manager import SimulationManager, getattr_by_path, setattr_by_path
from water_system_simulator.modeling.hydrology.routing_models import MuskingumModel
from water_system_simulator.modeling.integral_plus_delay_model import IntegralPlusDelayModel
from water_system_simulator.utils.metrics import calculate_nse
from water_system_simulator.tools.simulation_helpers import run_piecewise_model, run_single_model


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

        # Create a dummy response dataframe. In a real scenario, this would come
        # from running a high-fidelity model (e.g., StVenantModel).
        t_data = np.arange(0, sim_duration, dt)
        # Create a plausible-looking dummy response
        dummy_response = initial_output_val + (step_input_val - initial_input_val) * (1 - np.exp(-t_data / 3600))
        y_data = dummy_response

        # 3. Fit parameters using the new simulation helpers
        def muskingum_fit_func(t, K, x):
            inflow_series = np.full_like(t, step_input_val, dtype=np.float64)
            params = {'K': K, 'X': x}
            return run_single_model(inflow_series, 'Muskingum', params, dt, initial_inflow=initial_input_val, initial_outflow=initial_output_val)

        def integral_delay_fit_func(t, K, T):
            inflow_series = np.full_like(t, step_input_val, dtype=np.float64)
            params = {'K': K, 'T': T}
            return run_single_model(inflow_series, 'IntegralDelay', params, dt, initial_inflow=initial_input_val, initial_outflow=initial_output_val)

        try:
            if task['model_type'] == 'Muskingum':
                popt, _ = curve_fit(
                    muskingum_fit_func,
                    t_data, y_data, p0=[3600, 0.2], bounds=([0, 0], [np.inf, 0.5])
                )
                results[task_key] = {"K": popt[0], "X": popt[1]}
            elif task['model_type'] == 'IntegralDelay':
                 popt, _ = curve_fit(
                    integral_delay_fit_func,
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
        # Create a temporary model bank in the format expected by the simulation helper
        temp_model_bank = [
            {
                'max_value': seg['range_end'],
                'parameters': seg['params']
            }
            for seg in segments
        ]

        inflow_series = validation_hydrograph['flow'].values
        dt = validation_hydrograph['time'].values[1] - validation_hydrograph['time'].values[0] if len(validation_hydrograph['time'].values) > 1 else 1.0
        sim_out_flow = run_piecewise_model(inflow_series, temp_model_bank, task['model_type'], dt)
        sim_out_df = pd.DataFrame({'time': validation_hydrograph['time'], 'flow': sim_out_flow})
        current_nse = calculate_nse(sim_out_df['flow'].values, ground_truth_output['flow'].values)

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
