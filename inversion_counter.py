

def merge_count_inversions(arr):

    if len(arr) <= 1:
        return arr[:], 0

    mid = len(arr) // 2

    # divisão: resolve recursivamente cada metade
    left, left_inv = merge_count_inversions(arr[:mid])
    right, right_inv = merge_count_inversions(arr[mid:])

    # conquista: merge contando inversões entre as metades
    merged = []
    split_inv = 0
    i = j = 0

    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            merged.append(left[i])
            i += 1
        else:
            # Nota para josé: todos os elementos restantes em left[i:] formam inversão
            # com right[j], pois left é ordenado e left[i] > right[j]
            merged.append(right[j])
            split_inv += len(left) - i
            j += 1

    merged.extend(left[i:])
    merged.extend(right[j:])

    total_inversions = left_inv + right_inv + split_inv
    return merged, total_inversions


def brute_force_count_inversions(arr):
    count = 0
    n = len(arr)
    for i in range(n):
        for j in range(i + 1, n):
            if arr[i] > arr[j]:
                count += 1
    return count


def calculate_similarity(inversions, n):
  
    max_inversions = n * (n - 1) // 2
    if max_inversions == 0:
        return 1.0
    return 1.0 - (inversions / max_inversions)


def compare_two_rankings(ratings_a, ratings_b, common_keys):
    if len(common_keys) < 2:
        return None

    # ordena os filmes em comum pela nota do Usuário A (desc), desempate alfabético
    a_sorted = sorted(common_keys, key=lambda m: (-ratings_a[m], m))

    # ordena os filmes em comum pela nota do Usuário B (desc), desempate alfabético
    b_sorted = sorted(common_keys, key=lambda m: (-ratings_b[m], m))

    # cria mapeamento: filme → posição no ranking de B
    b_rank = {movie: i for i, movie in enumerate(b_sorted)}

    # permutação: posições de B na ordem de A
    permutation = [b_rank[movie] for movie in a_sorted]

    # conta inversões usando Merge Sort
    _, inversions = merge_count_inversions(permutation)

    n = len(common_keys)
    max_inversions = n * (n - 1) // 2
    similarity = calculate_similarity(inversions, n)

    # encontra maiores concordâncias e discordâncias
    differences = []
    for key in common_keys:
        diff = abs(ratings_a[key] - ratings_b[key])
        avg = (ratings_a[key] + ratings_b[key]) / 2
        differences.append({
            'key': key,
            'rating_a': ratings_a[key],
            'rating_b': ratings_b[key],
            'diff': diff,
            'avg': avg
        })

    # top concordâncias: menor diferença, maior média
    agreements = sorted(differences, key=lambda x: (x['diff'], -x['avg']))

    # top discordâncias: maior diferença
    disagreements = sorted(differences, key=lambda x: (-x['diff'], -x['avg']))

    return {
        'common_count': n,
        'inversions': inversions,
        'max_inversions': max_inversions,
        'similarity': similarity,
        'similarity_pct': round(similarity * 100, 1),
        'permutation': permutation,
        'a_sorted': a_sorted,
        'b_sorted': b_sorted,
        'agreements': agreements[:10],
        'disagreements': disagreements[:10],
    }
