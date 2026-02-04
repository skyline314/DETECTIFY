from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import analysis_bp
from .services import AnalysisService 
from app.decorators import premium_required
from io import BytesIO

# ENDPOINT UPLOAD AUDIO 
@analysis_bp.route('/analysis/audio', methods=['POST'])
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
@analysis_bp.route('/analysis/text', methods=['POST'])
@jwt_required()
def upload_text():
    # Cek apakah user mengirim file
    if 'file' not in request.files:
        return jsonify({"error": "Tidak ada file dokumen yang dikirim"}), 400
        
    file = request.files['file']
    user_id = get_jwt_identity()

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
@analysis_bp.route('/analysis/image', methods=['POST'])
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

# ENDPOINT UPLOAD VIDEO
@analysis_bp.route('/analysis/video', methods=['POST'])
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
@analysis_bp.route('/analysis/humanize', methods=['POST'])
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
@analysis_bp.route('/analysis/<string:analysis_id>', methods=['GET'])
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