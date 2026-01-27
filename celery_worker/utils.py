import os
import tempfile
from contextlib import contextmanager
from app.extensions import s3_client
from flask import current_app
import pypdf
import docx

@contextmanager
def s3_temp_file(file_location):
    """Context manager untuk download S3 ke lokal dan hapus otomatis."""
    bucket_name = current_app.config['AWS_S3_BUCKET_NAME']
    ext = os.path.splitext(file_location)[1]
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        s3_response = s3_client.get_object(Bucket=bucket_name, Key=file_location)
        tmp.write(s3_response['Body'].read())
        tmp_path = tmp.name
        
    try:
        yield tmp_path
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def cleanup_s3(file_location):
    """Hapus file di S3 setelah sukses diproses."""
    bucket_name = current_app.config['AWS_S3_BUCKET_NAME']
    try:
        s3_client.delete_object(Bucket=bucket_name, Key=file_location)
    except Exception as e:
        print(f"[Worker] S3 Cleanup Warning: {e}")

def extract_text_from_file(file_path):
    """
    Mengekstrak teks mentah dari file .txt, .pdf, atau .docx
    """
    ext = os.path.splitext(file_path)[1].lower()
    text = ""

    try:
        if ext == '.txt':
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        
        elif ext == '.pdf':
            with open(file_path, 'rb') as f:
                reader = pypdf.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
        
        elif ext == '.docx':
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        
        else:
            raise ValueError("Unsupported file format")

        return text.strip()
    
    except Exception as e:
        raise RuntimeError(f"Gagal membaca dokumen: {str(e)}")