

import csv
import io
import os
import re
import time
import zipfile


def parse_zip_export(zip_path):
   
    ratings = {}

    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {zip_path}")

    with zipfile.ZipFile(zip_path, 'r') as z:
        # Procura pelo ratings.csv (pode estar na raiz ou em subpasta)
        ratings_file = None
        for name in z.namelist():
            if name.endswith('ratings.csv'):
                ratings_file = name
                break

        if ratings_file is None:
            raise ValueError(
                f"Arquivo 'ratings.csv' não encontrado no ZIP.\n"
                f"Conteúdo do ZIP: {z.namelist()}\n"
                f"Certifique-se de exportar os dados do Letterboxd em "
                f"Settings > Import & Export > Export Your Data."
            )

        with z.open(ratings_file) as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8'))

            for row in reader:
                name = row.get('Name', '').strip()
                year = row.get('Year', '').strip()
                rating_str = row.get('Rating', '').strip()
                uri = row.get('Letterboxd URI', '').strip()

                if not name or not rating_str:
                    continue

                try:
                    rating = float(rating_str)
                except ValueError:
                    continue

                # Extrai o slug da URI do Letterboxd
                # Ex: https://letterboxd.com/film/the-godfather/ → the-godfather
                slug = _extract_slug_from_uri(uri) if uri else _name_to_slug(name, year)

                ratings[slug] = {
                    'name': name,
                    'year': year,
                    'rating': rating,
                    'slug': slug,
                }

    return ratings


def scrape_profile(username):
   
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        raise ImportError(
            "Para usar o modo de web scraping, instale as dependências:\n"
            "  pip install requests beautifulsoup4\n\n"
            "Ou use o modo ZIP: python main.py --zip arquivo1.zip arquivo2.zip"
        )

    ratings = {}
    page = 1
    # Usa /page/N/ diretamente para evitar Cloudflare challenge no path base
    base_url = f"https://letterboxd.com/{username}/films/ratings"
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/125.0.0.0 Safari/537.36'
        ),
        'Accept': (
            'text/html,application/xhtml+xml,application/xml;'
            'q=0.9,image/avif,image/webp,*/*;q=0.8'
        ),
        'Accept-Language': 'en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7',
    }

    print(f"  Buscando avaliações de @{username}...", end="", flush=True)

    while True:
        url = f"{base_url}/page/{page}/"
        try:
            resp = requests.get(url, headers=headers, timeout=15)
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"\nNão foi possível conectar ao Letterboxd.\n"
                f"Verifique sua conexão ou use o modo ZIP."
            )

        if resp.status_code == 404:
            if page == 1:
                raise ValueError(
                    f"\nPerfil @{username} não encontrado no Letterboxd.\n"
                    f"Verifique o nome de usuário."
                )
            break

        if resp.status_code != 200:
            if page == 1:
                raise ValueError(
                    f"\nErro ao acessar perfil @{username} (HTTP {resp.status_code})."
                )
            break

        soup = BeautifulSoup(resp.text, 'html.parser')

        # Busca os grid items (estrutura atual do Letterboxd)
        grid_items = soup.select('li.griditem')

        if not grid_items:
            if page == 1:
                raise ValueError(
                    f"\nPerfil @{username} não possui avaliações públicas."
                )
            break

        count_this_page = 0
        for item in grid_items:
            film_data = _extract_film_from_griditem(item)
            if film_data:
                ratings[film_data['slug']] = film_data
                count_this_page += 1

        print(".", end="", flush=True)

        # Verifica se há próxima página
        next_link = soup.select_one('a.next')
        if not next_link:
            break

        page += 1
        # Rate limiting - espera entre requisições
        time.sleep(1.0)

    print(f" {len(ratings)} filmes encontrados!")
    return ratings


def _extract_film_from_griditem(griditem_element):
   
    try:
        # Busca o div react-component com data-item-slug
        react_div = griditem_element.select_one(
            'div.react-component[data-item-slug]'
        )
        if not react_div:
            return None

        slug = react_div.get('data-item-slug', '')
        if not slug:
            return None

        # Nome do filme: usa data-item-name ou data-item-full-display-name
        name = react_div.get('data-item-name', '')
        if not name:
            name = react_div.get('data-item-full-display-name', '')
        if not name:
            img = react_div.select_one('img')
            if img:
                name = img.get('alt', '')
        if not name:
            name = slug.replace('-', ' ').title()

        # Ano: tenta extrair do data-item-full-display-name "Nome (Ano)"
        year = ''
        full_name = react_div.get('data-item-full-display-name', '')
        year_match = re.search(r'\((\d{4})\)$', full_name)
        if year_match:
            year = year_match.group(1)
            # Remove o ano do nome se data-item-name já o incluiu
            if name.endswith(f'({year})'):
                name = name[:-(len(year) + 3)].strip()

        # Rating: busca a classe rated-N no span de rating dentro de p.poster-viewingdata
        rating = 0.0
        rating_span = griditem_element.select_one(
            'p.poster-viewingdata span.rating'
        )
        if not rating_span:
            return None  # Sem rating, pula

        rating_classes = rating_span.get('class', [])
        for cls in rating_classes:
            match = re.match(r'rated-(\d+)', cls)
            if match:
                # rated-N: N vai de 1 a 10 (incrementos de meia estrela)
                # rated-1 = 0.5★, rated-2 = 1.0★, ..., rated-10 = 5.0★
                rating = int(match.group(1)) / 2.0
                break

        if rating == 0.0:
            return None

        return {
            'name': name,
            'year': year,
            'rating': rating,
            'slug': slug,
        }

    except Exception:
        return None


def _extract_slug_from_uri(uri):

    match = re.search(r'/film/([^/]+)/?', uri)
    if match:
        return match.group(1)
    return uri


def _name_to_slug(name, year=''):

    slug = name.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s]+', '-', slug).strip('-')
    if year:
        slug = f"{slug}-{year}"
    return slug


def find_common_movies(ratings_a, ratings_b):

    return sorted(set(ratings_a.keys()) & set(ratings_b.keys()))


def get_display_name(film_data):

    name = film_data.get('name', film_data.get('slug', '?'))
    year = film_data.get('year', '')
    if year:
        return f"{name} ({year})"
    return name


def rating_to_stars(rating):
    """
    Converte uma nota numérica (0.5–5.0) para representação em estrelas.

    Ex: 3.5 → '★★★½☆', 5.0 → '★★★★★'
    """
    full = int(rating)
    half = 1 if (rating - full) >= 0.5 else 0
    empty = 5 - full - half
    return '★' * full + ('½' if half else '') + '☆' * empty
