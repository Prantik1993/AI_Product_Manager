# 🚀 Enterprise AI Product Manager (LEAN Production Version)

[![CI](https://github.com/yourusername/ai-product-manager/workflows/CI%20Pipeline/badge.svg)](https://github.com/yourusername/ai-product-manager/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

A production-ready, LEAN AI Product Manager that evaluates product ideas using multi-agent orchestration, RAG-driven strategy enforcement, and real-time market research.

## ✨ What's New in v2.0 (LEAN Production Edition)

- **Production-Ready Infrastructure**: Docker, Redis caching, health checks
- **Enhanced Monitoring**: Structured logging, Prometheus metrics, tracing
- **Robust Error Handling**: Retry logic with exponential backoff, graceful degradation
- **Improved RAG**: Reranking, quality scoring, caching
- **Modern Python**: Type hints, Pydantic v2, SQLAlchemy ORM
- **CI/CD Pipeline**: Automated testing, linting, security scans
- **80% of Enterprise Value, 30% of the Code**: Minimal, focused, maintainable

## 🏗️ Architecture

### Core Stack
- **Orchestration**: LangGraph (Multi-Agent)
- **LLM**: OpenAI GPT-4 Turbo
- **Vector DB**: ChromaDB (RAG)
- **Cache**: Redis (with Memory fallback)
- **Database**: SQLite/PostgreSQL (async-ready)
- **Search**: Tavily API
- **Frontend**: Streamlit
- **Testing**: Pytest with 80%+ coverage

### Multi-Agent Decision Flow

```
Product Idea
    ↓
┌─────────────────────────────────────────┐
│  Parallel Agent Execution (LangGraph)  │
├─────────────────────────────────────────┤
│  • MarketAgent (web search + LLM)      │
│  • TechAgent (feasibility)             │
│  • RiskAgent (compliance check)        │
│  • UserFeedbackAgent (sentiment)       │
└─────────────────────────────────────────┘
    ↓
DecisionAgent
    ├─ RAG: Query company strategy
    └─ Synthesize → GO/NO-GO/PIVOT
    ↓
Save to Database + Display Results
```

## 📁 Project Structure (LEAN)

```
ai-product-manager/
├── .github/workflows/
│   └── ci.yml                    # CI pipeline: lint + test + docker
│
├── config/
│   └── production.yaml           # Production config overrides
│
├── data/
│   ├── internal_docs/            # Company strategy documents
│   ├── chroma_db/                # Vector database
│   └── cache/                    # File-based cache fallback
│
├── scripts/
│   ├── setup.sh                  # One-command setup
│   ├── ingest_docs.py            # RAG document ingestion
│   └── health_check.py           # Deployment health validation
│
├── src/
│   ├── agents/                   # Decision agents
│   │   ├── base.py
│   │   ├── market.py
│   │   ├── tech.py
│   │   ├── risk.py
│   │   ├── user_feedback.py
│   │   └── decision.py
│   │
│   ├── cache/
│   │   └── cache.py              # Memory + Redis fallback
│   │
│   ├── config/
│   │   └── settings.py           # Pydantic settings
│   │
│   ├── core/
│   │   ├── exceptions.py         # Custom exceptions
│   │   └── retry.py              # Retry logic with backoff
│   │
│   ├── graph/
│   │   ├── state.py              # Workflow state
│   │   └── workflow.py           # LangGraph orchestration
│   │
│   ├── monitoring/
│   │   ├── logger.py             # Structured logging + tracing
│   │   └── metrics.py            # Prometheus metrics
│   │
│   ├── prompts/
│   │   ├── manager.py            # Prompt loader
│   │   └── templates/            # YAML prompt templates
│   │
│   ├── rag/
│   │   ├── engine.py             # RAG with reranking
│   │   ├── evaluation.py         # Quality tests
│   │   └── ingest.py             # Document ingestion
│   │
│   ├── schemas/
│   │   └── output.py             # Pydantic output models
│   │
│   ├── storage/
│   │   ├── database.py           # Async SQLAlchemy
│   │   ├── db_manager.py         # Legacy compatibility
│   │   └── models.py             # ORM models
│   │
│   └── tools/
│       └── web_search.py         # Tavily with retry
│
├── tests/
│   ├── conftest.py               # Shared fixtures
│   ├── test_core.py              # Core utilities tests
│   ├── test_cache.py             # Cache tests
│   └── test_rag.py               # RAG quality tests
│
├── app.py                        # Streamlit UI
├── main.py                       # CLI runner
├── docker-compose.yml            # Redis + App stack
├── Dockerfile                    # Multi-stage production image
├── pyproject.toml                # Modern Python config
├── requirements.txt              # Dependencies
└── README.md                     # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- OpenAI API key
- Tavily API key (for web search)
- Docker (optional, for production)

### Option 1: Automated Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/ai-product-manager.git
cd ai-product-manager

# Run one-command setup
chmod +x scripts/setup.sh
./scripts/setup.sh
```

This script will:
1. Create a virtual environment
2. Install dependencies
3. Set up .env file
4. Initialize the database
5. Ingest strategy documents

### Option 2: Manual Setup

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and add your API keys:
# OPENAI_API_KEY=sk-...
# TAVILY_API_KEY=tvly-...

# 4. Add company strategy documents
# Place PDF/TXT files in data/internal_docs/

# 5. Ingest documents into RAG
python src/rag/ingest.py

# 6. Run the application
streamlit run app.py
```

### Option 3: Docker (Production)

```bash
# 1. Build and start services
docker-compose up -d

# 2. Access Streamlit UI
# Open http://localhost:8501

# 3. View logs
docker-compose logs -f app

# 4. Stop services
docker-compose down
```

## 🎯 Usage

### Streamlit UI (Web Interface)

```bash
streamlit run app.py
```

Navigate to http://localhost:8501 and:
1. Enter your product idea
2. Click "Analyze Product Idea"
3. View real-time agent analysis
4. See final decision with confidence score
5. Browse past reports in History tab

### CLI Mode (Headless)

```bash
python main.py
```

Follow prompts to enter product idea and view analysis results.

### Python API

```python
from src.graph.workflow import create_workflow

# Create workflow
workflow = create_workflow()

# Analyze product idea
state = {
    "user_input": "AI-powered fitness tracker app",
    "market_report": None,
    "tech_report": None,
    "risk_report": None,
    "user_feedback_report": None,
    "final_decision": None,
}

# Execute workflow
result = workflow.invoke(state)
print(result["final_decision"])
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_rag.py -v

# Run only unit tests
pytest -m unit

# Run integration tests
pytest -m integration
```

## 📊 Monitoring & Observability

### Structured Logging

All logs are JSON-formatted for easy parsing:

```json
{
  "timestamp": "2024-01-28T10:30:45.123Z",
  "level": "INFO",
  "app": "Enterprise AI Product Manager",
  "env": "production",
  "module": "rag.engine",
  "message": "RAG query completed",
  "trace_id": "abc-123",
  "duration_seconds": 0.45
}
```

### Metrics Collection

Prometheus-compatible metrics:

```python
from src.monitoring.metrics import metrics_collector

# View all metrics
metrics = metrics_collector.get_metrics()
print(metrics)
```

### Health Checks

```bash
# Check system health
python scripts/health_check.py

# Docker health check (automatic)
docker-compose ps
```

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Required
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...

# Optional
ENV=production               # development, staging, production
CACHE_BACKEND=redis          # memory, redis
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=sqlite:///data/app.db
LOG_LEVEL=INFO               # DEBUG, INFO, WARNING, ERROR
ENABLE_CACHE=true
ENABLE_METRICS=true
```

### Production Config (config/production.yaml)

Override settings for production deployment:

```yaml
cache:
  backend: redis
  ttl: 600

monitoring:
  log_level: INFO
  enable_metrics: true

rag:
  enable_reranking: true
  top_k: 5
```

## 🛠️ Development

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type checking
mypy src/ --ignore-missing-imports
```

### Adding New Agents

1. Create agent file in [src/agents/](src/agents/)
2. Inherit from `BaseAgent`
3. Implement `analyze()` method
4. Add to workflow in [src/graph/workflow.py](src/graph/workflow.py#L28-L51)

Example:

```python
from src.agents.base import BaseAgent

class CustomAgent(BaseAgent):
    def analyze(self, product_idea: str) -> dict:
        # Your analysis logic
        return {
            "verdict": "GO",
            "confidence": 0.8,
            "rationale": "...",
        }
```

## 🚢 Deployment

### Docker Production Deployment

```bash
# Build production image
docker build --target production -t ai-pm:latest .

# Run with environment file
docker run -d \
  --name ai-pm \
  -p 8501:8501 \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  ai-pm:latest
```

### Environment-Specific Builds

```bash
# Development (with hot reload)
docker build --target development -t ai-pm:dev .

# Production (optimized)
docker build --target production -t ai-pm:prod .
```

## 📈 Performance

- **Cold Start**: ~2-3 seconds
- **Analysis Time**: 15-30 seconds (parallel agents)
- **Cache Hit Rate**: ~60% (with Redis)
- **Memory Usage**: ~200MB base, ~500MB peak
- **Concurrency**: Supports 10+ concurrent analyses

## 🔒 Security

- **API Keys**: Never committed, loaded from .env
- **Input Validation**: Pydantic schema validation
- **SQL Injection**: Protected via SQLAlchemy ORM
- **Dependency Scanning**: Automated with Trivy
- **Rate Limiting**: Configured per API (OpenAI, Tavily)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- LangChain & LangGraph for multi-agent orchestration
- OpenAI for GPT-4 Turbo
- Tavily for real-time web search
- ChromaDB for vector storage

## 📧 Support

- Issues: https://github.com/yourusername/ai-product-manager/issues
- Discussions: https://github.com/yourusername/ai-product-manager/discussions
- Email: your.email@example.com

---

**Built with ❤️ for Product Managers who want AI to do the heavy lifting**
