import uuid
import os
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, Transaction, db
import midtransclient

payment_bp = Blueprint('payment', __name__)

def get_midtrans_snap():
    """Helper untuk koneksi ke Midtrans Snap API"""
    snap = midtransclient.Snap(
        is_production=os.getenv('MIDTRANS_IS_PRODUCTION') == 'True',
        server_key=os.getenv('MIDTRANS_SERVER_KEY')
    )
    return snap

# 1. CREATE TRANSACTION (Frontend Minta Token)
@payment_bp.route('/create-transaction', methods=['POST'])
@jwt_required()
def create_transaction():
    # Ambil identity dari token JWT
    current_user_id = get_jwt_identity()
    
    # Query user berdasarkan user id
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"error": "User tidak ditemukan"}), 404

    # Harga Paket (untuk sementara nanti akan diupdate)
    amount = 50000 
    

    safe_uid = str(user.user_id)[:8]
    
    # Format Order ID: ORDER-{UID}-{RANDOM}
    order_id = f"ORDER-{safe_uid}-{uuid.uuid4().hex[:6]}"
    
    # Parameter untuk Midtrans
    param = {
        "transaction_details": {
            "order_id": order_id,
            "gross_amount": amount
        },
        "customer_details": {
            "first_name": user.username,
            "email": user.email,
        },
        "item_details": [{
            "id": "PLAN-PREMIUM",
            "price": amount,
            "quantity": 1,
            "name": "Detectify Premium Plan"
        }]
    }

    try:
        # Minta Token ke Midtrans
        snap = get_midtrans_snap()
        transaction = snap.create_transaction(param)
        snap_token = transaction['token']
        redirect_url = transaction['redirect_url']


        new_trx = Transaction(
            order_id=order_id,
            amount=amount,
            user_id=user.user_id, 
            snap_token=snap_token,
            status='pending'
        )
        db.session.add(new_trx)
        db.session.commit()

        return jsonify({
            "token": snap_token,
            "redirect_url": redirect_url,
            "order_id": order_id
        })

    except Exception as e:
        print(f"Midtrans Error: {e}")
        return jsonify({"error": f"Gagal memproses pembayaran: {str(e)}"}), 500


# 2. WEBHOOK (Midtrans Feedback)
@payment_bp.route('/notification', methods=['POST'])
def midtrans_notification():
    try:
        notification_body = request.get_json()
        
        order_id = notification_body.get('order_id')
        transaction_status = notification_body.get('transaction_status')
        fraud_status = notification_body.get('fraud_status')

        print(f"Payment Notif: {order_id} -> {transaction_status}")

        # Cari transaksi di database kita
        trx = Transaction.query.filter_by(order_id=order_id).first()
        if not trx:
            return jsonify({"status": "order not found"}), 404

        # Logika Status Midtrans
        if transaction_status == 'capture':
            if fraud_status == 'challenge':
                trx.status = 'challenge'
            else:
                trx.status = 'success'
                activate_premium(trx.user_id) 
        
        elif transaction_status == 'settlement':
            trx.status = 'success'
            activate_premium(trx.user_id)
            
        elif transaction_status in ['cancel', 'deny', 'expire']:
            trx.status = 'failed'
            
        elif transaction_status == 'pending':
            trx.status = 'pending'

        db.session.commit()
        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print(f"Webhook Error: {e}")
        return jsonify({"status": "error"}), 500

def activate_premium(user_id):
    """Fungsi helper untuk upgrade user jadi Premium"""
    from datetime import timedelta, datetime
    
    # Query pakai user_id
    user = User.query.get(user_id)
    if user:
        user.plan = 'premium'
        user.subscription_end = datetime.utcnow() + timedelta(days=30)
        print(f"User {user.username} upgraded to Premium!")