#!/bin/bash
# One-command setup for Enterprise AI Product Manager
set -e

echo "🚀 Setting up Enterprise AI Product Manager..."
echo ""

# Check Python version
PY_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
MAJOR=$(echo $PY_VERSION | cut -d. -f1)
MINOR=$(echo $PY_VERSION | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 11 ]); then
    echo "❌ Python 3.11+ required. Found: $PY_VERSION"
    exit 1
fi
echo "✓ Python $PY_VERSION"

# Virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate

# Upgrade pip
pip install --upgrade pip -q

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt -q

# FIX: Install package in editable mode — eliminates all sys.path.append() hacks
echo "📦 Installing package (editable mode)..."
pip install -e . -q

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/internal_docs data/chroma_db data/cache

# .env setup
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "  ⚠️  IMPORTANT: Edit .env and add your API keys before running!"
    echo "  Required:"
    echo "    OPENAI_API_KEY=sk-proj-..."
    echo "    TAVILY_API_KEY=tvly-..."
    echo ""
fi

# Check for strategy documents
if [ -f "data/internal_docs/strategy.txt" ]; then
    echo "📚 Ingesting strategy documents..."
    python src/rag/ingest.py
else
    echo "⚠️  No documents found in data/internal_docs/"
    echo "   Add your company strategy PDF/TXT files then run:"
    echo "   python src/rag/ingest.py"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env — add OPENAI_API_KEY and TAVILY_API_KEY"
echo "  2. Add company docs to data/internal_docs/"
echo "  3. Run: python src/rag/ingest.py"
echo "  4. Launch:"
echo "     Streamlit UI  →  streamlit run app.py"
echo "     CLI mode      →  python main.py"
echo "     Tests         →  pytest"
echo ""
