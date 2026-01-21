import uuid
import logging
from werkzeug.utils import secure_filename
from datetime import datetime
from flask import current_app

from app.extensions import db, s3_client
from app.models import AnalysisHistory, User

class AnalysisService:
    ALLOWED_EXTENSIONS = {
        'AUDIO': {'mp3', 'wav', 'flac'},
        'TEXT': {'txt', 'pdf', 'docx'},
        'IMAGE': {'jpg', 'jpeg', 'png'}
    }

    @staticmethod
    def _validate_file(file, analysis_type):
        if not file or file.filename == '':
            raise ValueError("File tidak valid atau nama file kosong")
        
        filename = secure_filename(file.filename)
        if '.' not in filename:
            raise ValueError("File tidak memiliki ekstensi")
            
        ext = filename.rsplit('.', 1)[1].lower()
        
        # Validasi berdasarkan tipe (AUDIO/TEXT/IMAGE)
        allowed = AnalysisService.ALLOWED_EXTENSIONS.get(analysis_type, set())
        if ext not in allowed:
            raise ValueError(f"Format tidak didukung untuk {analysis_type}. Gunakan: {', '.join(allowed)}")
            
        return filename, ext

    @staticmethod
    def process_upload(user_id, file, analysis_type):
        # 1. Cek User & Kuota
        user = User.query.filter_by(user_id=user_id).first()
        if not user:
            raise ValueError("User tidak ditemukan")

        if not user.can_analyze():
            raise PermissionError(f"Kuota habis. Terpakai: {user.get_daily_usage_count()}")

        # 2. Validasi & Upload S3
        original_filename, file_extension = AnalysisService._validate_file(file, analysis_type)
        
        bucket_name = current_app.config['AWS_S3_BUCKET_NAME']
        unique_id = str(uuid.uuid4())
        
        # Folder di S3: audio/user_id/... atau text/user_id/...
        s3_folder = analysis_type.lower()
        s3_file_key = f"{s3_folder}/{user_id}/{unique_id}.{file_extension}"

        try:
            file.seek(0)
            s3_client.upload_fileobj(file, bucket_name, s3_file_key)
        except Exception as e:
            current_app.logger.error(f"S3 Upload Error: {e}")
            raise RuntimeError("Gagal upload ke storage cloud")

        # 3. DB Transaction
        job = AnalysisHistory(
            user_id=user_id,
            status='PENDING',
            analysis_type=analysis_type,
            file_name_original=original_filename,
            file_location=s3_file_key
        )
        
        try:
            db.session.add(job)
            db.session.commit()
            db.session.refresh(job)
        except Exception as e:
            db.session.rollback()
            try:
                s3_client.delete_object(Bucket=bucket_name, Key=s3_file_key)
            except:
                pass
            raise RuntimeError("Gagal menyimpan data transaksi")

        # 4. Dispatch Task (VERSI FINAL - TANPA QUEUE KHUSUS)
        try:
            if analysis_type == 'AUDIO':
                # Import dari modul tasks_audio yang baru
                from celery_worker.tasks_audio import process_audio_task
                process_audio_task.apply_async(args=[job.analysis_id]) 
            
            elif analysis_type == 'TEXT':
                # Import dari modul tasks_text yang baru
                from celery_worker.tasks_text import process_text_task
                process_text_task.apply_async(args=[job.analysis_id])

            elif analysis_type == 'IMAGE':
                # Import dari modul tasks_image yang baru
                from celery_worker.tasks_image import process_image_task
                task = process_image_task.apply_async(args=[job.analysis_id])

        except ImportError as e:
             current_app.logger.warning(f"Celery task import failed: {e}")
        except Exception as e:
             current_app.logger.error(f"Gagal dispatch Celery: {e}")
        
        return {
            "message": f"File {analysis_type} diterima",
            "analysis_id": job.analysis_id,
            "status": "PENDING",
            "type": analysis_type,
            "file_name": original_filename,
            "timestamp": datetime.utcnow().isoformat()
        }

    @staticmethod
    def get_user_history(user_id):
        history_list = AnalysisHistory.query.filter_by(user_id=user_id)\
            .order_by(AnalysisHistory.created_at.desc())\
            .all()

        results = []
        for item in history_list:
            results.append({
                "analysis_id": item.analysis_id,
                "status": item.status,
                "analysis_type": item.analysis_type,
                "file_name": item.file_name_original,
                "created_at": item.created_at.isoformat(),
                "result_summary": item.result_summary if item.status == 'COMPLETED' else None
            })
        return results

    @staticmethod
    def get_job_status(user_id, analysis_id):
        job = AnalysisHistory.query.filter_by(analysis_id=analysis_id, user_id=user_id).first()
        if not job:
            return None

        response = {
            "analysis_id": job.analysis_id,
            "status": job.status,
            "created_at": job.created_at.isoformat()
        }
        
        if job.status == 'COMPLETED':
            response["result"] = job.result_summary
        elif job.status == 'FAILED':
            response["error"] = job.error_message
            
        return response