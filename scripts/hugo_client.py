"""
hugo_client.py — Recupera contenido desde los endpoints del servidor Hugo.

Endpoints:
  SINGLE  GET /api/newsletter/single-es   (o -en)
          Respuesta: markdown + frontmatter YAML/TOML

  DIGEST  GET /api/newsletter/digest-es-15  (o -en-15, -es-30, -en-30)
          Respuesta: {
            "button_urls": ["https://..."],
            "total": N,
            "articles": [
              {"url": "https://...", "title": "...", "image": "https://...", "source": "..."},
              ...
            ]
          }
"""

import sys
import re
from datetime import datetime

import requests
import yaml

from scripts.config import (
    HUGO_SINGLE_ENDPOINT_ES, HUGO_SINGLE_ENDPOINT_EN,
    HUGO_DIGEST_ENDPOINT_ES, HUGO_DIGEST_ENDPOINT_EN,
)


# ── Helpers de frontmatter ────────────────────────────────────────────────────

def _parse_frontmatter(text: str) -> tuple[dict, str]:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if m:
        meta = yaml.safe_load(m.group(1)) or {}
        return meta, text[m.end():].strip()
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


# ── Single ────────────────────────────────────────────────────────────────────

def fetch_single_post(lang: str) -> dict:
    """
    Llama al endpoint single del idioma indicado.
    Ahora espera JSON (no markdown+frontmatter) con esta estructura:
      {
        "title": "...",
        "date": "2026-03-16T08:00:00+01:00",
        "permalink": "https://...",
        "params": {
          "description": "...",
          "topics": [...],
          "areas": [...],
          "references": [{"title","url","source","image"}, ...]
        },
        "content": "markdown del cuerpo..."
      }
    """
    endpoint = HUGO_SINGLE_ENDPOINT_ES if lang == "es" else HUGO_SINGLE_ENDPOINT_EN
    print(f"📡 GET {endpoint}  [lang={lang}]")
    try:
        resp = requests.get(endpoint, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        print(f"❌ Error en endpoint single: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"❌ El endpoint no devolvió JSON válido: {e}", file=sys.stderr)
        sys.exit(1)

    params = data.get("params", {})

    # Limpiar content markdown para excerpt (por si se necesita en el futuro)
    body_raw   = data.get("content", "")
    body_clean = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", body_raw)  # quitar links
    body_clean = re.sub(r"[#*`>]", "", body_clean)
    body_clean = re.sub(r"\s+", " ", body_clean).strip()

    # Las imágenes de referencias pueden ser rutas relativas — prefixar con SITE_BASE_URL
    from scripts.config import SITE_BASE_URL
    references = []
    for ref in params.get("references", []) or []:
        img = ref.get("image", "") or ""
        if img and img.startswith("/"):
            img = SITE_BASE_URL + img
        references.append({
            "title":  ref.get("title", ""),
            "url":    ref.get("url", ""),
            "source": ref.get("source", ""),
            "image":  img,
        })

    post = {
        "title":       data.get("title", "Sin título"),
        "description": params.get("description", ""),
        "url":         data.get("permalink", ""),
        "date":        _parse_date(data.get("date") or params.get("date")),
        "topics":      params.get("topics", []) or [],
        "areas":       params.get("areas", []) or [],
        "references":  references,
        "body":        body_raw,
        "body_clean":  body_clean,
    }
    print(f"   ✅ Post: {post['title']}")
    return post

# ── Digest ────────────────────────────────────────────────────────────────────

def fetch_digest_data(lang: str, days: int) -> dict:
    """
    Llama al endpoint digest con sufijo -{days}.
    Devuelve el JSON completo: {button_urls, total, articles}.
    articles es una lista de {url, title, image, source}.
    """
    base = HUGO_DIGEST_ENDPOINT_ES if lang == "es" else HUGO_DIGEST_ENDPOINT_EN
    # El endpoint incluye el período como sufijo: digest-es-15 o digest-en-30
    # Si el endpoint ya lleva el idioma embebido, solo añadimos -days
    endpoint = f"{base}-{days}"
    print(f"📡 GET {endpoint}  [lang={lang}, days={days}]")
    try:
        resp = requests.get(endpoint, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        print(f"❌ Error en endpoint digest: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"❌ El endpoint no devolvió JSON válido: {e}", file=sys.stderr)
        sys.exit(1)

    urls     = data.get("button_urls", [])
    articles = data.get("articles", [])
    total    = data.get("total", len(urls))

    if not urls and not articles:
        print(f"⚠️  El endpoint devolvió 0 contenidos para days={days}.")
        sys.exit(0)

    print(f"   ✅ {total} URLs recibidas, {len(articles)} artículos con metadata.")
    return {
        "button_urls": urls,
        "articles":    articles,
        "total":       total,
    }
