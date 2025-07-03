# data_generator.py (FINAL VERSION FOR THIS PHASE)
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import networkx as nx
from network_builder import build_simple_water_network # Keep this import

# --- REMOVE THIS LINE: from visualization import visualize_water_network_dynamic ---
# This file should not import visualization.

def generate_sensor_data(network, start_time, end_time, sampling_interval_minutes=5):
    """
    Generates synthetic time-series sensor data (flow, pressure, level).
    """
    time_index = pd.date_range(start=start_time, end=end_time, freq=f'{sampling_interval_minutes}min')
    data = []

    # Get nodes with sensors
    sensor_nodes = [node for node, attrs in network.nodes(data=True) if attrs.get('type') == 'Sensor']

    for timestamp in time_index:
        for sensor_id in sensor_nodes:
            sensor_type = network.nodes[sensor_id]['sensor_type']
            attached_to_node = network.nodes[sensor_id]['attached_to']
            
            value = 0.0
            # Simple simulation logic for sensor values
            if sensor_type == 'Flow':
                if network.nodes[attached_to_node]['type'] == 'ConsumptionZone':
                    base_flow = network.nodes[attached_to_node]['base_demand']
                elif network.nodes[attached_to_node]['type'] == 'Junction':
                    # Estimate flow for junctions based on downstream demands
                    downstream_demand = 0
                    for neighbor in network.successors(attached_to_node):
                        if network.nodes[neighbor]['type'] == 'ConsumptionZone':
                            downstream_demand += network.nodes[neighbor]['base_demand']
                    base_flow = downstream_demand if downstream_demand > 0 else 150 
                else: 
                    base_flow = network.nodes[attached_to_node].get('pump_rate', 0)

                hour = timestamp.hour
                if 0 <= hour < 6:
                    pattern_factor = 0.6 + np.random.normal(0, 0.05)
                elif 6 <= hour < 10:
                    pattern_factor = 1.2 + np.random.normal(0, 0.1)
                elif 10 <= hour < 17:
                    pattern_factor = 0.9 + np.random.normal(0, 0.08)
                elif 17 <= hour < 22:
                    pattern_factor = 1.3 + np.random.normal(0, 0.1)
                else:
                    pattern_factor = 0.7 + np.random.normal(0, 0.05)

                value = max(0, base_flow * pattern_factor + np.random.normal(0, 5))
                
            elif sensor_type == 'Pressure':
                if network.nodes[attached_to_node]['type'] == 'ConsumptionZone':
                    base_pressure = 400000 
                elif network.nodes[attached_to_node]['type'] == 'Junction':
                    base_pressure = 500000 
                elif network.nodes[attached_to_node]['type'] == 'PumpStation':
                    base_pressure = 600000
                elif network.nodes[attached_to_node]['type'] == 'Reservoir':
                    base_pressure = 200000

                value = max(0, base_pressure + np.random.normal(0, 10000))
                
            elif sensor_type == 'Level':
                if attached_to_node == 'R1':
                    initial_level = network.nodes['R1']['current_level']
                    value = initial_level + np.sin(timestamp.dayofyear / 365 * 2 * np.pi) * 50000 \
                            + np.random.normal(0, 10000)
                    value = max(0, min(network.nodes['R1']['capacity'], value))

            data.append({
                'timestamp': timestamp,
                'sensor_id': sensor_id,
                'attached_to': attached_to_node,
                'sensor_type': sensor_type,
                'value': value
            })

    return pd.DataFrame(data)

def generate_consumption_data(network, start_time, end_time, sampling_interval_minutes=5):
    """
    Generates synthetic time-series consumption data for zones.
    """
    time_index = pd.date_range(start=start_time, end=end_time, freq=f'{sampling_interval_minutes}min')
    data = []

    consumption_zones = [node for node, attrs in network.nodes(data=True) if attrs.get('type') == 'ConsumptionZone']

    for timestamp in time_index:
        for zone_id in consumption_zones:
            base_demand = network.nodes[zone_id]['base_demand']
            demand_profile = network.nodes[zone_id]['demand_profile']

            hour = timestamp.hour
            daily_factor = 1.0
            if demand_profile == 'residential':
                if 0 <= hour < 6: daily_factor = 0.5
                elif 6 <= hour < 9: daily_factor = 1.5
                elif 9 <= hour < 17: daily_factor = 0.8
                elif 17 <= hour < 21: daily_factor = 1.8
                else: daily_factor = 0.7
            elif demand_profile == 'commercial':
                if 0 <= hour < 8: daily_factor = 0.2
                elif 8 <= hour < 18: daily_factor = 1.5
                else: daily_factor = 0.4
            elif demand_profile == 'industrial':
                if 0 <= hour < 7 or hour >= 22: daily_factor = 0.7
                else: daily_factor = 1.3
            
            if timestamp.weekday() >= 5: 
                if demand_profile == 'commercial' or demand_profile == 'industrial':
                    daily_factor *= 0.7
                elif demand_profile == 'residential':
                    daily_factor *= 1.1

            day_of_year = timestamp.dayofyear
            seasonal_factor = 1 + 0.2 * np.sin(2 * np.pi * (day_of_year - 170) / 365)

            value = max(0, base_demand * daily_factor * seasonal_factor + np.random.normal(0, 2))

            data.append({
                'timestamp': timestamp,
                'zone_id': zone_id,
                'consumption_liters_per_sec': value
            })
    return pd.DataFrame(data)

def inject_leak_event(sensor_df, network, leak_node_id, start_time, end_time, severity_factor=0.2):
    """
    Injects a simulated leak event into sensor data.
    Increases flow in pipes leading to the leak and decreases pressure around it.
    
    leak_node_id: The node (e.g., Junction) where the leak occurs.
    severity_factor: How much the flow/pressure changes (e.g., 0.2 means 20% deviation).
    """
    print(f"Injecting leak at {leak_node_id} from {start_time} to {end_time}")
    
    upstream_nodes = list(nx.ancestors(network, leak_node_id))
    
    for _, row in sensor_df.iterrows():
        if start_time <= row['timestamp'] <= end_time:
            if row['sensor_type'] == 'Flow' and (row['attached_to'] in upstream_nodes or row['attached_to'] == leak_node_id):
                 sensor_df.loc[sensor_df.index == row.name, 'value'] = row['value'] * (1 + severity_factor * np.random.uniform(0.8, 1.2))
            
            if row['sensor_type'] == 'Pressure' and (row['attached_to'] in upstream_nodes or row['attached_to'] == leak_node_id):
                sensor_df.loc[sensor_df.index == row.name, 'value'] = row['value'] * (1 - severity_factor * np.random.uniform(0.8, 1.2))
    
    return sensor_df


if __name__ == '__main__':
    # This block is for independent testing of data generation only.
    # The main execution will happen in main.py
    G = build_simple_water_network()
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 1, 2) # Just a day for quick test
    sensor_df_test = generate_sensor_data(G, start_date, end_date, sampling_interval_minutes=60)
    consumption_df_test = generate_consumption_data(G, start_date, end_date, sampling_interval_minutes=60)
    print("Data generation test successful (1 day).")
    print(sensor_df_test.head())
    # No plots here, as visualization is handled by visualization.py