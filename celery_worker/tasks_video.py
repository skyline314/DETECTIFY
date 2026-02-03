import os
import cv2
from collections import Counter
from .celery_app import celery
from .core import ml_registry 
from app.models import AnalysisHistory
from app.extensions import db
from .utils import s3_temp_file, cleanup_s3

@celery.task(name='process_video_task')
def process_video_task(analysis_id):
    """
    Worker Video: Menggunakan model Image (EfficientNetV2) dengan Majority Voting.
    Alur: S3 -> Temp File -> OpenCV Frame Extraction -> Predict (Core) -> Voting -> Save DB -> Cleanup
    """
    print(f"[Worker] Starting Video Job: {analysis_id}")
    
    # 1. Ambil Data Job dari DB
    job = AnalysisHistory.query.filter_by(analysis_id=analysis_id).first()
    if not job:
        print(f"[Worker] Error: Job ID {analysis_id} not found in DB.")
        return

    try:
        # 2. Update Status -> PROCESSING
        job.status = 'PROCESSING'
        db.session.commit()

        # 3. Download Video dari S3 ke Lokal Sementara
        with s3_temp_file(job.file_location) as temp_path:
            cap = cv2.VideoCapture(temp_path)
            
            frame_results = []
            confidences = []
            
            # Optimasi: Skip frame agar proses tidak terlalu lama (misal: ambil setiap 1 detik)
            # Asumsi video 30 FPS, maka FRAME_SKIP = 30
            FRAME_SKIP = 30 
            frame_count = 0
            processed_frames = 0
            MAX_FRAMES_TO_ANALYZE = 20 # Batasi jumlah frame maksimal untuk stabilitas

            while cap.isOpened() and processed_frames < MAX_FRAMES_TO_ANALYZE:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_count % FRAME_SKIP == 0:
                    # Kirim frame langsung ke core.py (proses di memori/RAM)
                    res = ml_registry.predict_video_frame(frame)
                    
                    if "error" in res:
                        continue # Skip frame jika error
                        
                    frame_results.append(res["prediction"])
                    confidences.append(res["confidence"])
                    processed_frames += 1
                
                frame_count += 1

            cap.release()

            if not frame_results:
                raise ValueError("Gagal mengekstrak frame yang valid dari video.")

            # 4. Majority Voting (Logika Inti)
            vote_result = Counter(frame_results)
            final_prediction = vote_result.most_common(1)[0][0]
            avg_confidence = sum(confidences) / len(confidences)

            # Susun data hasil akhir
            result_data = {
                "prediction": final_prediction,
                "confidence_score": round(avg_confidence, 2),
                "details": {
                    "total_frames_analyzed": processed_frames,
                    "vote_distribution": dict(vote_result)
                }
            }
            
            # 5. Update Status -> COMPLETED
            job.status = 'COMPLETED'
            job.result_summary = result_data
            db.session.commit()
            print(f"[Worker] Video Job {analysis_id} SUCCESS with prediction: {final_prediction}")

    except Exception as e:
        print(f"[Worker] Video Job Failed: {e}")
        db.session.rollback()
        job.status = 'FAILED'
        job.error_message = str(e)
        db.session.commit()

    finally:
        # 6. Cleanup S3 dan Storage Lokal 
        cleanup_s3(job.file_location)