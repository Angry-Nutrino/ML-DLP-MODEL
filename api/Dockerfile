# FastAPI + Transformers (CPU-only) image
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \ 
    curl     && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
# Use PyTorch CPU wheels
RUN pip install --no-cache-dir --upgrade pip &&     pip install --no-cache-dir -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

# App
COPY app ./app

# A mount will provide /models at runtime
ENV MODEL_PATH=/models/dlp_model_distilbert-base
ENV API_KEY=DEMO_KEY

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
