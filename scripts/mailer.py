"""
mailer.py — Envía newsletters via Brevo (ex-SendinBlue) API v3.

Lee el dict que devuelve html_builder.build_*() y decide el payload:
  result["mode"] == "template"  →  templateId + params.body  (wrapper Brevo)
  result["mode"] == "html"      →  htmlContent completo       (fallback)
"""

import sys
from datetime import datetime

import requests

from scripts.config import (
    BREVO_API_KEY,
    BREVO_BASE_URL,
    BREVO_HEADERS,
    BREVO_LIST_ID,
    BREVO_TEMPLATE_ID,
    FROM_NAME,
    FROM_EMAIL,
    DRY_RUN,
)


def create_campaign(subject: str, build_result: dict) -> dict:
    """
    Crea y envía una campaña en Brevo.
    - subject       : asunto del email
    - build_result  : dict devuelto por html_builder.build_single_html() o build_digest_html()
    """
    timestamp = datetime.utcnow().isoformat()
    mode      = build_result.get("mode", "html")

    if DRY_RUN:
        html_size = len(build_result.get("html", "")) or len(
            build_result.get("params", {}).get("body", "")
        )
        result = {
            "dry_run":     True,
            "provider":    "brevo",
            "mode":        mode,
            "timestamp":   timestamp,
            "subject":     subject,
            "html_size":   html_size,
            "from_name":   FROM_NAME,
            "from_email":  FROM_EMAIL,
            "list_id":     BREVO_LIST_ID,
            "template_id": BREVO_TEMPLATE_ID,
            "campaign_id": None,
            "status":      "skipped (dry_run)",
        }
        print("\n" + "─" * 58)
        print(f"🔍 DRY RUN — no se envía ninguna campaña.")
        print(f"   Modo     : {mode} {'(plantilla Brevo #' + str(BREVO_TEMPLATE_ID) + ')' if mode == 'template' else '(HTML autónomo)'}")
        print(f"   Asunto   : {subject}")
        print(f"   HTML     : {html_size:,} chars")
        print(f"   Remitente: {FROM_NAME} <{FROM_EMAIL}>")
        print(f"   Lista    : {BREVO_LIST_ID}")
        print("─" * 58)
        return result

    campaign_name = f"WAIQ Newsletter {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC"

    # ── Construir payload según modo ──────────────────────────────────────────
    payload = {
        "name":       campaign_name,
        "subject":    subject,
        "sender":     {"name": FROM_NAME, "email": FROM_EMAIL},
        "type":       "classic",
        "recipients": {"listIds": [BREVO_LIST_ID]},
    }

    if mode == "template" and BREVO_TEMPLATE_ID:
        # Brevo inyecta params en la plantilla via {{ params.xxx }}
        payload["templateId"] = BREVO_TEMPLATE_ID
        payload["params"]     = build_result.get("params", {})
        print(f"   📐 Modo plantilla → templateId={BREVO_TEMPLATE_ID}")
    else:
        # HTML completo autónomo
        payload["htmlContent"] = build_result.get("html", "")
        print(f"   📄 Modo HTML autónomo")

    # ── 1. Crear campaña ──────────────────────────────────────────────────────
    print(f"   POST {BREVO_BASE_URL}/emailCampaigns")
    try:
        resp = requests.post(
            f"{BREVO_BASE_URL}/emailCampaigns",
            headers=BREVO_HEADERS,
            json=payload,
            timeout=20,
        )
        resp.raise_for_status()
    except requests.HTTPError as e:
        print(f"❌ Error creando campaña en Brevo: {e}", file=sys.stderr)
        print(f"   Respuesta: {resp.text[:500]}", file=sys.stderr)
        sys.exit(1)

    create_response = resp.json()
    campaign_id     = create_response["id"]
    print(f"   ✅ Campaña creada: {campaign_id}")

    # ── 2. Enviar inmediatamente ───────────────────────────────────────────────
    send_url = f"{BREVO_BASE_URL}/emailCampaigns/{campaign_id}/sendNow"
    print(f"   POST {send_url}")
    try:
        resp2 = requests.post(send_url, headers=BREVO_HEADERS, timeout=20)
        resp2.raise_for_status()
    except requests.HTTPError as e:
        print(f"❌ Error enviando campaña: {e}", file=sys.stderr)
        print(f"   Respuesta: {resp2.text[:500]}", file=sys.stderr)
        sys.exit(1)

    print(f"   ✅ Campaña enviada: {campaign_name}")

    return {
        "dry_run":         False,
        "provider":        "brevo",
        "mode":            mode,
        "timestamp":       timestamp,
        "subject":         subject,
        "from_name":       FROM_NAME,
        "from_email":      FROM_EMAIL,
        "list_id":         BREVO_LIST_ID,
        "template_id":     BREVO_TEMPLATE_ID,
        "campaign_id":     campaign_id,
        "campaign_name":   campaign_name,
        "status":          "sent",
        "create_response": create_response,
    }

