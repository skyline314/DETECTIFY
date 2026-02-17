from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import analysis_bp
from .services import AnalysisService 
from app.decorators import premium_required
from io import BytesIO
from flask import render_template

@analysis_bp.route('/')
def index():
    # Menampilkan file app/templates/index.html
    return render_template('index.html')

@analysis_bp.route('/application')
def apps():
    # Menampilkan file app/templates/apps.html
    return render_template('apps.html')

@analysis_bp.route('/audio-detection')
def audio_ui():
    # Menampilkan file app/templates/audio.html
    return render_template('audio.html')

@analysis_bp.route('/image-detection')
def image_ui():
    return render_template('image.html')

@analysis_bp.route('/video-detection')
def video_ui():
    return render_template('video.html')

@analysis_bp.route('/text-detection')
def text_ui():
    return render_template('text.html')

@analysis_bp.route('/humanize')
def humanize_ui():
    return render_template('humanize.html')

@analysis_bp.route('/history-page')
def history_page():
    return render_template('history.html')


# ENDPOINT UPLOAD AUDIO 
@analysis_bp.route('/audio', methods=['POST'])
@jwt_required()
def upload_audio():
    # Cek apakah user mengirim file
    if 'file' not in request.files:
        return jsonify({"error": "Tidak ada file yang dikirim"}), 400
        
    file = request.files['file']
    user_id = get_jwt_identity()

    try:
        # Panggil service dengan tipe 'AUDIO'
        result = AnalysisService.process_upload(user_id, file, 'AUDIO')
        return jsonify(result), 202
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Internal Error", "details": str(e)}), 500


# ENDPOINT UPLOAD TEXT
@analysis_bp.route('/text', methods=['POST'])
@jwt_required()
def upload_text():
    # Cek apakah user mengirim file
    if 'file' not in request.files:
        return jsonify({"error": "Tidak ada file dokumen yang dikirim"}), 400
        
    file = request.files['file']
    language = request.form.get('language', 'en')
    user_id = get_jwt_identity()

    file.filename = f"{language}_{file.filename}"

    try:
        # Panggil service dengan tipe 'TEXT'
        result = AnalysisService.process_upload(user_id, file, 'TEXT')
        return jsonify(result), 202
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Internal Error", "details": str(e)}), 500
    

# ENDPOINT UPLOAD IMAGE    
@analysis_bp.route('/image', methods=['POST'])
@jwt_required()
def upload_image():
    # Cek apakah user mengirim file
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
        
    file = request.files['file']
    user_id = get_jwt_identity()

    try:
        # Panggil Service dengan tipe 'IMAGE'
        result = AnalysisService.process_upload(user_id, file, 'IMAGE')
        return jsonify(result), 202
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Internal Error", "details": str(e)}), 500

@analysis_bp.route('/text/extract', methods=['POST'])
@jwt_required()
def extract_text():
    """Helper untuk ekstrak text dari file document (DOCX, PDF, TXT)"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
        
    try:
        # Import local utils (hindari circular import jika ada)
        from .utils import extract_text_from_file_object
        from io import BytesIO
        
        # Read file into memory to ensure it's seekable for docx/pypdf
        file_content = BytesIO(file.read())
        
        text = extract_text_from_file_object(file_content, file.filename)
        return jsonify({"text": text}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ENDPOINT UPLOAD VIDEO
@analysis_bp.route('/video', methods=['POST'])
@jwt_required()
def upload_video():
    # Cek apakah user mengirim file
    if 'file' not in request.files:
        return jsonify({"error": "Tidak ada file video yang dikirim"}), 400
        
    file = request.files['file']
    user_id = get_jwt_identity()

    try:
        result = AnalysisService.process_upload(user_id, file, 'VIDEO')
        return jsonify(result), 202
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Internal Error", "details": str(e)}), 500

# ENDPOINT HUMANIZE
@analysis_bp.route('/humanize', methods=['POST'])
@jwt_required()
def humanize_text():
    data = request.get_json()
    text_content = data.get('text')
    language = data.get('language', 'en') # id atau en
    user_id = get_jwt_identity()

    if not text_content:
        return jsonify({"error": "Teks tidak boleh kosong"}), 400

    # Buat file virtual dengan nama manual_text.input sesuai sistem sebelumnya
    # Tambahkan prefix bahasa agar task bisa mendeteksi
    filename = f"{language}_Humanize.txt"
    file_obj = BytesIO(text_content.encode('utf-8'))
    file_obj.filename = filename

    try:
        result = AnalysisService.process_upload(user_id, file_obj, 'HUMANIZE')
        return jsonify(result), 202
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ENDPOINT HISTORY 
@analysis_bp.route('/history', methods=['GET'])
@jwt_required()
def get_history():
    user_id = get_jwt_identity()
    try:
        results = AnalysisService.get_user_history(user_id)
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": "Gagal mengambil riwayat", "details": str(e)}), 500

# ENDPOINT STATUS
@analysis_bp.route('/status/<string:analysis_id>', methods=['GET'])
@jwt_required()
def get_analysis_status(analysis_id):
    user_id = get_jwt_identity()
    try:
        result = AnalysisService.get_job_status(user_id, analysis_id)
        if not result:
            return jsonify({"error": "Tidak ditemukan"}), 404
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": "Gagal cek status", "details": str(e)}), 500