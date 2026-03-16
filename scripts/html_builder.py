"""
html_builder.py — Genera el HTML del email para single y digest.
Diseño responsivo, compatible con clientes de email.
"""

from datetime import datetime
from scripts.config import SITE_BASE_URL, BRAND_COLOR, ACCENT, FROM_NAME


# ─────────────────────────────────────────────────────────────────────────────
# Componentes base
# ─────────────────────────────────────────────────────────────────────────────

def _tag_pill(tag: str) -> str:
    return (
        f'<span style="display:inline-block;background:#f0edff;color:{ACCENT};'
        f'font-size:11px;font-weight:600;padding:3px 10px;border-radius:20px;'
        f'margin:0 4px 4px 0;letter-spacing:0.3px;">{tag}</span>'
    )


def _button(url: str, label: str = "Leer artículo →") -> str:
    return (
        f'<a href="{url}" style="display:inline-block;background:{ACCENT};color:#ffffff;'
        f'padding:13px 28px;border-radius:8px;text-decoration:none;font-weight:700;'
        f'font-size:15px;letter-spacing:0.2px;">{label}</a>'
    )


def _wrap(inner: str, preheader: str = "") -> str:
    year = datetime.utcnow().year
    pre_tag = (
        f'<div style="display:none;max-height:0;overflow:hidden;'
        f'font-size:1px;line-height:1px;color:#ffffff;">{preheader}&nbsp;</div>'
        if preheader else ""
    )
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="x-apple-disable-message-reformatting">
  <title>{FROM_NAME} Newsletter</title>
</head>
<body style="margin:0;padding:0;background:#ffffff;
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;
  -webkit-text-size-adjust:100%;">
{pre_tag}

<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
  style="background:#f5f4f2;">
  <tr>
    <td align="center" style="padding:40px 16px 48px;">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"
        style="max-width:600px;width:100%;">

        <!-- ── HEADER ─────────────────────────────────── -->
        <tr>
          <td style="background:{BRAND_COLOR};border-radius:12px 12px 0 0;
            padding:24px 32px;">
            <a href="{SITE_BASE_URL}" style="text-decoration:none;">
              <span style="font-size:24px;font-weight:800;color:#ffffff;
                letter-spacing:-0.5px;">#WAIQ</span>
              <span style="font-size:24px;font-weight:300;color:{ACCENT};
                letter-spacing:-0.5px;">news</span>
            </a>
          </td>
        </tr>

        <!-- ── CUERPO ──────────────────────────────────── -->
        <tr>
          <td style="background:#ffffff;padding:32px;">
            {inner}
          </td>
        </tr>

        <!-- ── FOOTER ──────────────────────────────────── -->
        <tr>
          <td style="background:#f5f4f2;border-radius:0 0 12px 12px;
            padding:24px 32px;text-align:center;">
            <p style="font-size:13px;color:#888;margin:0 0 6px;">
              <a href="{SITE_BASE_URL}" style="color:{ACCENT};
                text-decoration:none;font-weight:600;">{SITE_BASE_URL}</a>
            </p>
            <p style="font-size:11px;color:#bbb;margin:0;">
              © {year} WAIQ · Recibes esto porque te suscribiste al newsletter.
              <a href="{{{{unsubscribe}}}}" style="color:#bbb;">Cancelar suscripción</a>
            </p>
          </td>
        </tr>

      </table>
    </td>
  </tr>
</table>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# Single — post destacado
# ─────────────────────────────────────────────────────────────────────────────

def build_single_html(post: dict) -> str:
    title       = post.get("title", "Sin título")
    description = post.get("description", "")
    url         = post.get("url", SITE_BASE_URL)
    tags        = post.get("tags", []) or []
    date_obj    = post.get("date")
    date_str    = date_obj.strftime("%d de %B de %Y") if date_obj else ""

    tags_html = "".join(_tag_pill(t) for t in tags[:4])
    tags_block = f'<div style="margin-bottom:16px;">{tags_html}</div>' if tags_html else ""

    # Extracto del cuerpo markdown (primeros ~300 chars, sin # ni *)
    body_raw = post.get("body", "")
    import re
    body_clean = re.sub(r"[#*`\[\]>]", "", body_raw)
    body_clean = re.sub(r"\s+", " ", body_clean).strip()
    excerpt = body_clean[:300].rsplit(" ", 1)[0] + "…" if len(body_clean) > 300 else body_clean

    inner = f"""
    <p style="font-size:12px;font-weight:700;letter-spacing:1.5px;
      color:{ACCENT};text-transform:uppercase;margin:0 0 20px;">
      Artículo destacado
    </p>

    {tags_block}

    <h1 style="font-size:28px;font-weight:800;line-height:1.25;
      color:{BRAND_COLOR};margin:0 0 14px;letter-spacing:-0.5px;">
      {title}
    </h1>

    {"<p style='font-size:12px;color:#aaa;margin:0 0 16px;'>📅 " + date_str + "</p>" if date_str else ""}

    <p style="font-size:17px;line-height:1.65;color:#333;
      margin:0 0 16px;font-weight:500;">
      {description}
    </p>

    {"<p style='font-size:15px;line-height:1.6;color:#555;margin:0 0 28px;'>" + excerpt + "</p>" if excerpt and excerpt != description else '<div style="margin-bottom:28px;"></div>'}

    <div style="margin-bottom:32px;">{_button(url)}</div>

    <div style="border-top:1px solid #f0f0f0;padding-top:24px;">
      <p style="font-size:13px;color:#aaa;margin:0;">
        O copia este enlace: <a href="{url}" style="color:{ACCENT};">{url}</a>
      </p>
    </div>
    """
    return _wrap(inner, preheader=description[:90])


# ─────────────────────────────────────────────────────────────────────────────
# Digest — newsletter editorial con secciones
# ─────────────────────────────────────────────────────────────────────────────

def _section_html(section: dict) -> str:
    title   = section.get("title", "")
    emoji   = section.get("emoji", "")
    summary = section.get("summary", "")
    items   = section.get("items", [])

    items_html = ""
    for item in items:
        label  = item.get("label", "Ver fuente")
        url    = item.get("url", "#")
        domain = item.get("domain", "")
        items_html += f"""
        <tr>
          <td style="padding:10px 0;border-bottom:1px solid #f5f5f5;">
            <a href="{url}" style="color:{BRAND_COLOR};text-decoration:none;
              font-size:14px;font-weight:600;line-height:1.4;">{label}</a>
            <br>
            <span style="font-size:11px;color:#aaa;">{domain}</span>
          </td>
        </tr>"""

    return f"""
    <div style="margin-bottom:36px;">
      <h2 style="font-size:18px;font-weight:800;color:{BRAND_COLOR};
        margin:0 0 6px;letter-spacing:-0.3px;">
        {emoji} {title}
      </h2>
      <p style="font-size:14px;line-height:1.6;color:#555;margin:0 0 16px;">
        {summary}
      </p>
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
        {items_html}
      </table>
    </div>"""


def build_digest_html(content: dict, since_date: str) -> str:
    editorial = content.get("editorial", "")
    sections  = content.get("sections", [])
    closing   = content.get("closing", "")
    preheader = content.get("preheader", "")

    sections_html = "".join(_section_html(s) for s in sections)

    inner = f"""
    <p style="font-size:12px;font-weight:700;letter-spacing:1.5px;
      color:{ACCENT};text-transform:uppercase;margin:0 0 20px;">
      Digest · desde {since_date}
    </p>

    <p style="font-size:16px;line-height:1.7;color:#333;
      margin:0 0 32px;border-left:3px solid {ACCENT};
      padding-left:16px;font-style:italic;">
      {editorial}
    </p>

    <div style="border-top:2px solid {BRAND_COLOR};margin-bottom:28px;"></div>

    {sections_html}

    {"<p style='font-size:14px;line-height:1.6;color:#888;margin:0;padding-top:16px;border-top:1px solid #eee;'>" + closing + "</p>" if closing else ""}
    """
    return _wrap(inner, preheader=preheader)
