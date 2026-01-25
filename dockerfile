# 1. Base Image: Use a lightweight, official Python runtime
FROM python:3.11-slim

# 2. Set Environment Variables to optimize Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 3. Set Working Directory
WORKDIR /app

# 4. Install System Dependencies (Needed for ChromaDB & PDF tools)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# 5. Copy Requirements & Install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy The Source Code
COPY . .

# 7. Healthcheck (Enterprise Requirement: "Are you alive?")
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# 8. Expose the Port
EXPOSE 8501

# 9. Run the App
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]