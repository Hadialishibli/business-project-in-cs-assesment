# network_builder.py
import networkx as nx
import random

def build_simple_water_network():
    """
    Builds a simplified smart water network using NetworkX.
    Nodes can be:
    - 'R': Reservoir
    - 'P': Pump Station
    - 'J': Junction/Intersection
    - 'Z': Consumption Zone (e.g., residential, commercial areas)
    - 'S': Sensor (can be attached to J or Z for flow/pressure)
    - 'V': Valve
    
    Edges represent pipes with properties.
    """
    G = nx.DiGraph() # Directed graph for water flow

    # Add Nodes with attributes (e.g., location, type)
    # Using arbitrary coordinates for now, could be real geo-coords.

    # Reservoir
    G.add_node('R1', type='Reservoir', capacity=1000000, current_level=900000, coords=(0, 0)) # Liters

    # Pump Stations
    G.add_node('P1', type='PumpStation', status='on', pump_rate=500, coords=(10, 5)) # Liters/sec
    G.add_node('P2', type='PumpStation', status='on', pump_rate=400, coords=(15, 10))

    # Junctions
    G.add_node('J1', type='Junction', coords=(20, 15))
    G.add_node('J2', type='Junction', coords=(25, 20))
    G.add_node('J3', type='Junction', coords=(30, 10))
    G.add_node('J4', type='Junction', coords=(35, 15))

    # Consumption Zones (e.g., District Metering Areas - DMAs)
    G.add_node('Z1', type='ConsumptionZone', demand_profile='residential', base_demand=100, coords=(40, 5)) # Liters/sec
    G.add_node('Z2', type='ConsumptionZone', demand_profile='commercial', base_demand=80, coords=(45, 10))
    G.add_node('Z3', type='ConsumptionZone', demand_profile='industrial', base_demand=120, coords=(50, 20))

    # Valves (can control flow to zones or sections)
    G.add_node('V1', type='Valve', status='open', coords=(22, 12)) # Controls flow to J2 from J1
    G.add_node('V2', type='Valve', status='open', coords=(32, 12)) # Controls flow to Z3 from J3

    # Add Pipes (Edges) with attributes (e.g., length, diameter, material)
    # Adding a rough length for pressure calculations later
    G.add_edge('R1', 'P1', length=500, diameter=0.8, material='PVC')
    G.add_edge('R1', 'P2', length=600, diameter=0.7, material='CastIron')

    G.add_edge('P1', 'J1', length=300, diameter=0.6, material='PVC')
    G.add_edge('P2', 'J3', length=400, diameter=0.5, material='DuctileIron')

    G.add_edge('J1', 'V1', length=100, diameter=0.4, material='PVC') # Pipe to valve
    G.add_edge('V1', 'J2', length=50, diameter=0.4, material='PVC') # Valve to junction

    G.add_edge('J1', 'Z1', length=250, diameter=0.3, material='PVC') # Direct connection
    
    G.add_edge('J2', 'J4', length=200, diameter=0.4, material='DuctileIron')
    G.add_edge('J3', 'V2', length=150, diameter=0.3, material='PVC') # Pipe to valve
    G.add_edge('V2', 'Z3', length=100, diameter=0.3, material='PVC') # Valve to zone
    
    G.add_edge('J4', 'Z2', length=150, diameter=0.3, material='PVC')
    G.add_edge('J4', 'Z3', length=100, diameter=0.3, material='PVC') # Z3 can also get water from J4

    # Add sensors to relevant nodes (e.g., flow/pressure at junctions and consumption zones)
    # We'll associate sensors with specific nodes for data generation
    # For simplicity, let's assume one flow and one pressure sensor per monitored node.
    G.add_node('S_F_J1', type='Sensor', sensor_type='Flow', attached_to='J1', coords=(19,16))
    G.add_node('S_P_J1', type='Sensor', sensor_type='Pressure', attached_to='J1', coords=(19.5,15.5))
    G.add_node('S_F_Z1', type='Sensor', sensor_type='Flow', attached_to='Z1', coords=(39,6))
    G.add_node('S_P_Z1', type='Sensor', sensor_type='Pressure', attached_to='Z1', coords=(39.5,5.5))
    G.add_node('S_F_Z2', type='Sensor', sensor_type='Flow', attached_to='Z2', coords=(44,11))
    G.add_node('S_P_Z2', type='Sensor', sensor_type='Pressure', attached_to='Z2', coords=(44.5,10.5))
    G.add_node('S_F_Z3', type='Sensor', sensor_type='Flow', attached_to='Z3', coords=(49,21))
    G.add_node('S_P_Z3', type='Sensor', sensor_type='Pressure', attached_to='Z3', coords=(49.5,20.5))
    G.add_node('S_L_R1', type='Sensor', sensor_type='Level', attached_to='R1', coords=(1,0.5)) # Reservoir level sensor

    # Store sensor associations
    G.nodes['J1']['sensors'] = ['S_F_J1', 'S_P_J1']
    G.nodes['Z1']['sensors'] = ['S_F_Z1', 'S_P_Z1']
    G.nodes['Z2']['sensors'] = ['S_F_Z2', 'S_P_Z2']
    G.nodes['Z3']['sensors'] = ['S_F_Z3', 'S_P_Z3']
    G.nodes['R1']['sensors'] = ['S_L_R1']


    print(f"Network created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
    return G

if __name__ == '__main__':
    # Example usage and basic visualization
    import matplotlib.pyplot as plt

    G = build_simple_water_network()

    pos = {node: G.nodes[node]['coords'] for node in G.nodes() if 'coords' in G.nodes[node]}
    
    node_colors = []
    node_labels = {}
    for node, data in G.nodes(data=True):
        if data['type'] == 'Reservoir':
            node_colors.append('blue')
        elif data['type'] == 'PumpStation':
            node_colors.append('red')
        elif data['type'] == 'Junction':
            node_colors.append('green')
        elif data['type'] == 'ConsumptionZone':
            node_colors.append('purple')
        elif data['type'] == 'Sensor':
            node_colors.append('orange')
        elif data['type'] == 'Valve':
            node_colors.append('cyan')
        else:
            node_colors.append('grey')
        
        node_labels[node] = node # Use node ID as label

    plt.figure(figsize=(12, 8))
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=1000, alpha=0.8)
    nx.draw_networkx_edges(G, pos, width=2, alpha=0.5, edge_color='gray')
    nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=8)
    
    plt.title("Simplified Smart Water Network Topology")
    plt.grid(True)
    plt.show()

    # Print some node/edge details for verification
    print("\nNode Details:")
    for node, data in G.nodes(data=True):
        print(f"  Node: {node}, Type: {data.get('type')}, Coords: {data.get('coords')}")
    
    print("\nEdge Details:")
    for u, v, data in G.edges(data=True):
        print(f"  Pipe from {u} to {v}, Length: {data.get('length')}m, Diameter: {data.get('diameter')}m")