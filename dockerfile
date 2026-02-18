# Multi-stage production Dockerfile
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System dependencies — add curl for health check
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Builder stage ────────────────────────────────────────────────────────────
FROM base AS builder

COPY requirements.txt pyproject.toml ./
COPY src/ ./src/

RUN pip install --user --no-cache-dir -r requirements.txt && \
    pip install --user --no-cache-dir -e .

# ── Production stage ─────────────────────────────────────────────────────────
FROM base AS production

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY . .

RUN mkdir -p data/internal_docs data/chroma_db data/cache && \
    chmod +x scripts/setup.sh 2>/dev/null || true

EXPOSE 8501

# FIX: Use Streamlit's built-in health endpoint instead of importing the entire app.
# Old approach ran health_check.py which imported ChromaDB + SQLAlchemy + OpenAI = slow.
# Streamlit exposes /_stcore/health natively at no cost.
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]

# ── Development stage ────────────────────────────────────────────────────────
FROM production AS development

RUN pip install --no-cache-dir pytest pytest-cov pytest-asyncio black ruff mypy

CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.runOnSave=true"]
