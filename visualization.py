# visualization.py (FINAL VERSION FOR THIS PHASE)
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd 



def visualize_water_network_dynamic(G, sensor_df, timestamp, leak_nodes=None, title="Smart Water Network State"):
    """
    Visualizes the smart water network dynamically based on sensor data at a specific timestamp.

    Args:
        G (nx.DiGraph): The networkx graph representing the water network.
        sensor_df (pd.DataFrame): DataFrame containing sensor data.
        timestamp (datetime): The specific timestamp to visualize the network's state.
        leak_nodes (list): Optional list of node IDs where leaks are active at this timestamp.
        title (str): Title for the plot.
    """
    if not isinstance(G, nx.DiGraph):
        raise TypeError("Input graph must be a NetworkX DiGraph.")
    if not isinstance(sensor_df, pd.DataFrame):
        raise TypeError("sensor_df must be a pandas DataFrame.")
    if not isinstance(timestamp, pd.Timestamp):
        timestamp = pd.to_datetime(timestamp)

    # Filter sensor data for the specific timestamp
    current_sensor_data = sensor_df[sensor_df['timestamp'] == timestamp]
    if current_sensor_data.empty:
        print(f"Warning: No exact data found for timestamp {timestamp}. Attempting nearest.")
        # Find the row closest to the desired timestamp
        idx = (sensor_df['timestamp'] - timestamp).abs().argsort()[:1]
        current_sensor_data = sensor_df.loc[idx]
        if current_sensor_data.empty:
            print(f"Error: No data found even for nearest timestamp to {timestamp}. Aborting visualization.")
            return

    pos = {node: G.nodes[node]['coords'] for node in G.nodes() if 'coords' in G.nodes[node]}

    plt.figure(figsize=(16, 12))

    # --- Draw Nodes ---
    node_colors = []
    node_sizes = []
    node_labels = {}
    node_border_colors = [] 
    
    pressure_values = current_sensor_data[current_sensor_data['sensor_type'] == 'Pressure']['value']
    if not pressure_values.empty:
        norm = mcolors.Normalize(vmin=pressure_values.min(), vmax=pressure_values.max())
        cmap = plt.cm.viridis
    else:
        norm = mcolors.Normalize(vmin=0, vmax=1)
        cmap = plt.cm.gray

    for node, data in G.nodes(data=True):
        node_border_color = 'black' 

        if data['type'] == 'Reservoir':
            node_colors.append('blue')
            node_sizes.append(2000)
        elif data['type'] == 'PumpStation':
            node_colors.append('red')
            node_sizes.append(1500)
        elif data['type'] == 'Junction':
            pressure_sensor_id = None
            for s_id in data.get('sensors', []):
                if G.nodes[s_id]['sensor_type'] == 'Pressure':
                    pressure_sensor_id = s_id
                    break
            
            if pressure_sensor_id:
                sensor_reading = current_sensor_data[
                    (current_sensor_data['sensor_id'] == pressure_sensor_id)
                ]
                if not sensor_reading.empty:
                    pressure = sensor_reading['value'].iloc[0]
                    node_colors.append(cmap(norm(pressure)))
                else:
                    node_colors.append('green')
            else:
                node_colors.append('green')
            node_sizes.append(900)
            
            if leak_nodes and node in leak_nodes:
                node_border_color = 'red'
                node_sizes[-1] = 1200
        
        elif data['type'] == 'ConsumptionZone':
            pressure_sensor_id = None
            for s_id in data.get('sensors', []):
                if G.nodes[s_id]['sensor_type'] == 'Pressure':
                    pressure_sensor_id = s_id
                    break
            
            if pressure_sensor_id:
                sensor_reading = current_sensor_data[
                    (current_sensor_data['sensor_id'] == pressure_sensor_id)
                ]
                if not sensor_reading.empty:
                    pressure = sensor_reading['value'].iloc[0]
                    node_colors.append(cmap(norm(pressure)))
                else:
                    node_colors.append('purple')
            else:
                node_colors.append('purple')

            node_sizes.append(1000)
            if leak_nodes and node in leak_nodes: 
                node_border_color = 'red'
                node_sizes[-1] = 1300

        elif data['type'] == 'Valve':
            node_colors.append('lightgray')
            node_sizes.append(700)
        elif data['type'] == 'Sensor':
            node_colors.append('orange')
            node_sizes.append(300)
        else:
            node_colors.append('grey')
            node_sizes.append(500)
        
        node_labels[node] = node
        node_border_colors.append(node_border_color)

    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, 
                           alpha=0.9, linewidths=2, edgecolors=node_border_colors)
    
    if not pressure_values.empty:
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=plt.gca(), orientation='vertical', fraction=0.02, pad=0.02)
        cbar.set_label('Pressure (Pa)', rotation=270, labelpad=15)

    # --- Draw Edges (Pipes) and Color by Flow Rate ---
    edge_colors = []
    edge_widths = []
    
    flow_values = current_sensor_data[current_sensor_data['sensor_type'] == 'Flow']['value']
    if not flow_values.empty:
        flow_norm = mcolors.Normalize(vmin=flow_values.min(), vmax=flow_values.max())
        flow_cmap = plt.cm.Blues
    else:
        flow_norm = mcolors.Normalize(vmin=0, vmax=1)
        flow_cmap = plt.cm.gray

    for u, v, data in G.edges(data=True):
        flow_value_proxy = 0
        if G.nodes[u]['type'] == 'PumpStation':
            flow_value_proxy = G.nodes[u]['pump_rate']
        elif G.nodes[v]['type'] == 'ConsumptionZone':
            flow_sensor_id = None
            for s_id in G.nodes[v].get('sensors', []):
                if G.nodes[s_id]['sensor_type'] == 'Flow':
                    flow_sensor_id = s_id
                    break
            if flow_sensor_id:
                sensor_reading = current_sensor_data[
                    (current_sensor_data['sensor_id'] == flow_sensor_id)
                ]
                if not sensor_reading.empty:
                    flow_value_proxy = sensor_reading['value'].iloc[0]
                else:
                    flow_value_proxy = G.nodes[v]['base_demand'] * 0.8
            else:
                 flow_value_proxy = G.nodes[v]['base_demand'] * 0.8


        edge_colors.append(flow_cmap(flow_norm(flow_value_proxy)))
        edge_widths.append(max(1, flow_value_proxy / 50))
        
        if leak_nodes and (u in leak_nodes or v in leak_nodes):
            edge_widths[-1] += 2
            edge_colors[-1] = 'orange'

    nx.draw_networkx_edges(G, pos, width=edge_widths, alpha=0.7, edge_color=edge_colors, arrows=True, arrowsize=20)

    if not flow_values.empty:
        sm_flow = plt.cm.ScalarMappable(cmap=flow_cmap, norm=flow_norm)
        sm_flow.set_array([])
        cbar_flow = plt.colorbar(sm_flow, ax=plt.gca(), orientation='vertical', fraction=0.02, pad=0.08)
        cbar_flow.set_label('Flow (L/s)', rotation=270, labelpad=15)

    nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=8, font_weight='bold', bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))
    
    plt.title(f"{title} at {timestamp.strftime('%Y-%m-%d %H:%M')}", size=16)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.xlabel("X Coordinate")
    plt.ylabel("Y Coordinate")
    plt.axis('on') 
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    # This block is for independent testing of visualization only.
    # The main execution will happen in main.py
    # This test block would typically load dummy data or a small pre-defined dataset
    print("Visualization module test: This module is intended to be called by main.py.")
    print("Please run main.py to see the full visualization flow.")