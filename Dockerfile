FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    ffmpeg \
    libmagic1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Setup user
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# Install requirements
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy all files (PASTIKAN SATU BARIS)
COPY --chown=user . .

# Buat folder log
RUN mkdir -p logs && chmod -R 777 logs

EXPOSE 7860

# Jalankan Flask dan Celery
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:7860 --workers 1 --threads 8 --timeout 0 run:app & celery -A celery_worker.celery_app.celery worker --loglevel=info --concurrency=2"]