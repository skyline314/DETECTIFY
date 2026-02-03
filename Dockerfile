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
    && apt-get clean && rm -rf /var/lib/apt/lists/*

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
COPY --chown=user . .

# Buat folder log dan tmp di dalam folder yang bisa ditulis user
RUN mkdir -p /app/logs /app/tmp

EXPOSE 7860

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:7860 --workers 1 --threads 8 --timeout 0 run:app & celery -A celery_worker.celery_app.celery worker --loglevel=info -P solo"]