"""
hugo_client.py — Recupera contenido desde los endpoints del servidor Hugo.

Endpoints esperados:
  SINGLE  GET /api/newsletter/single
          Respuesta: texto plano markdown con frontmatter YAML/TOML

  DIGEST  GET /api/newsletter/digest?since=YYYY-MM-DD
          Respuesta: { "button_urls": ["https://...", ...], "total": N }
"""

import sys
import re
from datetime import datetime

import requests
import yaml

from scripts.config import HUGO_SINGLE_ENDPOINT, HUGO_DIGEST_ENDPOINT


# ─────────────────────────────────────────────────────────────────────────────
# Parseo de frontmatter
# ─────────────────────────────────────────────────────────────────────────────

def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Devuelve (meta, body) extrayendo frontmatter YAML o TOML."""
    # YAML ---
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if m:
        meta = yaml.safe_load(m.group(1)) or {}
        return meta, text[m.end():].strip()

    # TOML +++
    m = re.match(r"^\+\+\+\s*\n(.*?)\n\+\+\+\s*\n", text, re.DOTALL)
    if m:
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
        return tomllib.loads(m.group(1)), text[m.end():].strip()

    return {}, text.strip()


def _parse_date(raw) -> datetime | None:
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw.replace(tzinfo=None)
    if hasattr(raw, "year"):
        return datetime(raw.year, raw.month, raw.day)
    if isinstance(raw, str):
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(raw[:len(fmt)], fmt)
            except ValueError:
                continue
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Clientes
# ─────────────────────────────────────────────────────────────────────────────

def fetch_single_post() -> dict:
    """
    Llama al endpoint single y devuelve el post parseado como dict con claves:
      title, description, date, tags, slug, url, body (markdown sin frontmatter)
    Aborta con sys.exit si hay error.
    """
    print(f"📡 GET {HUGO_SINGLE_ENDPOINT}")
    try:
        resp = requests.get(HUGO_SINGLE_ENDPOINT, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Error llamando al endpoint single: {e}", file=sys.stderr)
        sys.exit(1)

    meta, body = _parse_frontmatter(resp.text)

    if not meta:
        print("❌ El endpoint no devolvió frontmatter válido.", file=sys.stderr)
        sys.exit(1)

    # Construir URL pública
    slug = meta.get("slug", "")
    if not slug:
        # Intentar inferirla del título si no hay slug
        slug = re.sub(r"[^a-z0-9]+", "-", meta.get("title", "post").lower()).strip("-")

    post = {
        "title":       meta.get("title", "Sin título"),
        "description": meta.get("description", meta.get("summary", "")),
        "date":        _parse_date(meta.get("date")),
        "tags":        meta.get("tags", []) or [],
        "slug":        slug,
        "url":         meta.get("url") or f"{meta.get('_site_base','')}/article/{slug}/",
        "body":        body,
        "_raw_meta":   meta,
    }

    print(f"   ✅ Post obtenido: {post['title']}")
    return post


def fetch_digest_urls(since_date: str) -> list[str]:
    """
    Llama al endpoint digest con ?since=YYYY-MM-DD.
    Devuelve la lista de URLs (button_urls).
    Aborta con sys.exit si hay error o respuesta inválida.
    """
    url = f"{HUGO_DIGEST_ENDPOINT}?since={since_date}"
    print(f"📡 GET {url}")
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        print(f"❌ Error llamando al endpoint digest: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"❌ El endpoint no devolvió JSON válido: {e}", file=sys.stderr)
        sys.exit(1)

    urls = data.get("button_urls", [])
    total = data.get("total", len(urls))

    if not urls:
        print(f"⚠️  El endpoint devolvió 0 URLs para since={since_date}.")
        sys.exit(0)

    print(f"   ✅ {total} URLs recibidas.")
    return urls
