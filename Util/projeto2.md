# README: Análise e Integração de Dados de Transportes Públicos (STCP e Metro do Porto)

## 📌 Visão Geral

Este projeto Python realiza a integração e análise de dados GTFS de duas redes de transportes públicos do Porto:
- **STCP** (Serviço de Transportes Coletivos do Porto)
- **Metro do Porto**

O objetivo principal é criar um **grafo multimodal** que representa as paragens e ligações entre os dois sistemas, identificando pontos de proximidade física (multimodais) onde os utentes podem transitar entre redes.

---

## 📁 Estrutura de Ficheiros

### Diretórios de entrada:
```
dataset/
├── stcp/
│   ├── stops.txt
│   ├── stop_times.txt
│   └── transfers.txt
└── metro_porto/
    ├── stops.txt
    ├── stop_times.txt
    ├── fare_rules.txt
    └── fare_attributes.txt
```

### Ficheiro principal:
- `Projeto2.py` – Código principal de processamento

---

## 🧠 Funcionalidades Principais

1. **Cálculo de distância geográfica** (fórmula de Haversine)
2. **Carregamento e fusão de paragens** STCP e Metro
3. **Criação de arestas** a partir das sequências de viagens (`stop_times`)
4. **Identificação de clusters multimodais** – paragens a menos de 50 metros entre redes
5. **Mapeamento de transfers (STCP) e fares (Metro)** conforme regras GTFS
6. **Validação completa** da integridade dos dados GTFS vs. grafo gerado
7. **Visualização geográfica** das paragens e pontos multimodais

---

## ⚙️ Configuração

```python
STCP_PATH = "dataset/stcp"
METRO_PATH = "dataset/metro_porto"
MAX_DISTANCE_KM = 0.05  # 50 metros → limite para considerar "multimodal"
```

---

## 🔧 Fluxo de Execução

### 1. **Carregamento dos dados**
- Carrega `stops.txt` de ambas as redes
- Adiciona coluna `operator` para distinguir origem

### 2. **Criação de arestas**
- Lê `stop_times.txt` para cada operador
- Agrupa por `trip_id` e ordena por `stop_sequence`
- Gera arestas direcionadas entre paragens consecutivas

### 3. **Carregamento de metadados GTFS**
- `transfers.txt` (STCP) → mapeia transferências diretas entre paragens
- `fare_rules.txt` + `fare_attributes.txt` (Metro) → mapeia tarifas entre zonas

### 4. **Identificação de pontos multimodais**
- Para cada paragem do Metro, procura paragens STCP a ≤ 50m
- Cria um nó multimodal representando o grupo
- Calcula posição média (centroide) do cluster

### 5. **Atualização do grafo**
- Substitui paragens originais pelo nó multimodal nos trajetos
- Adiciona arestas de ligação (`LINK`) entre paragens e seu nó multimodal

### 6. **Validação GTFS**
- Verifica se todos os nós têm coordenadas
- Confirma se transfers e fares do GTFS estão representados no grafo
- Reporta discrepâncias

### 7. **Visualização**
- Gráfico com:
  - STCP (azul)
  - Metro (verde)
  - Pontos multimodais (vermelho)

---

## 📊 Saída do Programa

### Exemplo de output no terminal:
```
Número de paragens STCP: 1200
Número de paragens Metro: 85
Total de paragens: 1285
Arestas STCP criadas: 9500
Arestas Metro criadas: 420
Total de arestas combinadas: 9920
Nós multimodais criados: 18

=== VERIFICAÇÃO COMPLETA DO GRAFO ===
Total de nós: 1303
Nós multimodais: 18
Nós sem posição: 0
Arestas totais: 10100
Arestas inválidas: 0

--- TRANSFERS STCP ---
GTFS: 150
No grafo: 150
Em falta: 0
Extras: 0

--- FARES METRO ---
GTFS: 45
No grafo: 45
Em falta: 0
Extras: 0
=== VERIFICAÇÃO CONCLUÍDA ===
```

---

## 🧩 Estruturas de Dados Principais

### `multimodal_clusters` (lista de dicionários)
```python
{
    'multimodal_id': 'M001',
    'lat': 41.123456,
    'lon': -8.654321,
    'stcp_stops': ['STCP_123', 'STCP_124'],
    'metro_stops': ['METRO_45']
}
```

### Arestas no grafo final:
```python
{
    'from': 'STCP_123',
    'to': 'M001',
    'operator': 'LINK',
    'trip_id': None,
    'fare': None,
    'transfer': None
}
```

---

## 📈 Visualização

- **STCP**: pontos azuis pequenos
- **Metro**: pontos verdes maiores
- **Multimodais**: pontos vermelhos (tamanho aumentado)
- Gráfico gerado com `matplotlib`

---

## ✅ Validações Implementadas

1. **Posições geográficas** – todos os nós têm coordenadas
2. **Transfers STCP** – comparativo entre GTFS e grafo
3. **Fares Metro** – comparativo entre GTFS e grafo
4. **Arestas inválidas** – conexões para nós inexistentes

---

## 🛠️ Dependências

```txt
pandas
matplotlib
math (built-in)
```

---

## 🎯 Possíveis Extensões

- Adicionar cálculo de caminho mais curto (Dijkstra/A*)
- Integrar horários (`stop_times`) para análise temporal
- Exportar grafo para formato GEXF/GraphML
- Adicionar interface web com Folium/Leaflet
- Calcular métricas de centralidade e conectividade multimodal

---

## 📌 Notas Finais

Este código serve como **base para análise de redes de transportes multimodais**, permitindo:
- Identificar pontos de interligação física entre redes
- Preservar regras de tarifação e transferência do GTFS
- Criar um modelo graph-based para simulação e planeamento

A abordagem é **modular** e pode ser adaptada para outras cidades com dados GTFS disponíveis.