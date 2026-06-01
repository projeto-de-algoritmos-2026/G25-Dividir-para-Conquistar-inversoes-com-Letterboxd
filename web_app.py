import json
import os
import tempfile
import time
import webbrowser
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

try:
    import cgi
except ImportError:  # pragma: no cover - Python 3.13+ fallback message.
    cgi = None

from inversion_counter import (
    brute_force_count_inversions,
    compare_two_rankings,
    merge_count_inversions,
)
from letterboxd_parser import find_common_movies, parse_zip_export, scrape_profile


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")


def match_message(similarity_pct):
    if similarity_pct >= 90:
        return "Praticamente a mesma pessoa", "excellent"
    if similarity_pct >= 70:
        return "Muito compatíveis", "great"
    if similarity_pct >= 50:
        return "Gosto razoavelmente parecido", "good"
    if similarity_pct >= 30:
        return "Opiniões bem diferentes", "warning"
    return "Gostos completamente opostos", "danger"


def movie_rows(items, ratings_a, ratings_b):
    rows = []
    for item in items:
        key = item["key"]
        movie = ratings_a[key]
        rows.append(
            {
                "name": movie.get("name", key),
                "year": movie.get("year", ""),
                "rating_a": item["rating_a"],
                "rating_b": item["rating_b"],
                "diff": item["diff"],
            }
        )
    return rows


def compare_sources(user_a, user_b, source_a, source_b, mode):
    if mode == "zip":
        ratings_a = parse_zip_export(source_a)
        ratings_b = parse_zip_export(source_b)
    else:
        ratings_a = scrape_profile(source_a)
        ratings_b = scrape_profile(source_b)

    common = find_common_movies(ratings_a, ratings_b)
    if len(common) < 2:
        raise ValueError("Nao ha filmes em comum suficientes para comparar.")

    ratings_a_values = {slug: ratings_a[slug]["rating"] for slug in common}
    ratings_b_values = {slug: ratings_b[slug]["rating"] for slug in common}
    result = compare_two_rankings(ratings_a_values, ratings_b_values, common)
    if result is None:
        raise ValueError("Nao foi possivel comparar os rankings.")

    merge_start = time.perf_counter()
    _, merge_inversions = merge_count_inversions(result["permutation"])
    merge_ms = (time.perf_counter() - merge_start) * 1000

    brute_start = time.perf_counter()
    brute_inversions = brute_force_count_inversions(result["permutation"])
    brute_ms = (time.perf_counter() - brute_start) * 1000

    message, tone = match_message(result["similarity_pct"])

    return {
        "users": {"a": user_a, "b": user_b},
        "message": message,
        "tone": tone,
        "stats": {
            "similarity": result["similarity"],
            "similarity_pct": result["similarity_pct"],
            "common_count": result["common_count"],
            "inversions": result["inversions"],
            "max_inversions": result["max_inversions"],
            "ratings_a_count": len(ratings_a),
            "ratings_b_count": len(ratings_b),
        },
        "performance": {
            "merge_inversions": merge_inversions,
            "merge_ms": round(merge_ms, 3),
            "brute_inversions": brute_inversions,
            "brute_ms": round(brute_ms, 3),
            "speedup": round(brute_ms / merge_ms, 1) if merge_ms > 0 else None,
        },
        "agreements": movie_rows(result["agreements"][:10], ratings_a, ratings_b),
        "disagreements": movie_rows(result["disagreements"][:10], ratings_a, ratings_b),
    }


class TasteMatchHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def log_message(self, format, *args):
        print(f"[frontend] {format % args}")

    def do_POST(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path != "/api/compare":
            self.send_error(HTTPStatus.NOT_FOUND, "Rota nao encontrada")
            return

        try:
            payload = self._read_compare_payload()
            result = compare_sources(**payload)
            self._send_json({"ok": True, "result": result})
        except Exception as exc:
            self._send_json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)
        finally:
            if "payload" in locals() and payload.get("mode") == "zip":
                for key in ("source_a", "source_b"):
                    try:
                        os.remove(payload[key])
                    except OSError:
                        pass

    def _read_compare_payload(self):
        content_type = self.headers.get("Content-Type", "")

        if content_type.startswith("application/json"):
            length = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            return {
                "mode": "scrape",
                "user_a": data.get("user_a", "").strip().lstrip("@"),
                "user_b": data.get("user_b", "").strip().lstrip("@"),
                "source_a": data.get("user_a", "").strip().lstrip("@"),
                "source_b": data.get("user_b", "").strip().lstrip("@"),
            }

        if cgi is None:
            raise ValueError("Upload de ZIP requer Python com suporte ao modulo cgi.")

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": content_type,
                "CONTENT_LENGTH": self.headers.get("Content-Length", "0"),
            },
        )
        mode = form.getfirst("mode", "scrape")

        if mode == "zip":
            zip_a = self._save_upload(form["zip_a"])
            zip_b = self._save_upload(form["zip_b"])
            user_a = form.getfirst("user_a", "").strip() or _upload_name(form["zip_a"])
            user_b = form.getfirst("user_b", "").strip() or _upload_name(form["zip_b"])
            return {
                "mode": "zip",
                "user_a": user_a,
                "user_b": user_b,
                "source_a": zip_a,
                "source_b": zip_b,
            }

        user_a = form.getfirst("user_a", "").strip().lstrip("@")
        user_b = form.getfirst("user_b", "").strip().lstrip("@")
        return {
            "mode": "scrape",
            "user_a": user_a,
            "user_b": user_b,
            "source_a": user_a,
            "source_b": user_b,
        }

    def _save_upload(self, field):
        if not getattr(field, "filename", ""):
            raise ValueError("Selecione os dois arquivos ZIP.")

        fd, path = tempfile.mkstemp(prefix="letterboxd_", suffix=".zip")
        with os.fdopen(fd, "wb") as tmp:
            tmp.write(field.file.read())
        return path

    def _send_json(self, payload, status=HTTPStatus.OK):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _upload_name(field):
    filename = os.path.basename(getattr(field, "filename", "") or "")
    return os.path.splitext(filename)[0] or "Usuario"


def run_web_frontend(host="127.0.0.1", port=8000, open_browser=True):
    selected_port = port
    server = None

    for selected_port in range(port, port + 50):
        try:
            server = ThreadingHTTPServer((host, selected_port), TasteMatchHandler)
            break
        except OSError:
            continue

    if server is None:
        raise OSError("Nao foi possivel iniciar o servidor local.")

    url = f"http://{host}:{selected_port}/"
    print(f"Interface web rodando em {url}")
    print("Pressione Ctrl+C para encerrar.")

    if open_browser:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
    finally:
        server.server_close()
