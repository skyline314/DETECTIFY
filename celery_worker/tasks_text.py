from .celery_app import celery
from .core import ml_registry 
import tempfile
from app.models import AnalysisHistory
from app.extensions import db, s3_client
from flask import current_app
import os
from .utils import s3_temp_file, cleanup_s3, extract_text_from_file


@celery.task(name='process_text_task')
def process_text_task(analysis_id):
    """Worker for Text Analysis"""
    print(f"[Worker] Starting Text Job: {analysis_id}")
    
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
            raw_text = extract_text_from_file(temp_path)
            
            if not raw_text or len(raw_text.strip()) < 10:
                raise ValueError("Teks tidak ditemukan atau terlalu pendek untuk dianalisis.")
            
            # Deteksi bahasa dari prefix nama file (id_ atau en_)
            lang = 'id' if job.file_name_original.startswith('id_') else 'en'
            
            result_data = ml_registry.predict_text(raw_text, language=lang)

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