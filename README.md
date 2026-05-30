# G25_DivConquer_PA-26.1

**Número do trabalho:** 3  
**Conteúdo do Módulo:** Divisão e Conquista (Contagem de Inversões)

---

## Alunos

| Matrícula  | Nome Completo                     |
|------------|-----------------------------------|
| 211062929  | Davi dos Santos Brito Nobre       |
| 221008202  | José Eduardo Vieira do Prado      |

---

## Sobre o Trabalho

Este projeto implementa um **Comparador de Gostos Cinematográficos** que utiliza dados do [Letterboxd](https://letterboxd.com) para medir a similaridade entre os rankings de filmes de dois usuários, usando o algoritmo de **Contagem de Inversões baseado em Merge Sort (Divisão e Conquista)**.

### Caso de Uso Prático
Sistemas de recomendação frequentemente precisam medir quão similares são as preferências de dois usuários. A **contagem de inversões** entre dois rankings é uma métrica eficiente para isso — quanto menos inversões, mais parecidos são os gostos.

### Funcionalidades
- **Importação via Web Scraping**: Busca avaliações diretamente do perfil público do usuário no Letterboxd (basta fornecer o username).
- **Importação via ZIP**: Suporta os arquivos exportados do Letterboxd (Settings > Import & Export).
- **Relatório Visual**: Gera um arquivo HTML auto-contido com design *Glassmorphism* que abre automaticamente no navegador (sem necessidade de servidor).
- **Comparação de Performance**: Exibe no terminal a diferença de tempo entre o Merge Sort O(n log n) e Força Bruta O(n²).
- **Modo Interativo**: Execução guiada para quem não quer usar argumentos de linha de comando.

---

## Pré-requisitos

- Python 3.10+
- (Recomendado) Ambiente virtual ativo

---


### Exportar dados do Letterboxd:

1. Acesse [letterboxd.com](https://letterboxd.com) e faça login
2. Vá em **Settings** > **Import & Export** > **Export Your Data**
3. Baixe o arquivo `.zip` gerado
4. Use o arquivo com a flag `--zip`

---

## Como o Algoritmo Funciona?

O algoritmo mede a similaridade entre dois rankings contando o número de **inversões** — pares de filmes que estão em ordem diferente nos dois rankings.

### Passo a Passo

1. **Encontrar filmes em comum** entre os dois usuários
2. **Criar rankings** ordenando os filmes pela nota de cada usuário
3. **Montar uma permutação** mapeando a posição de cada filme no ranking B para a ordem do ranking A
4. **Contar inversões** na permutação usando **Merge Sort modificado**
5. **Calcular similaridade**: `1 - (inversões / máximo_possível)`

### Exemplo

Dois usuários avaliaram 4 filmes em comum:

| Filme        | Nota Usuário A | Nota Usuário B |
|--------------|:--------------:|:--------------:|
| O Poderoso Chefão | 5.0 | 4.5 |
| Inception    | 4.5            | 3.0            |
| Matrix       | 4.0            | 5.0            |
| Morbius      | 1.0            | 4.0            |

**Ranking A** (por nota): Chefão → Inception → Matrix → Morbius → posições [0, 1, 2, 3]

**Ranking B** (por nota): Matrix → Chefão → Morbius → Inception → posições [0, 1, 2, 3]

**Permutação** (posições de B na ordem de A): [1, 3, 0, 2]

**Inversões**: (1,0), (3,0), (3,2) → **3 inversões**

**Máximo possível**: 4×3/2 = **6 inversões**

**Similaridade**: 1 - (3/6) = **50%**



## Estrutura do Projeto

```
├── main.py                  # Ponto de entrada — CLI e orquestração
├── inversion_counter.py     # Algoritmo de contagem de inversões (Merge Sort)
├── letterboxd_parser.py     # Parser de dados do Letterboxd (ZIP + scraping)
├── report_generator.py      # Gerador de relatório HTML (Glassmorphism)
├── requirements.txt         # Dependências Python
├── .gitignore               # Arquivos ignorados pelo Git
└── README.md                # Este arquivo
```

---

## Screenshots (demonstração)

<!-- Adicionar screenshots do terminal e do relatório HTML aqui -->

---

## Vídeo (demonstração)

<!-- Adicionar link do vídeo de apresentação aqui -->
