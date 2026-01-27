from .extensions import db
from sqlalchemy.dialects.postgresql import ENUM, JSON
from sqlalchemy import text
import uuid
import enum
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    

    # KOMPATIBEL DENGAN MIDTRANS
    # default 'free', nanti diubah jadi 'premium'
    plan = db.Column(db.String(20), default='free', nullable=False)
    subscription_end = db.Column(db.DateTime, nullable=True) # Kapan premium habis
    
    created_at = db.Column(db.TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    # updated_at = db.Column(db.TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')) #mysql
    updated_at = db.Column(db.TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'), onupdate=datetime.utcnow)

    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiration = db.Column(db.TIMESTAMP, nullable=True)

    # Relasi
    history = db.relationship('AnalysisHistory', backref='user', lazy=True, cascade="all, delete-orphan")
    transactions = db.relationship('Transaction', backref='user', lazy=True)

    # Hitung Penggunaan Hari Ini
    def get_daily_usage_count(self):
        from .models import AnalysisHistory  # Import lokal untuk hindari circular import
        
        # Tentukan awal hari ini (jam 00:00:00)
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Hitung jumlah analisis user ini sejak jam 00:00 tadi
        count = AnalysisHistory.query.filter_by(user_id=self.user_id)\
            .filter(AnalysisHistory.created_at >= today_start)\
            .count()
            
        return count

    # Helper: Cek Izin 
    def can_analyze(self):
        # Jika Premium, bebas tanpa batas
        if self.plan == 'premium':
            return True
            
        # Jika Free, batasi (3 kali sehari)
        LIMIT_HARIAN = 3 
        return self.get_daily_usage_count() < LIMIT_HARIAN

    def __repr__(self):
        return f'<User {self.email} [{self.plan}]>'
    
    def set_password(self, password):
        """Logika hashing terpusat di sini."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    

class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(50), unique=True, nullable=False) # ID unik dari kita (misal: ORDER-12345)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending') # pending, success, failed, expired
    payment_type = db.Column(db.String(50)) # gopay, bank_transfer, dll
    snap_token = db.Column(db.String(255)) # Token dari Midtrans
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=False)

    def __repr__(self):
        return f'<Transaction {self.order_id} - {self.status}>'


class AnalysisHistory(db.Model):
    __tablename__ = 'analysishistory'

    # id = db.Column(db.Integer, primary_key=True) # DUPLIKASI PK, komen dulu

    analysis_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    
    status = db.Column(
        ENUM('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='analysis_status_enum'), 
        nullable=False, 
        default='PENDING'
    )
    
    analysis_type = db.Column(
        ENUM('AUDIO', 'VIDEO', 'TEXT', 'IMAGE', name='analysis_type_enum'), 
        nullable=False
    )
    
    file_name_original = db.Column(db.String(255), nullable=True)
    file_location = db.Column(db.String(1024), nullable=False)
    result_summary = db.Column(JSON, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    # updated_at = db.Column(db.TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    updated_at = db.Column(db.TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'), onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<AnalysisHistory {self.analysis_id} [{self.status}]>'