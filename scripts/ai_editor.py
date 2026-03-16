"""
ai_editor.py — Usa Claude (Anthropic) para generar el contenido editorial
del newsletter digest a partir de una lista de URLs.

La IA analiza dominios y slugs de las URLs para inferir temas, agruparlos
y redactar un newsletter editorial en español con voz propia de WAIQ.
"""

import json
import sys
from urllib.parse import urlparse

import anthropic

from scripts.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _extract_url_signals(urls: list[str]) -> list[dict]:
    """
    Extrae señales legibles de cada URL: dominio, path, slug inferido.
    Limpia parámetros de tracking (utm_*, etc.)
    """
    signals = []
    for url in urls:
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "")
            # Limpiar path: quitar extensiones y separar por - /
            path = parsed.path.rstrip("/")
            slug_raw = path.split("/")[-1] if path else ""
            # Convertir slug kebab-case a palabras legibles
            readable = slug_raw.replace("-", " ").replace("_", " ").strip()
            signals.append({
                "url":      url,
                "domain":   domain,
                "path":     path,
                "readable": readable or path,
            })
        except Exception:
            signals.append({"url": url, "domain": url, "path": "", "readable": url})
    return signals


_SYSTEM_PROMPT = """Eres el editor de #WAIQ, un newsletter de referencia en español sobre 
tecnologías emergentes: Inteligencia Artificial, Blockchain/Web3 y Computación Cuántica, 
con foco en Europa y España.

Tu misión: analizar una lista de URLs (fuentes externas recopiladas como señales del radar 
de WAIQ) y generar el contenido estructurado de un newsletter digest en JSON.

TONO: analítico, directo, con criterio propio. No neutro. WAIQ tiene voz.
IDIOMA: español.
AUDIENCIA: profesionales y líderes del sector tech en España y Europa.

Responde ÚNICAMENTE con un objeto JSON válido, sin markdown, sin explicaciones."""


def _build_user_prompt(signals: list[dict], since_date: str) -> str:
    signals_text = "\n".join(
        f'- {s["domain"]} → {s["readable"]}  [url: {s["url"]}]'
        for s in signals
    )
    return f"""Período cubierto: desde {since_date} hasta hoy.
Fuentes recogidas ({len(signals)} URLs):

{signals_text}

Genera el contenido del newsletter digest con esta estructura JSON exacta:

{{
  "subject": "Línea de asunto del email (max 60 chars, con emoji inicial)",
  "preheader": "Texto preheader del email (max 90 chars)",
  "editorial": "Párrafo editorial de apertura (3-4 frases, voz WAIQ, sin mencionar las URLs explícitamente)",
  "sections": [
    {{
      "title": "Título de la sección temática",
      "emoji": "emoji representativo",
      "summary": "Resumen editorial de 2-3 frases sobre lo que ocurre en este tema",
      "items": [
        {{
          "label": "Titular corto (max 80 chars)",
          "url": "URL original exacta",
          "domain": "dominio fuente"
        }}
      ]
    }}
  ],
  "closing": "Frase de cierre editorial (1-2 frases, firma de WAIQ)"
}}

Agrupa las URLs en 2-4 secciones temáticas coherentes según los temas que detectes 
(IA, Blockchain/Web3, Cuántica, Regulación, etc.). 
Cada item debe usar la URL EXACTA del listado de fuentes. No inventes URLs.
Prioriza calidad sobre cantidad: si una URL no encaja en ningún tema, omítela."""


# ─────────────────────────────────────────────────────────────────────────────
# Función principal
# ─────────────────────────────────────────────────────────────────────────────

def generate_digest_content(urls: list[str], since_date: str) -> dict:
    """
    Llama a Claude para generar el contenido editorial del digest.
    Devuelve el dict con subject, preheader, editorial, sections, closing.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    signals = _extract_url_signals(urls)

    print(f"🤖 Generando contenido editorial con {ANTHROPIC_MODEL}…")
    print(f"   Analizando {len(signals)} fuentes…")

    try:
        message = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=4096,
            system=_SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": _build_user_prompt(signals, since_date)}
            ],
        )
    except anthropic.APIError as e:
        print(f"❌ Error en Anthropic API: {e}", file=sys.stderr)
        sys.exit(1)

    raw = message.content[0].text.strip()

    # Limpiar posibles backticks si el modelo los añade
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        raw = raw.rsplit("```", 1)[0]

    try:
        content = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"❌ La IA no devolvió JSON válido: {e}", file=sys.stderr)
        print(f"   Respuesta recibida:\n{raw[:500]}", file=sys.stderr)
        sys.exit(1)

    sections = content.get("sections", [])
    total_items = sum(len(s.get("items", [])) for s in sections)
    print(f"   ✅ {len(sections)} secciones generadas, {total_items} items.")
    return content
