import os
import io
import tempfile
from .celery_app import celery
from .core import ml_registry 
from app.models import AnalysisHistory
from app.extensions import db, s3_client
from flask import current_app
from .utils import s3_temp_file, cleanup_s3

@celery.task(name='process_audio_task')
def process_audio_task(analysis_id):
    """
    Worker Audio: Menggunakan Deep Learning (CNN).
    Alur: S3 -> Temp File -> Predict (Core) -> Save DB -> Cleanup
    """
    print(f"[Worker] Starting Audio Job: {analysis_id}")

    # Ambil Data Job dari DB
    job = AnalysisHistory.query.filter_by(analysis_id=analysis_id).first()
    if not job:
        print(f"[Worker] Error: Job ID {analysis_id} not found in DB.")
        return

    try:
        # Update Status -> PROCESSING
        job.status = 'PROCESSING'
        db.session.commit()

        # Pakai shared utility: Download -> Pakai -> Hapus Lokal otomatis
        with s3_temp_file(job.file_location) as temp_path:
            result_data = ml_registry.predict_audio(temp_path)

            if "error" in result_data:
                raise ValueError(result_data["error"])
            
            # Update Status -> COMPLETED (Success)
            job.status = 'COMPLETED'
            job.result_summary = result_data
            db.session.commit()
            print(f"[Worker] Job {analysis_id} SUCCESS.")

    except Exception as e:
        print(f"[Worker] Job Failed: {e}")
        db.session.rollback()
        job.status = 'FAILED'
        job.error_message = str(e)
        db.session.commit()

    finally:
        cleanup_s3(job.file_location) # Hapus di S3 setelah selesai