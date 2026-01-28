import uuid
import logging
from werkzeug.utils import secure_filename
from datetime import datetime, time, timezone
from flask import current_app
from app.extensions import db, s3_client
from app.models import AnalysisHistory, db

class AnalysisService:
    ALLOWED_EXTENSIONS = {
        'AUDIO': {'mp3', 'wav', 'flac'},
        'TEXT': {'txt', 'pdf', 'docx'},
        'IMAGE': {'jpg', 'jpeg', 'png'}
    }

    @staticmethod
    def get_daily_usage(user_id):
        """
        Menghitung jumlah analisis yang dilakukan user dalam 24 jam terakhir.
        """
        today_start = datetime.combine(datetime.now(timezone.utc).date(), time.min)
        return AnalysisHistory.query.filter(
            AnalysisHistory.user_id == user_id,
            AnalysisHistory.created_at >= today_start
        ).count()

    @classmethod
    def process_upload(cls, user_id, file, analysis_type):
        """Entry point utama untuk proses upload."""
        # 1. Validasi Awal (User & File)
        user = cls._get_and_validate_user(user_id)
        original_filename, ext = cls._validate_file(file, analysis_type)
        
        # 2. Upload ke S3
        s3_file_key = cls._handle_s3_upload(file, user_id, analysis_type, ext)

        # 3. Simpan ke Database (Atomic)
        try:
            job = cls._create_analysis_job(user_id, analysis_type, original_filename, s3_file_key)
            db.session.commit()
            db.session.refresh(job)
        except Exception as e:
            db.session.rollback()
            cls._rollback_s3(s3_file_key) # Hapus file di S3 jika DB gagal
            raise RuntimeError("Gagal menyimpan data transaksi")

        # 4. Kirim ke Celery Worker
        cls._dispatch_task(job)
        
        return cls._format_response(job, original_filename)

    @staticmethod
    def _get_and_validate_user(user_id):
        from app.models import User

        user = db.session.get(User, user_id)
        if not user:
            raise ValueError("User tidak ditemukan")
        
        # jike premium langsung bisa
        if user.is_premium_active():
            return user
        
        # jika tidak hitung limit
        usage_count = AnalysisService.get_daily_usage(user_id)
        limit = int(current_app.config.get('LIMIT_DAILY'))
        if usage_count >= limit: 
            raise PermissionError("Kuota harian habis.")
            
        return user
    
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
    def _handle_s3_upload(file, user_id, analysis_type, ext):
        bucket_name = current_app.config['AWS_S3_BUCKET_NAME']
        s3_key = f"{analysis_type.lower()}/{user_id}/{uuid.uuid4()}.{ext}"
        try:
            file.seek(0)
            s3_client.upload_fileobj(file, bucket_name, s3_key)
            return s3_key
        except Exception as e:
            current_app.logger.error(f"S3 Upload Error: {e}")
            raise RuntimeError("Gagal upload ke storage cloud")

    @staticmethod
    def _create_analysis_job(user_id, analysis_type, original_filename, s3_key):
        job = AnalysisHistory(
            user_id=user_id,
            status='PENDING',
            analysis_type=analysis_type,
            file_name_original=original_filename,
            file_location=s3_key
        )
        db.session.add(job)
        return job

    @staticmethod
    def _rollback_s3(s3_key):
        try:
            bucket = current_app.config['AWS_S3_BUCKET_NAME']
            s3_client.delete_object(Bucket=bucket, Key=s3_key)
        except:
            pass

    @staticmethod
    def _dispatch_task(job):
        """Pusat kontrol pengiriman tugas ke Celery."""
        try:
            if job.analysis_type == 'AUDIO':
                from celery_worker.tasks_audio import process_audio_task
                process_audio_task.apply_async(args=[job.analysis_id])
            elif job.analysis_type == 'TEXT':
                from celery_worker.tasks_text import process_text_task
                process_text_task.apply_async(args=[job.analysis_id])
            elif job.analysis_type == 'IMAGE':
                from celery_worker.tasks_image import process_image_task
                process_image_task.apply_async(args=[job.analysis_id])
        except Exception as e:
            current_app.logger.error(f"Celery Dispatch Error: {e}")

    @staticmethod
    def _format_response(job, filename):
        return {
            "analysis_id": job.analysis_id,
            "status": "PENDING",
            "file_name": filename,
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