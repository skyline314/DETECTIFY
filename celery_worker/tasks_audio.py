import os
import io
import tempfile
from .celery_app import celery
from .core import ml_registry 
from app.models import AnalysisHistory
from app.extensions import db, s3_client
from flask import current_app

@celery.task(name='process_audio_task')
def process_audio_task(analysis_id):
    """
    Worker Audio: Menggunakan Deep Learning (CNN).
    Alur: S3 -> Temp File -> Predict (Core) -> Save DB -> Cleanup
    """
    print(f"[Worker] Starting Audio Job: {analysis_id}")
    
    job = AnalysisHistory.query.filter_by(analysis_id=analysis_id).first()
    if not job:
        print(f"[Worker] Error: Job ID {analysis_id} not found in DB.")
        return

    temp_path = None 

    try:
        # 1. Update Status -> PROCESSING
        job.status = 'PROCESSING'
        db.session.commit()

        # 2. Ambil File dari S3
        bucket_name = current_app.config['AWS_S3_BUCKET_NAME']
        file_key = job.file_location
        
        print(f"[Worker] Fetching from S3: {file_key}")
        s3_response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        audio_data_bytes = s3_response['Body'].read()

        # 3. Simpan ke Temporary File (PENTING!)
        # Torchaudio butuh file fisik untuk dibaca, bukan bytes di RAM.
        # Kita gunakan ekstensi asli file (misal .wav atau .mp3)
        file_ext = os.path.splitext(job.file_name_original)[1] if job.file_name_original else ".wav"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            temp_file.write(audio_data_bytes)
            temp_path = temp_file.name # Simpan lokasi path file ini

        # 4. Prediksi menggunakan ML Registry (Logic Baru)
        print(f"[Worker] Running Deep Learning Inference on {temp_path}...")
        
        # Panggil fungsi predict_audio di core.py dengan path file
        result_data = ml_registry.predict_audio(temp_path)

        # Cek jika ada error dari core
        if "error" in result_data:
            raise ValueError(result_data["error"])

        # 5. Simpan Hasil ke Database
        job.status = 'COMPLETED'
        job.result_summary = result_data # Simpan JSON lengkap hasil prediksi
        
        db.session.commit()
        print(f"[Worker] Job {analysis_id} COMPLETED. Result: {result_data.get('prediction')}")

        # 6. Cleanup S3 
        try:
            s3_client.delete_object(Bucket=bucket_name, Key=file_key)
            print("[Worker] S3 Cleanup done.")
        except Exception as cleanup_error:
            print(f"[Worker] S3 Cleanup Warning: {cleanup_error}")

    except Exception as e:
        print(f"[Worker] Job Failed: {e}")
        db.session.rollback()
        job.status = 'FAILED'
        job.error_message = str(e)
        db.session.commit()

    finally:
        # 7. Cleanup Temporary File 
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
            print("[Worker] Temp file cleaned.")