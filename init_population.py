# init_population.py

from datetime import datetime
import routing
from path_evaluation import path_objective  # Função objetivo que devolve [tempo, CO2]

from graph_builder import (
    all_nodes,
    updated_edges,
    node_positions,
    stcp_calendar,
    stcp_calendar_dates,
    metro_calendar,
    metro_calendar_dates
)

# ============================================================
# Serviços ativos numa data
# ============================================================

def active_services_on_date(date, calendar, calendar_dates):
    active = set()
    weekday_str = [
        'monday','tuesday','wednesday',
        'thursday','friday','saturday','sunday'
    ][date.weekday()]

    for _, r in calendar.iterrows():
        if r['start_date'] <= int(date.strftime("%Y%m%d")) <= r['end_date']:
            if r[weekday_str] == 1:
                active.add(r['service_id'])

    for _, r in calendar_dates.iterrows():
        if int(r['date']) == int(date.strftime("%Y%m%d")):
            if r['exception_type'] == 1:
                active.add(r['service_id'])
            elif r['exception_type'] == 2:
                active.discard(r['service_id'])

    return active

# ============================================================
# Encontrar paragens próximas a um ponto GPS
# ============================================================

def find_nearby_stops(lat, lon, node_positions, max_distance_km=0.8):
    nearby = []
    for stop_id, (stop_lon, stop_lat) in node_positions.items():
        dist = routing.haversine_distance(lat, lon, stop_lat, stop_lon)
        if dist <= max_distance_km:
            nearby.append((stop_id, dist))
    return nearby

# ============================================================
# Criar arestas WALK temporárias (origem)
# ============================================================

def add_walking_edges_from_point(edges, point_id, lat, lon, nearby_stops, walk_speed_kmh=5.0):
    new_edges = []
    for stop_id, dist_km in nearby_stops:
        time_min = dist_km / walk_speed_kmh * 60
        new_edges.append({
            'from': point_id,
            'to': stop_id,
            'operator': 'WALK',
            'trip_id': None,
            'route_id': None,
            'service_id': None,
            'fare': None,
            'transfer': None,
            'travel_time': time_min,
            'from_pos': (lon, lat),
            'to_pos': node_positions[stop_id]
        })
    return edges + new_edges

# ============================================================
# Criar arestas WALK temporárias (destino)
# ============================================================

def add_walking_edges_to_point(edges, point_id, lat, lon, nearby_stops, walk_speed_kmh=5.0):
    new_edges = []
    for stop_id, dist_km in nearby_stops:
        time_min = dist_km / walk_speed_kmh * 60
        new_edges.append({
            'from': stop_id,
            'to': point_id,
            'operator': 'WALK',
            'trip_id': None,
            'route_id': None,
            'service_id': None,
            'fare': None,
            'transfer': None,
            'travel_time': time_min,
            'from_pos': node_positions[stop_id],
            'to_pos': (lon, lat)
        })
    return edges + new_edges

# ============================================================
# Função principal para inicializar população
# ============================================================

def initialize_population(start_coords=(41.1780, -8.5980), end_coords=(41.1612, -8.6306)):
    """
    Retorna o caminho inicial e o grafo utilizável hoje.
    """
    today = datetime.today().date()

    # Serviços ativos
    active_stcp = active_services_on_date(today, stcp_calendar, stcp_calendar_dates)
    active_metro = active_services_on_date(today, metro_calendar, metro_calendar_dates)
    active_services = active_stcp.union(active_metro)

    # Filtrar arestas ativas
    edges_today = [
        e for e in updated_edges
        if (e.get('service_id') in active_services) or e['operator'] in ('LINK', 'WALK')
    ]

    # Garantir nós válidos
    edges_today = [
        e for e in edges_today
        if str(e['from']) in node_positions and str(e['to']) in node_positions
    ]

    # Adicionar posições às arestas existentes
    for e in edges_today:
        e['from_pos'] = node_positions[str(e['from'])]
        e['to_pos'] = node_positions[str(e['to'])]

    # Calcular travel_time
    routing.compute_travel_time(edges_today)

    # Definir nós especiais
    start_lat, start_lon = start_coords
    end_lat, end_lon = end_coords
    START_ID = "__START__"
    END_ID = "__END__"
    node_positions[START_ID] = (start_lon, start_lat)
    node_positions[END_ID] = (end_lon, end_lat)

    # Encontrar paragens próximas
    nearby_start = find_nearby_stops(start_lat, start_lon, node_positions)
    nearby_end = find_nearby_stops(end_lat, end_lon, node_positions)

    # Criar arestas WALK temporárias
    edges_augmented = edges_today.copy()
    edges_augmented = add_walking_edges_from_point(edges_augmented, START_ID, start_lat, start_lon, nearby_start)
    edges_augmented = add_walking_edges_to_point(edges_augmented, END_ID, end_lat, end_lon, nearby_end)

    # Lista final de nós
    nodes_augmented = all_nodes + [START_ID, END_ID]

    # Routing Dijkstra
    total_time, path = routing.dijkstra(nodes_augmented, edges_augmented, START_ID, END_ID)

    return path, nodes_augmented, edges_augmented
