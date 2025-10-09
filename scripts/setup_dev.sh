#!/bin/bash
set -e

echo "Setting up Thematic-LM development environment..."

# Check if .env exists
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env from template"
    echo "⚠️  Please configure your API keys in .env before continuing"
    exit 1
fi

echo "Installing dependencies..."
if command -v uv &> /dev/null; then
    uv sync
elif command -v poetry &> /dev/null; then
    poetry install
else
    echo "❌ Neither uv nor poetry found. Please install one of them."
    exit 1
fi

echo "Running contract validation..."
python3 scripts/validate_contracts.py

echo "Initializing database migrations..."
alembic upgrade head

echo ""
echo "✅ Development environment ready!"
echo ""
echo "Next steps:"
echo "  1. Ensure .env is configured with your API keys"
echo "  2. Create identities.yaml with your identity configurations"
echo "  3. Start API: uvicorn src.thematic_lm.api.main:app --reload"
echo "  4. Test endpoint: curl http://localhost:8000/health"
