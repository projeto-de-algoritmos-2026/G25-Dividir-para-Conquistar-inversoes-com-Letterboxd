

import html
import os


def rating_to_stars_html(rating):
    """Converte nota para estrelas em HTML com cores."""
    full = int(rating)
    half = 1 if (rating - full) >= 0.5 else 0
    empty = 5 - full - half
    stars = (
        '<span class="star filled">★</span>' * full
        + ('<span class="star half">★</span>' if half else '')
        + '<span class="star empty">☆</span>' * empty
    )
    return f'<span class="stars">{stars}</span>'


def generate_movie_rows(items, ratings_a, ratings_b, user_a, user_b):
    """Gera linhas HTML da tabela de filmes."""
    rows = []
    for item in items:
        slug = item['key']
        name_a = ratings_a[slug].get('name', slug)
        year = ratings_a[slug].get('year', '')
        display = html.escape(f"{name_a} ({year})" if year else name_a)
        diff = abs(item['rating_a'] - item['rating_b'])

        rows.append(f"""
            <tr>
                <td class="movie-name">{display}</td>
                <td class="rating-cell">
                    {rating_to_stars_html(item['rating_a'])}
                    <span class="rating-num">{item['rating_a']:.1f}</span>
                </td>
                <td class="rating-cell">
                    {rating_to_stars_html(item['rating_b'])}
                    <span class="rating-num">{item['rating_b']:.1f}</span>
                </td>
                <td class="diff-cell">
                    <span class="diff-badge {'diff-low' if diff <= 0.5 else 'diff-mid' if diff <= 1.5 else 'diff-high'}">
                        {diff:.1f}
                    </span>
                </td>
            </tr>
        """)
    return '\n'.join(rows)


def generate_report(user_a, user_b, ratings_a, ratings_b, result, output_path):
    """
    Gera um relatório HTML completo com os resultados da comparação.

    Args:
        user_a (str): Nome/identificador do usuário A.
        user_b (str): Nome/identificador do usuário B.
        ratings_a (dict): Ratings do usuário A.
        ratings_b (dict): Ratings do usuário B.
        result (dict): Resultado de compare_two_rankings().
        output_path (str): Caminho para salvar o HTML.
    """

    similarity_pct = result['similarity_pct']
    inversions = result['inversions']
    max_inversions = result['max_inversions']
    common_count = result['common_count']

    # Determina a mensagem baseada na similaridade
    if similarity_pct >= 90:
        match_msg = "Almas Gêmeas Cinematográficas! "
        match_color = "#00e676"
    elif similarity_pct >= 70:
        match_msg = "Muito Compatíveis! "
        match_color = "#69f0ae"
    elif similarity_pct >= 50:
        match_msg = "Gosto Razoavelmente Parecido "
        match_color = "#ffd740"
    elif similarity_pct >= 30:
        match_msg = "Opiniões Bem Diferentes "
        match_color = "#ff9100"
    else:
        match_msg = "Gostos Completamente Opostos! "
        match_color = "#ff5252"

    # Calcula offset do SVG circular (circunferência = 2 * π * 54 ≈ 339.29)
    circle_circumference = 339.29
    circle_offset = circle_circumference * (1 - result['similarity'])

    # Gera tabelas de concordâncias e discordâncias
    agreement_rows = generate_movie_rows(
        result['agreements'][:8], ratings_a, ratings_b, user_a, user_b
    )
    disagreement_rows = generate_movie_rows(
        result['disagreements'][:8], ratings_a, ratings_b, user_a, user_b
    )

    # Exemplo do algoritmo
    example_movies = result['agreements'][:4] + result['disagreements'][:1]
    example_movies = example_movies[:5]
    example_a_names = [html.escape(ratings_a[m['key']]['name']) for m in example_movies]
    example_a_ratings = [m['rating_a'] for m in example_movies]
    example_b_ratings = [m['rating_b'] for m in example_movies]

    user_a_escaped = html.escape(user_a)
    user_b_escaped = html.escape(user_b)

    report_html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Taste Match — {user_a_escaped} vs {user_b_escaped}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #14181c;
            color: #e0e0e0;
            min-height: 100vh;
            padding: 2rem 1rem;
            overflow-x: hidden;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
            position: relative;
            z-index: 1;
        }}

        .glass-card {{
            background: rgba(44, 52, 64, 0.5);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 20px;
            padding: 2rem;
            margin-bottom: 1.5rem;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}

        .glass-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 40px rgba(0, 0, 0, 0.3);
        }}

        /* Header */
        .header {{
            text-align: center;
            padding: 2.5rem 2rem;
            margin-bottom: 2rem;
            background: rgba(44, 52, 64, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}

        .header-icon {{
            font-size: 3rem;
            margin-bottom: 0.5rem;
            animation: float 3s ease-in-out infinite;
        }}

        @keyframes float {{
            0%, 100% {{ transform: translateY(0); }}
            50% {{ transform: translateY(-10px); }}
        }}

        .header h1 {{
            font-size: 2rem;
            font-weight: 800;
            background: linear-gradient(135deg, #00e676, #00b0ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 1.2rem;
            letter-spacing: -0.02em;
        }}

        .vs-container {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 1.5rem;
            flex-wrap: wrap;
        }}

        .user-badge {{
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 0.6rem 1.5rem;
            font-size: 1.1rem;
            font-weight: 600;
            color: #c084fc;
            letter-spacing: 0.01em;
        }}

        .vs-text {{
            font-size: 1.4rem;
            font-weight: 800;
            color: rgba(255, 255, 255, 0.3);
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }}

        /* Similarity Circle */
        .similarity-section {{
            text-align: center;
            padding: 3rem 2rem;
        }}

        .circle-container {{
            position: relative;
            width: 200px;
            height: 200px;
            margin: 0 auto 1.5rem;
        }}

        .circle-bg {{
            fill: none;
            stroke: rgba(255, 255, 255, 0.06);
            stroke-width: 10;
        }}

        .circle-progress {{
            fill: none;
            stroke: url(#progressGradient);
            stroke-width: 10;
            stroke-linecap: round;
            stroke-dasharray: {circle_circumference};
            stroke-dashoffset: {circle_circumference};
            transform: rotate(-90deg);
            transform-origin: center;
            animation: fillCircle 2s ease-out 0.5s forwards;
        }}

        @keyframes fillCircle {{
            to {{
                stroke-dashoffset: {circle_offset:.2f};
            }}
        }}

        .circle-text {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
        }}

        .circle-pct {{
            font-size: 2.8rem;
            font-weight: 900;
            color: {match_color};
            line-height: 1;
            opacity: 0;
            animation: fadeIn 0.5s ease 1s forwards;
        }}

        .circle-label {{
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.15em;
            color: rgba(255, 255, 255, 0.5);
            margin-top: 4px;
            opacity: 0;
            animation: fadeIn 0.5s ease 1.2s forwards;
        }}

        @keyframes fadeIn {{
            to {{ opacity: 1; }}
        }}

        .match-message {{
            font-size: 1.3rem;
            font-weight: 700;
            color: {match_color};
            margin-bottom: 0.5rem;
            opacity: 0;
            animation: fadeIn 0.6s ease 1.5s forwards;
        }}

        /* Stats Grid */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            margin-top: 1.5rem;
        }}

        .stat-card {{
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 14px;
            padding: 1.2rem;
            text-align: center;
            opacity: 0;
            animation: slideUp 0.5s ease forwards;
        }}

        .stat-card:nth-child(1) {{ animation-delay: 1.6s; }}
        .stat-card:nth-child(2) {{ animation-delay: 1.8s; }}
        .stat-card:nth-child(3) {{ animation-delay: 2.0s; }}

        @keyframes slideUp {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .stat-number {{
            font-size: 2rem;
            font-weight: 800;
            background: linear-gradient(135deg, #00e676, #00b0ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .stat-label {{
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: rgba(255, 255, 255, 0.4);
            margin-top: 0.3rem;
        }}

        /* Tables */
        .section-title {{
            font-size: 1.2rem;
            font-weight: 700;
            margin-bottom: 1.2rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .section-title .icon {{ font-size: 1.3rem; }}

        table {{
            width: 100%;
            border-collapse: collapse;
        }}

        thead th {{
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: rgba(255, 255, 255, 0.35);
            padding: 0.5rem 0.75rem;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }}

        tbody tr {{
            border-bottom: 1px solid rgba(255, 255, 255, 0.03);
            transition: background 0.2s;
        }}

        tbody tr:hover {{
            background: rgba(255, 255, 255, 0.03);
        }}

        td {{
            padding: 0.7rem 0.75rem;
            font-size: 0.9rem;
        }}

        .movie-name {{
            font-weight: 500;
            max-width: 250px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}

        .rating-cell {{
            white-space: nowrap;
        }}

        .stars {{
            font-size: 0.85rem;
            letter-spacing: 1px;
        }}

        .star.filled {{ color: #fbbf24; }}
        .star.half {{ color: #fbbf24; opacity: 0.6; }}
        .star.empty {{ color: rgba(255, 255, 255, 0.15); }}

        .rating-num {{
            font-size: 0.75rem;
            color: rgba(255, 255, 255, 0.4);
            margin-left: 0.4rem;
        }}

        .diff-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
        }}

        .diff-low {{
            background: rgba(0, 230, 118, 0.15);
            color: #69f0ae;
        }}

        .diff-mid {{
            background: rgba(255, 215, 64, 0.15);
            color: #ffd740;
        }}

        .diff-high {{
            background: rgba(255, 82, 82, 0.15);
            color: #ff5252;
        }}

        /* Algorithm Section */
        .algo-section {{
            padding: 2rem;
        }}

        .algo-step {{
            display: flex;
            gap: 1rem;
            margin-bottom: 1.2rem;
            align-items: flex-start;
        }}

        .step-num {{
            flex-shrink: 0;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: linear-gradient(135deg, #7c3aed, #06b6d4);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8rem;
            font-weight: 700;
            color: white;
        }}

        .step-content {{
            font-size: 0.9rem;
            line-height: 1.6;
            color: rgba(255, 255, 255, 0.7);
        }}

        .step-content strong {{
            color: rgba(255, 255, 255, 0.9);
        }}

        .complexity-box {{
            background: rgba(124, 58, 237, 0.1);
            border: 1px solid rgba(124, 58, 237, 0.2);
            border-radius: 12px;
            padding: 1rem 1.5rem;
            margin-top: 1.5rem;
            display: flex;
            justify-content: space-around;
            text-align: center;
            flex-wrap: wrap;
            gap: 1rem;
        }}

        .complexity-item {{
            flex: 1;
            min-width: 150px;
        }}

        .complexity-label {{
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: rgba(255, 255, 255, 0.4);
            margin-bottom: 0.3rem;
        }}

        .complexity-value {{
            font-size: 1.2rem;
            font-weight: 700;
            color: #c084fc;
        }}

        /* Footer */
        .footer {{
            text-align: center;
            padding: 1.5rem;
            font-size: 0.75rem;
            color: rgba(255, 255, 255, 0.25);
        }}

        .footer a {{
            color: rgba(255, 255, 255, 0.4);
            text-decoration: none;
        }}

        /* Responsive */
        @media (max-width: 600px) {{
            .stats-grid {{ grid-template-columns: 1fr; }}
            .vs-container {{ flex-direction: column; gap: 0.5rem; }}
            .header h1 {{ font-size: 1.4rem; }}
            .circle-pct {{ font-size: 2rem; }}
            .movie-name {{ max-width: 120px; }}
            table {{ font-size: 0.8rem; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="glass-card header">
            <div class="header-icon">🎬</div>
            <h1>Letterboxd Taste Match</h1>
            <div class="vs-container">
                <span class="user-badge">@{user_a_escaped}</span>
                <span class="vs-text">vs</span>
                <span class="user-badge">@{user_b_escaped}</span>
            </div>
        </div>

        <!-- Similarity Score -->
        <div class="glass-card similarity-section">
            <div class="circle-container">
                <svg viewBox="0 0 120 120" width="200" height="200">
                    <defs>
                        <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stop-color="#7c3aed" />
                            <stop offset="50%" stop-color="#06b6d4" />
                            <stop offset="100%" stop-color="#34d399" />
                        </linearGradient>
                    </defs>
                    <circle class="circle-bg" cx="60" cy="60" r="54" />
                    <circle class="circle-progress" cx="60" cy="60" r="54" />
                </svg>
                <div class="circle-text">
                    <div class="circle-pct">{similarity_pct}%</div>
                    <div class="circle-label">Similaridade</div>
                </div>
            </div>
            <div class="match-message">{match_msg}</div>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{common_count}</div>
                    <div class="stat-label">Filmes em Comum</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{inversions:,}</div>
                    <div class="stat-label">Inversões</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{max_inversions:,}</div>
                    <div class="stat-label">Máx. Possível</div>
                </div>
            </div>
        </div>

        <!-- Concordâncias -->
        <div class="glass-card">
            <div class="section-title">
                <span class="icon">🤝</span> Maior Concordância
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Filme</th>
                        <th>@{user_a_escaped}</th>
                        <th>@{user_b_escaped}</th>
                        <th>Diff</th>
                    </tr>
                </thead>
                <tbody>
                    {agreement_rows}
                </tbody>
            </table>
        </div>

        <!-- Discordâncias -->
        <div class="glass-card">
            <div class="section-title">
                <span class="icon">⚡</span> Maior Discordância
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Filme</th>
                        <th>@{user_a_escaped}</th>
                        <th>@{user_b_escaped}</th>
                        <th>Diff</th>
                    </tr>
                </thead>
                <tbody>
                    {disagreement_rows}
                </tbody>
            </table>
        </div>

    </div>
</body>
</html>"""

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_html)

    return output_path
