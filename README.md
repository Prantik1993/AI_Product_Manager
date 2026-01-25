# 🚀 Enterprise AI Product Manager

An Agentic RAG application that acts as an autonomous Product Manager. It evaluates product ideas against internal company strategy, market trends, and technical feasibility using a Multi-Agent architecture.

## 🏗️ Architecture
- **Framework**: LangGraph (Multi-Agent Orchestration)
- **Frontend**: Streamlit
- **Brain (RAG)**: ChromaDB (Vector Store)
- **Models**: OpenAI GPT-4 Turbo
- **Tools**: Tavily (Live Web Search)

## ⚡ Features
- **Strategy Enforcement**: RAG retrieves strict company PDF rules (e.g., "No Hardware", "Budget < $50k").
- **Real-time Research**: Agents search the web for live competitor data.
- **Decision Engine**: Rejects ideas that violate internal policies, even if they are profitable.

## 🛠️ Installation

### 1. Clone & Setup
```bash
git clone [https://github.com/yourusername/ai-product-manager.git](https://github.com/yourusername/ai-product-manager.git)
cd ai-product-manager
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt