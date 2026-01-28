from flask import request, jsonify, current_app, url_for
from . import auth_bp
from app.models import User
from app.extensions import db, mail
from flask_mail import Message
from flask_jwt_extended import create_access_token
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime, timedelta, timezone
from flask import render_template
import resend
import os


def generate_confirmation_token(email):
    """Membuat token aman yang berisi email user."""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-confirm-salt')

def confirm_token(token, expiration=86400):
    """
    Membaca token balik menjadi email.
    Default expiration: 86400 detik (24 jam).
    """
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt='email-confirm-salt',
            max_age=expiration
        )
    except Exception:
        return False
    return email

def send_email(to, subject, body):
    """Mengirim email (dibungkus try-except agar app tidak crash jika gagal)."""
    resend.api_key = os.environ.get("RESEND_API_KEY")
    try:
        from_email = "Detectify <no-reply@detectify-app.online>"

        msg = {
            "from": from_email,
            "to": [to],
            "subject": subject,
            "html": body,
        }

        resend.Emails.send(msg)
        print(f" [EMAIL] Berhasil dikirim via API ke {to}", flush=True)
        return True
    except Exception as e:
        print(f" [EMAIL] GAGAL mengirim via API ke {to}: {str(e)}", flush=True)
        return False


@auth_bp.route('/register', methods=['POST'])
def register_user():
    try:
        data = request.get_json()
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({"error": "Email dan password diperlukan"}), 400

        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        

        # 1. Cek apakah email sudah terdaftar dan semua sudah di isi
        if not username or not email or not password:
            return jsonify({"error": "Username, Email, dan Password wajib diisi!"}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email ini sudah terdaftar"}), 409
        
        if User.query.filter_by(username=username).first():
            return jsonify({"error": "Username ini sudah digunakan, pilih yang lain"}), 409
    
        # 2. Simpan User Baru (Default is_verified=False)
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        # 3. Proses Token & Email 
        try:
            # Generate Token
            token = generate_confirmation_token(new_user.email)
            
            # # DEBUG: Print Token ke Terminal 
            # print("="*50)
            # print(f"DEBUG TOKEN (Copy ini): {token}")
            # print("="*50)

            # Buat Link Verifikasi
            # Link akan berbentuk: baseurl/auth/verify/<token>
            verify_url = url_for('auth.verify_email', token=token, _external=True)
            
            # Kirim Email
            html_body = f"""
            <p>Halo,</p>
            <p>Terima kasih telah mendaftar di Detectify.</p>
            <p>Silakan klik link di bawah untuk memverifikasi akun Anda:</p>
            <a href="{verify_url}">Verifikasi Akun Saya</a>
            <br>
            <p>Link ini berlaku selama 24 jam.</p>
            """
            send_email(new_user.email, "Verifikasi Email Detectify", html_body)
            
        except Exception as e:
            # Jika email gagal, jangan batalkan registrasi, tapi log errornya
            print(f"Error saat proses email/token: {e}")

        return jsonify({
            "message": "Registrasi berhasil. Silakan cek email (atau terminal) untuk verifikasi.",
            "user_id": new_user.user_id
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Critical Error Register: {e}")
        return jsonify({"error": "Terjadi kesalahan internal"}), 500


@auth_bp.route('/verify/<token>', methods=['GET'])
def verify_email(token):
    """
    Endpoint ini dipanggil saat user mengklik link di email.
    Format URL: /auth/verify/<token_panjang>
    """
    try:
        email = confirm_token(token)
        if not email:
            return jsonify({"error": "Link verifikasi tidak valid atau sudah kadaluarsa."}), 400
        
        user = User.query.filter_by(email=email).first_or_404()
        
        if user.is_verified:
            return jsonify({"message": "Akun sudah terverifikasi sebelumnya."}), 200

        # Update Status Verifikasi
        user.is_verified = True
        user.updated_at = db.func.now()
        db.session.commit()
        
        return jsonify({"message": "Selamat! Email berhasil diverifikasi. Silakan login."}), 200

    except Exception as e:
        return jsonify({"error": "Terjadi kesalahan saat verifikasi", "details": str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login_user():
    try:
        data = request.get_json(silent=True)
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({"error": "Email dan password diperlukan"}), 400

        email = data.get('email')
        password = data.get('password')

        user = User.query.filter_by(email=email).first()

        # Cek User Ada & Password Cocok
        if not user or not user.check_password(password):
            return jsonify({"error": "Email atau password salah"}), 401 
        
        if not user.is_verified:
            return jsonify({
                "error": "Akun belum diverifikasi", 
                "message": "Silakan cek email Anda untuk memverifikasi akun sebelum login."
            }), 403

        access_token = create_access_token(identity=user.user_id)
        return jsonify(access_token=access_token), 200

    except Exception as e:
        print(f"ERROR LOGIN: {e}") 
        return jsonify({"error": "Terjadi kesalahan internal"}), 500
    

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """
    User mengirim email, server mengirim link reset password.
    """
    try:
        data = request.get_json()
        email = data.get('email')
        if not email:
            return jsonify({"error": "Email diperlukan"}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            # Demi keamanan, jangan beritahu jika email tidak ditemukan
            # Tetap return 200 agar hacker tidak bisa menebak email yang terdaftar
            return jsonify({"message": "Jika email terdaftar, link reset akan dikirim."}), 200

        # 1. Generate Token Unik (Kita pakai token hex sederhana untuk DB)
        # Note: Bisa pakai JWT/Serializer, tapi karena kita punya kolom DB, 
        # kita pakai random string saja biar beda variasi.
        import secrets
        reset_token = secrets.token_hex(32)
        
        # 2. Simpan ke Database
        user.reset_token = reset_token
        # Token berlaku 1 jam
        user.reset_token_expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        db.session.commit()

        # 3. Kirim Email
        # DEBUG: 
        # print("="*50)
        # print(f"DEBUG RESET TOKEN (Copy ini): {reset_token}")
        # print("="*50)
        # ----------------------------------------------

        # Note: Di frontend nanti URL-nya biasanya mengarah ke halaman React/Vue
        # Tapi untuk API testing, kita anggap user mengirim tokennya mentah-mentah
        send_email(
            to=user.email,
            subject="Reset Password Detectify",
            body=f"Token Reset Password Anda: {reset_token} \n\nToken ini berlaku 1 jam."
        )

        return jsonify({"message": "Jika email terdaftar, link reset akan dikirim."}), 200

    except Exception as e:
        print(f"Error Forgot Password: {e}")
        return jsonify({"error": "Terjadi kesalahan internal"}), 500


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """
    User mengirim token & password baru.
    """
    try:
        data = request.get_json()
        token = data.get('token')
        new_password = data.get('new_password')

        if not token or not new_password:
            return jsonify({"error": "Token dan password baru diperlukan"}), 400

        # 1. Cari User berdasarkan Token
        user = User.query.filter_by(reset_token=token).first()

        if not user:
            return jsonify({"error": "Token tidak valid atau salah"}), 400

        # 2. Cek Kadaluarsa
        if user.reset_token_expiration < datetime.utcnow():
            return jsonify({"error": "Token sudah kadaluarsa. Silakan request ulang."}), 400

        # 3. Update Password
        user.set_password(new_password)
        
        # 4. Hapus Token (Supaya tidak bisa dipakai lagi)
        user.reset_token = None
        user.reset_token_expiration = None
        
        db.session.commit()

        return jsonify({"message": "Password berhasil diubah. Silakan login."}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error Reset Password: {e}")
        return jsonify({"error": "Terjadi kesalahan internal"}), 500
    

@auth_bp.route('/console')
def developer_console():
    return render_template('console.html')