# --- START OF FILE mpc_controller.py ---
# 这是最终的、修正了 deepcopy 陷阱的权威版本

import cvxpy as cp
import numpy as np
import copy
from .base_controller import BaseController
from chs_sdk.modules.modeling.base_model import BaseModel


class MPCController(BaseController):
    def __init__(self,
                 prediction_model: BaseModel,
                 prediction_horizon: int,
                 control_horizon: int,
                 set_point: float,
                 q_weight: float = 1.0,
                 r_weight: float = 0.1,
                 u_min: float = -np.inf,
                 u_max: float = np.inf,
                 **kwargs):
        super().__init__(**kwargs)
        if not isinstance(prediction_model, BaseModel):
            raise TypeError("prediction_model必须是BaseModel的子类。")
        if not (control_horizon <= prediction_horizon and control_horizon > 0):
            raise ValueError("控制时域 M 必须 > 0 且 <= 预测时域 P。")
        self.prediction_model = prediction_model
        self.P = prediction_horizon
        self.M = control_horizon
        self.set_point = set_point
        self.q_weight = q_weight
        self.r_weight = r_weight
        self.u_min = u_min
        self.u_max = u_max
        self.last_optimal_u = np.zeros(self.M)
        self.current_control_action = 0.0
        self.u_M = cp.Variable(self.M, name="u_M")
        self.x_P = cp.Variable(self.P + 1, name="x_P")
        self.x_init = cp.Parameter(1, name="x_init")
        self.A_pred = cp.Parameter((self.P, 1), name="A_pred")
        self.B_pred = cp.Parameter((self.P, self.M), name="B_pred")
        self.C_pred = cp.Parameter(self.P, name="C_pred")
        objective = 0
        constraints = [self.x_P[0] == self.x_init]
        for k in range(self.P):
            objective += self.q_weight * cp.power(self.x_P[k + 1] - self.set_point, 2)
        for k in range(self.M):
            objective += self.r_weight * cp.power(self.u_M[k], 2)
        constraints += [self.u_M >= self.u_min, self.u_M <= self.u_max]
        constraints += [self.x_P[1:] == self.A_pred @ self.x_init + self.B_pred @ self.u_M + self.C_pred]
        self.problem = cp.Problem(cp.Minimize(objective), constraints)

    def _linearize_model_at_point(self, model_instance: BaseModel, current_state: float):
        dt = getattr(getattr(model_instance, 'solver', None), 'dt', 1.0)

        # 1. 计算零输入响应
        model_c = copy.deepcopy(model_instance)
        # ★★★ 关键修正 ★★★
        # 修正克隆体求解器的"电话号码"，让它指向克隆体自己的微分方程
        if hasattr(model_c, 'ode_function') and hasattr(model_c, 'solver'):
            model_c.solver.f = model_c.ode_function

        model_c.state.storage = current_state
        free_response = np.zeros(self.P)
        for i in range(self.P):
            model_c.input.inflow = 0.0
            model_c.step(t=i, dt=dt)
            free_response[i] = model_c.get_state()['storage']

        # 2. 计算受控响应
        B = np.zeros((self.P, self.M))
        delta_u = 1e-5
        for j in range(self.M):
            model_b = copy.deepcopy(model_instance)
            # ★★★ 关键修正 ★★★
            # 同样修正这个克隆体的求解器
            if hasattr(model_b, 'ode_function') and hasattr(model_b, 'solver'):
                model_b.solver.f = model_b.ode_function

            model_b.state.storage = current_state
            u_sequence = np.zeros(self.P)
            u_sequence[j:] = delta_u
            forced_response_j = np.zeros(self.P)
            for i in range(self.P):
                model_b.input.inflow = u_sequence[i]
                model_b.step(t=i, dt=dt)
                forced_response_j[i] = model_b.get_state()['storage']
            B[:, j] = (forced_response_j - free_response) / delta_u

        A = np.zeros((self.P, 1))
        C = free_response
        return A, B, C

    def step(self, current_state: float, **kwargs):
        A, B, C = self._linearize_model_at_point(self.prediction_model, current_state)
        self.x_init.value = np.array([float(current_state)])
        self.A_pred.value = A
        self.B_pred.value = B
        self.C_pred.value = C
        try:
            self.problem.solve(solver=cp.OSQP, warm_start=True)
            if self.problem.status in ["infeasible", "unbounded"]:
                print(f"警告: MPC 问题 {self.problem.status}.")
            else:
                self.last_optimal_u = self.u_M.value
        except Exception as e:
            print(f"MPC 求解出错: {e}.")
        if self.last_optimal_u is None:
            self.last_optimal_u = np.zeros(self.M)
        self.current_control_action = self.last_optimal_u[0]
        return self.current_control_action

    def get_state(self):
        return {'output': self.current_control_action}