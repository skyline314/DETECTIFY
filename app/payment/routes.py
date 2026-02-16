import hashlib
import uuid
import os
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, Transaction, db
import midtransclient
from flask import render_template

payment_bp = Blueprint('payment', __name__)

@payment_bp.route('/pricing')
def pricing():
    price = int(current_app.config.get('PREMIUM_PRICE', 100000))
    limit = int(current_app.config.get('LIMIT_DAILY', 3))
    midtrans_client_key = current_app.config.get('MIDTRANS_CLIENT_KEY', '')
    midtrans_is_production = current_app.config.get('MIDTRANS_IS_PRODUCTION', False)
    return render_template('pricing.html',
        premium_price=price,
        daily_limit=limit,
        midtrans_client_key=midtrans_client_key,
        midtrans_is_production=midtrans_is_production
    )

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
    """
    Endpoint untuk mengawali pembayaran. 
    Menghasilkan Snap Token untuk digunakan di Frontend.
    """
    # Ambil identity dari token JWT
    current_user_id = get_jwt_identity()
    
    # Query user berdasarkan user id
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"error": "User tidak ditemukan"}), 404

    # Harga Paket 
    amount = int(current_app.config.get('PREMIUM_PRICE') or 100000)

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
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Midtrans Create Error: {str(e)}")
        return jsonify({"error": "Gagal membuat transaksi"}), 500


# 2. WEBHOOK (Midtrans Feedback)
@payment_bp.route('/notification', methods=['POST'])
def midtrans_notification():
    """
    Webhook yang dipanggil oleh Midtrans secara asinkron.
    Menangani update status transaksi dan aktivasi premium.
    """

    data = request.get_json()
    if not data:
        return jsonify({"error": "Empty payload"}), 400

    try:
        order_id = data.get('order_id')
        status_code = data.get('status_code')
        gross_amount = data.get('gross_amount')
        signature_from_midtrans = data.get('signature_key')
        server_key = current_app.config.get('MIDTRANS_SERVER_KEY')

        #  VERIFIKASI SIGNATURE
        # Format: SHA512(order_id + status_code + gross_amount + ServerKey)
        payload = f"{order_id}{status_code}{gross_amount}{server_key}"
        calc_signature = hashlib.sha512(payload.encode()).hexdigest()

        if calc_signature != signature_from_midtrans:
            current_app.logger.warning(f"[SECURITY] Invalid Signature for Order: {order_id}")
            return jsonify({"status": "invalid signature"}), 403

        # PROSES TRANSAKSI
        trx = Transaction.query.filter_by(order_id=order_id).first()
        if not trx:
            return jsonify({"status": "order not found"}), 404

        # Idempotency check: Jangan proses jika sudah sukses
        if trx.status == 'success':
            return jsonify({"status": "already processed"}), 200
        
        transaction_status = data.get('transaction_status')
        fraud_status = data.get('fraud_status')

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
        db.session.rollback()
        current_app.logger.error(f"Webhook Error: {str(e)}")
        return jsonify({"status": "error"}), 500

# HELPER FUNCTION

def activate_premium(user_id):
    """Fungsi helper untuk upgrade user jadi Premium"""
    from datetime import timedelta, datetime
    
    # Query pakai user_id
    user = User.query.get(user_id)
    if not user:
        return False

    now = datetime.utcnow()

    if user.is_premium and user.premium_expiry and user.premium_expiry > now:
        user.premium_expiry += timedelta(days=30)
    else:
        user.is_premium = True
        user.premium_expiry = now + timedelta(days=30)

    print(f"[Premium] User {user_id} is now PREMIUM until {user.premium_expiry}")
    return True