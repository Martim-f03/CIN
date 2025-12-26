# path_objective.py

import math
from typing import List, Dict
from Constants import (
    WALK_SPEED_KMH,
    BUS_SPEED_KMH,
    METRO_SPEED_KMH,
    MODE_CHANGE_PENALTY_MIN,
    LINE_CHANGE_PENALTY_MIN,
    BUS_EMISSION_GCO2_PER_KM,
    METRO_EMISSION_GCO2_PER_KM,
    WALK_EMISSION_GCO2_PER_KM,
)

def haversine_distance(lat1, lon1, lat2, lon2):
    """Distância entre duas coordenadas GPS em km"""
    R = 6371  # km
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

def path_objective(path: List[str], edges: List[Dict], 
                   max_mode_changes=None, max_line_changes=None, max_walking_time=None,
                   penalty_multiplier=100.0):
    """
    Função objetivo para MOEA/D:
    - Minimizar tempo total
    - Minimizar emissão CO2
    Penalizações aplicadas por restrições:
    1) Limite máximo de mudanças de modo
    2) Limite máximo de mudanças de linha
    3) Limite máximo de tempo a pé
    """
    total_time = 0.0
    walking_time = 0.0
    num_mode_changes = 0
    num_line_changes = 0
    total_co2 = 0.0

    prev_operator = None
    prev_route = None

    # Mapa rápido de arestas
    edge_map = {(e['from'], e['to']): e for e in edges}

    for i in range(len(path) - 1):
        from_node = path[i]
        to_node = path[i+1]

        if (from_node, to_node) not in edge_map:
            continue  # ignorar arestas inexistentes

        e = edge_map[(from_node, to_node)]
        operator = e['operator']
        route = e.get('route_id')
        time_min = e.get('travel_time', 0.0)

        total_time += time_min

        # Tempo a pé
        if operator == 'WALK':
            walking_time += time_min
            co2_per_km = WALK_EMISSION_GCO2_PER_KM
        elif operator == 'STCP':
            co2_per_km = BUS_EMISSION_GCO2_PER_KM
        elif operator == 'METRO':
            co2_per_km = METRO_EMISSION_GCO2_PER_KM
        else:
            co2_per_km = 0.0

        # Distância aproximada para CO2
        lat1, lon1 = e['from_pos'][1], e['from_pos'][0]
        lat2, lon2 = e['to_pos'][1], e['to_pos'][0]
        dist_km = haversine_distance(lat1, lon1, lat2, lon2)
        total_co2 += dist_km * co2_per_km

        # Mudanças de modo
        if prev_operator is not None and operator != prev_operator:
            num_mode_changes += 1
            total_time += MODE_CHANGE_PENALTY_MIN

        # Mudanças de linha
        if prev_route is not None and route != prev_route:
            if route is not None and prev_route is not None:
                num_line_changes += 1
                total_time += LINE_CHANGE_PENALTY_MIN

        prev_operator = operator
        prev_route = route

    # Penalizações por restrições externas
    penalty_time = 0.0
    if max_mode_changes is not None and num_mode_changes > max_mode_changes:
        penalty_time += (num_mode_changes - max_mode_changes) * MODE_CHANGE_PENALTY_MIN * penalty_multiplier
    if max_line_changes is not None and num_line_changes > max_line_changes:
        penalty_time += (num_line_changes - max_line_changes) * LINE_CHANGE_PENALTY_MIN * penalty_multiplier
    if max_walking_time is not None and walking_time > max_walking_time:
        penalty_time += (walking_time - max_walking_time) * penalty_multiplier

    total_time_with_penalty = total_time + penalty_time
    total_co2_with_penalty = total_co2 + penalty_time  # opcional: penalizar CO2 também

    # Retornar objetivos para MOEA/D
    return [total_time_with_penalty, total_co2_with_penalty]
