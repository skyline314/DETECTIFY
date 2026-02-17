import os
import pypdf
import docx

def extract_text_from_file_object(file, filename):
    """
    Ekstrak text dari file object (Storage/Memory).
    """
    ext = os.path.splitext(filename)[1].lower()
    text = ""
    
    try:
        if ext == '.txt':
            text = file.read().decode('utf-8', errors='ignore')
            
        elif ext == '.pdf':
            reader = pypdf.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
                
        elif ext == '.docx':
            doc = docx.Document(file)
            for para in doc.paragraphs:
                text += para.text + "\n"
                
        else:
            raise ValueError("Unsupported file format")
            
        # Cleanup known artifacts
        text = text.replace("Top of Form", "").replace("Bottom of Form", "")
        return text.strip()
    except Exception as e:
        raise RuntimeError(f"Gagal membaca dokumen: {str(e)}")
