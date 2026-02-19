from flask import request, jsonify, current_app, url_for, redirect
from . import auth_bp
from app.models import User
from app.extensions import db, mail
from flask_mail import Message
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime, timedelta, timezone
from flask import render_template
import resend
import os
import secrets


@auth_bp.route('/get-started')
def auth_page():
    # Menampilkan file app/templates/auth.html
    return render_template('auth.html')


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    """Return the current user's profile info from JWT."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({
        "username": user.username,
        "email": user.email,
        "plan": user.plan.value if user.plan else "free",
        "daily_limit": int(current_app.config.get('LIMIT_DAILY') or 5)
    }), 200


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
    """Mengirim email via Resend API."""
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
        print(f" [EMAIL] Success sent via API to {to}", flush=True)
        return True
    except Exception as e:
        print(f" [EMAIL] Failed to send via API to {to}: {str(e)}", flush=True)
        return False


@auth_bp.route('/register', methods=['POST'])
def register_user():
    try:
        data = request.get_json()
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({"error": "Email and password are required"}), 400

        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        # 1. Cek apakah email sudah terdaftar dan semua sudah di isi
        if not username or not email or not password:
            return jsonify({"error": "Username, Email, and Password are required"}), 400
        
        existing_email_user = User.query.filter_by(email=email).first()
        new_user = None

        if existing_email_user:
            if existing_email_user.is_verified:
                return jsonify({"error": "Email already exists"}), 409
            else:
                # User exists but NOT verified. Allow overwrite.
                # Check if username is taken by another separate user
                if User.query.filter(User.username == username, User.user_id != existing_email_user.user_id).first():
                    return jsonify({"error": "Username already exists, please choose another"}), 409
                
                # Overwrite existing unverified user
                new_user = existing_email_user
                new_user.username = username
                new_user.set_password(password)
                new_user.updated_at = datetime.now(timezone.utc)
        else:
            # New User
            if User.query.filter_by(username=username).first():
                return jsonify({"error": "Username already exists, please choose another"}), 409
        
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
        
        db.session.commit()

        # 3. Proses Token & Email 
        try:
            # Generate Token
            token = generate_confirmation_token(new_user.email)

            # Buat Link Verifikasi
            verify_url = url_for('auth.verify_email', token=token, _external=True)
            
            # Kirim Email
            html_body = f"""
            <div style="max-width:480px;margin:0 auto;font-family:Arial,sans-serif;padding:20px">
                <h2 style="color:#0ea5c7">Verify Email Detectify</h2>
                <p>Hello <strong>{new_user.username}</strong>,</p>
                <p>Thank you for registering with Detectify. Click the button below to verify your account:</p>
                <div style="text-align:center;margin:24px 0">
                    <a href="{verify_url}" style="display:inline-block;padding:14px 32px;background:linear-gradient(135deg,#0ea5c7,#7c3aed);color:#fff;text-decoration:none;border-radius:999px;font-weight:bold;font-size:15px">
                        Verify My Account
                    </a>
                </div>
                <p style="font-size:13px;color:#9ca3af">This link is valid for 24 hours.</p>
                <p style="font-size:12px;color:#9ca3af">— Detectify Team</p>
            </div>
            """
            send_email(new_user.email, "Verify Email Detectify", html_body)
            
        except Exception as e:
            # Jika email gagal, jangan batalkan registrasi, tapi log errornya
            print(f"Error saat proses email/token: {e}")

        return jsonify({
            "message": "Registration successful. Please check your email for verification.",
            "user_id": new_user.user_id
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Critical Error Register: {e}")
        return jsonify({"error": "Internal server error"}), 500


@auth_bp.route('/verify/<token>', methods=['GET'])
def verify_email(token):
    """
    User clicks verification link from email.
    Redirect to auth page with status query param.
    """
    try:
        email = confirm_token(token)
        if not email:
            return redirect('/auth/get-started?verified=error&msg=Token+is+invalid+or+expired')
        
        user = User.query.filter_by(email=email).first()
        if not user:
            return redirect('/auth/get-started?verified=error&msg=User+not+found')
        
        if user.is_verified:
            return redirect('/auth/get-started?verified=already&msg=Account+already+verified')

        # Update Status Verifikasi
        user.is_verified = True
        user.updated_at = db.func.now()
        db.session.commit()
        
        return redirect('/auth/get-started?verified=success&msg=Email+has+been+verified!+Please+login.')

    except Exception as e:
        return redirect('/auth/get-started?verified=error&msg=Error+occurred+during+verification')


@auth_bp.route('/login', methods=['POST'])
def login_user():
    try:
        data = request.get_json(silent=True)
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({"error": "Email and password are required"}), 400

        email = data.get('email')
        password = data.get('password')

        user = User.query.filter_by(email=email).first()

        # Cek User Ada & Password Cocok
        if not user or not user.check_password(password):
            return jsonify({"error": "Wrong Email or Password, please check again"}), 401 
        
        if not user.is_verified:
            return jsonify({
                "error": "Account not verified", 
                "message": "Please verify your account before logging in."
            }), 403

        access_token = create_access_token(identity=user.user_id)
        return jsonify(access_token=access_token), 200

    except Exception as e:
        print(f"ERROR LOGIN: {e}") 
        return jsonify({"error": "Internal server error"}), 500
    

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """
    User mengirim email, server mengirim link reset password.
    """
    try:
        data = request.get_json()
        email = data.get('email')
        if not email:
            return jsonify({"error": "Email is required"}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"message": "If email is registered, reset link will be sent."}), 200

        # 1. Generate Token
        reset_token = secrets.token_hex(32)
        
        # 2. Simpan ke Database
        user.reset_token = reset_token
        user.reset_token_expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        db.session.commit()

        # 3. Build reset link
        reset_url = url_for('auth.reset_password_page', token=reset_token, _external=True)

        # 4. Kirim Email dengan link
        send_email(
            to=user.email,
            subject="Reset Password Detectify",
            body=f"""
            <div style="max-width:480px;margin:0 auto;font-family:Arial,sans-serif;padding:20px">
                <h2 style="color:#0ea5c7">Reset Password Detectify</h2>
                <p>You received this email because a password reset request was made for your account.</p>
                <p>Click the button below to create a new password:</p>
                <div style="text-align:center;margin:24px 0">
                    <a href="{reset_url}" style="display:inline-block;padding:14px 32px;background:linear-gradient(135deg,#0ea5c7,#7c3aed);color:#fff;text-decoration:none;border-radius:999px;font-weight:bold;font-size:15px">
                        Reset Password
                    </a>
                </div>
                <p style="font-size:13px;color:#9ca3af">This link is valid for <strong>1 hour</strong>.</p>
                <p style="font-size:13px;color:#9ca3af">If you did not request a password reset, ignore this email.</p>
                <p style="font-size:12px;color:#9ca3af">— Detectify Team</p>
            </div>
            """
        )

        return jsonify({"message": "If email is registered, reset link will be sent."}), 200

    except Exception as e:
        print(f"Error Forgot Password: {e}")
        return jsonify({"error": "Internal server error"}), 500


@auth_bp.route('/reset-password-page/<token>', methods=['GET'])
def reset_password_page(token):
    """
    Page where user enters new password after clicking reset link.
    """
    # Validate token exists
    user = User.query.filter_by(reset_token=token).first()
    if not user:
        return redirect('/auth/get-started?verified=error&msg=Token+reset+is+invalid')
    
    # Check expiration (handle naive vs aware datetime)
    now = datetime.utcnow()
    expiry = user.reset_token_expiration.replace(tzinfo=None) if user.reset_token_expiration.tzinfo else user.reset_token_expiration
    if expiry < now:
        return redirect('/auth/get-started?verified=error&msg=Token+is+expired')
    
    return render_template('reset_password.html', token=token)


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
            return jsonify({"error": "Token and new password are required"}), 400

        # 1. Cari User berdasarkan Token
        user = User.query.filter_by(reset_token=token).first()

        if not user:
            return jsonify({"error": "Token is invalid or expired"}), 400

        # 2. Cek Kadaluarsa (handle naive vs aware datetime)
        now = datetime.utcnow()
        expiry = user.reset_token_expiration.replace(tzinfo=None) if user.reset_token_expiration.tzinfo else user.reset_token_expiration
        if expiry < now:
            return jsonify({"error": "Token is expired. Please request again."}), 400

        # 3. Update Password
        user.set_password(new_password)
        
        # 4. Hapus Token
        user.reset_token = None
        user.reset_token_expiration = None
        
        db.session.commit()

        return jsonify({"message": "Password has been changed. Please login."}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error Reset Password: {e}")
        return jsonify({"error": "Internal server error"}), 500


@auth_bp.route('/change-username', methods=['POST'])
@jwt_required()
def change_username():
    """
    User mengirim username baru, server mengganti username jika tidak duplikat.
    """
    try:
        data = request.get_json()
        new_username = data.get('new_username')

        if not new_username:
            return jsonify({"error": "New username is required"}), 400
        
        # 1. Cari User saat ini
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # 2. Cek apakah username baru sama dengan yang lama
        if user.username == new_username:
            return jsonify({"message": "Username is the same"}), 200

        # 3. Cek apakah username baru sudah dipakai orang lain
        existing_user = User.query.filter_by(username=new_username).first()
        if existing_user:
            return jsonify({"error": "Username already exists, please choose another"}), 409

        # 4. Update Username
        user.username = new_username
        user.updated_at = datetime.now(timezone.utc)
        
        db.session.commit()

        return jsonify({"message": "Username has been changed.", "new_username": new_username}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error Change Username: {e}")
        return jsonify({"error": "Internal server error"}), 500