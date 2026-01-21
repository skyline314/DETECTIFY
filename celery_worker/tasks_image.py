import os
import tempfile
from .celery_app import celery
from .core import ml_registry 
from app.models import AnalysisHistory
from app.extensions import db, s3_client
from flask import current_app

@celery.task(name='process_image_task')
def process_image_task(analysis_id):
    """
    Worker Image: Menggunakan EfficientNetV2.
    Alur: S3 -> Temp File -> Predict (Core) -> Save DB -> Cleanup
    """
    print(f"[Worker] Starting Image Job: {analysis_id}")
    
    # 1. Ambil Data Job dari DB
    job = AnalysisHistory.query.filter_by(analysis_id=analysis_id).first()
    if not job:
        print(f"[Worker] Error: Job ID {analysis_id} not found in DB.")
        return

    temp_path = None 

    try:
        # 2. Update Status -> PROCESSING
        job.status = 'PROCESSING'
        db.session.commit()

        # 3. Ambil File dari S3
        bucket_name = current_app.config['AWS_S3_BUCKET_NAME']
        file_key = job.file_location
        
        print(f"[Worker] Fetching Image from S3: {file_key}")
        s3_response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        image_data_bytes = s3_response['Body'].read()

        # 4. Simpan ke Temporary File
        # PIL (Python Imaging Library) butuh file fisik atau BytesIO.
        # Kita pakai file fisik agar konsisten dengan cara kerja Audio/Core.
        file_ext = os.path.splitext(job.file_name_original)[1] if job.file_name_original else ".jpg"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            temp_file.write(image_data_bytes)
            temp_path = temp_file.name # Simpan path lokasi file sementara

        # 5. Prediksi menggunakan ML Registry (Logic Image)
        print(f"[Worker] Running Image Inference on {temp_path}...")
        
        result_data = ml_registry.predict_image(temp_path)

        # Cek jika ada error dari core
        if "error" in result_data:
            raise ValueError(result_data["error"])

        # 6. Simpan Hasil ke Database
        job.status = 'COMPLETED'
        job.result_summary = result_data # Simpan JSON lengkap
        
        db.session.commit()
        print(f"[Worker] Job {analysis_id} COMPLETED. Result: {result_data.get('prediction')}")

        # 7. Cleanup S3 (Hapus file dari bucket setelah selesai)
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
        # 8. Cleanup Temporary File (Hapus file sementara di server)
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
            print("[Worker] Temp file cleaned.")