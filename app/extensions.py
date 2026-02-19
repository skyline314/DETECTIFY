from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate
from flask_mail import Mail
from boto3 import Session
from botocore.config import Config
import os

# 1. Inisialisasi Database (SQLAlchemy) & Migrasi
db = SQLAlchemy()
migrate = Migrate()

# 2. Inisialisasi JWT (Otentikasi)
jwt = JWTManager()

# 3. Inisialisasi CORS (Cross-Origin Resource Sharing) dan FLask_Mail
cors = CORS()
mail = Mail()

# 4. Inisialisasi Sesi Boto3 (AWS S3)
s3_client = None

def init_s3_client(app):
    """
    Fungsi helper untuk menginisialisasi S3 client setelah app dibuat,
    karena kita butuh config dari app.
    """
    global s3_client
    
    # Konfigurasi untuk S3, misal region
    # s3_config = Config(
    #     region_name=app.config.get('AWS_S3_REGION', 'ap-southeast-1') 
    # )

    session = Session(
        aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY']
        # config=s3_config  # jika butuh region
    )
    
    s3_client = session.client('s3')
    app.config['S3_CLIENT'] = s3_client

# 5. Inisialisasi Prometheus Metrics (Monitoring)
# Import di dalam fungsi atau global tergantung kebutuhan, tapi extension biasanya global
from prometheus_flask_exporter import PrometheusMetrics
metrics = PrometheusMetrics(app=None) # Lazy init