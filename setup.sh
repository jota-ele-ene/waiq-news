#!/usr/bin/env bash
# setup.sh — Crea el repositorio waiq-news en GitHub y sube todos los archivos
# Uso: bash setup.sh
# Requiere: git, gh (GitHub CLI) instalados y autenticados

set -e

REPO="waiq-news"
OWNER="jota-ele-ene"
DESCRIPTION="Automatización del newsletter WAIQ con GitHub Actions + MailerLite"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   WAIQ News — Setup del repositorio          ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# 1. Crear el repositorio remoto (público)
echo "📦 Creando repositorio $OWNER/$REPO en GitHub…"
gh repo create "$OWNER/$REPO" \
  --public \
  --description "$DESCRIPTION" \
  --confirm 2>/dev/null || echo "  (el repositorio ya existe, continuando…)"

# 2. Inicializar git local si no está inicializado
if [ ! -d ".git" ]; then
  echo "🔧 Inicializando repositorio git local…"
  git init
  git branch -M main
fi

# 3. Añadir remote si no existe
if ! git remote get-url origin &>/dev/null; then
  echo "🔗 Añadiendo remote origin…"
  git remote add origin "https://github.com/$OWNER/$REPO.git"
fi

# 4. Commit inicial
echo "📝 Haciendo commit inicial…"
git add -A
git commit -m "feat: newsletter automation inicial

- 3 workflows: semanal, quincenal, mensual
- Script Python que lee Hugo desde GitHub API
- Soporte dry_run para pruebas sin envío
- HTML responsivo con branding WAIQ"

# 5. Push
echo "🚀 Subiendo a GitHub…"
git push -u origin main --force

echo ""
echo "✅ ¡Repositorio creado y subido!"
echo ""
echo "📋 Próximos pasos — añade estos Secrets en:"
echo "   https://github.com/$OWNER/$REPO/settings/secrets/actions"
echo ""
echo "   MAILERLITE_API_KEY  → Tu API key de MailerLite"
echo "   MAILERLITE_GROUP_ID → ID de tu lista/grupo en MailerLite"
echo "   GH_TOKEN            → GitHub PAT con permiso 'repo' (lectura)"
echo ""
echo "🔗 Repositorio: https://github.com/$OWNER/$REPO"
echo "⚙️  Actions:    https://github.com/$OWNER/$REPO/actions"
echo ""
