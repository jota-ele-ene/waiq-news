"""
store.py — Persistencia de datos entre fases en data/<run_id>/

Estructura de un run:
  data/
  └── run_20260317_110000/        ← directorio del run
      ├── meta.json               ← modo, since, fases completadas, timestamps
      ├── 01_hugo_raw.json        ← (single) post parseado
      ├── 01_hugo_urls.json       ← (digest) {button_urls, total}
      ├── 02_ai_content.json      ← (digest) editorial generado por Claude
      ├── 03_campaign.json        ← subject + html + html_size
      └── 04_send_result.json      ← respuesta de Brevo (campaign_id, etc.)

  data/latest -> run_20260317_110000   ← symlink al run más reciente
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


# ─────────────────────────────────────────────────────────────────────────────
# Init & resolve
# ─────────────────────────────────────────────────────────────────────────────

def init_run(mode: str, params: dict) -> Path:
    """Crea un nuevo directorio de run y actualiza el symlink latest."""
    run_id  = f"run_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    run_dir = DATA_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "run_id":            run_id,
        "mode":              mode,
        "since":             params.get("since", ""),
        "dry_run":           params.get("dry_run", False),
        "started_at":        datetime.utcnow().isoformat(),
        "phases_completed":  [],
    }
    _write(run_dir / "meta.json", meta)

    # Actualizar symlink latest
    latest = DATA_DIR / "latest"
    if latest.is_symlink() or latest.exists():
        latest.unlink()
    latest.symlink_to(run_id)

    print(f"📁 Run iniciado: data/{run_id}")
    return run_dir


def resolve_run_dir(run_id: str | None = None) -> Path:
    """
    Devuelve el Path del run especificado o del último (data/latest).
    Aborta si no existe ningún run.
    """
    if run_id:
        run_dir = DATA_DIR / run_id
    else:
        latest = DATA_DIR / "latest"
        if not latest.exists():
            print("❌ No se encontró ningún run en data/. Ejecuta --phase fetch primero.",
                  file=sys.stderr)
            sys.exit(1)
        run_dir = latest.resolve()

    if not run_dir.exists():
        print(f"❌ Run no encontrado: {run_dir}", file=sys.stderr)
        sys.exit(1)

    return run_dir


# ─────────────────────────────────────────────────────────────────────────────
# Meta
# ─────────────────────────────────────────────────────────────────────────────

def get_meta(run_dir: Path) -> dict:
    return _read(run_dir / "meta.json")


def mark_phase_done(run_dir: Path, phase: str) -> None:
    meta = get_meta(run_dir)
    if phase not in meta["phases_completed"]:
        meta["phases_completed"].append(phase)
    meta[f"{phase}_at"] = datetime.utcnow().isoformat()
    _write(run_dir / "meta.json", meta)


# ─────────────────────────────────────────────────────────────────────────────
# Fase fetch
# ─────────────────────────────────────────────────────────────────────────────

def save_hugo_raw(run_dir: Path, post: dict) -> None:
    """Guarda el post parseado (single)."""
    # datetime no es serializable — convertir a str
    data = {k: (v.isoformat() if isinstance(v, datetime) else v)
            for k, v in post.items()}
    _write(run_dir / "01_hugo_raw.json", data)
    print(f"   💾 Guardado: {run_dir.name}/01_hugo_raw.json")


def load_hugo_raw(run_dir: Path) -> dict:
    path = run_dir / "01_hugo_raw.json"
    _assert_exists(path, "fetch (single)")
    data = _read(path)
    # Restaurar fecha si existe
    if "date" in data and isinstance(data["date"], str):
        try:
            data["date"] = datetime.fromisoformat(data["date"])
        except ValueError:
            pass
    return data


def save_hugo_urls(run_dir: Path, data: dict) -> None:
    """Guarda el payload digest {button_urls, total}."""
    _write(run_dir / "01_hugo_urls.json", data)
    print(f"   💾 Guardado: {run_dir.name}/01_hugo_urls.json ({data.get('total', 0)} URLs)")


def load_hugo_urls(run_dir: Path) -> dict:
    path = run_dir / "01_hugo_urls.json"
    _assert_exists(path, "fetch (digest)")
    return _read(path)


# ─────────────────────────────────────────────────────────────────────────────
# Fase edit
# ─────────────────────────────────────────────────────────────────────────────

def save_ai_content(run_dir: Path, content: dict) -> None:
    _write(run_dir / "02_ai_content.json", content)
    print(f"   💾 Guardado: {run_dir.name}/02_ai_content.json")


def load_ai_content(run_dir: Path) -> dict:
    path = run_dir / "02_ai_content.json"
    _assert_exists(path, "edit")
    return _read(path)


# ─────────────────────────────────────────────────────────────────────────────
# Fase build
# ─────────────────────────────────────────────────────────────────────────────

def save_campaign(run_dir: Path, campaign: dict) -> None:
    # Guardar HTML también como archivo independiente para previsualizar
    html = campaign.get("html", "")
    (run_dir / "03_preview.html").write_text(html, encoding="utf-8")

    # Guardar todo el payload sin el HTML (demasiado grande para JSON legible)
    payload = {k: v for k, v in campaign.items() if k != "html"}
    payload["html_file"] = "03_preview.html"
    _write(run_dir / "03_campaign.json", payload)

    print(f"   💾 Guardado: {run_dir.name}/03_campaign.json")
    print(f"   💾 Preview : {run_dir.name}/03_preview.html  ← ábrelo en el navegador")


def load_campaign(run_dir: Path) -> dict:
    path = run_dir / "03_campaign.json"
    _assert_exists(path, "build")
    data = _read(path)
    # Recargar HTML desde el archivo separado
    html_file = run_dir / data.get("html_file", "03_preview.html")
    if html_file.exists():
        data["html"] = html_file.read_text(encoding="utf-8")
    return data


# ─────────────────────────────────────────────────────────────────────────────
# Fase send
# ─────────────────────────────────────────────────────────────────────────────

def save_send_result(run_dir: Path, result: dict) -> None:
    _write(run_dir / "04_send_result.json", result)
    print(f"   💾 Guardado: {run_dir.name}/04_send_result.json")


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────

def print_run_summary(run_dir: Path) -> None:
    meta = get_meta(run_dir)
    phases = meta.get("phases_completed", [])
    print(f"\n{'─'*50}")
    print(f"📋 Run: {meta['run_id']}")
    print(f"   Modo   : {meta['mode']}")
    if meta.get("since"):
        print(f"   Since  : {meta['since']}")
    print(f"   Dry run: {meta['dry_run']}")
    print(f"   Fases  : {' → '.join(phases) if phases else '(ninguna)'}")

    ml_file = run_dir / "04_send_result.json"
    if ml_file.exists():
        ml = _read(ml_file)
        if ml.get("dry_run"):
            print(f"   Envío  : DRY RUN (no enviado)")
        elif ml.get("campaign_id"):
            print(f"   Campaña: {ml['campaign_id']}")
    print(f"{'─'*50}")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers internos
# ─────────────────────────────────────────────────────────────────────────────

def _write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_exists(path: Path, phase: str) -> None:
    if not path.exists():
        print(f"❌ Archivo no encontrado: {path.name}", file=sys.stderr)
        print(f"   ¿Ejecutaste --phase {phase} antes?", file=sys.stderr)
        sys.exit(1)
