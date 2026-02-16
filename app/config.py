import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path=ENV_PATH)

class Config:
    """
    Konfigurasi dasar (Base) yang akan digunakan oleh semua lingkungan.
    Rahasia DIMUAT dari .env, BUKAN ditulis di sini.
    """

    # Flask & Keamanan
    SECRET_KEY = os.getenv('SECRET_KEY')
    DEBUG = False
    TESTING = False

    # JWT (Otentikasi) 
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    # Bisa tambahkan konfigurasi JWT lain di sini (misal: waktu kedaluwarsa token)

    # DATABASE
    raw_db_url = os.getenv('DATABASE_URL', '')
    
    # Perbaikan Dialek: SQLAlchemy butuh postgresql:// bukan postgres://
    if raw_db_url and raw_db_url.startswith("postgres://"):
        raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)
    
    
    # connection string di sini dari variabel di atas
    SQLALCHEMY_DATABASE_URI = raw_db_url
    
    # Nonaktifkan event tracking dari SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,  # Cek koneksi sebelum digunakan
        "pool_recycle": 1800,   # Reset koneksi setiap 30 menit
        "pool_size": 10,        # Jumlah koneksi maksimal
        "max_overflow": 20      # Toleransi kelebihan koneksi
    }

    # Celery (Async Tasks)
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND')

    # AWS S3 (Object Storage)
    AWS_S3_BUCKET_NAME = os.getenv('AWS_S3_BUCKET_NAME')
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

    # MAIL
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

    #LIMIT
    LIMIT_DAILY = os.environ.get('LIMIT_DAILY')

    # PRICE
    PREMIUM_PRICE = os.environ.get('PREMIUM_PRICE')

    # MIDTRANS
    MIDTRANS_CLIENT_KEY = os.environ.get('MIDTRANS_CLIENT_KEY')
    MIDTRANS_IS_PRODUCTION = os.environ.get('MIDTRANS_IS_PRODUCTION', 'False') == 'True'


class DevelopmentConfig(Config):
    """
    Konfigurasi khusus untuk Development.
    Mewarisi (inherits) dari Config dasar.
    """
    DEBUG = True
    DATABASE_URL="sqlite:///detectify_local.db"


class ProductionConfig(Config):
    """
    Konfigurasi khusus untuk Production.
    Mewarisi (inherits) dari Config dasar.
    """
    DEBUG = False
    # Di production, menggunakan variabel env yang berbeda
    # DB_USER = os.getenv('PROD_DB_USER')
    # ... dll

class TestingConfig(Config):
    """Konfigurasi khusus untuk Unit Testing."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_ENGINE_OPTIONS = {}

# Dictionary untuk memetakan string ke class Konfigurasi
# Ini akan digunakan oleh Application Factory (di __init__.py)
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,  
    'default': DevelopmentConfig
}