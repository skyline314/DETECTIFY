from celery import Celery
from app import create_app, config
import os
from .core import ml_registry

def create_celery_app(config_name=os.getenv('FLASK_ENV', 'default')):
    """
    Membuat instance Celery, terhubung ke konfigurasi Flask.
    """
    
    # 1. Buat aplikasi Flask sementara hanya untuk mendapatkan konfigurasinya
    flask_app = create_app(config_name)
    
    # 2. Buat instance Celery
    celery_app = Celery(
        __name__,
        broker=flask_app.config['CELERY_BROKER_URL'],
        backend=flask_app.config['CELERY_RESULT_BACKEND'],
        include=[
            'celery_worker.tasks_audio', # Load modul Audio
            'celery_worker.tasks_text',  # Load modul Text
            'celery_worker.tasks_image', # Load modul Image
            'celery_worker.tasks_video',  # Load modul Video
            'celery_worker.tasks_humanize' # Load modul Humanize
        ]
    )
    
    # 3. Sinkronkan konfigurasi Celery dari Flask
    # celery_app.conf.update(flask_app.config)

    celery_app.flask_app = flask_app

    # 4. Buat "Task Context"
    class ContextTask(celery_app.Task):
        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
                return self.run(*args, **kwargs)

    celery_app.Task = ContextTask
    
    return celery_app

# Inisialisasi Global 
celery = create_celery_app()

# Temukan dan daftarkan tasks.py
celery.autodiscover_tasks(['celery_worker'])

from .core import ml_registry
with celery.flask_app.app_context():
    ml_registry.load_assets()