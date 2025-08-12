import matplotlib.pyplot as plt
from pid_controller import PID
from water_tank_simulator import WaterTank

def main():
    # Simulation parameters
    total_time = 100  # seconds
    dt = 0.1         # time step

    # Water tank parameters
    tank_area = 1.0
    initial_level = 0.0
    q_out = 0.5  # Constant outflow

    # PID controller parameters
    Kp = 2.0
    Ki = 0.5
    Kd = 1.0
    setpoint = 10.0

    # Initialize objects
    tank = WaterTank(tank_area, initial_level)
    pid = PID(Kp, Ki, Kd, setpoint)

    # Simulation loop
    time_points = []
    level_points = []

    for t in range(int(total_time / dt)):
        current_time = t * dt

        # Get current water level
        current_level = tank.level

        # Update PID controller
        q_in = pid.update(current_level, dt)

        # Ensure inflow is non-negative
        if q_in < 0:
            q_in = 0

        # Update water tank
        tank.update(q_in, q_out, dt)

        # Store data for plotting
        time_points.append(current_time)
        level_points.append(tank.level)

        # Print status
        print(f"Time: {current_time:.2f}s, Level: {tank.level:.2f}m, Inflow: {q_in:.2f}")

    # Plotting the results
    plt.figure()
    plt.plot(time_points, level_points, label='Water Level')
    plt.axhline(y=setpoint, color='r', linestyle='--', label='Setpoint')
    plt.xlabel('Time (s)')
    plt.ylabel('Water Level (m)')
    plt.title('Water Tank PID Control')
    plt.legend()
    plt.grid(True)
    plt.savefig('water_level_simulation.png')
    plt.show()

if __name__ == "__main__":
    main()
