# moead.py

import random
import numpy as np
from init_population import initialize_population
from path_evaluation import path_objective
from routing import dijkstra

# ----------------------------
# Classe Individual
# ----------------------------
class Individual:
    def __init__(self, path):
        self.path = path
        self.objectives = None  # [tempo, CO2]

# ----------------------------
# Mutação de caminho agressiva e segura
# ----------------------------
def mutate_path(path, edges, max_mutations=2, max_subpath_length=3):
    """
    Mutação diversificada e segura:
    - Reconstrói múltiplos subtrechos curtos do caminho original.
    - Garante caminhos válidos usando apenas nós/arestas ativos.
    - Não altera caminhos curtos demais.
    """
    if len(path) <= 3:
        return path.copy()  # caminho muito curto, não muta
    
    # Criar mapa de adjacência do grafo ativo
    adjacency = {}
    for e in edges:
        adjacency.setdefault(e['from'], []).append(e['to'])

    new_path = path.copy()
    for _ in range(max_mutations):
        if len(new_path) <= 3:
            break  # não há trecho suficiente para mutar
        start_idx = random.randint(1, len(new_path)-3)
        end_idx = min(start_idx + max_subpath_length, len(new_path)-2)

        # Reconstruir subtrecho
        sub_start = new_path[start_idx-1]
        reconstructed = []
        current = sub_start
        for _ in range(end_idx-start_idx+1):
            neighbors = adjacency.get(current, [])
            if not neighbors:
                break
            current = random.choice(neighbors)
            reconstructed.append(current)

        new_path[start_idx:end_idx+1] = reconstructed

    new_path[-1] = path[-1]  # garantir destino correto
    return new_path

# ----------------------------
# Funções MOEA/D
# ----------------------------
def tchebycheff(ind, weights, ideal_point):
    return max([w * abs(f - z) for w, f, z in zip(weights, ind.objectives, ideal_point)])

def generate_weight_vectors(num_objs, pop_size):
    weights = []
    for _ in range(pop_size):
        w = np.random.dirichlet(np.ones(num_objs))
        weights.append(w.tolist())
    return weights

def get_neighbors(weights, T=10):
    neighbors = []
    for i, w in enumerate(weights):
        distances = [np.linalg.norm(np.array(w)-np.array(wj)) for wj in weights]
        idx = np.argsort(distances)[:T]
        neighbors.append(idx)
    return neighbors

def get_ideal_point(population):
    num_objs = len(population[0].objectives)
    ideal = [min([ind.objectives[i] for ind in population]) for i in range(num_objs)]
    return ideal

# ----------------------------
# Inicializar população
# ----------------------------
def initialize_population_MOEAD(pop_size=10,
                                max_mode_changes=None,
                                max_line_changes=None,
                                max_walking_time=None):
    path_init, nodes, edges = initialize_population()
    population = [Individual(path_init)]
    
    for _ in range(pop_size-1):
        new_path = mutate_path(path_init, edges, max_mutations=2, max_subpath_length=3)
        population.append(Individual(new_path))
    
    for ind in population:
        ind.objectives = path_objective(
            ind.path, edges,
            max_mode_changes=max_mode_changes,
            max_line_changes=max_line_changes,
            max_walking_time=max_walking_time
        )
    
    return population, nodes, edges

# ----------------------------
# Loop principal do MOEA/D
# ----------------------------
def moead(num_gens=10, pop_size=20, T=5,
          max_mode_changes=None, max_line_changes=None, max_walking_time=None):
    population, nodes, edges = initialize_population_MOEAD(
        pop_size=pop_size,
        max_mode_changes=max_mode_changes,
        max_line_changes=max_line_changes,
        max_walking_time=max_walking_time
    )
    
    weights = generate_weight_vectors(2, pop_size)
    neighbors = get_neighbors(weights, T)
    ideal = get_ideal_point(population)
    
    for gen in range(num_gens):
        print(f"\n=== Geração {gen+1} ===")
        for i, ind in enumerate(population):
            print(f"Ind {i}: Caminho atual: {ind.path}")

            nb_idx = random.choice(neighbors[i])
            child_path = mutate_path(population[nb_idx].path, edges, max_mutations=2, max_subpath_length=3)
            child = Individual(child_path)
            
            # Avaliar objetivos do filho com restrições
            child.objectives = path_objective(
                child.path, edges,
                max_mode_changes=max_mode_changes,
                max_line_changes=max_line_changes,
                max_walking_time=max_walking_time
            )

            ideal = [min(zi, fi) for zi, fi in zip(ideal, child.objectives)]

            for j in neighbors[i]:
                f_old = tchebycheff(population[j], weights[j], ideal)
                f_new = tchebycheff(child, weights[j], ideal)
                if f_new < f_old:
                    population[j] = child
                    print(f"  -> Atualizado Ind {j} com novo caminho: {child.path}")
    
    return population, nodes, edges, ideal

# ----------------------------
# Teste rápido
# ----------------------------
if __name__ == "__main__":
    pop, nodes, edges, ideal = moead(
        num_gens=5, pop_size=10, T=3,
        max_mode_changes=3, max_line_changes=3, max_walking_time=5
    )
    print("\nPopulação final:")
    for i, ind in enumerate(pop):
        print(f"Ind {i}: Tempo={ind.objectives[0]:.2f} min, CO2={ind.objectives[1]:.2f} g")
        print(f"  Caminho final: {ind.path}")
