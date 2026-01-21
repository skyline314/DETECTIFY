from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from app.models import User

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
            
        # Logika Subscription
        if str(user.plan.name) != 'PREMIUM': 
            return jsonify({
                "error": "Upgrade Required",
                "message": "Fitur ini khusus untuk akun Premium."
            }), 403
            
        return fn(*args, **kwargs)
    return wrapper