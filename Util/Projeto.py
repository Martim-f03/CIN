import pandas as pd
import gtfs_kit as gk
import math

# --- Carregar dados GTFS ---
stcp_path = "dataset/stcp"
metro_path = "dataset/metro_porto"

stcp_feed = gk.read_feed(stcp_path, dist_units='km')
metro_feed = gk.read_feed(metro_path, dist_units='km')

stcp_stops = stcp_feed.stops.copy()
metro_stops = metro_feed.stops.copy()

stcp_stops['operator'] = 'stcp'
metro_stops['operator'] = 'metro'

print("Número de paragens STCP:", len(stcp_stops))
print("Número de paragens Metro:", len(metro_stops))
print("Número total de paragens (STCP + Metro):", len(stcp_stops) + len(metro_stops))

# --- Função Haversine ---
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # km
    lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
    lon1_rad, lon2_rad = math.radians(lon1), math.radians(lon2)
    delta_lat, delta_lon = lat2_rad - lat1_rad, lon2_rad - lon1_rad
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad)*math.cos(lat2_rad)*math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

MAX_DISTANCE_KM = 0.05  # 50 metros

# --- Criar clusters multimodais ---
def create_multimodal_clusters(stcp_df, metro_df, max_distance_km=MAX_DISTANCE_KM):
    stcp_df = stcp_df.copy()
    metro_df = metro_df.copy()
    
    stcp_df['is_multimodal'] = False
    metro_df['is_multimodal'] = False
    
    multimodal_clusters = []
    multimodal_id = 1

    # Para cada paragem Metro, encontrar todas as STCP próximas
    for j, metro_row in metro_df.iterrows():
        lat_m, lon_m = metro_row['stop_lat'], metro_row['stop_lon']
        close_stcp = stcp_df[
            stcp_df.apply(lambda r: haversine_distance(r['stop_lat'], r['stop_lon'], lat_m, lon_m) <= max_distance_km, axis=1)
        ]
        if not close_stcp.empty:
            # Marcar como multimodal
            metro_df.at[j, 'is_multimodal'] = True
            stcp_df.loc[close_stcp.index, 'is_multimodal'] = True

            # Criar nó multimodal único
            all_lats = list(close_stcp['stop_lat']) + [lat_m]
            all_lons = list(close_stcp['stop_lon']) + [lon_m]
            multimodal_clusters.append({
                'multimodal_id': f'M{multimodal_id:03d}',
                'lat': sum(all_lats)/len(all_lats),
                'lon': sum(all_lons)/len(all_lons),
                'stcp_stops': close_stcp['stop_id'].tolist(),
                'metro_stops': [metro_row['stop_id']]
            })
            multimodal_id += 1

    multimodal_df = pd.DataFrame(multimodal_clusters)
    return stcp_df, metro_df, multimodal_df

# --- Executar ---
stcp_marked, metro_marked, multimodal_df = create_multimodal_clusters(stcp_stops, metro_stops, MAX_DISTANCE_KM)

# --- Criar coluna de tipo de paragem ---
stcp_marked['stop_type'] = stcp_marked['is_multimodal'].apply(lambda x: 'multimodal' if x else 'stcp')
metro_marked['stop_type'] = metro_marked['is_multimodal'].apply(lambda x: 'multimodal' if x else 'metro')

# --- Juntar todas as paragens sem duplicar multimodais ---
# Multimodais são representados apenas no DataFrame multimodal_df
stcp_only = stcp_marked[stcp_marked['stop_type'] == 'stcp']
metro_only = metro_marked[metro_marked['stop_type'] == 'metro']

all_stops = pd.concat([stcp_only, metro_only], ignore_index=True)

print("\nNúmero de paragens STCP isoladas:", len(stcp_only))
print("Número de paragens Metro isoladas:", len(metro_only))
print("Número de paragens multimodais:", len(multimodal_df))
print("Total de paragens no grafo:", len(stcp_only) + len(metro_only) + len(multimodal_df))
print("Total original (STCP + Metro):", len(stcp_stops) + len(metro_stops))

# --- Exemplo de multimodais ---
print("\nExemplo de clusters multimodais:")
print(multimodal_df.head())

import matplotlib.pyplot as plt

# Criar figura
plt.figure(figsize=(12,12))

# STCP
stcp_only = all_stops[all_stops['stop_type'] == 'stcp']
plt.scatter(stcp_only['stop_lon'], stcp_only['stop_lat'], c='blue', s=20, label='STCP', alpha=0.7)

# Metro
metro_only = all_stops[all_stops['stop_type'] == 'metro']
plt.scatter(metro_only['stop_lon'], metro_only['stop_lat'], c='green', s=20, label='Metro', alpha=0.7)

# Multimodais
plt.scatter(multimodal_df['lon'], multimodal_df['lat'], c='red', s=50, label='Multimodal', alpha=0.9)

# Ajustes do gráfico
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.title('Paragens STCP, Metro e Multimodais')
plt.legend()
plt.grid(True)
plt.show()

