import pandas as pd
import math

# -----------------------------
# --- Configurações
# -----------------------------
STCP_PATH = "dataset/stcp"
METRO_PATH = "dataset/metro_porto"
MAX_DISTANCE_KM = 0.05  # 50 metros para multimodais

# -----------------------------
# --- Função Haversine
# -----------------------------
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # km
    lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
    lon1_rad, lon2_rad = math.radians(lon1), math.radians(lon2)
    delta_lat, delta_lon = lat2_rad - lat1_rad, lon2_rad - lon1_rad
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad)*math.cos(lat2_rad)*math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

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
def create_edges(stop_times_file, operator_name):
    stop_times = pd.read_csv(stop_times_file)
    edges = []
    for trip_id, group in stop_times.groupby("trip_id"):
        group = group.sort_values("stop_sequence")
        stops = group["stop_id"].tolist()
        for i in range(len(stops) - 1):
            edges.append((stops[i], stops[i+1]))
    print(f"Arestas {operator_name} criadas:", len(edges))
    return edges

edges_stcp = create_edges(f"{STCP_PATH}/stop_times.txt", "STCP")
edges_metro = create_edges(f"{METRO_PATH}/stop_times.txt", "Metro")
all_edges = edges_stcp + edges_metro

# -----------------------------
# --- Verificação stops vs stop_times
# -----------------------------
stcp_times = pd.read_csv(f"{STCP_PATH}/stop_times.txt")
metro_times = pd.read_csv(f"{METRO_PATH}/stop_times.txt")

stcp_missing = set(stcp_times['stop_id']) - set(stcp_stops['stop_id'])
metro_missing = set(metro_times['stop_id']) - set(metro_stops['stop_id'])

print("\n=== VERIFICAÇÃO DE STOPS ===")
print(f"Total de stops STCP: {len(stcp_stops)}")
print(f"Total de stops Metro: {len(metro_stops)}")
print(f"Stops em stop_times mas não em stops.txt (STCP): {len(stcp_missing)}")
print(f"Stops em stop_times mas não em stops.txt (Metro): {len(metro_missing)}")

# -----------------------------
# --- Verificação arestas
# -----------------------------
invalid_edges = [e for e in all_edges if e[0] not in set(stcp_stops['stop_id']).union(metro_stops['stop_id']) 
                                         or e[1] not in set(stcp_stops['stop_id']).union(metro_stops['stop_id'])]
print("\n=== VERIFICAÇÃO DE ARESTAS ===")
print(f"Total de arestas STCP: {len(edges_stcp)}")
print(f"Total de arestas Metro: {len(edges_metro)}")
print(f"Total de arestas combinadas: {len(all_edges)}")
print(f"Arestas inválidas (referenciam stops inexistentes): {len(invalid_edges)}")

# -----------------------------
# --- Verificação transfers STCP
# -----------------------------
stcp_transfers = pd.read_csv(f"{STCP_PATH}/transfers.txt")
transfer_issues = [t for t in stcp_transfers[['from_stop_id','to_stop_id']].itertuples(index=False)
                   if t[0] not in stcp_stops['stop_id'].values or t[1] not in stcp_stops['stop_id'].values]

print("\n=== VERIFICAÇÃO DE TRANSFERS STCP ===")
print(f"Total de transfers STCP: {len(stcp_transfers)}")
print(f"Transfers inválidos (stop_id ausente): {len(transfer_issues)}")

# -----------------------------
# --- Verificação fares Metro
# -----------------------------
fare_attrs = pd.read_csv(f"{METRO_PATH}/fares_attributes.csv")
fare_rules = pd.read_csv(f"{METRO_PATH}/fares_rules.csv")

# Criar set de pares válidos (origin_id, destination_id)
valid_fares = set(zip(fare_rules['origin_id'], fare_rules['destination_id']))
metro_edges_without_fare = [e for e in edges_metro if (e[0], e[1]) not in valid_fares]

print("\n=== VERIFICAÇÃO DE FARES METRO ===")
print(f"Total de fares definidas: {len(fare_rules)}")
print(f"Arestas Metro sem fare definido: {len(metro_edges_without_fare)}")

# -----------------------------
# --- Resumo completo
# -----------------------------
print("\n=== RESUMO COMPLETO DA VERIFICAÇÃO ===")
print(f"Stops STCP: {len(stcp_stops)}, Stops Metro: {len(metro_stops)}")
print(f"Arestas STCP: {len(edges_stcp)}, Arestas Metro: {len(edges_metro)}, Total: {len(all_edges)}")
print(f"Arestas inválidas: {len(invalid_edges)}")
print(f"Transfers STCP inválidos: {len(transfer_issues)}")
print(f"Arestas Metro sem fare: {len(metro_edges_without_fare)}")
print("=== VERIFICAÇÃO CONCLUÍDA ===")
