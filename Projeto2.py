import pandas as pd
import math
import matplotlib.pyplot as plt

# -----------------------------
# --- Configurações
# -----------------------------
STCP_PATH = "dataset/stcp"
METRO_PATH = "dataset/metro_porto"
MAX_DISTANCE_KM = 0.05  # 50 metros

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
# --- Carregar stops
# -----------------------------
stcp_stops = pd.read_csv(f"{STCP_PATH}/stops.txt")
metro_stops = pd.read_csv(f"{METRO_PATH}/stops.txt")
stcp_stops['operator'] = 'STCP'
metro_stops['operator'] = 'Metro'

print("Número de paragens STCP:", len(stcp_stops))
print("Número de paragens Metro:", len(metro_stops))
print("Total de paragens:", len(stcp_stops) + len(metro_stops))

# -----------------------------
# --- Criar arestas originais
# -----------------------------
def create_edges(stop_times_file, operator):
    stop_times = pd.read_csv(stop_times_file)
    edges = []
    for trip_id, group in stop_times.groupby("trip_id"):
        group = group.sort_values("stop_sequence")
        stops = group["stop_id"].tolist()
        for i in range(len(stops)-1):
            edges.append({
                'from': stops[i],
                'to': stops[i+1],
                'trip_id': trip_id,
                'operator': operator
            })
    print(f"Arestas {operator} criadas:", len(edges))
    return edges

edges_stcp = create_edges(f"{STCP_PATH}/stop_times.txt", "STCP")
edges_metro = create_edges(f"{METRO_PATH}/stop_times.txt", "Metro")
all_edges = edges_stcp + edges_metro

print("Total de arestas combinadas:", len(all_edges))

# -----------------------------
# --- Posições dos nós
# -----------------------------
node_positions = {}
for _, r in stcp_stops.iterrows():
    node_positions[r['stop_id']] = (r['stop_lon'], r['stop_lat'])
for _, r in metro_stops.iterrows():
    node_positions[r['stop_id']] = (r['stop_lon'], r['stop_lat'])

# -----------------------------
# --- Carregar Transfers e Fares (ANTES dos multimodais)
# -----------------------------
stcp_transfers = pd.read_csv(f"{STCP_PATH}/transfers.txt")
metro_fare_rules = pd.read_csv(f"{METRO_PATH}/fare_rules.txt")
metro_fare_attr = pd.read_csv(f"{METRO_PATH}/fare_attributes.txt")

# Mapas GTFS
transfer_map = {
    (r['from_stop_id'], r['to_stop_id']): r['transfer_type']
    for _, r in stcp_transfers.iterrows()
}

fare_map = {
    (r['origin_id'], r['destination_id']): r['fare_id']
    for _, r in metro_fare_rules.iterrows()
}

# Atribuir fares / transfers às arestas originais
for e in all_edges:
    if e['operator'] == 'STCP':
        e['transfer'] = transfer_map.get((e['from'], e['to']))
        e['fare'] = None
    else:
        e['fare'] = fare_map.get((e['from'], e['to']))
        e['transfer'] = None

# -----------------------------
# --- Criar clusters multimodais
# -----------------------------
multimodal_clusters = []
stcp_stops['is_multimodal'] = False
metro_stops['is_multimodal'] = False
mm_id_counter = 1

for _, metro in metro_stops.iterrows():
    close_stcp = stcp_stops[
        stcp_stops.apply(
            lambda r: haversine_distance(
                r['stop_lat'], r['stop_lon'],
                metro['stop_lat'], metro['stop_lon']
            ) <= MAX_DISTANCE_KM,
            axis=1
        )
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

print("Nós multimodais criados:", len(multimodal_clusters))

# -----------------------------
# --- Mapear stops → multimodal
# -----------------------------
mm_mapping = {}
for c in multimodal_clusters:
    for s in c['stcp_stops'] + c['metro_stops']:
        mm_mapping[s] = c['multimodal_id']
    node_positions[c['multimodal_id']] = (c['lon'], c['lat'])

# -----------------------------
# --- Atualizar arestas
# -----------------------------
updated_edges = []

for e in all_edges:
    updated_edges.append({
        'from': mm_mapping.get(e['from'], e['from']),
        'to': mm_mapping.get(e['to'], e['to']),
        'operator': e['operator'],
        'trip_id': e['trip_id'],
        'fare': e['fare'],
        'transfer': e['transfer']
    })

# Ligações explícitas ao multimodal
for c in multimodal_clusters:
    for s in c['stcp_stops'] + c['metro_stops']:
        updated_edges.append({'from': s, 'to': c['multimodal_id'], 'operator': 'LINK'})
        updated_edges.append({'from': c['multimodal_id'], 'to': s, 'operator': 'LINK'})

# -----------------------------
# --- Lista final de nós
# -----------------------------
all_nodes = (
    list(stcp_stops['stop_id']) +
    list(metro_stops['stop_id']) +
    [c['multimodal_id'] for c in multimodal_clusters]
)

# -----------------------------
# --- VERIFICAÇÃO CORRETA (GTFS-aware)
# -----------------------------
nodes_without_position = [n for n in all_nodes if n not in node_positions]
edges_invalid = [e for e in updated_edges if e['from'] not in node_positions or e['to'] not in node_positions]

# Transfers
gtfs_transfers = set(transfer_map.keys())
graph_transfers = set(
    (e['from'], e['to']) for e in updated_edges
    if e.get('transfer') is not None
)

# Fares
gtfs_fares = set(fare_map.keys())
graph_fares = set(
    (e['from'], e['to']) for e in updated_edges
    if e.get('fare') is not None
)

print("\n=== VERIFICAÇÃO COMPLETA DO GRAFO ===")
print("Total de nós:", len(all_nodes))
print("Nós multimodais:", len(multimodal_clusters))
print("Nós sem posição:", len(nodes_without_position))
print("Arestas totais:", len(updated_edges))
print("Arestas inválidas:", len(edges_invalid))

print("\n--- TRANSFERS STCP ---")
print("GTFS:", len(gtfs_transfers))
print("No grafo:", len(graph_transfers))
print("Em falta:", len(gtfs_transfers - graph_transfers))
print("Extras:", len(graph_transfers - gtfs_transfers))

print("\n--- FARES METRO ---")
print("GTFS:", len(gtfs_fares))
print("No grafo:", len(graph_fares))
print("Em falta:", len(gtfs_fares - graph_fares))
print("Extras:", len(graph_fares - gtfs_fares))
print("=== VERIFICAÇÃO CONCLUÍDA ===")

# -----------------------------
# --- Plot
# -----------------------------
plt.figure(figsize=(12,10))
plt.scatter(stcp_stops['stop_lon'], stcp_stops['stop_lat'], s=10, c='blue', label='STCP')
plt.scatter(metro_stops['stop_lon'], metro_stops['stop_lat'], s=20, c='green', label='Metro')

for c in multimodal_clusters:
    plt.scatter(c['lon'], c['lat'], c='red', s=50)

plt.legend()
plt.title("STCP, Metro e Multimodais")
plt.grid(True)
plt.show()
