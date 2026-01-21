import os
import PyPDF2
import docx

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
                reader = PyPDF2.PdfReader(f)
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