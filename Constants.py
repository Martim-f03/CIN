"""
constants.py

Constantes globais do sistema de planeamento multimodal.
Este ficheiro define parâmetros físicos, operacionais e ambientais
usados na avaliação de percursos.
"""

# -----------------------------
# --- VELOCIDADES MÉDIAS (km/h)
# -----------------------------

# Caminhada urbana média
WALK_SPEED_KMH = 4.5

# Autocarro urbano (inclui paragens e tráfego)
BUS_SPEED_KMH = 18.0

# Metro ligeiro (velocidade comercial)
METRO_SPEED_KMH = 30.0


# -----------------------------
# --- EMISSÕES CO₂ (g/km/pessoa)
# -----------------------------

# Valores típicos para transporte público urbano
# gramas de CO2 por km por passageiro
BUS_EMISSION_GCO2_PER_KM = 109.9
METRO_EMISSION_GCO2_PER_KM = 40 
WALK_EMISSION_GCO2_PER_KM = 0


# -----------------------------
# --- PENALIZAÇÕES
# -----------------------------

# Penalização temporal por transbordo (minutos)
TRANSFER_PENALTY_MIN = 4.0

# Penalização por entrada num novo modo
MODE_CHANGE_PENALTY_MIN = 5.0
LINE_CHANGE_PENALTY_MIN = 2.0


# -----------------------------
# --- CAMINHADA
# -----------------------------

# Distância máxima aceitável para caminhar até uma paragem (km)
MAX_WALK_DISTANCE_KM = 0.8   # ~10 minutos a pé

# Distância usada para ligações WALK no grafo (km)
WALK_EDGE_MAX_KM = 0.05      # 50 metros


# -----------------------------
# --- PESOS (multi-objetivo)
# -----------------------------

# Pesos padrão para função de custo
WEIGHT_TIME = 1.0
WEIGHT_CO2 = 0.0
WEIGHT_WALK = 0.0
WEIGHT_TRANSFERS = 0.0
