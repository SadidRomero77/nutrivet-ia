#!/usr/bin/env bash
# ─── init_db.sh — Bootstrap de base de datos NutriVet.IA ────────────────────
#
# Uso:
#   ./scripts/init_db.sh              # Corre migraciones Alembic
#   ./scripts/init_db.sh --reset      # Dropea y recrea la DB (solo dev!)
#
# En Docker:
#   docker compose -f docker-compose.prod.yml exec app ./scripts/init_db.sh
#
# Prerequisitos:
#   - PostgreSQL corriendo y accesible via DATABASE_URL
#   - Variables de entorno configuradas (.env o Docker env)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "═══════════════════════════════════════════════════════"
echo "  NutriVet.IA — Database Bootstrap"
echo "═══════════════════════════════════════════════════════"

# Verificar que las variables de entorno están configuradas
if [ -z "${DATABASE_URL:-}" ] && [ -z "${DATABASE_URL_ASYNC:-}" ]; then
    echo "ERROR: DATABASE_URL o DATABASE_URL_ASYNC no está configurada."
    echo "Configura las variables de entorno antes de ejecutar este script."
    exit 1
fi

# Reset mode (solo para desarrollo!)
if [ "${1:-}" = "--reset" ]; then
    echo ""
    echo "⚠️  MODO RESET — esto borrará TODOS los datos de la base de datos."
    echo "    Solo usar en desarrollo. NUNCA en producción."
    echo ""
    read -p "¿Estás seguro? (escribe 'SI' para confirmar): " confirm
    if [ "$confirm" != "SI" ]; then
        echo "Cancelado."
        exit 0
    fi

    echo "→ Dropeando todas las tablas..."
    python -c "
from sqlalchemy import create_engine, text
import os
url = os.environ.get('DATABASE_URL', 'postgresql+psycopg2://nutrivet:nutrivet_dev_pass@localhost:5432/nutrivet_dev')
engine = create_engine(url)
with engine.connect() as conn:
    conn.execute(text('DROP SCHEMA public CASCADE'))
    conn.execute(text('CREATE SCHEMA public'))
    conn.commit()
print('Schema recreado.')
"
    echo "✓ Schema limpio."
fi

# Correr migraciones Alembic
echo ""
echo "→ Ejecutando migraciones Alembic..."
python -m alembic upgrade head

echo ""
echo "→ Verificando estado de migraciones..."
python -m alembic current

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  ✓ Base de datos inicializada correctamente"
echo "═══════════════════════════════════════════════════════"
