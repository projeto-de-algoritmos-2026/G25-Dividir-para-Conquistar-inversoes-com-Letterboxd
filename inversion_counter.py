

def merge_count_inversions(arr):

    n = len(arr)
    sorted_arr = list(arr)
    temp = [None] * n

    def sort_and_count(start, end):
        if end - start <= 1:
            return 0

        mid = (start + end) // 2

        # divisão: resolve recursivamente cada metade sem criar slices
        left_inv = sort_and_count(start, mid)
        right_inv = sort_and_count(mid, end)

        # conquista: merge contando inversões entre as metades
        split_inv = 0
        left = start
        right = mid
        merged = start

        while left < mid and right < end:
            if sorted_arr[left] <= sorted_arr[right]:
                temp[merged] = sorted_arr[left]
                left += 1
            else:
                # Todos os elementos restantes em sorted_arr[left:mid] formam inversão
                # com sorted_arr[right], pois a metade esquerda está ordenada.
                temp[merged] = sorted_arr[right]
                split_inv += mid - left
                right += 1
            merged += 1

        while left < mid:
            temp[merged] = sorted_arr[left]
            left += 1
            merged += 1

        while right < end:
            temp[merged] = sorted_arr[right]
            right += 1
            merged += 1

        for index in range(start, end):
            sorted_arr[index] = temp[index]

        return left_inv + right_inv + split_inv

    inversions = sort_and_count(0, n)
    return sorted_arr, inversions


def brute_force_count_inversions(arr):
    count = 0
    n = len(arr)
    for i in range(n - 1):
        current = arr[i]
        for j in range(i + 1, n):
            if current > arr[j]:
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
