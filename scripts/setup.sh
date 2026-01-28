#!/bin/bash
# One-command setup script for AI Product Manager

set -e  # Exit on error

echo "🚀 Setting up AI Product Manager..."

# Check Python version
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate || source venv/Scripts/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p data/internal_docs
mkdir -p data/chroma_db
mkdir -p data/cache

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✏️  Please edit .env and add your API keys"
    else
        echo "❌ .env.example not found. Please create .env manually"
    fi
fi

# Initialize database
echo "🗄️  Initializing database..."
python -c "from src.storage.database import get_db_manager; get_db_manager()"

# Ingest documents if strategy.txt exists
if [ -f "data/internal_docs/strategy.txt" ]; then
    echo "📚 Ingesting company strategy documents..."
    python src/rag/ingest.py
else
    echo "⚠️  No strategy.txt found in data/internal_docs/"
    echo "   Add company documents there and run: python src/rag/ingest.py"
fi

# Run health check
echo "🏥 Running health check..."
python scripts/health_check.py || echo "⚠️  Health check failed (this is OK for first setup)"

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your API keys (OPENAI_API_KEY, TAVILY_API_KEY)"
echo "  2. Add company strategy documents to data/internal_docs/"
echo "  3. Run ingestion: python src/rag/ingest.py"
echo "  4. Start the app:"
echo "     - Streamlit UI: streamlit run app.py"
echo "     - CLI mode: python main.py"
echo ""
