#!/usr/bin/env python3
"""
main.py — Punto de entrada del sistema de newsletter WAIQ.

Uso local:
  python main.py --mode single
  python main.py --mode digest --since 2026-03-01
  python main.py --mode digest --since 2026-03-01 --dry-run

En GitHub Actions las mismas opciones se pasan como variables de entorno
(MODE, SINCE_DATE, DRY_RUN) — no son necesarios los flags CLI.
Los argumentos CLI tienen prioridad sobre las variables de entorno.
"""

import argparse
import os
import sys
from datetime import datetime, timedelta


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="WAIQ Newsletter — generador y enviador via MailerLite"
    )
    parser.add_argument(
        "--mode",
        choices=["single", "digest"],
        default=None,
        help="Modo de envío: single (post destacado) o digest (resumen editorial)",
    )
    parser.add_argument(
        "--since",
        default=None,
        metavar="YYYY-MM-DD",
        help="[solo digest] Fecha desde la que recuperar artículos",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Genera el HTML y lo muestra sin enviar ninguna campaña",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # ── Aplicar flags CLI sobre las variables de entorno ──────────────────────
    if args.mode:
        os.environ["MODE"] = args.mode
    if args.since:
        os.environ["SINCE_DATE"] = args.since
    if args.dry_run:
        os.environ["DRY_RUN"] = "true"

    # Importar DESPUÉS de ajustar el entorno para que config.py los recoja
    from scripts.config import MODE, SINCE_DATE, DRY_RUN
    from scripts.hugo_client import fetch_single_post, fetch_digest_urls
    from scripts.ai_editor import generate_digest_content
    from scripts.html_builder import build_single_html, build_digest_html
    from scripts.mailer import send_campaign

    print("\n╔══════════════════════════════════════════════╗")
    print(f"║  WAIQ Newsletter · modo: {MODE:<20}║")
    print(f"║  dry_run: {str(DRY_RUN):<35}║")
    print("╚══════════════════════════════════════════════╝\n")

    # ── MODO SINGLE ───────────────────────────────────────────────────────────
    if MODE == "single":
        post = fetch_single_post()
        subject = f"✦ {post['title']}"
        html = build_single_html(post)
        send_campaign(subject, html)

    # ── MODO DIGEST ───────────────────────────────────────────────────────────
    elif MODE == "digest":
        since = SINCE_DATE
        if not since:
            # Default: últimas 2 semanas si no se especifica
            since = (datetime.utcnow() - timedelta(days=14)).strftime("%Y-%m-%d")
            print(f"⚠️  --since no especificado, usando {since} (últimos 14 días)")

        # Validar formato de fecha
        try:
            datetime.strptime(since, "%Y-%m-%d")
        except ValueError:
            print(f"❌ Formato de fecha inválido: '{since}'. Usa YYYY-MM-DD.", file=sys.stderr)
            sys.exit(1)

        urls = fetch_digest_urls(since)
        content = generate_digest_content(urls, since)
        subject = content.get("subject", f"✦ WAIQ Digest — desde {since}")
        html = build_digest_html(content, since)
        send_campaign(subject, html)

    else:
        print(f"❌ MODE no reconocido: '{MODE}'. Usa 'single' o 'digest'.", file=sys.stderr)
        sys.exit(1)

    print("\n✅ Proceso completado.\n")


if __name__ == "__main__":
    main()
