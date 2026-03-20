#!/usr/bin/env python3
"""
main.py — Newsletter WAIQ. Punto de entrada.

Uso local:
  python main.py --mode single --lang es
  python main.py --mode single --lang en --dry-run

  python main.py --mode digest --lang es --days 15
  python main.py --mode digest --lang en --days 30 --dry-run

  # Fases individuales:
  python main.py --mode digest --lang es --days 15 --phase fetch
  python main.py --mode digest --lang es --days 15 --phase edit
  python main.py --mode digest --lang es --days 15 --phase build
  python main.py --mode digest --lang es --days 15 --phase send --dry-run
  python main.py --mode digest --lang es --days 15 --phase all --dry-run

  # Ver estado del último run:
  python main.py --status

En GitHub Actions las mismas opciones se pasan como variables de entorno:
  MODE, LANG, DAYS, DRY_RUN, PHASE
"""

import argparse
import os
import sys
from pathlib import Path

PHASES_SINGLE = ["fetch", "build", "send"]
PHASES_DIGEST = ["fetch", "edit", "build", "send"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="WAIQ Newsletter")
    parser.add_argument("--mode",  choices=["single", "digest"], default=None)
    parser.add_argument("--lang",  choices=["es", "en"],         default=None)
    parser.add_argument("--days",  choices=["15", "30"],         default=None,
                        help="[digest] Período en días: 15 o 30")
    parser.add_argument("--phase", choices=["fetch","edit","build","send","all"],
                        default=None)
    parser.add_argument("--dry-run",  action="store_true", default=False)
    parser.add_argument("--run-id",   default=None, metavar="run_YYYYMMDD_HHMMSS")
    parser.add_argument("--status",   action="store_true", default=False)
    return parser.parse_args()


def apply_args(args: argparse.Namespace) -> None:
    if args.mode:    os.environ["MODE"]    = args.mode
    if args.lang:    os.environ["LANG"]    = args.lang
    if args.days:    os.environ["DAYS"]    = args.days
    if args.dry_run: os.environ["DRY_RUN"] = "true"


# ── Fases ─────────────────────────────────────────────────────────────────────

def phase_fetch(run_dir: Path, mode: str, lang: str, days: int) -> None:
    from scripts.hugo_client import fetch_single_post, fetch_digest_data
    from scripts.store import save_hugo_raw, save_hugo_urls, mark_phase_done

    print("\n── FASE 1: fetch ─────────────────────────────────────────────")
    if mode == "single":
        post = fetch_single_post(lang)
        save_hugo_raw(run_dir, post)
    else:
        data = fetch_digest_data(lang, days)
        save_hugo_urls(run_dir, data)
    mark_phase_done(run_dir, "fetch")
    print("   ✅ fetch completado.")


def phase_edit(run_dir: Path, lang: str, days: int) -> None:
    from scripts.store import load_hugo_urls, save_ai_content, mark_phase_done
    from scripts.ai_editor import generate_digest_content

    print("\n── FASE 2: edit ──────────────────────────────────────────────")
    data = load_hugo_urls(run_dir)
    if not data.get("button_urls") and not data.get("articles"):
        print("❌ No hay URLs en 01_hugo_urls.json. ¿Ejecutaste --phase fetch?",
              file=sys.stderr)
        sys.exit(1)
    content = generate_digest_content(data, lang, days)
    save_ai_content(run_dir, content)
    mark_phase_done(run_dir, "edit")
    print("   ✅ edit completado.")


def phase_build(run_dir: Path, mode: str, lang: str, days: int) -> None:
    from scripts.store import (
        load_hugo_raw, load_ai_content, save_campaign, mark_phase_done, get_meta,
    )
    from scripts.html_builder import build_single_html, build_digest_html

    print("\n── FASE 3: build ─────────────────────────────────────────────")

    if mode == "single":
        post         = load_hugo_raw(run_dir)
        build_result = build_single_html(post, lang)
    else:
        meta = get_meta(run_dir)
        if "edit" not in meta.get("phases_completed", []):
            print("❌ Ejecuta --phase edit primero.", file=sys.stderr)
            sys.exit(1)
        ai_content   = load_ai_content(run_dir)
        build_result = build_digest_html(ai_content, lang, days)

    subject = build_result["subject"]
    html    = build_result.get("html") or build_result.get("params", {}).get("body", "")

    save_campaign(run_dir, {
        "subject":      subject,
        "preheader":    build_result.get("preheader", ""),
        "mode":         build_result.get("mode", "html"),
        "html":         html,
        "html_size":    len(html),
        "build_result": build_result,
    })
    mark_phase_done(run_dir, "build")
    print(f"   Asunto : {subject}")
    print(f"   HTML   : {len(html):,} chars")
    print("   ✅ build completado.")


def phase_send(run_dir: Path) -> None:
    from scripts.store import load_campaign, save_send_result, mark_phase_done, get_meta
    from scripts.mailer import create_campaign

    print("\n── FASE 4: send ──────────────────────────────────────────────")
    meta = get_meta(run_dir)
    if "build" not in meta.get("phases_completed", []):
        print("❌ Ejecuta --phase build primero.", file=sys.stderr)
        sys.exit(1)

    campaign_data = load_campaign(run_dir)
    build_result  = campaign_data.get("build_result") or {
        "mode": "html", "html": campaign_data["html"]
    }

    # lang, mode y days vienen del meta del run (guardados en init_run)
    lang = meta.get("lang", "es")
    mode = meta.get("mode", "single")
    days = int(meta.get("days", 0))

    result = create_campaign(campaign_data["subject"], build_result, lang, mode, days)
    save_send_result(run_dir, result)
    mark_phase_done(run_dir, "send")
    print("   ✅ send completado.")

# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    args = parse_args()
    apply_args(args)

    from scripts.config import MODE, LANG, DAYS, DRY_RUN
    from scripts.store import init_run, resolve_run_dir, print_run_summary, get_meta

    if args.status:
        print_run_summary(resolve_run_dir(args.run_id))
        return

    if not MODE:
        print("❌ --mode es obligatorio (single | digest)", file=sys.stderr)
        sys.exit(1)
    if LANG not in ("es", "en"):
        print("❌ --lang debe ser 'es' o 'en'", file=sys.stderr)
        sys.exit(1)

    days  = int(DAYS) if DAYS in ("15", "30") else 15
    phase = args.phase or os.environ.get("PHASE", "all")

    print(f"\n╔══════════════════════════════════════════════╗")
    print(f"║  WAIQ Newsletter                             ║")
    print(f"║  modo : {MODE:<37}║")
    print(f"║  lang : {LANG:<37}║")
    print(f"║  fase : {phase:<37}║")
    if MODE == "digest":
        print(f"║  days : {days:<37}║")
    print(f"║  dry  : {str(DRY_RUN):<37}║")
    print(f"╚══════════════════════════════════════════════╝")

    # Resolver/crear directorio de run
    if phase in ("fetch", "all"):
        run_dir = init_run(MODE, {"lang": LANG, "days": days, "dry_run": DRY_RUN})
    else:
        run_dir = resolve_run_dir(args.run_id)

    # Fases a ejecutar
    if phase == "all":
        phases_to_run = PHASES_SINGLE if MODE == "single" else PHASES_DIGEST
    else:
        phases_to_run = [phase]

    for p in phases_to_run:
        if p == "fetch":
            phase_fetch(run_dir, MODE, LANG, days)
        elif p == "edit":
            if MODE == "single":
                print("   ⏭️  fase 'edit' no aplica en modo single.")
                continue
            phase_edit(run_dir, LANG, days)
        elif p == "build":
            phase_build(run_dir, MODE, LANG, days)
        elif p == "send":
            phase_send(run_dir)

    print()
    print_run_summary(run_dir)
    print("\n✅ Proceso completado.\n")


if __name__ == "__main__":
    main()
