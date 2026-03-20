"""
html_builder.py — Genera el HTML del email con estilos WAIQ (waiq.css).

Cambios respecto a versión anterior:
  - Sin h1 en modo single
  - Sin topics/tags en modo single
  - Descripción completa (sin truncar)
  - Referencias con imagen en miniatura a la izquierda (campo image del JSON)
  - Idioma (lang) propagado a textos UI

Tokens de diseño de /css/waiq.css:
  NAVY    = rgb(2,21,71)   textos, fondos, botones
  CYAN    = #00A8BC        acentos, h2, links, tags topics
  CYAN_LT = #9cecf5        hover, gradiente
  FONT    = tradegothiclt-bold
"""

from datetime import datetime
from scripts.config import SITE_BASE_URL, FROM_NAME, BREVO_TEMPLATE_ID

NAVY    = "rgb(2,21,71)"
CYAN    = "#00A8BC"
CYAN_LT = "#9cecf5"
FONT    = "'tradegothiclt-bold',Arial,sans-serif"

# Textos UI por idioma
_UI = {
    "es": {
        "featured":  "Artículo destacado de la semana",
        "read_more": "Leer el artículo completo →",
        "sources":   "Fuentes",
        "digest":    "Digest · últimos {days} días",
        "unsubscribe": "Cancelar suscripción",
        "footer_msg": "Recibes esto porque eres parte de la comunidad WAIQ.",
    },
    "en": {
        "featured":  "Article of the week",
        "read_more": "Read full article →",
        "sources":   "Sources",
        "digest":    "Digest · last {days} days",
        "unsubscribe": "Unsubscribe",
        "footer_msg": "You receive this because you are part of the WAIQ community.",
    },
}


def _ui(key: str, lang: str, **kwargs) -> str:
    text = _UI.get(lang, _UI["es"]).get(key, _UI["es"][key])
    return text.format(**kwargs) if kwargs else text


# ── Componentes base ──────────────────────────────────────────────────────────

def _tag_topic(tag: str) -> str:
    return (
        f'<span style="display:inline-block;background:{CYAN};color:#ffffff;'
        f'font-size:11px;padding:2px 10px;border-radius:8px;'
        f'margin:0 4px 4px 0;letter-spacing:normal;">{tag}</span>'
    )


def _tag_area(tag: str) -> str:
    return (
        f'<span style="display:inline-block;background:#ffffff;color:{CYAN};'
        f'border:1px solid {CYAN};font-size:11px;padding:2px 10px;border-radius:8px;'
        f'margin:0 4px 4px 0;letter-spacing:normal;">{tag}</span>'
    )


def _button(url: str, label: str) -> str:
    return (
        f'<a href="{url}" style="display:inline-block;background:{NAVY};color:#ffffff;'
        f'padding:10px 24px;border-radius:4px;text-decoration:none;font-weight:700;'
        f'font-size:14px;letter-spacing:1px;font-family:{FONT};">{label}</a>'
    )


def _h2(text: str) -> str:
    """h2 WAIQ: línea de 100px encima en CYAN + texto CYAN (emulado con tabla para email)."""
    return f"""
    <table role="presentation" cellpadding="0" cellspacing="0" border="0"
      style="margin:0 0 6px;">
      <tr>
        <td style="border-top:6px solid {CYAN};width:100px;font-size:0;line-height:0;">
          &nbsp;
        </td>
      </tr>
      <tr>
        <td style="font-family:{FONT};font-size:18px;font-weight:bold;
          color:{CYAN};padding-top:6px;">
          {text}
        </td>
      </tr>
    </table>"""


def _ref_item(title: str, url: str, source: str = "", image: str = "") -> str:
    """
    Item de referencia estilo radar-ref-item:
    - border-left 3px CYAN
    - miniatura a la izquierda si hay imagen (64x64, object-fit cover)
    - título + fuente a la derecha
    """
    thumb = ""
    if image:
        thumb = f"""
        <td style="width:64px;min-width:64px;padding-right:10px;vertical-align:top;">
          <a href="{url}" style="display:block;width:64px;height:64px;overflow:hidden;
            border-radius:2px;text-decoration:none;">
            <img src="{image}" width="64" height="64"
              style="width:64px;height:64px;object-fit:cover;display:block;border:0;"
              alt="">
          </a>
        </td>"""

    content_td = f"""
        <td style="vertical-align:top;">
          <a href="{url}" style="font-family:{FONT};font-size:13px;font-weight:600;
            color:{NAVY};text-decoration:none;line-height:1.35;display:block;">
            {title}
          </a>
          {"<span style='font-size:11px;color:" + CYAN + ";opacity:0.8;letter-spacing:0.03em;display:block;margin-top:3px;'>" + source + "</span>" if source else ""}
        </td>"""

    return f"""
    <tr>
      <td style="padding:0;border-left:3px solid {CYAN};
        background:rgba(0,168,188,0.04);border-radius:2px;">
        <table role="presentation" cellpadding="10" cellspacing="0" border="0"
          width="100%">
          <tr>
            {thumb}
            {content_td}
          </tr>
        </table>
      </td>
    </tr>
    <tr><td style="height:8px;font-size:0;line-height:0;">&nbsp;</td></tr>"""


# ── Wrapper HTML autónomo (fallback sin plantilla Brevo) ─────────────────────

def _standalone_wrap(inner: str, preheader: str, lang: str) -> str:
    year = datetime.utcnow().year
    pre_tag = (
        f'<div style="display:none;max-height:0;overflow:hidden;mso-hide:all;'
        f'font-size:1px;line-height:1px;color:#f5f5f5;">{preheader}&nbsp;</div>'
        if preheader else ""
    )
    lang_path = "es/" if lang == "es" else ""
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="x-apple-disable-message-reformatting">
  <title>{FROM_NAME} Newsletter</title>
</head>
<body style="margin:0;padding:0;background:#f5f5f5;
  font-family:{FONT};color:{NAVY};-webkit-text-size-adjust:100%;">
{pre_tag}
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
  style="background:#f5f5f5;">
  <tr>
    <td align="center" style="padding:32px 16px 48px;">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"
        style="max-width:600px;width:100%;">

        <!-- NAVBAR -->
        <tr>
          <td style="background:{NAVY};padding:10px 24px;text-align:center;">
            <a href="{SITE_BASE_URL}" style="text-decoration:none;">
              <span style="font-family:{FONT};font-size:20px;font-weight:700;
                color:#ffffff;letter-spacing:8px;">#WAIQ</span>
              <span style="font-family:{FONT};font-size:20px;font-weight:400;
                color:{CYAN};letter-spacing:8px;">news</span>
            </a>
            &nbsp;&nbsp;
            <a href="{SITE_BASE_URL}/{lang_path}topics/ai"
              style="color:#f2f2f2;font-size:11px;letter-spacing:8px;
              text-decoration:none;padding:0 8px;">AI</a>
            <a href="{SITE_BASE_URL}/{lang_path}topics/web3"
              style="color:#f2f2f2;font-size:11px;letter-spacing:8px;
              text-decoration:none;padding:0 8px;">WEB3</a>
            <a href="{SITE_BASE_URL}/{lang_path}topics/quantum"
              style="color:#f2f2f2;font-size:11px;letter-spacing:8px;
              text-decoration:none;padding:0 8px;">QUANTUM</a>
          </td>
        </tr>

        <!-- BANNER -->
        <tr>
          <td style="background:linear-gradient(45deg,#ffffff 0%,{CYAN_LT} 100%);
            border:4px solid {CYAN};border-top:none;
            padding:20px 32px 16px;">
            <p style="font-family:{FONT};font-size:11px;font-weight:700;
              letter-spacing:5px;color:{NAVY};text-transform:uppercase;margin:0;">
              Newsletter
            </p>
          </td>
        </tr>

        <!-- CUERPO -->
        <tr>
          <td style="background:#ffffff;padding:32px 32px 24px;
            border-left:4px solid {CYAN};border-right:4px solid {CYAN};">
            {inner}
          </td>
        </tr>

        <!-- FOOTER -->
        <tr>
          <td style="background:{NAVY};padding:20px 32px;text-align:center;
            border:4px solid {CYAN};border-top:none;">
            <p style="font-family:{FONT};font-size:11px;letter-spacing:3px;
              color:rgba(255,255,255,0.6);margin:0 0 8px;">
              {_ui("footer_msg", lang)}
            </p>
            <p style="font-family:{FONT};font-size:10px;color:rgba(255,255,255,0.4);
              margin:0;letter-spacing:2px;">
              © {year} WAIQ ·
              <a href="{{{{unsubscribe}}}}"
                style="color:rgba(255,255,255,0.4);text-decoration:none;">
                {_ui("unsubscribe", lang)}
              </a>
            </p>
          </td>
        </tr>

      </table>
    </td>
  </tr>
</table>
</body>
</html>"""


# ── Single ────────────────────────────────────────────────────────────────────

def _md_to_html(md: str) -> str:
    """
    Convierte markdown básico a HTML inline compatible con email.
    Cubre: párrafos, negrita, cursiva, links (convertidos a texto+footnote),
    y elimina headings (no apropiados en email).
    """
    if not md:
        return ""
    import re

    # Eliminar headings (# ## ###)
    md = re.sub(r"^#{1,6}\s+(.+)$", r"\1", md, flags=re.MULTILINE)

    # Negrita **texto** o __texto__
    md = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", md)
    md = re.sub(r"__(.+?)__",     r"<strong>\1</strong>", md)

    # Cursiva *texto* o _texto_
    md = re.sub(r"\*(.+?)\*", r"<em>\1</em>", md)
    md = re.sub(r"_(.+?)_",   r"<em>\1</em>", md)

    # Links [texto](url) → href 
    md = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: (
            f'<a href="{m.group(2)}" style="color:{CYAN};text-decoration:none;'
            f'font-weight:600;">{m.group(1)}</a>'
        ),
        md
    )

    # Párrafos: separar bloques por líneas en blanco
    paragraphs = re.split(r"\n{2,}", md.strip())
    html = "".join(
        f'<p style="margin:0 0 14px;">{p.strip().replace(chr(10), " ")}</p>'
        for p in paragraphs if p.strip()
    )
    return html

def _references_block(references: list[dict], lang: str) -> str:
    if not references:
        return ""
    rows = "".join(
        _ref_item(
            ref.get("title", "Ver fuente"),
            ref.get("url", "#"),
            ref.get("source", ref.get("domain", "")),
            ref.get("image", ""),
        )
        for ref in references[:10]
    )
    return f"""
    <div style="margin-top:32px;padding-top:20px;
      border-top:1px solid rgba(0,168,188,0.2);">
      <p style="font-family:{FONT};font-size:10px;font-weight:700;
        letter-spacing:5px;color:{CYAN};text-transform:uppercase;
        margin:0 0 14px;">{_ui("sources", lang)}</p>
      <table role="presentation" width="100%" cellpadding="0"
        cellspacing="0" border="0">
        {rows}
      </table>
    </div>"""


def _single_body(post: dict, lang: str) -> str:
    description = post.get("description", "")
    url         = post.get("url", SITE_BASE_URL)
    title       = post.get("title", "")
    references  = post.get("references", []) or []
    date_obj    = post.get("date")
    date_str    = date_obj.strftime("%d/%m/%Y") if date_obj else ""
    body_html   = _md_to_html(post.get("body", ""))

    # Bloques opcionales calculados ANTES del f-string para evitar
    # conflictos de comillas simples/dobles dentro de style=""
    title_block = (
        f'<h1 style="font-family:{FONT};font-size:22px;font-weight:700;'
        f'line-height:1.25;color:{NAVY};margin:0 0 10px;">'
        f'{title}</h1>'
    ) if title else ""

    date_block = (
        f'<p style="font-family:{FONT};font-size:11px;color:{CYAN};'
        f'letter-spacing:3px;margin:0 0 16px;text-transform:uppercase;">'
        f'{date_str}</p>'
    ) if date_str else ""

    body_block = (
        f'<div style="font-family:{FONT};'
        f'margin:0 0 28px;text-align:justify;">'
        f'{body_html}</div>'
    ) if body_html else ""

    return f"""
    <!--
    <p style="font-family:{FONT};font-size:10px;font-weight:700;
      letter-spacing:5px;color:{NAVY};text-transform:uppercase;
      margin:0 0 20px;padding-bottom:10px;
      border-bottom:1px solid rgba(0,168,188,0.2);">
      {_ui("featured", lang)}
    </p>
    -->

    {title_block}

    {date_block}

    <p style="font-family:{FONT};font-sstyle:italic;
      color:{NAVY};margin:0 0 24px;text-align:justify;
      border-left:3px solid {CYAN};padding-left:14px;">
      {description}
    </p>

    {body_block}

    <!--
    <div style="margin-bottom:32px;">
      {_button(url, _ui("read_more", lang))}
    </div>
    -->

    {_references_block(references, lang)}
    """

def build_single_html(post: dict, lang: str = "es") -> dict:
    subject   = f"✦ {post.get('title', 'The WAIQ State of Play')}"
    preheader = post.get("description", "")[:90]
    body      = _single_body(post, lang)

    if BREVO_TEMPLATE_ID:
        return {
            "mode":      "template",
            "subject":   subject,
            "preheader": preheader,
            "params": {
                "body":        body,
                "subject":     subject,
                "preheader":   preheader,
                "type":        "single",
                "lang":        lang,
                "title":       post.get("title", ""),
                "description": post.get("description", ""),
                "url":         post.get("url", ""),
                "date":        post["date"].strftime("%d/%m/%Y") if post.get("date") else "",
            },
        }
    return {
        "mode":    "html",
        "subject": subject,
        "html":    _standalone_wrap(body, preheader, lang),
    }


# ── Digest ────────────────────────────────────────────────────────────────────

def _section_block(section: dict, lang: str) -> str:
    title   = section.get("title", "")
    emoji   = section.get("emoji", "")
    summary = section.get("summary", "")
    items   = section.get("items", [])

    rows = "".join(
        _ref_item(
            item.get("label", item.get("title", "Ver fuente")),
            item.get("url", "#"),
            item.get("domain", item.get("source", "")),
            item.get("image", ""),
        )
        for item in items
    )

    return f"""
    <div style="margin-bottom:36px;">
      {_h2(f"{emoji} {title}")}
      <p style="font-family:{FONT};font-size:14px;line-height:1.65;
        color:rgba(2,21,71,0.8);margin:12px 0 16px;text-align:justify;">
        {summary}
      </p>
      <table role="presentation" width="100%" cellpadding="0"
        cellspacing="0" border="0">
        {rows}
      </table>
    </div>"""


def _digest_body(content: dict, lang: str, days: int) -> str:
    editorial     = content.get("editorial", "")
    sections      = content.get("sections", [])
    closing       = content.get("closing", "")
    sections_html = "".join(_section_block(s, lang) for s in sections)

    return f"""
    <!-- Eyebrow -->
    <p style="font-family:{FONT};font-size:10px;font-weight:700;
      letter-spacing:5px;color:{NAVY};text-transform:uppercase;
      margin:0 0 20px;padding-bottom:10px;
      border-bottom:1px solid rgba(0,168,188,0.2);">
      {_ui("digest", lang, days=days)}
    </p>

    <!-- Editorial -->
    <p style="font-family:{FONT};font-size:15px;line-height:1.75;
      color:{NAVY};margin:0 0 32px;text-align:justify;
      border-left:3px solid {CYAN};padding-left:16px;">
      {editorial}
    </p>

    <!-- Separador -->
    <div style="border-top:6px solid {NAVY};width:100px;
      margin:0 0 32px;font-size:0;line-height:0;">&nbsp;</div>

    {sections_html}

    {"<p style='font-family:" + FONT + ";font-size:13px;line-height:1.6;color:rgba(2,21,71,0.55);margin:0;padding-top:20px;border-top:1px solid rgba(0,168,188,0.2);letter-spacing:0.5px;'>" + closing + "</p>" if closing else ""}
    """


def build_digest_html(content: dict, lang: str = "es", days: int = 15) -> dict:
    subject   = content.get("subject", f"✦ WAIQ Digest")
    preheader = content.get("preheader", "")
    body      = _digest_body(content, lang, days)

    sections_summary = " · ".join(
        f"{s.get('emoji','')} {s.get('title','')}"
        for s in content.get("sections", [])
    )

    if BREVO_TEMPLATE_ID:
        return {
            "mode":      "template",
            "subject":   subject,
            "preheader": preheader,
            "params": {
                "body":             body,
                "subject":          subject,
                "preheader":        preheader,
                "type":             "digest",
                "lang":             lang,
                "days":             days,
                "editorial":        content.get("editorial", ""),
                "sections_summary": sections_summary,
                "closing":          content.get("closing", ""),
            },
        }
    return {
        "mode":    "html",
        "subject": subject,
        "html":    _standalone_wrap(body, preheader, lang),
    }
