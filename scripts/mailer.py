"""
mailer.py — Envía newsletters via Brevo API v3.
El segmento de destino se resuelve por lang + mode + days.
Siempre usa htmlContent (HTML autónomo, sin plantillas Brevo).

Tracking habilitado via payload Brevo:
  - Aperturas  : tracking.opens = True  + pixel {{track_open}} en el HTML
  - Clicks      : tracking.clicks = True  (Brevo reescribe los hrefs)
  - UTM params  : utmCampaign / utmSource / utmMedium en el payload raíz
  - Baja        : enlace {{unsubscribe}} en el footer del HTML

Segmentos:
  single      → ES_1  / EN_1
  digest 15d  → ES_15 / EN_15
  digest 30d  → ES_30 / EN_30
"""

import sys
from datetime import datetime

import requests

from scripts.config import (
    BREVO_API_KEY,
    BREVO_BASE_URL,
    BREVO_HEADERS,
    BREVO_SEGMENTS,
    FROM_NAME,
    FROM_EMAIL,
    DRY_RUN,
)

def _resolve_segment(lang: str, mode: str, days: int) -> int:
    days_key = 1 if mode == "single" else days
    key = f"{lang.upper()}_{days_key}"
    segment_id = BREVO_SEGMENTS.get(key)
    if not segment_id:
        print(f"❌ Segmento '{key}' no encontrado en BREVO_SEGMENTS", file=sys.stderr)
        print(f"   Disponibles: {list(BREVO_SEGMENTS.keys())}", file=sys.stderr)
        sys.exit(1)
    return segment_id


def create_campaign(subject: str, build_result: dict,
                    lang: str, mode: str, days: int = 0) -> dict:
    timestamp  = datetime.utcnow().isoformat()
    segment_id = _resolve_segment(lang, mode, days)

    # Nombre de campaña y parámetros UTM para tracking
    date_tag      = datetime.utcnow().strftime("%Y-%m-%d")
    campaign_name = f"WAIQ {lang.upper()} {mode} {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC"
    utm_campaign  = f"waiq-{mode}-{lang}-{date_tag}"

    if DRY_RUN:
        print("\n" + "─" * 58)
        print("🔍 DRY RUN — no se envía ninguna campaña.")
        print(f"   Asunto     : {subject}")
        print(f"   Segmento   : {segment_id} (lang={lang}, mode={mode}, days={days})")
        print(f"   Remitente  : {FROM_NAME} <{FROM_EMAIL}>")
        print(f"   UTM        : {utm_campaign}")
        print(f"   Tracking   : opens=True, clicks=True")
        print("─" * 58)
        return {
            "dry_run":     True,
            "provider":    "brevo",
            "timestamp":   timestamp,
            "subject":     subject,
            "segment_id":  segment_id,
            "lang":        lang,
            "mode":        mode,
            "days":        days,
            "utm_campaign": utm_campaign,
            "status":      "skipped (dry_run)",
        }

    payload = {
        "name":       campaign_name,
        "subject":    subject,
        "sender":     {"name": FROM_NAME, "email": FROM_EMAIL},
        "type":       "classic",
        "recipients": {"segmentIds": [segment_id]},
        # HTML autónomo — siempre, sin plantillas Brevo
        "htmlContent": build_result.get("html", ""),
        # Tracking de aperturas y clicks
        "tracking": {
            "opens":  True,
            "clicks": True,
        },
        # Parámetros UTM (añadidos por Brevo a cada link)
        "utmCampaign": utm_campaign,
        "utmSource":   "brevo",
        "utmMedium":   "email",
    }

    print(f"   📄 HTML autónomo | tracking opens+clicks | UTM: {utm_campaign}")
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
        print(f"❌ Error creando campaña: {e}", file=sys.stderr)
        print(f"   Respuesta: {resp.text[:500]}", file=sys.stderr)
        sys.exit(1)

    campaign_id = resp.json()["id"]
    print(f"   ✅ Campaña creada: {campaign_id}")

    send_url = f"{BREVO_BASE_URL}/emailCampaigns/{campaign_id}/sendNow"
    try:
        resp2 = requests.post(send_url, headers=BREVO_HEADERS, timeout=20)
        resp2.raise_for_status()
    except requests.HTTPError as e:
        print(f"❌ Error enviando: {e}", file=sys.stderr)
        print(f"   Respuesta: {resp2.text[:500]}", file=sys.stderr)
        sys.exit(1)

    print(f"   ✅ Enviado a segmento {segment_id}: {campaign_name}")

    return {
        "dry_run":        False,
        "provider":       "brevo",
        "timestamp":      timestamp,
        "subject":        subject,
        "segment_id":     segment_id,
        "lang":           lang,
        "mode":           mode,
        "days":           days,
        "campaign_id":    campaign_id,
        "campaign_name":  campaign_name,
        "utm_campaign":   utm_campaign,
        "status":         "sent",
    }