# Etapa 1 — Parser GTFS e grafo base


- construir arestas de transporte entre stops consecutivos por trip

- estimar tempo médio por par (u,v) por modo

- calcular distâncias haversine (para CO₂ e walking)

# Etapa 2 — Walking edges

- criar origem e destino virtuais

- ligar origem/destino às paragens dentro de raio R (ex.: 800m)

- ligações a pé entre paragens próximas (transfer)

# Etapa 3 — Avaliação de rota

- calcular tempo, CO₂, tempo a pé, nº transbordos

- validar restrições

# Etapa 4 — Inicialização MOEA/D com Dijkstra/A*

- gerar K pesos

- para cada peso, fazer shortest path escalarizado

- guardar rotas

# Etapa 5 — MOEA/D loop + operadores com domínio

- vizinhanças de pesos

- variações (mutação reroute + crossover subpath)

- repair + seleção por subproblema

# Etapa 6 — Cenários + avaliação + gráficos

- gerar cenários random walk

- correr N seeds

- produzir Pareto fronts

# Etapa 7 — Relatório e apresentação

- explicar modelação

- justificar escolhas

- mostrar resultados e trade-offs
