# main.py (NEW SCRIPT)
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt # For basic time-series plots

# Import functions from our modules
from network_builder import build_simple_water_network
from data_generator import generate_sensor_data, generate_consumption_data, inject_leak_event
from visualization import visualize_water_network_dynamic

if __name__ == '__main__':
    print("--- Smart Water Grid Simulation: Starting Orchestration ---")

    # 1. Build the Network
    G = build_simple_water_network()
    print("\nNetwork built successfully.")

    # 2. Define Simulation Timeframe
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 1, 8) # One week of data
    sampling_interval_minutes = 15
    print(f"\nSimulating data from {start_date} to {end_date} with {sampling_interval_minutes}-minute intervals.")

    # 3. Generate Raw Sensor Data
    sensor_df = generate_sensor_data(G, start_date, end_date, sampling_interval_minutes)
    print("\nRaw sensor data generated.")
    # print(sensor_df.head()) # Uncomment to see head of data

    # 4. Generate Consumption Data
    consumption_df = generate_consumption_data(G, start_date, end_date, sampling_interval_minutes)
    print("\nConsumption data generated.")
    # print(consumption_df.head()) # Uncomment to see head of data

    # 5. Inject a Leak Event
    leak_start_time = datetime(2023, 1, 3, 10, 0)
    leak_end_time = datetime(2023, 1, 4, 18, 0)
    leak_node = 'J1' # Leak at junction J1
    sensor_df = inject_leak_event(sensor_df, G, leak_node, leak_start_time, leak_end_time, severity_factor=0.3)
    print(f"\nLeak injected at {leak_node} between {leak_start_time} and {leak_end_time}.")

    # 6. Dynamic Network Visualization (State at specific timestamps)
    print("\nDisplaying dynamic network visualizations:")

    # Choose a timestamp during the leak for visualization
    vis_timestamp_during_leak = pd.to_datetime('2023-01-03 14:00:00')
    active_leak_nodes_during = [leak_node] if leak_start_time <= vis_timestamp_during_leak <= leak_end_time else []
    
    print(f"  Visualizing network state at {vis_timestamp_during_leak} (during leak).")
    visualize_water_network_dynamic(G, sensor_df, vis_timestamp_during_leak, 
                                     leak_nodes=active_leak_nodes_during,
                                     title="Smart Water Network State - During Leak")

    # Choose a timestamp before the leak for comparison
    vis_timestamp_before_leak = pd.to_datetime('2023-01-02 12:00:00')
    print(f"  Visualizing network state at {vis_timestamp_before_leak} (before leak).")
    visualize_water_network_dynamic(G, sensor_df, vis_timestamp_before_leak, 
                                     leak_nodes=[], # No active leaks
                                     title="Smart Water Network State - Before Leak")

    # 7. Basic Time-Series Plots (Existing from data_generator.py, moved here)
    print("\nDisplaying time-series plots...")

    # Plot reservoir level
    plt.figure(figsize=(14, 6))
    reservoir_level_data = sensor_df[(sensor_df['sensor_id'] == 'S_L_R1')]
    plt.plot(reservoir_level_data['timestamp'], reservoir_level_data['value'])
    plt.title('Simulated Reservoir 1 Level Over Time')
    plt.xlabel('Timestamp')
    plt.ylabel('Level (Liters)')
    plt.grid(True)
    plt.show()

    # Plot a consumption zone's flow and pressure (with leak effect)
    plt.figure(figsize=(14, 10))

    # Flow at Z1
    plt.subplot(2, 1, 1)
    z1_flow_data = sensor_df[(sensor_df['sensor_id'] == 'S_F_Z1')]
    plt.plot(z1_flow_data['timestamp'], z1_flow_data['value'], label='Z1 Flow')
    plt.axvspan(leak_start_time, leak_end_time, color='red', alpha=0.2, label='Leak Event')
    plt.title('Simulated Zone Z1 Flow Rate (L/s)')
    plt.xlabel('Timestamp')
    plt.ylabel('Flow (L/s)')
    plt.legend()
    plt.grid(True)

    # Pressure at J1 (where leak is injected)
    plt.subplot(2, 1, 2)
    j1_pressure_data = sensor_df[(sensor_df['sensor_id'] == 'S_P_J1')]
    plt.plot(j1_pressure_data['timestamp'], j1_pressure_data['value'], label='J1 Pressure')
    plt.axvspan(leak_start_time, leak_end_time, color='red', alpha=0.2, label='Leak Event')
    plt.title('Simulated Junction J1 Pressure (Pa)')
    plt.xlabel('Timestamp')
    plt.ylabel('Pressure (Pa)')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    # Plot overall consumption for a zone
    plt.figure(figsize=(14, 6))
    z1_consumption_data = consumption_df[(consumption_df['zone_id'] == 'Z1')]
    plt.plot(z1_consumption_data['timestamp'], z1_consumption_data['consumption_liters_per_sec'])
    plt.title('Simulated Zone Z1 Consumption (L/s)')
    plt.xlabel('Timestamp')
    plt.ylabel('Consumption (L/s)')
    plt.grid(True)
    plt.show()

    print("\n--- Simulation complete ---")