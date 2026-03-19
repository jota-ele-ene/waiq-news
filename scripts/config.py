"""
config.py — Carga y valida la configuración desde .env o variables de entorno.
En local usa python-dotenv; en GitHub Actions usa los secrets/env del workflow.
"""

import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"📄 .env cargado desde {env_path}")
    else:
        load_dotenv()
except ImportError:
    pass


def _require(name: str) -> str:
    val = os.environ.get(name, "").strip()
    if not val:
        print(f"❌ Variable requerida no encontrada: {name}", file=sys.stderr)
        sys.exit(1)
    return val


def _optional(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


# ── Brevo ─────────────────────────────────────────────────────────────────────
BREVO_API_KEY   = _require("BREVO_API_KEY")
BREVO_LIST_ID   = int(_require("BREVO_LIST_ID"))
BREVO_BASE_URL  = "https://api.brevo.com/v3"
BREVO_HEADERS   = {
    "api-key":      BREVO_API_KEY,
    "Content-Type": "application/json",
    "Accept":       "application/json",
}
BREVO_TEMPLATE_ID = _optional("BREVO_TEMPLATE_ID", "")
BREVO_TEMPLATE_ID = int(BREVO_TEMPLATE_ID) if BREVO_TEMPLATE_ID else None

# ── Remitente ─────────────────────────────────────────────────────────────────
FROM_NAME  = _optional("FROM_NAME",  "#WAIQ")
FROM_EMAIL = _optional("FROM_EMAIL", "hello@waiq.technology")

# ── Endpoints Hugo — un par por idioma ────────────────────────────────────────
# single: GET → markdown+frontmatter del post con radar:true más reciente
HUGO_SINGLE_ENDPOINT_ES = _require("HUGO_SINGLE_ENDPOINT_ES")
HUGO_SINGLE_ENDPOINT_EN = _require("HUGO_SINGLE_ENDPOINT_EN")

# digest: GET → {button_urls, total, articles:[{url,title,image,source}]}
# El script añade el sufijo -15 o -30 según --days antes de llamar
HUGO_DIGEST_ENDPOINT_ES = _require("HUGO_DIGEST_ENDPOINT_ES")
HUGO_DIGEST_ENDPOINT_EN = _require("HUGO_DIGEST_ENDPOINT_EN")

# ── Sitio ─────────────────────────────────────────────────────────────────────
SITE_BASE_URL = _optional("SITE_BASE_URL", "https://waiq.technology")

# ── Anthropic ─────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = _require("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL   = _optional("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

# ── Comportamiento (sobreescritos desde CLI en main.py) ───────────────────────
MODE    = _optional("MODE",    "single")  # "single" | "digest"
LANG    = _optional("LANG",    "es")      # "es" | "en"
DAYS    = _optional("DAYS",    "15")      # "15" | "30" — solo digest
DRY_RUN = _optional("DRY_RUN", "false").lower() == "true"
