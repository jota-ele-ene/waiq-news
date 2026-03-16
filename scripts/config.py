"""
config.py — Carga y valida la configuración desde .env o variables de entorno.
En local usa python-dotenv; en GitHub Actions usa los secrets/env del workflow.
"""

import os
import sys
from pathlib import Path

# Intentar cargar .env si existe (local). En CI no hay .env y no falla.
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"📄 .env cargado desde {env_path}")
    else:
        load_dotenv()  # busca .env en cwd
except ImportError:
    pass  # en CI python-dotenv puede no estar; las vars vienen del entorno


def _require(name: str) -> str:
    val = os.environ.get(name, "").strip()
    if not val:
        print(f"❌ Variable requerida no encontrada: {name}", file=sys.stderr)
        sys.exit(1)
    return val


def _optional(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


# ── MailerLite ────────────────────────────────────────────────────────────────
MAILERLITE_API_KEY  = _require("MAILERLITE_API_KEY")
MAILERLITE_GROUP_ID = _require("MAILERLITE_GROUP_ID")
MAILERLITE_BASE_URL = "https://connect.mailerlite.com/api"
MAILERLITE_HEADERS  = {
    "Authorization": f"Bearer {MAILERLITE_API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

# ── Remitente ─────────────────────────────────────────────────────────────────
FROM_NAME  = _optional("FROM_NAME",  "#WAIQ")
FROM_EMAIL = _optional("FROM_EMAIL", "hello@waiq.technology")

# ── Endpoints Hugo ────────────────────────────────────────────────────────────
HUGO_SINGLE_ENDPOINT  = _require("HUGO_SINGLE_ENDPOINT")
HUGO_DIGEST_ENDPOINT  = _require("HUGO_DIGEST_ENDPOINT")

# ── Sitio ─────────────────────────────────────────────────────────────────────
SITE_BASE_URL = _optional("SITE_BASE_URL", "https://waiq.technology")

# ── Anthropic ─────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = _require("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL   = _optional("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

# ── Comportamiento ────────────────────────────────────────────────────────────
MODE       = _optional("MODE",     "single")   # "single" | "digest"
SINCE_DATE = _optional("SINCE_DATE", "")       # YYYY-MM-DD (solo digest)
DRY_RUN    = _optional("DRY_RUN",   "false").lower() == "true"

# ── Branding ─────────────────────────────────────────────────────────────────
BRAND_COLOR = "#0A0A0A"
ACCENT      = "#6C47FF"
