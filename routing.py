# routing.py

import heapq
from typing import List, Dict, Tuple, Optional

# Cada aresta do grafo tem:
# {'from': str, 'to': str, 'operator': str, 'trip_id': str, 'route_id': str,
#  'fare': Optional[str], 'transfer': Optional[int], 'travel_time': float}

def dijkstra(
    nodes: List[str],
    edges: List[Dict],
    source: str,
    target: str,
    weight_key: str = 'travel_time'
) -> Tuple[float, List[str]]:
    """
    Algoritmo de Dijkstra para encontrar o caminho mais curto.
    nodes: lista de IDs de nós
    edges: lista de arestas do grafo
    source: nó inicial
    target: nó final
    weight_key: atributo da aresta usado como custo (tempo, CO2, etc.)
    
    Retorna: (custo_total, caminho como lista de nós)
    """
    # Construir mapa de adjacência
    graph = {n: [] for n in nodes}
    for e in edges:
        cost = e.get(weight_key)
        if cost is None:
            continue
        graph[e['from']].append((e['to'], cost, e))  # guardamos a aresta também

    # Dicionários de distância e predecessor
    dist = {n: float('inf') for n in nodes}
    prev = {n: None for n in nodes}
    dist[source] = 0

    heap = [(0, source)]
    while heap:
        d, u = heapq.heappop(heap)
        if u == target:
            break
        for v, cost, edge_data in graph[u]:
            alt = d + cost
            if alt < dist[v]:
                dist[v] = alt
                prev[v] = (u, edge_data)
                heapq.heappush(heap, (alt, v))

    # Reconstruir caminho
    path = []
    u = target
    while prev[u] is not None:
        path.insert(0, u)
        u, edge_data = prev[u]
    path.insert(0, source)

    return dist[target], path

def compute_travel_time(edges: List[Dict], default_walk_speed_kmh: float = 5.0):
    """
    Atribui tempo de viagem a cada aresta.
    Para ligações a pé (operator == 'LINK'), calcula baseado na distância e velocidade de caminhada.
    """
    for e in edges:
        if e['operator'] == 'LINK':
            lat1, lon1 = e['from_pos']
            lat2, lon2 = e['to_pos']
            distance_km = haversine_distance(lat1, lon1, lat2, lon2)
            e['travel_time'] = distance_km / default_walk_speed_kmh * 60  # minutos
        else:
            if 'scheduled_time' in e:
                e['travel_time'] = e['scheduled_time']
            else:
                e['travel_time'] = 1  # fallback 1 minuto

def haversine_distance(lat1, lon1, lat2, lon2):
    import math
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))
