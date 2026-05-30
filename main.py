import argparse
import io
import os
import sys
import time
import webbrowser

from inversion_counter import (
    brute_force_count_inversions,
    compare_two_rankings,
    merge_count_inversions,
)
from letterboxd_parser import (
    find_common_movies,
    get_display_name,
    parse_zip_export,
    rating_to_stars,
    scrape_profile,
)
from report_generator import generate_report

def print_header():
    """Imprime o cabeçalho estilizado no terminal."""
    print()
    print("=" * 60)
    print("  🎬  Letterboxd Taste Match")
    print("  Comparador de Gostos — Contagem de Inversões")
    print("=" * 60)
    print()


def print_results(user_a, user_b, ratings_a, ratings_b, result):
    """Imprime os resultados formatados no terminal."""
    sim = result['similarity_pct']
    inv = result['inversions']
    max_inv = result['max_inversions']
    common = result['common_count']

    # Mensagem de compatibilidade
    if sim >= 90:
        msg = "Praticamente a mesma pessoa! Você tem um gosto de 90% pra cima, é estatisticamente improvavel normalmente, então parabéns"
    elif sim >= 70:
        msg = "Muito Compatíveis! Vocês se conhecem, não é?"
    elif sim >= 50:
        msg = "Gosto Razoavelmente Parecido! Tentem ser amigos!"
    elif sim >= 30:
        msg = "Opiniões Bem Diferentes :()"
    else:
        msg = "Gostos Completamente Opostos! >:( )"

    print()
    print("─" * 60)
    print(f"  @{user_a}  VS  @{user_b}")
    print("─" * 60)
    print()

    # Barra visual de similaridade
    bar_len = 40
    filled = int(bar_len * result['similarity'])
    bar = "█" * filled + "░" * (bar_len - filled)
    print(f"  Similaridade:  {sim}%")
    print(f"  [{bar}]")
    print(f"  {msg}")
    print()

    # Estatísticas
    print(f"  📊 Filmes em comum:    {common}")
    print(f"  🔄 Inversões:          {inv:,} / {max_inv:,}")
    print()

    # Top concordâncias
    if result['agreements']:
        print("   Maior Concordância:")
        print("  " + "-" * 56)
        for item in result['agreements'][:5]:
            name = ratings_a[item['key']]['name']
            stars_a = rating_to_stars(item['rating_a'])
            stars_b = rating_to_stars(item['rating_b'])
            name_display = name[:28].ljust(28)
            print(f"  {name_display}  {stars_a}  {stars_b}")
        print()

    # Top discordâncias
    if result['disagreements']:
        print("  ⚡ Maior Discordância:")
        print("  " + "-" * 56)
        for item in result['disagreements'][:5]:
            name = ratings_a[item['key']]['name']
            stars_a = rating_to_stars(item['rating_a'])
            stars_b = rating_to_stars(item['rating_b'])
            diff = item['diff']
            name_display = name[:28].ljust(28)
            print(f"  {name_display}  {stars_a}  {stars_b}  (Δ{diff:.1f})")
        print()


def print_algorithm_info(result):
    """Imprime explicação do algoritmo usado."""
    common = result['common_count']
    inv = result['inversions']
    max_inv = result['max_inversions']
    sim = result['similarity_pct']

    print("─" * 60)
    print("  📖 Como o Algoritmo Funciona:")
    print("─" * 60)
    print()
    print("  1. Encontramos os filmes avaliados por ambos os usuários")
    print(f"     → {common} filmes em comum")
    print()
    print("  2. Ordenamos os filmes pela nota de cada usuário,")
    print("     criando dois rankings independentes")
    print()
    print("  3. Mapeamos o ranking do Usuário B para a ordem do A,")
    print("     gerando uma permutação de posições")
    print()
    print("  4. Contamos as inversões na permutação usando Merge Sort")
    print(f"     → {inv:,} inversões encontradas (O(n log n))")
    print()
    print("  5. Calculamos a similaridade:")
    print(f"     1 - ({inv:,} / {max_inv:,}) = {sim}%")
    print()
    print(f"  Complexidade: O(n log n) vs O(n²) com força bruta")
    print(f"  Para n={common}: ~{common * (common.bit_length()):,} operações"
          f" vs ~{common * common:,} operações")
    print()


def run_performance_comparison(result):
    """Compara performance entre merge sort e força bruta."""
    permutation = result['permutation']

    print("─" * 60)
    print("  ⏱️  Comparação de Performance:")
    print("─" * 60)
    print()

    # merge Sort
    start = time.perf_counter()
    _, inv_ms = merge_count_inversions(permutation)
    time_ms = time.perf_counter() - start

    print(f"  Merge Sort (O(n log n)):")
    print(f"    Inversões: {inv_ms:,}")
    print(f"    Tempo: {time_ms * 1000:.3f} ms")
    print()

    
    start = time.perf_counter()
    inv_bf = brute_force_count_inversions(permutation)
    time_bf = time.perf_counter() - start

    print(f"  Força Bruta (O(n²)):")
    print(f"    Inversões: {inv_bf:,}")
    print(f"    Tempo: {time_bf * 1000:.3f} ms")
    print()

    # Validação
    if inv_ms == inv_bf:
        print(f"   Resultados conferem! Ambos encontraram {inv_ms:,} inversões.")
    else:
        print(f"   Divergência! Merge Sort: {inv_ms}, Força Bruta: {inv_bf}")

    if time_bf > 0:
        speedup = time_bf / time_ms if time_ms > 0 else float('inf')
        print(f"  🚀 Merge Sort foi {speedup:.1f}x mais rápido")
    print()



# puxando dados

def load_ratings(source, mode='scrape'):

    if mode == 'zip':
        print(f"   Lendo arquivo: {source}")
        return parse_zip_export(source)
    else:
        return scrape_profile(source)



# modo usuário

def interactive_mode():
    print_header()

    print("Como deseja fornecer os dados?")
    print("  1. Perfis do Letterboxd (requer internet obviamente)")
    print("  2. Arquivos ZIP exportados do Letterboxd")
    print()

    choice = input("Escolha (1 ou 2): ").strip()

    if choice == '2':
        print()
        zip_a = input("Caminho do ZIP do Usuário 1: ").strip().strip('"')
        zip_b = input("Caminho do ZIP do Usuário 2: ").strip().strip('"')
        user_a = input("Nome do Usuário 1 (para o relatório): ").strip() or "Usuário 1"
        user_b = input("Nome do Usuário 2 (para o relatório): ").strip() or "Usuário 2"
        return user_a, user_b, zip_a, zip_b, 'zip'
    else:
        print()
        user_a = input("Username do Usuário 1: ").strip().lstrip('@')
        user_b = input("Username do Usuário 2: ").strip().lstrip('@')
        return user_a, user_b, user_a, user_b, 'scrape'



# Main


def main():
    parser = argparse.ArgumentParser(
        description='🎬 Letterboxd Taste Match — Compara gostos de filmes usando Contagem de Inversões',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exportar dados do Letterboxd:
  Vá em letterboxd.com > Settings > Import & Export > Export Your Data
        """
    )

    parser.add_argument(
        'users',
        nargs='*',
        help='Dois usernames do Letterboxd para comparar'
    )
    parser.add_argument(
        '--zip',
        nargs=2,
        metavar=('ZIP1', 'ZIP2'),
        help='Dois arquivos ZIP exportados do Letterboxd'
    )
    parser.add_argument(
        '--no-report',
        action='store_true',
        help='Não gerar relatório HTML (só exibir no terminal)'
    )
    parser.add_argument(
        '--no-browser',
        action='store_true',
        help='Gerar relatório mas não abrir automaticamente no navegador'
    )
    parser.add_argument(
        '--terminal',
        action='store_true',
        help='Modo terminal (equivalente a --no-report)'
    )

    args = parser.parse_args()

    print_header()

    # modo e fontes
    if args.zip:
        mode = 'zip'
        source_a, source_b = args.zip
        user_a = os.path.splitext(os.path.basename(source_a))[0]
        user_b = os.path.splitext(os.path.basename(source_b))[0]
    elif args.users and len(args.users) >= 2:
        mode = 'scrape'
        user_a, user_b = args.users[0].lstrip('@'), args.users[1].lstrip('@')
        source_a, source_b = user_a, user_b
    elif args.users and len(args.users) == 1:
        print("❌ Forneça dois usernames para comparar.")
        print("   Uso: python main.py user1 user2")
        sys.exit(1)
    else:
        # Modo interativo
        user_a, user_b, source_a, source_b, mode = interactive_mode()

    # Carregar ratings
    try:
        print()
        print("Carregando dados... Ao infinito e além!")
        print()
        ratings_a = load_ratings(source_a, mode)
        ratings_b = load_ratings(source_b, mode)
    except (FileNotFoundError, ValueError, ConnectionError, ImportError) as e:
        print(f"\n❌ Erro: {e}")
        sys.exit(1)

    print()
    print(f"  @{user_a}: {len(ratings_a)} filmes avaliados")
    print(f"  @{user_b}: {len(ratings_b)} filmes avaliados")

    # Encontrar filmes em comum
    common = find_common_movies(ratings_a, ratings_b)
    print(f"  Filmes em comum: {len(common)}")

    if len(common) < 2:
        print()
        print("❌ Não há filmes em comum suficientes para comparar (mínimo: 2).")
        print("   Certifique-se de que ambos os usuários avaliaram filmes.")
        sys.exit(1)

    # Executar comparação
    ratings_a_values = {slug: ratings_a[slug]['rating'] for slug in common}
    ratings_b_values = {slug: ratings_b[slug]['rating'] for slug in common}

    result = compare_two_rankings(ratings_a_values, ratings_b_values, common)

    if result is None:
        print("❌ Erro ao comparar rankings.")
        sys.exit(1)

    # Mostrar resultados no terminal
    print_results(user_a, user_b, ratings_a, ratings_b, result)
    print_algorithm_info(result)
    run_performance_comparison(result)

    #htmlinho
    if not args.no_report and not args.terminal:
        report_dir = os.path.join(os.path.dirname(__file__), 'reports')
        report_path = os.path.join(report_dir, f'taste_match_{user_a}_vs_{user_b}.html')

        print("─" * 60)
        print("  📄 Gerando relatório HTML...")

        generate_report(user_a, user_b, ratings_a, ratings_b, result, report_path)

        print(f"  ✅ Relatório salvo em: {report_path}")

        if not args.no_browser:
            abs_path = os.path.abspath(report_path)
            webbrowser.open(f'file:///{abs_path}')
            print("   Abrindo no navegador...")

        print()

    print("=" * 60)
    print("  Feito! 🎬")
    print("=" * 60)
    print()


if __name__ == '__main__':
    main()
