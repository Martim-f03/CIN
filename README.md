# Grupo

- Lucas Lomba pg60389
- Martim Melo Ferreira pg60391
- Paulo Cabrita pg58782
- Vicente Castro pg60395


# Modo de utilização

É apenas preciso ir para a pasta **Projeto** e correr o ficheiro ***run_tests.py***.
cd path/CIN/Projeto
python3 run_tests.py

Para observar os resultados basta ir à pasta **tests** e no ficheiro ***moead_results.txt*** estaram as soluções para os casos no ficheiro ***test_cases.txt*** que se encontra na mesma pasta.

# Relatório

Ficheiro Relatório.pdf feito em latex.

# Projeto

## Ficheiros:

- ### ***graph_builder.py***
Este é o módulo de pré-processamento e construção do grafo. Ele lê os ficheiros GTFS (STCP e Metro) e converte-os num grafo multimodal.
**Função principal**: Criar as arestas de transporte, calcular distâncias entre paragens e, gerar os  nós multimodais (clusters) que permitem a transferência física entre o Metro e os autocarros num raio de 50 metros.

- ### ***init_population.py***
Responsável por criar o "ponto de partida" do algoritmo evolutivo.
**Função principal**: Implementar a função ***initialize_population***. Em vez de gerar caminhos aleatórios, este ficheiro utiliza o algoritmo de Dijkstra para criar uma solução inicial de tempo mínimo e depois gera variantes para garantir que a população inicial do MOEA/D seja diversificada e, acima de tudo, válida (composta por caminhos conectados).

- ### ***moead.py***
Contém o "cérebro" da otimização multi-objetivo baseada em decomposição.
**Função principal**: Implementar a lógica do MOEA/D. Gere os vetores de peso ($\lambda$), a vizinhança entre subproblemas e o processo de atualização das soluções. É aqui que os objetivos de Tempo e CO2 são equilibrados através da função Tchebycheff.

- ### ***path_evaluation.py***
Este ficheiro define a métrica de "sucesso" de qualquer caminho gerado.

**Função principal**: Implementa a Função Objetivo (path_objective). Ele calcula o custo total de um trajeto, somando o tempo de viagem, as emissões de CO2 e aplicando penalizações pesadas por transbordos excessivos (MODE_CHANGE_PENALTY) ou tempos de caminhada superiores ao limite configurado.

- ### ***routing.py***
Atua como a interface de alto nível para o cálculo de rotas.

**Função principal**: Orquestrar a ligação entre o ponto de partida do utilizador (__START__) e o destino (__END__). Ele utiliza a fórmula de Haversine para encontrar as paragens mais próximas (raio de 800m) e integra esses pontos temporários no grafo principal para que os algoritmos de procura possam funcionar.

- ### ***run_tests.py***
É o módulo de validação usado para correr o projeto.

**Função principal**: Automatiza a execução de múltiplos cenários de teste (pares origem-destino com as suas restrições). Ele lê o ficheiros ***test_cases.txt***, executa o motor de otimização e gera o relatório final (***moead_results.txt***), comparando os caminhos "Mais Rápido", "Mais Ecológico" e "Equilibrado".

- ### ***Constants.py
Este ficheiro funciona como o painel de controlo central de todo o projeto, onde são definidos os parâmetros físicos e ambientais.
**Função principal**: Armazenar constantes globais como as velocidades médias de deslocação (WALK_SPEED_KMH), os coeficientes de emissão de $CO_2$ por operador e as penalizações temporais para transbordos e mudanças de linha.