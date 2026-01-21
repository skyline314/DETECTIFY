from .celery_app import celery
from .core import ml_registry 
import tempfile
from app.models import AnalysisHistory
from app.extensions import db, s3_client
from flask import current_app
from app.analysis.utils import extract_text_from_file
import os

@celery.task(name='process_text_task')
def process_text_task(analysis_id):
    """Worker for Text Analysis"""
    print(f"[Worker] Starting Text Job: {analysis_id}")
    
    job = AnalysisHistory.query.filter_by(analysis_id=analysis_id).first()
    if not job: 
        print(f"[Worker] Error: Job ID {analysis_id} not found in DB.")
        return

    try:
        job.status = 'PROCESSING'
        db.session.commit()

        # Fetch S3
        bucket_name = current_app.config['AWS_S3_BUCKET_NAME']
        file_key = job.file_location
        
        print(f"[Worker] Fetching Document from S3: {file_key}")
        s3_response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        file_data_bytes = s3_response['Body'].read()

        original_ext = os.path.splitext(job.file_name_original)[1] if job.file_name_original else ".txt"

        with tempfile.NamedTemporaryFile(delete=False, suffix=original_ext) as temp_file:
            temp_file.write(file_data_bytes)
            temp_path = temp_file.name

        print(f"[Worker] Extracting text from {temp_path}...")
        raw_text = extract_text_from_file(temp_path)

        if not raw_text.strip():
            raise ValueError("File teks kosong")

        # Predict (default logreg)
        result = ml_registry.predict_text('LogReg', raw_text)

        if "error" in result:
            raise ValueError(result['error'])

        # Save
        job.status = 'COMPLETED'
        job.result_summary = result
        db.session.commit()

        # Cleanup
        s3_client.delete_object(Bucket=bucket_name, Key=job.file_location)
        print(f"[Worker] Text Job Completed: {result['prediction']}")

    except Exception as e:
        print(f"[Worker] Text Job Failed: {e}")
        db.session.rollback()
        job.status = 'FAILED'
        job.error_message = str(e)
        db.session.commit()