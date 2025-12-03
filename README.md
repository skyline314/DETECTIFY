# Detectify Backend (MVP)

Backend API untuk deteksi Deepfake menggunakan Flask, Celery, dan Machine Learning.

## Arsitektur
- **Lobby:** Flask API (Port 5000)
- **Factory:** Celery Worker (Background Process)
- **Broker:** Redis
- **Storage:** AWS S3
- **Database:** MySQL

## Cara Menjalankan (Development)

1. **Persiapan:**
   - Pastikan Redis Server berjalan.
   - Isi file `.env` (lihat contoh di bawah).

2. **Jalankan Worker:**
   ```bash
   celery -A celery_worker.celery_app.celery worker --loglevel=info --pool=solo -Q audio_queue