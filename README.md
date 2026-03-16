# waiq-news

Automatización del newsletter de [WAIQ](https://waiq.technology) mediante **GitHub Actions + MailerLite + Claude AI**.

---

## Arquitectura

```
main.py
  ├── modo: single
  │     └── hugo_client → GET /api/newsletter/single (markdown+frontmatter)
  │                     → html_builder → mailer (MailerLite)
  │
  └── modo: digest
        └── hugo_client → GET /api/newsletter/digest?since=YYYY-MM-DD
            ({button_urls, total})
                        → ai_editor (Claude analiza URLs y genera editorial)
                        → html_builder → mailer (MailerLite)
```

---

## Workflows

| Workflow | Cron | Modo | `--since` por defecto |
|---|---|---|---|
| `newsletter-weekly.yml` | Cada viernes 11:00 UTC | `single` | — |
| `newsletter-biweekly.yml` | Viernes semanas pares | `digest` | Hace 14 días |
| `newsletter-monthly.yml` | Primer viernes del mes | `digest` | Hace 31 días |

Todos admiten **ejecución manual** (botón *Run workflow*) con:
- `dry_run`: genera HTML y lo muestra en logs sin enviar
- `since_date`: override manual de la fecha de inicio del digest
- `force`: ignora la condición de semana/día y fuerza el envío

---

## Uso local

### 1. Instalar dependencias

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar variables

```bash
cp .env.example .env
# Editar .env con tus valores reales
```

### 3. Ejecutar

```bash
# Newsletter single (post con radar:true más reciente)
python main.py --mode single

# Digest desde una fecha concreta
python main.py --mode digest --since 2026-03-01

# Cualquiera de los dos en dry-run (no envía)
python main.py --mode single --dry-run
python main.py --mode digest --since 2026-03-01 --dry-run
```

Los flags `--mode`, `--since` y `--dry-run` tienen **prioridad** sobre las variables de entorno.

---

## Variables de entorno / Secrets

| Variable | Local (`.env`) | GitHub Secret | Descripción |
|---|---|---|---|
| `MAILERLITE_API_KEY` | ✅ | ✅ | API key de MailerLite |
| `MAILERLITE_GROUP_ID` | ✅ | ✅ | ID del grupo de suscriptores |
| `FROM_NAME` | ✅ | ✅ | Nombre remitente (ej: `#WAIQ`) |
| `FROM_EMAIL` | ✅ | ✅ | Email remitente |
| `HUGO_SINGLE_ENDPOINT` | ✅ | ✅ | URL endpoint single (markdown+frontmatter) |
| `HUGO_DIGEST_ENDPOINT` | ✅ | ✅ | URL endpoint digest (`?since=YYYY-MM-DD`) |
| `SITE_BASE_URL` | ✅ | ✅ | URL base del sitio Hugo |
| `ANTHROPIC_API_KEY` | ✅ | ✅ | API key de Anthropic (para digest) |
| `ANTHROPIC_MODEL` | opcional | — | Modelo Claude (default: `claude-sonnet-4-20250514`) |
| `MODE` | opcional | via workflow | `single` \| `digest` |
| `SINCE_DATE` | opcional | via workflow | Fecha desde `YYYY-MM-DD` (solo digest) |
| `DRY_RUN` | opcional | via input | `true` \| `false` |

### Añadir secrets en GitHub

`Settings → Secrets and variables → Actions → New repository secret`

---

## Endpoints Hugo esperados

### `HUGO_SINGLE_ENDPOINT` — GET

Devuelve el cuerpo como **texto plano** con markdown + frontmatter YAML o TOML del artículo más reciente con `radar: true`.

```
HTTP/1.1 200 OK
Content-Type: text/plain; charset=utf-8

---
title: "Título del artículo"
date: 2026-03-14
draft: false
radar: true
description: "Resumen breve"
tags: ["IA", "Europa"]
slug: "titulo-del-articulo"
---

Cuerpo del artículo en markdown...
```

### `HUGO_DIGEST_ENDPOINT` — GET `?since=YYYY-MM-DD`

Devuelve JSON con las URLs de referencia recopiladas desde la fecha indicada.

```json
{
  "button_urls": [
    "https://ejemplo.com/articulo-1",
    "https://otro.com/noticia-2"
  ],
  "total": 2
}
```

---

## Estructura del repositorio

```
waiq-news/
├── main.py                          ← Punto de entrada
├── requirements.txt
├── .env.example                     ← Plantilla de variables (copiar a .env)
├── .gitignore
├── scripts/
│   ├── __init__.py
│   ├── config.py                    ← Carga de configuración
│   ├── hugo_client.py               ← Llamadas a endpoints Hugo
│   ├── ai_editor.py                 ← Generación editorial con Claude AI
│   ├── html_builder.py              ← Generación de HTML del email
│   └── mailer.py                    ← Envío via MailerLite API
└── .github/
    └── workflows/
        ├── newsletter-weekly.yml
        ├── newsletter-biweekly.yml
        └── newsletter-monthly.yml
```
