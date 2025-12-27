import json
from moead import moead, initialize_population_MOEAD
from path_evaluation import path_objective

# Ler casos de teste
def read_test_cases(filename):
    cases = []
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split(',')
            lat_start, lon_start, lat_end, lon_end = map(float, parts[:4])
            max_mode, max_line, max_walk = map(int, parts[4:])
            cases.append({
                'start': (lat_start, lon_start),
                'end': (lat_end, lon_end),
                'max_mode_changes': max_mode,
                'max_line_changes': max_line,
                'max_walking_time': max_walk
            })
    return cases

# Função para gerar relatório simplificado
def format_path_report_simple(path, edges, objectives):
    """
    Gera um caminho simplificado:
    - Agrupa as paragens por operador/linha
    - Indica troca de transporte ou linha de forma concisa
    - Acrescenta tempo e CO2 no final
    """
    report_lines = []
    segment = []
    prev_operator = None
    prev_route = None

    for i in range(len(path)-1):
        from_node = path[i]
        to_node = path[i+1]
        edge = next((e for e in edges if e['from']==from_node and e['to']==to_node), None)
        if edge is None:
            continue
        operator = edge.get('operator') or "WALK"
        route = edge.get('route_id') or "WALK"

        # Se mudar operador ou linha, finalizar segmento
        if prev_operator and (operator != prev_operator or route != prev_route):
            report_lines.append(f"{prev_operator}/{prev_route} " + " - ".join(map(str, segment)))
            segment = []
        segment.append(to_node)
        prev_operator = operator
        prev_route = route

    # Adicionar último segmento
    if segment:
        report_lines.append(f"{prev_operator}/{prev_route} " + " - ".join(map(str, segment)))

    # Acrescentar tempo e CO2
    time, co2 = objectives
    report_lines.append(f"[Tempo: {time:.2f} min, CO2: {co2:.2f} g]")
    return "\n".join(report_lines)

# Executar todos os testes
def run_all_tests(test_file, output_file):
    test_cases = read_test_cases(test_file)
    with open(output_file, 'w') as f_out:
        for idx, case in enumerate(test_cases, 1):
            f_out.write(f"=== Caso {idx} ===\n")
            print(f"Executando caso {idx} ...")
            
            # Inicializar população e grafo com restrições do caso
            population, nodes, edges = initialize_population_MOEAD(
                pop_size=10,
                max_mode_changes=case['max_mode_changes'],
                max_line_changes=case['max_line_changes'],
                max_walking_time=case['max_walking_time']
            )
            
            # Executar MOEA/D com as restrições do caso
            population, nodes, edges, ideal = moead(
                num_gens=10, pop_size=10, T=3,
                max_mode_changes=case['max_mode_changes'],
                max_line_changes=case['max_line_changes'],
                max_walking_time=case['max_walking_time']
            )
            
            # Avaliar objetivos finais (garantia)
            for ind in population:
                ind.objectives = path_objective(
                    ind.path, edges,
                    max_mode_changes=case['max_mode_changes'],
                    max_line_changes=case['max_line_changes'],
                    max_walking_time=case['max_walking_time']
                )
            
            # Selecionar soluções de interesse
            fastest = min(population, key=lambda x: x.objectives[0])
            cleanest = min(population, key=lambda x: x.objectives[1])
            balanced = min(population, key=lambda x: sum(x.objectives))  # trade-off simples
            
            f_out.write(">> Caminho mais rápido:\n")
            f_out.write(format_path_report_simple(fastest.path, edges, fastest.objectives) + "\n\n")
            
            f_out.write(">> Caminho com menos CO2:\n")
            f_out.write(format_path_report_simple(cleanest.path, edges, cleanest.objectives) + "\n\n")
            
            f_out.write(">> Caminho equilibrado (tempo+CO2):\n")
            f_out.write(format_path_report_simple(balanced.path, edges, balanced.objectives) + "\n\n")
            f_out.write("="*50 + "\n\n")

# Executar
if __name__ == "__main__":
    run_all_tests("tests/test_cases.txt", "tests/moead_results.txt")
