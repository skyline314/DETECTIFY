FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HOME=/home/user
ENV PATH="/home/user/.local/bin:$PATH"


# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    libtiff-dev \
    ffmpeg \
    libsndfile1 \
    libmagic1 \
    libgl1 \
    libglib2.0-0 \
    zstd \
    curl \
    gpg \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Grafana Alloy
RUN mkdir -p /etc/apt/keyrings/ && \
    curl -fsSL https://apt.grafana.com/gpg.key | gpg --dearmor -o /etc/apt/keyrings/grafana.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | tee /etc/apt/sources.list.d/grafana.list && \
    apt-get update && apt-get install -y alloy && \
    apt-get clean

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Setup user and workdir
RUN useradd -m -u 1000 user
WORKDIR /app

RUN chown user:user /app
USER user

# Install requirements
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy sisa file
# Copy sisa file
COPY --chown=user . .

# Buat folder log dan tmp di dalam folder yang bisa ditulis user
RUN mkdir -p /app/logs /app/tmp /app/tmp/alloy

EXPOSE 7860

CMD ["sh", "-c", "alloy run --storage.path=/app/tmp/alloy /app/config.alloy & ollama serve & sleep 5 && ollama pull llama3 && gunicorn --bind 0.0.0.0:7860 --workers 1 --threads 8 --timeout 0 run:app & celery -A celery_worker.celery_app.celery worker --loglevel=info -P solo"]