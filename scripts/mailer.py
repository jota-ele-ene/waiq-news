"""
mailer.py — Crea y envía (o programa) campañas en MailerLite v3 API.
"""

import sys
from datetime import datetime

import requests

from scripts.config import (
    MAILERLITE_BASE_URL,
    MAILERLITE_HEADERS,
    MAILERLITE_GROUP_ID,
    FROM_NAME,
    FROM_EMAIL,
    DRY_RUN,
)


def send_campaign(subject: str, html: str) -> None:
    """
    Crea una campaña en MailerLite y la envía inmediatamente.
    Si DRY_RUN=true, imprime el resultado sin enviar nada.
    """
    if DRY_RUN:
        print("\n" + "─" * 60)
        print("🔍 DRY RUN — no se envía ninguna campaña.")
        print(f"   Asunto   : {subject}")
        print(f"   HTML     : {len(html):,} chars generados")
        print(f"   Remitente: {FROM_NAME} <{FROM_EMAIL}>")
        print(f"   Grupo    : {MAILERLITE_GROUP_ID}")
        print("─" * 60 + "\n")
        return

    campaign_name = f"WAIQ Newsletter {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC"

    # ── 1. Crear campaña ──────────────────────────────────────────────────────
    payload = {
        "name": campaign_name,
        "type": "regular",
        "emails": [{
            "subject":   subject,
            "from_name": FROM_NAME,
            "from":      FROM_EMAIL,
            "content":   html,
        }],
        "groups": [MAILERLITE_GROUP_ID],
    }

    print("📤 Creando campaña en MailerLite…")
    try:
        resp = requests.post(
            f"{MAILERLITE_BASE_URL}/campaigns",
            headers=MAILERLITE_HEADERS,
            json=payload,
            timeout=20,
        )
        resp.raise_for_status()
    except requests.HTTPError as e:
        print(f"❌ Error creando campaña: {e}", file=sys.stderr)
        print(f"   Respuesta: {resp.text[:400]}", file=sys.stderr)
        sys.exit(1)
    except requests.RequestException as e:
        print(f"❌ Error de red: {e}", file=sys.stderr)
        sys.exit(1)

    campaign_id = resp.json()["data"]["id"]
    print(f"   ✅ Campaña creada: {campaign_id}")

    # ── 2. Enviar inmediatamente ───────────────────────────────────────────────
    print("🚀 Programando envío inmediato…")
    try:
        resp2 = requests.post(
            f"{MAILERLITE_BASE_URL}/campaigns/{campaign_id}/schedule",
            headers=MAILERLITE_HEADERS,
            json={"delivery": "now"},
            timeout=20,
        )
        resp2.raise_for_status()
    except requests.HTTPError as e:
        print(f"❌ Error al enviar: {e}", file=sys.stderr)
        print(f"   Respuesta: {resp2.text[:400]}", file=sys.stderr)
        sys.exit(1)

    print(f"   ✅ Campaña enviada correctamente → {campaign_name}")
