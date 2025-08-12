import numpy as np

from basic_tools.loggers import CSVLogger
from modeling.storage_models import FirstOrderInertiaModel, IntegralDelayModel
from modeling.control_structure_models import GateModel
from control.pid_controller import PIDController
from disturbances.disturbance_models import RainfallModel, WaterConsumptionModel

def main():
    # Simulation parameters
    dt = 1.0  # time step (hours)
    simulation_time = 24 * 7  # 1 week
    n_steps = int(simulation_time / dt)

    # System components
    # Reservoir
    reservoir = FirstOrderInertiaModel(initial_storage=1000, time_constant=50)

    # River
    river = IntegralDelayModel(initial_outflow=10, delay_steps=5)

    # Gate
    gate = GateModel(discharge_coefficient=0.6, area=1.0)

    # Disturbances
    rainfall_pattern = [5] * (24*2) + [0] * (24*5) # Rain for 2 days
    rainfall = RainfallModel(rainfall_pattern)

    consumption_pattern = [10] * 24 * 7 # Constant consumption
    consumption = WaterConsumptionModel(consumption_pattern)

    # Controller
    pid = PIDController(kp=0.5, ki=0.1, kd=0.01, setpoint=1000)

    # Logger
    logger = CSVLogger("simulation_log.csv", ["time", "reservoir_storage", "river_outflow", "gate_flow", "control_output"])

    # Simulation loop
    for t in range(n_steps):
        # Get disturbances
        current_rainfall = rainfall.get_rainfall(t)
        current_consumption = consumption.get_consumption(t)

        # Reservoir inflow
        reservoir_inflow = current_rainfall # Simplified: rainfall directly into reservoir

        # Control
        control_output = pid.calculate(reservoir.storage, dt)

        # Gate operation
        # For simplicity, let's assume control_output directly controls gate opening area
        gate.area = max(0, control_output)

        # Calculate flows
        # Assume reservoir water level is proportional to storage
        reservoir_level = reservoir.storage / 100
        downstream_level = 5 # constant downstream level
        gate_flow = gate.calculate_flow(reservoir_level, downstream_level)

        # Update models
        reservoir_net_inflow = reservoir_inflow - gate_flow - current_consumption
        reservoir.step(reservoir_net_inflow)
        river_outflow = river.step(gate_flow) # Outflow from gate is inflow to river

        # Log data
        logger.log([t, reservoir.storage, river_outflow, gate_flow, control_output])

    print("Simulation complete. Log saved to simulation_log.csv")

if __name__ == "__main__":
    main()
