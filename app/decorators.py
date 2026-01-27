from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from app.models import User
from app.analysis.services import AnalysisService

def premium_required(fn):
    """
    Decorator: Hanya izinkan jika user memiliki plan 'PREMIUM'.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user_id = get_jwt_identity()
        
        # Cek User di DB
        user = User.query.filter_by(user_id=current_user_id).first()
        if not user:
            return jsonify({"error": "User tidak ditemukan"}), 404
        
        is_premium = user.is_premium_active()
            
        # Logika Subscription
        if not is_premium:
            usage = AnalysisService.get_daily_usage(user.user_id)
            limit = 3

            if usage >= limit:
                return jsonify({
                    "error": "Limit Reached",
                    "message": f"Kuota harian gratis ({limit}) sudah habis. Silakan upgrade ke Premium."
                }), 403
            
        return fn(*args, **kwargs)
    
    return wrapper