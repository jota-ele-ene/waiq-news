# waiq-news

Automatización del newsletter de [WAIQ](https://waiq.technology) mediante GitHub Actions + MailerLite.

Lee los artículos publicados en [`jota-ele-ene/waiq-multi`](https://github.com/jota-ele-ene/waiq-multi) (`content/es/article/`) y envía campañas automáticas cada viernes.

---

## Workflows

| Workflow | Frecuencia | Tipo | Contenido |
|---|---|---|---|
| `newsletter-weekly.yml` | Cada viernes 11:00 UTC | **Single** | El artículo más reciente con `radar: true` |
| `newsletter-biweekly.yml` | Cada 2 viernes (semanas pares) | **Digest** | Todos los artículos de los últimos 14 días |
| `newsletter-monthly.yml` | Primer viernes del mes | **Digest** | Todos los artículos de los últimos 31 días |

Todos los workflows tienen un botón **"Run workflow"** en GitHub Actions para lanzarlos manualmente, con opción de `dry_run` para previsualizar sin enviar.

---

## Configuración

### 1. Secrets requeridos

Ve a **Settings → Secrets and variables → Actions** y añade:

| Secret | Descripción |
|---|---|
| `MAILERLITE_API_KEY` | API key de MailerLite (*Integrations → API*) |
| `MAILERLITE_GROUP_ID` | ID del grupo/lista de suscriptores en MailerLite |
| `GH_TOKEN` | GitHub Personal Access Token con permiso `repo` (lectura) |

### 2. Frontmatter esperado en los posts Hugo

El newsletter semanal busca el post más reciente con **`radar: true`**:

```yaml
---
title: "Título del artículo"
date: 2025-03-14
draft: false
radar: true
description: "Resumen breve que aparece en el email"
tags: ["IA", "tecnología"]
---
```

Los newsletters de digest recogen todos los posts publicados en el período, independientemente de `radar`.

---

## Estructura del repositorio

```
waiq-news/
├── .github/
│   ├── scripts/
│   │   └── send_newsletter.py   ← Script principal
│   └── workflows/
│       ├── newsletter-weekly.yml
│       ├── newsletter-biweekly.yml
│       └── newsletter-monthly.yml
└── README.md
```

---

## Ejecución manual con dry run

1. Ve a **Actions** → selecciona el workflow
2. Haz clic en **Run workflow**
3. Activa **Dry run = true**
4. Revisa los logs — verás el asunto y el tamaño del HTML generado sin que se envíe nada

---

## Zona horaria

Los crons están configurados a las **11:00 UTC**, que corresponde a:
- 🕛 12:00 en España (CET, invierno)
- 🕐 13:00 en España (CEST, verano)

Ajusta el cron a `0 10 * * 5` si prefieres que sea siempre a las 12:00 en verano.
