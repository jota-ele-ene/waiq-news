"""
send_newsletter.py
------------------
Lee el contenido Hugo de un rel repositorio jota-ele-ene/waiq-multi,
genera el HTML del newsletter y lo envía via MailerLite API.

Variables de entorno requeridas:
  MAILERLITE_API_KEY   → API key de MailerLite
  MAILERLITE_GROUP_ID  → ID del grupo/lista de suscriptores
  GH_TOKEN             → GitHub token con permisos de lectura (repo)

Variables opcionales (tienen defaults):
  MODE        → "single" (semanal) | "digest" (quincenal/mensual)
  DAYS_BACK   → días atrás para buscar posts en modo digest (default: 14)
  DRY_RUN     → "true" para imprimir sin enviar
"""

import os
import json
import re
import sys
from datetime import datetime, timedelta

import requests
import yaml

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

MAILERLITE_API_KEY = os.environ["MAILERLITE_API_KEY"]
MAILERLITE_GROUP_ID = os.environ["MAILERLITE_GROUP_ID"]
GH_TOKEN = os.environ["GH_TOKEN"]

HUGO_REPO   = "jota-ele-ene/waiq-multi"
CONTENT_DIR = "content/es/article"
SITE_BASE   = "https://waiq.technology"
FROM_NAME   = "#WAIQ"
FROM_EMAIL  = "hello@waiq.technology"

MODE      = os.environ.get("MODE", "single")
DAYS_BACK = int(os.environ.get("DAYS_BACK", 14))
DRY_RUN   = os.environ.get("DRY_RUN", "false").lower() == "true"

MAILERLITE_BASE = "https://connect.mailerlite.com/api"
ML_HEADERS = {
    "Authorization": f"Bearer {MAILERLITE_API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

GH_HEADERS = {
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# ---------------------------------------------------------------------------
# GitHub Content API
# ---------------------------------------------------------------------------

def gh_get_tree() -> list[dict]:
    """Devuelve el árbol de archivos del directorio de contenido Hugo."""
    url = f"https://api.github.com/repos/{HUGO_REPO}/git/trees/HEAD?recursive=1"
    resp = requests.get(url, headers=GH_HEADERS)
    resp.raise_for_status()
    tree = resp.json().get("tree", [])
    # Solo .md dentro del directorio de artículos
    return [
        f for f in tree
        if f["type"] == "blob"
        and f["path"].startswith(CONTENT_DIR)
        and f["path"].endswith(".md")
        and not f["path"].endswith("_index.md")
    ]


def gh_get_file(path: str) -> str:
    """Descarga el contenido de un archivo del repositorio Hugo."""
    url = f"https://api.github.com/repos/{HUGO_REPO}/contents/{path}"
    resp = requests.get(url, headers=GH_HEADERS)
    resp.raise_for_status()
    import base64
    data = resp.json()
    return base64.b64decode(data["content"]).decode("utf-8")

# ---------------------------------------------------------------------------
# Parseo de frontmatter
# ---------------------------------------------------------------------------

def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Extrae frontmatter YAML o TOML y devuelve (meta, body)."""
    meta = {}

    # YAML (---)
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if m:
        meta = yaml.safe_load(m.group(1)) or {}
        body = text[m.end():].strip()
        return meta, body

    # TOML (+++)
    m = re.match(r"^\+\+\+\s*\n(.*?)\n\+\+\+\s*\n", text, re.DOTALL)
    if m:
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
        meta = tomllib.loads(m.group(1))
        body = text[m.end():].strip()
        return meta, body

    return meta, text.strip()


def parse_date(raw) -> datetime | None:
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw.replace(tzinfo=None)
    if hasattr(raw, "year"):  # date object
        return datetime(raw.year, raw.month, raw.day)
    if isinstance(raw, str):
        for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(raw[:19], fmt[:len(raw[:19])])
                return dt.replace(tzinfo=None)
            except ValueError:
                continue
    return None

# ---------------------------------------------------------------------------
# Lectura de posts desde GitHub
# ---------------------------------------------------------------------------

def build_post_url(path: str, meta: dict) -> str:
    """Construye la URL pública del post."""
    slug = meta.get("slug")
    if not slug:
        # Inferir desde la ruta: content/es/article/mi-post/index.md → mi-post
        parts = path.replace(CONTENT_DIR + "/", "").split("/")
        slug = parts[-2] if parts[-1] == "index.md" else parts[-1].replace(".md", "")
    return f"{SITE_BASE}/article/{slug}/"


def fetch_all_posts() -> list[dict]:
    """Descarga y parsea todos los posts del repositorio Hugo."""
    tree = gh_get_tree()
    posts = []
    for item in tree:
        try:
            text = gh_get_file(item["path"])
            meta, body = parse_frontmatter(text)
        except Exception as e:
            print(f"⚠️  Error leyendo {item['path']}: {e}", file=sys.stderr)
            continue

        if meta.get("draft", False):
            continue

        dt = parse_date(meta.get("date"))
        if dt is None:
            continue

        posts.append({
            **meta,
            "_body": body,
            "_path": item["path"],
            "_date": dt,
            "_url": build_post_url(item["path"], meta),
        })

    return sorted(posts, key=lambda p: p["_date"], reverse=True)


def get_latest_radar_post(posts: list[dict]) -> dict | None:
    """Devuelve el post más reciente con radar: true."""
    for post in posts:
        if post.get("radar") is True:
            return post
    return None


def get_posts_since(posts: list[dict], days: int) -> list[dict]:
    """Filtra posts publicados en los últimos N días."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    return [p for p in posts if p["_date"] >= cutoff]

# ---------------------------------------------------------------------------
# Generación de HTML
# ---------------------------------------------------------------------------

BRAND_COLOR = "#0A0A0A"
ACCENT      = "#6C47FF"

def _post_card(post: dict, featured: bool = False) -> str:
    title       = post.get("title", "Sin título")
    description = post.get("description", post.get("summary", ""))
    url         = post["_url"]
    date_str    = post["_date"].strftime("%d %b %Y")
    tags        = post.get("tags", []) or []
    tag_html    = "".join(
        f'<span style="display:inline-block;background:#f0edff;color:{ACCENT};'
        f'font-size:11px;padding:2px 8px;border-radius:20px;margin-right:4px;">{t}</span>'
        for t in tags[:3]
    )

    if featured:
        return f"""
        <div style="background:#fafafa;border-radius:12px;padding:32px;margin-bottom:32px;">
          <div style="margin-bottom:12px;">{tag_html}</div>
          <h1 style="margin:0 0 12px;font-size:26px;line-height:1.3;color:{BRAND_COLOR};">
            <a href="{url}" style="color:{BRAND_COLOR};text-decoration:none;">{title}</a>
          </h1>
          <p style="font-size:15px;color:#555;line-height:1.65;margin:0 0 20px;">{description}</p>
          <p style="font-size:12px;color:#999;margin:0 0 20px;">{date_str}</p>
          <a href="{url}" style="display:inline-block;background:{ACCENT};color:#fff;
            padding:12px 28px;border-radius:8px;text-decoration:none;
            font-weight:600;font-size:15px;">Leer artículo →</a>
        </div>"""
    else:
        return f"""
        <div style="border-top:1px solid #eee;padding:20px 0;">
          <div style="margin-bottom:6px;">{tag_html}</div>
          <h3 style="margin:0 0 6px;font-size:17px;color:{BRAND_COLOR};">
            <a href="{url}" style="color:{BRAND_COLOR};text-decoration:none;">{title}</a>
          </h3>
          <p style="font-size:14px;color:#666;line-height:1.55;margin:0 0 8px;">{description}</p>
          <span style="font-size:12px;color:#aaa;">{date_str}</span>
          &nbsp;·&nbsp;
          <a href="{url}" style="font-size:13px;color:{ACCENT};text-decoration:none;">Leer →</a>
        </div>"""


def _wrap_html(inner: str, preheader: str = "") -> str:
    year = datetime.utcnow().year
    pre = f'<span style="display:none;max-height:0;overflow:hidden;">{preheader}</span>' if preheader else ""
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>WAIQ Newsletter</title>
</head>
<body style="margin:0;padding:0;background:#ffffff;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
{pre}
<table width="100%" cellpadding="0" cellspacing="0" border="0">
  <tr>
    <td align="center" style="padding:40px 16px;">
      <table width="600" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;width:100%;">

        <!-- Header -->
        <tr>
          <td style="padding-bottom:32px;border-bottom:2px solid {BRAND_COLOR};">
            <a href="{SITE_BASE}" style="text-decoration:none;">
              <span style="font-size:22px;font-weight:700;color:{BRAND_COLOR};">#WAIQ</span>
              <span style="font-size:22px;font-weight:300;color:{ACCENT};">news</span>
            </a>
          </td>
        </tr>

        <!-- Contenido -->
        <tr>
          <td style="padding-top:32px;">
            {inner}
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="padding-top:40px;border-top:1px solid #eee;text-align:center;">
            <p style="font-size:12px;color:#aaa;margin:0 0 8px;">
              © {year} WAIQ · <a href="{SITE_BASE}" style="color:#aaa;">{SITE_BASE}</a>
            </p>
            <p style="font-size:11px;color:#ccc;margin:0;">
              Recibes esto porque te suscribiste al newsletter de WAIQ.
              <a href="{{{{unsubscribe}}}}" style="color:#ccc;">Cancelar suscripción</a>
            </p>
          </td>
        </tr>

      </table>
    </td>
  </tr>
</table>
</body>
</html>"""


def build_html_single(post: dict) -> str:
    inner = _post_card(post, featured=True)
    return _wrap_html(inner, preheader=post.get("description", ""))


def build_html_digest(posts: list[dict], days: int) -> str:
    if not posts:
        inner = "<p style='color:#666;'>No hay contenido nuevo en este período.</p>"
        return _wrap_html(inner)

    period = "las últimas 2 semanas" if days <= 14 else "el último mes"
    header = f"""
    <h2 style="font-size:20px;color:{BRAND_COLOR};margin:0 0 4px;">
      Resumen de {period}
    </h2>
    <p style="font-size:14px;color:#888;margin:0 0 24px;">
      {len(posts)} artículo{'s' if len(posts) != 1 else ''} publicado{'s' if len(posts) != 1 else ''}
    </p>
    """
    # Primero featured el más reciente con radar:true, el resto como cards
    radar = next((p for p in posts if p.get("radar")), None)
    others = [p for p in posts if p is not radar]

    cards = header
    if radar:
        cards += _post_card(radar, featured=True)
    for p in others:
        cards += _post_card(p, featured=False)

    preheader = f"{len(posts)} nuevos artículos en WAIQ"
    return _wrap_html(cards, preheader=preheader)

# ---------------------------------------------------------------------------
# MailerLite API
# ---------------------------------------------------------------------------

def create_and_send_campaign(subject: str, html: str):
    if DRY_RUN:
        print("🔍 DRY RUN — no se envía ninguna campaña.")
        print(f"   Asunto: {subject}")
        print(f"   HTML ({len(html)} chars) generado correctamente.")
        return

    # 1. Crear campaña
    payload = {
        "name": f"WAIQ Newsletter {datetime.utcnow().strftime('%Y-%m-%d')}",
        "type": "regular",
        "emails": [{
            "subject": subject,
            "from_name": FROM_NAME,
            "from": FROM_EMAIL,
            "content": html,
        }],
        "groups": [MAILERLITE_GROUP_ID],
    }
    resp = requests.post(f"{MAILERLITE_BASE}/campaigns", headers=ML_HEADERS, json=payload)
    resp.raise_for_status()
    campaign_id = resp.json()["data"]["id"]
    print(f"✅ Campaña creada: {campaign_id}")

    # 2. Enviar inmediatamente
    resp2 = requests.post(
        f"{MAILERLITE_BASE}/campaigns/{campaign_id}/schedule",
        headers=ML_HEADERS,
        json={"delivery": "now"},
    )
    resp2.raise_for_status()
    print("🚀 Campaña enviada correctamente.")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"📡 Descargando posts de {HUGO_REPO}/{CONTENT_DIR}…")
    all_posts = fetch_all_posts()
    print(f"   {len(all_posts)} posts encontrados.")

    if MODE == "single":
        post = get_latest_radar_post(all_posts)
        if not post:
            print("⚠️  No se encontró ningún post con radar:true. Abortando.")
            sys.exit(0)
        print(f"   Post seleccionado: {post.get('title')}")
        subject = f"✦ {post.get('title', 'Nuevo artículo en WAIQ')}"
        html = build_html_single(post)

    else:  # digest
        posts = get_posts_since(all_posts, DAYS_BACK)
        if not posts:
            print(f"⚠️  No hay posts en los últimos {DAYS_BACK} días. Abortando.")
            sys.exit(0)
        print(f"   {len(posts)} posts en los últimos {DAYS_BACK} días.")
        label = "2 semanas" if DAYS_BACK <= 14 else "mes"
        subject = f"✦ WAIQ — Lo mejor de {'las últimas ' + label if DAYS_BACK <= 14 else 'este ' + label}"
        html = build_html_digest(posts, DAYS_BACK)

    create_and_send_campaign(subject, html)


if __name__ == "__main__":
    main()
