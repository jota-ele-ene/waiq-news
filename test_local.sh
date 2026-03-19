#!/usr/bin/env bash
# test_local.sh — Prueba completa en local con mock server y dry-run
set -e

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   WAIQ News — Test local                     ║"
echo "╚══════════════════════════════════════════════╝"

[ ! -f ".env" ] && echo "❌ Crea .env desde .env.example" && exit 1
[ -d ".venv" ] && source .venv/bin/activate

echo "🟢 Arrancando mock server..."
python mock_server.py &
MOCK_PID=$!
sleep 1

export HUGO_SINGLE_ENDPOINT_ES=http://localhost:1313/es/api/newsletter/single
export HUGO_SINGLE_ENDPOINT_EN=http://localhost:1313/api/newsletter/single
export HUGO_DIGEST_ENDPOINT_ES=http://localhost:1313/es/api/newsletter/digest
export HUGO_DIGEST_ENDPOINT_EN=http://localhost:1313/api/newsletter/digest
export DRY_RUN=true

echo ""
echo "━━ TEST 1: single ES ━━━━━━━━━━━━━━━━━━━━━━━━━━"
python main.py --mode single --lang es --dry-run

echo ""
echo "━━ TEST 2: single EN ━━━━━━━━━━━━━━━━━━━━━━━━━━"
python main.py --mode single --lang en --dry-run

echo ""
echo "━━ TEST 3: digest ES 15d ━━━━━━━━━━━━━━━━━━━━━━"
python main.py --mode digest --lang es --days 15 --dry-run

echo ""
echo "━━ TEST 4: digest ES 30d ━━━━━━━━━━━━━━━━━━━━━━"
python main.py --mode digest --lang es --days 30 --dry-run

echo ""
echo "━━ TEST 5: digest EN 15d ━━━━━━━━━━━━━━━━━━━━━━"
python main.py --mode digest --lang en --days 15 --dry-run

kill $MOCK_PID 2>/dev/null
echo ""
echo "✅ Tests completados. Revisa data/latest/03_preview.html en el navegador."
