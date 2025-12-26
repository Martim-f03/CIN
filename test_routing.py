# test_routing.py

import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import routing
import math

# -----------------------------
# --- Função Haversine
# -----------------------------
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

# -----------------------------
# --- Configurações
# -----------------------------
STCP_PATH = "dataset/stcp"
METRO_PATH = "dataset/metro_porto"
MAX_DISTANCE_KM = 0.05  # 50 metros
DEFAULT_WALK_SPEED = 5.0  # km/h

# -----------------------------
# --- Carregar stops
# -----------------------------
stcp_stops = pd.read_csv(f"{STCP_PATH}/stops.txt")
metro_stops = pd.read_csv(f"{METRO_PATH}/stops.txt")
stcp_stops['operator'] = 'STCP'
metro_stops['operator'] = 'Metro'

# -----------------------------
# --- Carregar trips (route_id e service_id)
# -----------------------------
stcp_trips = pd.read_csv(f"{STCP_PATH}/trips.txt")
metro_trips = pd.read_csv(f"{METRO_PATH}/trips.txt")
stcp_trip_to_route = dict(zip(stcp_trips['trip_id'], stcp_trips['route_id']))
stcp_trip_to_service = dict(zip(stcp_trips['trip_id'], stcp_trips['service_id']))
metro_trip_to_route = dict(zip(metro_trips['trip_id'], metro_trips['route_id']))
metro_trip_to_service = dict(zip(metro_trips['trip_id'], metro_trips['service_id']))

# -----------------------------
# --- Criar arestas originais
# -----------------------------
def create_edges(stop_times_file, operator, trip_to_route, trip_to_service):
    stop_times = pd.read_csv(stop_times_file)
    edges = []
    for trip_id, group in stop_times.groupby("trip_id"):
        group = group.sort_values("stop_sequence")
        stops = group["stop_id"].tolist()
        route_id = trip_to_route.get(trip_id)
        service_id = trip_to_service.get(trip_id)
        for i in range(len(stops) - 1):
            edges.append({
                'from': stops[i],
                'to': stops[i+1],
                'trip_id': trip_id,
                'route_id': route_id,
                'service_id': service_id,
                'operator': operator
            })
    return edges

edges_stcp = create_edges(f"{STCP_PATH}/stop_times.txt", "STCP", stcp_trip_to_route, stcp_trip_to_service)
edges_metro = create_edges(f"{METRO_PATH}/stop_times.txt", "Metro", metro_trip_to_route, metro_trip_to_service)
all_edges = edges_stcp + edges_metro

# -----------------------------
# --- Posições dos nós
# -----------------------------
node_positions = {**{r['stop_id']: (r['stop_lon'], r['stop_lat']) for _, r in stcp_stops.iterrows()},
                  **{r['stop_id']: (r['stop_lon'], r['stop_lat']) for _, r in metro_stops.iterrows()}}

# -----------------------------
# --- Criar clusters multimodais
# -----------------------------
multimodal_clusters = []
stcp_stops['is_multimodal'] = False
metro_stops['is_multimodal'] = False
mm_id_counter = 1
for _, metro in metro_stops.iterrows():
    close_stcp = stcp_stops[
        stcp_stops.apply(lambda r: haversine_distance(r['stop_lat'], r['stop_lon'], metro['stop_lat'], metro['stop_lon']) <= MAX_DISTANCE_KM, axis=1)
    ]
    if not close_stcp.empty:
        mm_id = f"M{mm_id_counter:03d}"
        mm_id_counter += 1
        multimodal_clusters.append({
            'multimodal_id': mm_id,
            'lat': (close_stcp['stop_lat'].sum() + metro['stop_lat']) / (len(close_stcp)+1),
            'lon': (close_stcp['stop_lon'].sum() + metro['stop_lon']) / (len(close_stcp)+1),
            'stcp_stops': close_stcp['stop_id'].tolist(),
            'metro_stops': [metro['stop_id']]
        })
        stcp_stops.loc[close_stcp.index, 'is_multimodal'] = True
        metro_stops.loc[metro_stops['stop_id'] == metro['stop_id'], 'is_multimodal'] = True

# -----------------------------
# --- Mapear stops → multimodal
# -----------------------------
mm_mapping = {}
for c in multimodal_clusters:
    for s in c['stcp_stops'] + c['metro_stops']:
        mm_mapping[s] = c['multimodal_id']
    node_positions[c['multimodal_id']] = (c['lon'], c['lat'])

# -----------------------------
# --- Atualizar arestas com multimodal
# -----------------------------
updated_edges = []
for e in all_edges:
    updated_edges.append({
        'from': mm_mapping.get(e['from'], e['from']),
        'to': mm_mapping.get(e['to'], e['to']),
        'operator': e['operator'],
        'trip_id': e['trip_id'],
        'route_id': e['route_id'],
        'service_id': e['service_id']
    })
# Ligações multimodais (a pé)
for c in multimodal_clusters:
    for s in c['stcp_stops'] + c['metro_stops']:
        updated_edges.append({'from': s, 'to': c['multimodal_id'], 'operator': 'LINK', 'trip_id': None, 'route_id': None, 'service_id': None})
        updated_edges.append({'from': c['multimodal_id'], 'to': s, 'operator': 'LINK', 'trip_id': None, 'route_id': None, 'service_id': None})

# -----------------------------
# --- Lista de nós
# -----------------------------
all_nodes = list(stcp_stops['stop_id']) + list(metro_stops['stop_id']) + [c['multimodal_id'] for c in multimodal_clusters]

# -----------------------------
# --- Teste de routing
# -----------------------------
def main():
    start_node = "CRG2"
    end_node = "M024"

    # Adicionar posições para edges LINK
    for e in updated_edges:
        if e['operator'] == 'LINK':
            e['from_pos'] = node_positions[e['from']]
            e['to_pos'] = node_positions[e['to']]

    # Calcular tempo
    routing.compute_travel_time(updated_edges, DEFAULT_WALK_SPEED)

    # Garantir travel_time numérico
    for e in updated_edges:
        e['travel_time'] = float(e.get('travel_time', 1))

    # Dijkstra
    total_time, path = routing.dijkstra(all_nodes, updated_edges, start_node, end_node)

    print(f"Tempo total estimado: {total_time:.2f} min")
    print("Caminho encontrado:", path)

    # Identificar trechos por operador/linha
    path_edges = []
    for i in range(len(path)-1):
        f, t = path[i], path[i+1]
        for e in updated_edges:
            if e['from'] == f and e['to'] == t:
                path_edges.append(e)
                break

    # -----------------------------
    # --- Plot com cores
    # -----------------------------
    plt.figure(figsize=(12,10))
    plt.scatter(stcp_stops['stop_lon'], stcp_stops['stop_lat'], s=10, c='blue', label='STCP')
    plt.scatter(metro_stops['stop_lon'], metro_stops['stop_lat'], s=20, c='green', label='Metro')
    for c in multimodal_clusters:
        plt.scatter(c['lon'], c['lat'], c='red', s=50)

    # Traçar caminho
    for e in path_edges:
        x = [node_positions[e['from']][0], node_positions[e['to']][0]]
        y = [node_positions[e['from']][1], node_positions[e['to']][1]]
        if e['operator'] == 'STCP':
            plt.plot(x, y, c='blue', linewidth=3)
        elif e['operator'] == 'Metro':
            plt.plot(x, y, c='green', linewidth=3)
        elif e['operator'] == 'LINK':
            plt.plot(x, y, c='orange', linewidth=2, linestyle='--')

    plt.legend()
    plt.title("Caminho Dijkstra: STCP, Metro e Walks")
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main()
