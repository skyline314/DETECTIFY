import os
from .celery_app import celery
from .core import ml_registry 
from app.models import AnalysisHistory
from app.extensions import db
from .utils import s3_temp_file, cleanup_s3, extract_text_from_file

@celery.task(name='process_humanize_task')
def process_humanize_task(analysis_id):
    """
    Worker Humanize: Menggunakan Llama 3 via Ollama.
    Alur: S3 -> Temp File -> Extract Text -> Predict (Core) -> Save DB -> Cleanup
    """
    print(f"[Worker] Starting Humanize Job: {analysis_id}")

    job = AnalysisHistory.query.filter_by(analysis_id=analysis_id).first()
    if not job:
        print(f"[Worker] Error: Job ID {analysis_id} not found.")
        return

    try:
        job.status = 'PROCESSING'
        db.session.commit()

        with s3_temp_file(job.file_location) as temp_path:
<<<<<<< HEAD
<<<<<<< HEAD
            # Baca teks dari file
            raw_text = extract_text_from_file(temp_path)
            
            if not raw_text or len(raw_text.strip()) < 5:
                raise ValueError("Text is not found or too short to process.")
            
=======
            # Baca teks dari file .input
            raw_text = extract_text_from_file(temp_path)
            
>>>>>>> 1a28d7f5a860d74198facd1c65210be6a133fa59
=======
            # Baca teks dari file .input
            raw_text = extract_text_from_file(temp_path)
            
>>>>>>> 45a07fcd43bd6fae16c3910ebcd43151321b3a1f
            # Deteksi bahasa dari nama file (id_manual_text.input atau en_manual_text.input)
            lang = 'id' if job.file_name_original.startswith('id_') else 'en'
            
            result_data = ml_registry.humanize_text(raw_text, lang)

            if "error" in result_data:
                raise ValueError(result_data["error"])
            
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
        cleanup_s3(job.file_location)