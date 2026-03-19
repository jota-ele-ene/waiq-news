"""
ai_editor.py — Usa Claude para generar el newsletter digest editorial.
Recibe el payload completo del endpoint (button_urls + articles con metadata)
y genera las secciones temáticas agrupadas.
"""

import json
import sys
from urllib.parse import urlparse

import anthropic

from scripts.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL


def _extract_url_signals(data: dict) -> list[dict]:
    """
    Combina la metadata rica de 'articles' con las URLs de 'button_urls'.
    Prioriza articles (tienen título, imagen, fuente).
    """
    articles    = data.get("articles", [])
    button_urls = data.get("button_urls", [])

    # Indexar articles por URL
    articles_by_url = {a["url"]: a for a in articles if a.get("url")}

    signals = []
    for url in button_urls:
        if url in articles_by_url:
            art = articles_by_url[url]
            signals.append({
                "url":    url,
                "title":  art.get("title", ""),
                "image":  art.get("image", ""),
                "source": art.get("source", ""),
                "domain": urlparse(url).netloc.replace("www.", ""),
            })
        else:
            parsed  = urlparse(url)
            domain  = parsed.netloc.replace("www.", "")
            slug    = parsed.path.rstrip("/").split("/")[-1]
            readable = slug.replace("-", " ").replace("_", " ").strip()
            signals.append({
                "url":    url,
                "title":  readable,
                "image":  "",
                "source": domain,
                "domain": domain,
            })
    return signals


_SYSTEM_PROMPT = """Eres el editor de #WAIQ, newsletter de referencia en español sobre 
tecnologías emergentes: Inteligencia Artificial, Blockchain/Web3 y Computación Cuántica, 
con foco en Europa y España.

Tu misión: analizar una lista de fuentes (con título, dominio y URL) y generar el 
contenido estructurado de un newsletter digest en JSON.

TONO: analítico, directo, con criterio propio. No neutro. WAIQ tiene voz.
IDIOMA: español (aunque las fuentes sean en inglés, el editorial va en español).
AUDIENCIA: profesionales y líderes del sector tech en España y Europa.

Responde ÚNICAMENTE con JSON válido, sin markdown, sin explicaciones."""


def _build_prompt(signals: list[dict], lang: str, days: int) -> str:
    lines = "\n".join(
        f'- [{s["source"] or s["domain"]}] {s["title"] or s["domain"]}  →  {s["url"]}'
        for s in signals
    )
    lang_label = "español" if lang == "es" else "inglés"
    return f"""Período: últimos {days} días. Idioma del editorial: {lang_label}.
Fuentes ({len(signals)}):

{lines}

Genera el contenido del digest con esta estructura JSON exacta:

{{
  "subject": "Asunto del email (max 60 chars, emoji inicial)",
  "preheader": "Preheader (max 90 chars)",
  "editorial": "Párrafo editorial de apertura (3-4 frases, voz WAIQ)",
  "sections": [
    {{
      "title": "Título de la sección temática",
      "emoji": "emoji",
      "summary": "Resumen editorial 2-3 frases",
      "items": [
        {{
          "label": "Titular corto (max 80 chars)",
          "url": "URL EXACTA del listado",
          "domain": "dominio",
          "image": "URL imagen (copia exacta del campo image del input, vacío si no hay)"
        }}
      ]
    }}
  ],
  "closing": "Frase de cierre (1-2 frases)"
}}

Agrupa en 2-4 secciones temáticas. Usa las URLs EXACTAS del input.
El campo image debe copiarse exactamente tal como viene en el input (puede ser vacío)."""


def generate_digest_content(data: dict, lang: str, days: int) -> dict:
    client  = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    signals = _extract_url_signals(data)

    print(f"🤖 Generando editorial con {ANTHROPIC_MODEL} [{lang}, {days}d, {len(signals)} fuentes]…")

    try:
        message = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=4096,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": _build_prompt(signals, lang, days)}],
        )
    except anthropic.APIError as e:
        print(f"❌ Error Anthropic API: {e}", file=sys.stderr)
        sys.exit(1)

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        raw = raw.rsplit("```", 1)[0]

    try:
        content = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"❌ JSON inválido de la IA: {e}", file=sys.stderr)
        print(f"   Respuesta:\n{raw[:500]}", file=sys.stderr)
        sys.exit(1)

    # Enriquecer items con imágenes del input si la IA no las propagó
    signals_by_url = {s["url"]: s for s in signals}
    for section in content.get("sections", []):
        for item in section.get("items", []):
            if not item.get("image"):
                item["image"] = signals_by_url.get(item.get("url", ""), {}).get("image", "")

    total = sum(len(s.get("items", [])) for s in content.get("sections", []))
    print(f"   ✅ {len(content.get('sections', []))} secciones, {total} items.")
    return content
