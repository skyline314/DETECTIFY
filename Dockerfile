# Gunakan image Python slim untuk efisiensi
FROM python:3.10-slim

# 1. Install System Dependencies (diperlukan untuk audio & database)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    git \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Setup User agar sesuai dengan kebijakan Hugging Face
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# 3. Setup Working Directory
WORKDIR /app

# 4. Install Python Dependencies
# Tips: Upgrade pip terlebih dahulu untuk menghindari masalah instalasi torch cpu
COPY --chown=user requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5. Copy Seluruh Kodingan Aplikasi (Perbaikan: harus satu baris)
COPY --chown=user . .

# 6. Environment Variables Default
ENV PORT=7860
ENV FLASK_ENV=production
ENV MPLBACKEND=Agg 

# 7. Script startup untuk menjalankan Celery & Flask bersamaan
# Perbaikan: Gunicorn harus memanggil 'run:app' karena file utama Anda adalah run.py
RUN echo '#!/bin/bash \n\
celery -A celery_worker.celery_app.celery worker --loglevel=info --pool=threads & \n\
gunicorn -w 1 -b 0.0.0.0:7860 run:app \n\
wait' > start.sh && chmod +x start.sh

# 8. Jalankan Script saat Container nyala
CMD ["./start.sh"]