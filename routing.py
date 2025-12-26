# routing.py

import heapq
from typing import List, Dict, Tuple
from Constants import (
    WALK_SPEED_KMH,
    BUS_SPEED_KMH,
    METRO_SPEED_KMH
)

# ---------------------------
# Distância Haversine
# ---------------------------
def haversine_distance(lat1, lon1, lat2, lon2):
    import math
    R = 6371  # km
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ---------------------------
# Cálculo de travel_time
# ---------------------------
def compute_travel_time(edges: List[Dict]):
    """
    Calcula o tempo de viagem (minutos) para cada aresta
    com base na distância e no operador.
    """
    for e in edges:
        lat1, lon1 = e['from_pos']
        lat2, lon2 = e['to_pos']

        distance_km = haversine_distance(lat1, lon1, lat2, lon2)

        operator = e['operator'].upper()

        if operator in ('WALK', 'LINK'):
            speed = WALK_SPEED_KMH

        elif operator == 'STCP':
            speed = BUS_SPEED_KMH

        elif operator == 'METRO':
            speed = METRO_SPEED_KMH

        else:
            # operador desconhecido → ignorar aresta
            e['travel_time'] = None
            continue

        e['travel_time'] = (distance_km / speed) * 60  # minutos


# ---------------------------
# Dijkstra seguro
# ---------------------------
def dijkstra(
    nodes: List[str],
    edges: List[Dict],
    source: str,
    target: str,
    weight_key: str = 'travel_time'
) -> Tuple[float, List[str]]:

    graph = {n: [] for n in nodes}

    for e in edges:
        cost = e.get(weight_key)
        if cost is None:
            continue
        if e['from'] not in graph or e['to'] not in graph:
            continue

        graph[e['from']].append((e['to'], cost, e))

    dist = {n: float('inf') for n in nodes}
    prev = {n: None for n in nodes}
    dist[source] = 0.0

    counter = 0
    heap = [(0.0, counter, source)]

    while heap:
        d, _, u = heapq.heappop(heap)

        if u == target:
            break

        if d > dist[u]:
            continue

        for v, cost, edge_data in graph[u]:
            alt = d + cost
            if alt < dist[v]:
                dist[v] = alt
                prev[v] = (u, edge_data)
                counter += 1
                heapq.heappush(heap, (alt, counter, v))

    # Reconstrução do caminho
    path = []
    u = target
    while prev[u] is not None:
        path.insert(0, u)
        u, _ = prev[u]

    if path:
        path.insert(0, source)

    return dist[target], path
