import time
# Import the main functions from our target scripts
# Note: The 2D inflow example uses a 'main' function which includes setup/teardown
# The semi-distributed example uses a 'run_simulation' function
from examples.case_12_simple_2d_inflow import main as run_2d_inflow_case
from examples.case_10_semi_distributed_simulation import run_simulation as run_hydrology_case

def run_benchmark(func, name, iterations=1):
    """
    A simple benchmarking function.

    Args:
        func (callable): The function to benchmark.
        name (str): The name of the benchmark.
        iterations (int): How many times to run the function.
    """
    print(f"--- Running benchmark: {name} ---")
    total_time = 0

    # Run once to handle any initial setup or JIT compilation overhead
    print("Performing a warm-up run...")
    func()
    print("Warm-up complete.")

    print(f"Running {iterations} iteration(s)...")
    for i in range(iterations):
        start_time = time.perf_counter()
        func()
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        print(f"Iteration {i+1}/{iterations} took {elapsed_time:.4f} seconds.")
        total_time += elapsed_time

    avg_time = total_time / iterations
    print(f"Average time for {name}: {avg_time:.4f} seconds")
    print("-" * (28 + len(name)))
    print("\n")
    return avg_time

def main():
    """
    Main function to run all benchmarks.
    """
    print("=======================================")
    print("  CHS SDK PERFORMANCE BENCHMARK (BEFORE)  ")
    print("=======================================")
    print("This script will run simulations to establish a performance baseline.")
    print("The timings gathered here will be compared against the optimized versions.\n")

    # For the 2D case, we only run it once as it's slower and has file I/O
    run_benchmark(run_2d_inflow_case, "2D Hydrodynamic Model (case_12)", iterations=1)

    # The hydrology case is faster, so we can run it multiple times for a better average
    # However, for a simple before/after, one run is sufficient to show the difference.
    run_benchmark(run_hydrology_case, "Semi-Distributed Hydrology Model (case_10)", iterations=1)

if __name__ == "__main__":
    main()
