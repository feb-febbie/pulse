FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# libgomp1 required by faiss-cpu (OpenMP)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN uv sync --no-dev

# Pre-download the embedding model into the image — avoids slow cold-start download
RUN uv run python -c "\
from sentence_transformers import SentenceTransformer; \
SentenceTransformer('all-MiniLM-L6-v2'); \
print('Model cached.')"

COPY . .

# .streamlit/config.toml sets port=8080, headless=true, address=0.0.0.0
CMD ["uv", "run", "streamlit", "run", "app.py"]
