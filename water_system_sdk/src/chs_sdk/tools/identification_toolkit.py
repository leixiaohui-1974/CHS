import numpy as np
import pandas as pd
from scipy.optimize import curve_fit, minimize
from typing import Dict, List, Any, Callable

from chs_sdk.modeling.integral_plus_delay_model import IntegralPlusDelayModel
from chs_sdk.control.kalman_filter import KalmanFilter
from chs_sdk.utils.metrics import calculate_nse, calculate_rmse


class IdentificationToolkit:
    """
    A comprehensive toolkit for system identification and data assimilation.
    """

    def __init__(self):
        # This toolkit is stateless for now, but can hold configuration state in the future.
        pass

    def identify_offline(self, model_type: str, inflow: np.ndarray, outflow: np.ndarray, dt: float,
                         initial_guess: List[float], bounds: List[tuple]) -> Dict[str, Any]:
        """
        Performs offline parameter identification for a given model.
        """
        if model_type not in ['Muskingum', 'IntegralDelay']:
            raise ValueError(f"Unsupported model type: {model_type}")

        # Define the objective function for curve_fit
        def model_response(t, *params):
            inflow_series = inflow

            if model_type == 'Muskingum':
                K, X = params[0], params[1]
                if K <= 0 or not (0 <= X <= 0.5):
                    return np.full_like(inflow_series, 1e10)

                denominator = 2 * K * (1 - X) + dt
                if abs(denominator) < 1e-9:
                    return np.full_like(inflow_series, 1e10)

                C1 = (dt - 2 * K * X) / denominator
                C2 = (dt + 2 * K * X) / denominator
                C3 = (2 * K * (1 - X) - dt) / denominator

                sim_outflow = np.zeros_like(inflow_series)
                if len(inflow_series) > 0:
                    sim_outflow[0] = outflow[0]
                for i in range(1, len(inflow_series)):
                    sim_outflow[i] = C1 * inflow_series[i] + C2 * inflow_series[i-1] + sim_outflow[i-1] * C3
                return sim_outflow

            elif model_type == 'IntegralDelay':
                initial_inflow = inflow[0] if len(inflow) > 0 else 0
                initial_outflow = outflow[0] if len(outflow) > 0 else 0
                model = IntegralPlusDelayModel(K=params[0], T=params[1], dt=dt, initial_value=initial_inflow)
                model.state.output = initial_outflow
                sim_outflow = np.zeros_like(inflow_series)
                if len(inflow_series) > 0:
                    sim_outflow[0] = initial_outflow
                for i in range(1, len(inflow_series)):
                    model.input.inflow = inflow_series[i]
                    model.step()
                    sim_outflow[i] = model.output
                return sim_outflow

            return np.array([])

        time_array = np.arange(len(inflow)) * dt

        try:
            popt, _ = curve_fit(model_response, time_array, outflow, p0=initial_guess, bounds=bounds)
        except (RuntimeError, ValueError) as e:
            raise RuntimeError(f"Parameter identification failed: {e}")

        final_response = model_response(time_array, *popt)
        rmse = calculate_rmse(final_response, outflow)
        param_names = ['K', 'X'] if model_type == 'Muskingum' else ['K', 'T']
        return {"params": dict(zip(param_names, popt)), "rmse": rmse}

    def _run_piecewise_model(self, inflow: np.ndarray, model_bank: List[Dict], model_type: str, dt: float, initial_outflow: float) -> np.ndarray:
        """
        Runs a simulation using a piecewise model bank.
        """
        sim_outflow = np.zeros_like(inflow)
        if len(inflow) == 0:
            return sim_outflow
        sim_outflow[0] = initial_outflow

        models = {}
        if model_type == 'Muskingum':
            for i, segment in enumerate(model_bank):
                params = segment['parameters']
                K, X = params['K'], params['X']
                denominator = 2 * K * (1 - X) + dt
                C1 = (dt - 2 * K * X) / denominator
                C2 = (dt + 2 * K * X) / denominator
                C3 = (2 * K * (1 - X) - dt) / denominator
                models[i] = (C1, C2, C3)
        else:
            raise NotImplementedError(f"Piecewise simulation for {model_type} is not yet supported.")

        sorted_model_bank = sorted(model_bank, key=lambda x: x['max_value'])

        for i in range(1, len(inflow)):
            current_inflow = inflow[i]
            segment_idx = -1
            for idx, segment in enumerate(sorted_model_bank):
                if current_inflow <= segment['max_value']:
                    segment_idx = idx
                    break
            if segment_idx == -1:
                segment_idx = len(sorted_model_bank) - 1

            if model_type == 'Muskingum':
                C1, C2, C3 = models[segment_idx]
                sim_outflow[i] = C1 * inflow[i] + C2 * inflow[i - 1] + sim_outflow[i - 1] * C3

        return sim_outflow

    def identify_piecewise(self, model_type: str, operating_inflows: List[np.ndarray],
                         operating_outflows: List[np.ndarray], operating_points: List[float], dt: float,
                         initial_guess: List[float], bounds: List[tuple], validation_inflow: np.ndarray,
                         validation_outflow: np.ndarray, target_nse: float = 0.8,
                         max_iter: int = 10) -> List[Dict[str, Any]]:
        """
        Implements the 'optimal segmentation search' to build a model bank.
        """
        param_map = []
        for i, op_point_val in enumerate(operating_points):
            try:
                result = self.identify_offline(
                    model_type=model_type, inflow=operating_inflows[i], outflow=operating_outflows[i],
                    dt=dt, initial_guess=initial_guess, bounds=bounds)
                param_map.append({'operating_point': op_point_val, 'params': result['params']})
            except RuntimeError:
                continue

        if not param_map:
            raise ValueError("Could not identify parameters for any operating point.")

        param_map.sort(key=lambda x: x['operating_point'])

        all_params = [p['params'] for p in param_map]
        avg_params = {k: np.mean([p[k] for p in all_params]) for k in all_params[0]}

        segments = [{'range_start': param_map[0]['operating_point'], 'range_end': param_map[-1]['operating_point'],
                     'params': avg_params, 'points_in_segment': param_map}]

        current_nse = -np.inf
        iter_count = 0

        while current_nse < target_nse and iter_count < max_iter and len(segments) < len(param_map):
            temp_model_bank = [{'max_value': seg['range_end'], 'parameters': seg['params']} for seg in segments]
            sim_outflow = self._run_piecewise_model(
                validation_inflow, temp_model_bank, model_type, dt, initial_outflow=validation_outflow[0])
            current_nse = calculate_nse(sim_outflow, validation_outflow)

            if current_nse >= target_nse:
                break

            variances = []
            for i, seg in enumerate(segments):
                if len(seg['points_in_segment']) < 2:
                    variances.append(-1)
                    continue
                params_in_seg = [p['params'] for p in seg['points_in_segment']]
                total_variance = sum(np.var([p[key] for p in params_in_seg]) for key in params_in_seg[0])
                variances.append(total_variance)

            if not any(v > 0 for v in variances):
                break

            idx_to_split = np.argmax(variances)

            seg_to_split = segments.pop(idx_to_split)
            points = seg_to_split['points_in_segment']
            split_idx = len(points) // 2

            for new_points in [points[:split_idx], points[split_idx:]]:
                if not new_points: continue
                params_in_new_seg = [p['params'] for p in new_points]
                avg_params = {k: np.mean([p[k] for p in params_in_new_seg]) for k in params_in_new_seg[0]}
                new_segment = {'range_start': new_points[0]['operating_point'], 'range_end': new_points[-1]['operating_point'],
                               'params': avg_params, 'points_in_segment': new_points}
                segments.append(new_segment)

            segments.sort(key=lambda x: x['range_start'])
            iter_count += 1

        final_model_bank = [{'condition_variable': 'inflow', 'max_value': seg['range_end'],
                             'parameters': seg['params']} for seg in segments]
        return final_model_bank

    def track_online_rls(self, inflow: np.ndarray, outflow: np.ndarray, dt: float,
                         model_type: str, initial_guess: Dict[str, float], forgetting_factor: float,
                         initial_covariance: float = 1000.0) -> pd.DataFrame:
        """
        Tracks model parameters online using Recursive Least Squares (RLS).
        """
        if model_type != 'Muskingum':
            raise NotImplementedError(f"Online RLS tracking for {model_type} is not yet supported.")

        K0, X0 = initial_guess['K'], initial_guess['X']
        denominator = 2 * K0 * (1 - X0) + dt
        if abs(denominator) < 1e-9:
            raise ValueError("Initial guess for K and X leads to a zero denominator.")
        c1_0 = (dt - 2 * K0 * X0) / denominator
        c2_0 = (dt + 2 * K0 * X0) / denominator
        c3_0 = (2 * K0 * (1 - X0) - dt) / denominator

        theta = np.array([c1_0, c2_0, c3_0])
        P = np.eye(3) * initial_covariance
        lambda_ = forgetting_factor
        history = []

        for k in range(1, len(inflow)):
            H = np.array([inflow[k], inflow[k-1], outflow[k-1]])
            PH_T = P @ H.T
            denominator_gain = lambda_ + H @ PH_T
            if abs(denominator_gain) < 1e-9:
                if history: history.append({**history[-1], 'time': k * dt})
                continue
            K_gain = PH_T / denominator_gain

            prediction = H @ theta
            error = outflow[k] - prediction
            theta = theta + K_gain * error
            P = (1 / lambda_) * (P - np.outer(K_gain, H) @ P)

            c1, c2, c3 = theta[0], theta[1], theta[2]
            K, X = K0, X0
            if abs(1 - c3) > 1e-6 and abs(1 - c1) > 1e-6:
                temp_K = dt * (1 - c1) / (1 - c3)
                temp_X = 0.5 * (c2 - c1) / (1 - c1)
                if temp_K > 0 and 0 <= temp_X <= 0.5:
                    K, X = temp_K, temp_X
                elif history: K, X = history[-1]['K'], history[-1]['X']
            elif history: K, X = history[-1]['K'], history[-1]['X']
            history.append({'time': k * dt, 'K': K, 'X': X})

        return pd.DataFrame(history)

    def track_online_kf(self, model_type: str, inflow: np.ndarray, outflow: np.ndarray, dt: float,
                        initial_guess: Dict[str, float], process_noise: float, measurement_noise: float,
                        initial_covariance: float = 1000.0) -> pd.DataFrame:
        """
        Tracks model parameters online using a Kalman Filter (KF) with an augmented state.
        """
        if model_type != 'Muskingum':
            raise NotImplementedError(f"Online KF tracking for {model_type} is not yet supported.")

        K0, X0 = initial_guess['K'], initial_guess['X']
        denominator = 2 * K0 * (1 - X0) + dt
        if abs(denominator) < 1e-9:
            raise ValueError("Initial guess for K and X leads to a zero denominator.")
        c1_0 = (dt - 2 * K0 * X0) / denominator
        c2_0 = (dt + 2 * K0 * X0) / denominator
        c3_0 = (2 * K0 * (1 - X0) - dt) / denominator

        x0 = np.array([c1_0, c2_0, c3_0])
        F = np.eye(3)
        Q = np.eye(3) * process_noise
        R = np.array([[measurement_noise]])
        P0 = np.eye(3) * initial_covariance
        H0 = np.array([[inflow[1], inflow[0], outflow[0]]])

        kf = KalmanFilter(F=F, H=H0, Q=Q, R=R, x0=x0, P0=P0)
        history = []

        for k in range(1, len(inflow)):
            kf.predict()
            H_k = np.array([[inflow[k], inflow[k-1], outflow[k-1]]])
            kf.H = H_k
            observation = np.array([outflow[k]])
            kf.update(observation)

            estimated_coeffs = kf.get_state()
            c1, c2, c3 = estimated_coeffs[0], estimated_coeffs[1], estimated_coeffs[2]

            K, X = K0, X0
            if abs(1 - c3) > 1e-6 and abs(1 - c1) > 1e-6:
                temp_K = dt * (1 - c1) / (1 - c3)
                temp_X = 0.5 * (c2 - c1) / (1 - c1)
                if temp_K > 0 and 0 <= temp_X <= 0.5:
                    K, X = temp_K, temp_X
                elif history: K, X = history[-1]['K'], history[-1]['X']
            elif history: K, X = history[-1]['K'], history[-1]['X']
            history.append({'time': k * dt, 'K': K, 'X': X})

        return pd.DataFrame(history)
