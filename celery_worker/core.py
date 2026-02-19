import os
os.environ['OMP_NUM_THREADS'] = '1'

import joblib
import mlflow.sklearn
import pandas as pd
import numpy as np
import librosa
import re
import string
import torch
import torchaudio
import torch.nn.functional as F
import torch.nn as nn
import soundfile
from collections import Counter
from torchvision import transforms
from PIL import Image
from timm import create_model
import cv2
from gensim.models.doc2vec import Doc2Vec
from gensim.utils import simple_preprocess
import boto3

###########################################################################################################
# GLOBAL CONFIGURATION & PATHS

# CONFIG & PATHS 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
MODEL_DIR = os.path.join(ASSETS_DIR, 'models')
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# AUDIO
AUDIO_MODEL_PATH = os.path.join(MODEL_DIR, 'audio', 'AUDIO_MODEL.pth')
AUDIO_MODEL = None

# TEXT
TEXT_MODEL_DIR = os.path.join(MODEL_DIR, 'text') 
ENGLISH_TEXT_MODEL_PATH = os.path.join(TEXT_MODEL_DIR, 'English', 'logistic_regression' ,'log_reg_model.pkl')
ENGLISH_TEXT_VECTORIZER_PATH = os.path.join(TEXT_MODEL_DIR, 'English', 'logistic_regression' ,'tfidf_vectorizer.pkl')

INDONESIAN_TEXT_MODEL_PATH = os.path.join(TEXT_MODEL_DIR, 'Indonesia', 'bi_lstm.pth')
INDONESIAN_TEXT_VECTORIZER_PATH = os.path.join(TEXT_MODEL_DIR, 'Indonesia', 'doc2Vec.d2v')
# tf.config.set_visible_devices([], 'GPU')


# IMAGE
IMAGE_MODEL_PATH = os.path.join(MODEL_DIR, 'image', 'IMAGE_MODEL.pth')

###########################################################################################################

# HELPER FUNCTIONS 
def clean_text(text):
    """
    Cleaning function untuk Text Analysis (untuk XGBoost pipeline)
    """
    text = str(text).lower()
    # Remove square brackets
    text = re.sub(r'\[.*?\]', '', text)
    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    # Remove punctuation
    text = re.sub(r'[%s]' % re.escape(string.punctuation), ' ', text)
    # Remove newlines
    text = re.sub(r'\n', ' ', text)
    # Remove words containing numbers
    text = re.sub(r'\w*\d\w*', '', text)
    return text

def text_preprocessing_id(text):
    """Preprocessing khusus Bahasa Indonesia"""
    text = text.replace('-', ' ')
    text = re.sub(r'[\r\xa0\t]', '', text)
    text = re.sub(r"http\S+|www\S+", '', text)
    text = re.sub(r'\b\w*\.com\w*\b', '', text)
    text = re.sub(r'\[.*?\]|\(.*?\}|\{.*?\}', '', text)
    text = re.sub(r'\b(\w+)/(\w+)\b', r'\1 atau \2', text)
    text = re.sub(r'@[A-Za-z0-9]+|#[A-Za-z0-9]+', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return text.strip()

def ensure_model_exists(s3_key, local_path):
    """Fungsi untuk mengunduh model dari AWS S3 jika tidak ada di lokal."""
    if not os.path.exists(local_path):
        print(f"[S3] Mengunduh aset dari S3: {s3_key} -> {local_path}...")
        try:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            s3 = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            s3.download_file(os.getenv('AWS_S3_BUCKET_NAME'), s3_key, local_path)
            print(f"[S3] Selesai mengunduh ke {local_path}")
        except Exception as e:
            print(f"[S3] Gagal mengunduh {s3_key}: {e}")

###########################################################################################################

# MODEL CLASSES

class SimpleAudioCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.spec_layer = torchaudio.transforms.MelSpectrogram(
            sample_rate=16000, n_fft=1024, hop_length=256, n_mels=64
        )
        self.to_db = torchaudio.transforms.AmplitudeToDB()
        self.conv_layers = nn.Sequential(
            nn.Conv2d(1, 16, 3, padding=1), nn.BatchNorm2d(16), nn.ReLU(), nn.MaxPool2d(2, 2),
            nn.Conv2d(16, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(), nn.MaxPool2d(2, 2),
            nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(), nn.MaxPool2d(2, 2),
            nn.Conv2d(64, 128, 3, padding=1), nn.BatchNorm2d(128), nn.ReLU(), 
            nn.AdaptiveAvgPool2d((4, 4))
        )
        self.flatten = nn.Flatten()
        self.fc = nn.Sequential(
            nn.Linear(128 * 4 * 4, 128), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(128, 2)
        )

    def forward(self, x):
        x = self.spec_layer(x)
        x = self.to_db(x)
        x = self.conv_layers(x)
        x = self.flatten(x)
        x = self.fc(x)
        return x
    

class EfficientNetV2(nn.Module):
    def __init__(self, num_classes=1, dropout_rate=0.3, pretrained=False):
        super().__init__()
        self.base_model = create_model(
            "tf_efficientnetv2_l",
            pretrained=pretrained,
            num_classes=0
        )

        num_features = self.base_model.num_features

        self.classifier = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(num_features, 512),
            nn.SiLU(),
            nn.BatchNorm1d(512),
            nn.Dropout(dropout_rate),
            nn.Linear(512, num_classes)
        )

    def forward(self, x):
        features = self.base_model.forward_features(x)
        out = self.classifier(features)
        return out.squeeze(1)
    

class BiLSTM(nn.Module):
    def __init__(self, hidden_dim=50, num_layers=4, dropout=0.2):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=1,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            dropout=dropout,
            bidirectional=True,
            batch_first=True
        )
        self.fc = nn.Linear(hidden_dim * 2, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        out, _ = self.lstm(x)
        out = out[:, -1, :]  # Ambil output dari timestep terakhir
        out = self.fc(out)
        return self.sigmoid(out)

###########################################################################################################
# REGISTRY CORE

class ModelRegistry:
    """
    Kelas tunggal untuk mengelola pemuatan aset ML dan prediksi.
    Menerapkan Lazy Loading agar hemat memori saat idle.
    """
    def __init__(self):
        # Audio Assets
        self.audio_model = None
        
        # Text Assets
        self.en_text_model = None
        # self.en_text_vectorizer = None # Removed: Included in MLflow Pipeline
        self.id_text_model = None
        self.id_text_vectorizer = None

        # Image Assets
        self.image_model = None
        
        self._is_loaded = False

    def load_assets(self):
        """Metode utama pemuatan aset (Entry Point)."""
        if self._is_loaded:
            return
        
        # Ensure Env Vars are loaded for MLflow
        if not os.getenv("MLFLOW_TRACKING_URI"):
            from app.config import Config
            if Config.MLFLOW_TRACKING_URI:
                os.environ["MLFLOW_TRACKING_URI"] = Config.MLFLOW_TRACKING_URI
                os.environ["MLFLOW_TRACKING_USERNAME"] = Config.MLFLOW_TRACKING_USERNAME or ""
                os.environ["MLFLOW_TRACKING_PASSWORD"] = Config.MLFLOW_TRACKING_PASSWORD or ""
            else:
                print("[CORE] WARNING: MLFLOW_TRACKING_URI is not set in Environment or Config. MLflow model loading may fail.")

        print(f"[CORE] Loading ML Models on {DEVICE}")
        self._load_audio_model()
        self._load_text_model()
        self._load_image_model()
        self._is_loaded = True
        print("[Core] All Assets Loaded.")

    # --- Loader Sub-methods ---
    def _load_audio_model(self):
        ensure_model_exists("assets/models/audio/AUDIO_MODEL.pth", AUDIO_MODEL_PATH)
        try:
            if os.path.exists(AUDIO_MODEL_PATH):
                print(f"[Core] Loading Audio Model from: {AUDIO_MODEL_PATH}")
                self.audio_model = SimpleAudioCNN().to(DEVICE)
                self.audio_model.load_state_dict(torch.load(AUDIO_MODEL_PATH, map_location=DEVICE, weights_only=True))
                self.audio_model.eval()
        except Exception as e:
            print(f"[Core]  Error loading Audio Model: {e}")

    def _load_text_model(self):
        # Load English Model (MLflow Pipeline)
        try:
            model_name = "detectify-text-en-logreg"
            version = "2" # Gunakan versi terbaru yang sudah diverifikasi (Pipeline)
            model_uri = f"models:/{model_name}/{version}"
            
            print(f"[Core] Loading English Text Model from MLflow: {model_uri}")
            self.en_text_model = mlflow.sklearn.load_model(model_uri)
            print(f"[Core] Loaded English Text Model (Pipeline)")
            
        except Exception as e:
            print(f"[Core] Error loading English Text Model from MLflow: {e}")
            # Fallback logic could go here if needed


        # Load indonesia model
        try:
            ensure_model_exists("assets/models/text/Indonesia/bi_lstm.pth", INDONESIAN_TEXT_MODEL_PATH)
            ensure_model_exists("assets/models/text/Indonesia/doc2Vec.d2v", INDONESIAN_TEXT_VECTORIZER_PATH)
            
            # PENTING: Download file .npy pendamping Doc2Vec
            ensure_model_exists("assets/models/text/Indonesia/doc2vec.d2v.wv.vectors.npy", INDONESIAN_TEXT_VECTORIZER_PATH + ".wv.vectors.npy")
            ensure_model_exists("assets/models/text/Indonesia/doc2vec.d2v.syn1neg.npy", INDONESIAN_TEXT_VECTORIZER_PATH + ".syn1neg.npy")
            if os.path.exists(INDONESIAN_TEXT_MODEL_PATH) and os.path.exists(INDONESIAN_TEXT_VECTORIZER_PATH):
                    # Load Doc2Vec
                    self.id_text_vectorizer = Doc2Vec.load(INDONESIAN_TEXT_VECTORIZER_PATH)
                    
                    # Load PyTorch Model
                    self.id_text_model = BiLSTM().to(DEVICE)
                    self.id_text_model.load_state_dict(torch.load(INDONESIAN_TEXT_MODEL_PATH, map_location=DEVICE, weights_only=True))
                    self.id_text_model.eval()
                    
                    print(f"[Core] Loaded PyTorch Text Model: Indonesian Text Detection")
        except Exception as e:
            print(f"[Core] Error loading Text Models: {e}")

    
    def _load_image_model(self):
        try:
            ensure_model_exists("assets/models/image/IMAGE_MODEL.pth", IMAGE_MODEL_PATH)
            
            if os.path.exists(IMAGE_MODEL_PATH):
                self.image_model = EfficientNetV2(pretrained=False).to(DEVICE)
                checkpoint = torch.load(IMAGE_MODEL_PATH, map_location=DEVICE, weights_only=True)
                
                # Handle dictionary vs full model save
                if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
                    self.image_model.load_state_dict(checkpoint["model_state_dict"])
                else:
                    self.image_model.load_state_dict(checkpoint)
                
                self.image_model.eval()
                print(f"[Core] Image Model Loaded")
        except Exception as e:
            print(f"[Core] Error loading Image Model: {e}")
    
    # --- Audio Inference Sub-methods ---

    def _preprocess_audio(self, file_path):
        waveform, sample_rate = torchaudio.load(file_path, backend='soundfile')
        if sample_rate != 16000:
            waveform = torchaudio.transforms.Resample(sample_rate, 16000)(waveform)
        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)
        return waveform
    
    def _segment_audio(self, waveform):
        segment_len = 16000 * 4
        total_len = waveform.shape[1]
        segments = []
        if total_len <= segment_len:
            segments.append(F.pad(waveform, (0, segment_len - total_len)))
        else:
            for i in range(0, total_len - segment_len + 1, segment_len):
                segments.append(waveform[:, i : i + segment_len])
            if total_len % segment_len != 0:
                segments.append(waveform[:, -segment_len:])
        return segments

    def predict_audio(self, file_path):
        """
        Melakukan prediksi Audio Deepfake.
        Input: Path file audio 
        Output: Dictionary hasil prediksi.
        """
        if not self._is_loaded: self.load_assets()
        
        if self.audio_model is None:
            return {"error": "Model Audio tidak tersedia/gagal dimuat."}

        try:
            # Preprocess and Segementation
            waveform = self._preprocess_audio(file_path)
            segments = self._segment_audio(waveform)

            # Prediction Loop
            segment_preds = []
            total_confidence = 0.0

            with torch.no_grad():
                for seg in segments:
                    seg_input = seg.unsqueeze(0).to(DEVICE)
                    output = self.audio_model(seg_input)
                    prob = F.softmax(output, dim=1)
                    pred = torch.max(output, 1)[1].item()
                    
                    segment_preds.append(pred)
                    total_confidence += prob[0][pred].item()

            # Majority Voting
            # Label: 0 = REAL, 1 = FAKE (Asumsi dari training notebook)
            vote_result = Counter(segment_preds)
            final_pred_idx = vote_result.most_common(1)[0][0]
            avg_confidence = (total_confidence / len(segments)) * 100
            label = "FAKE" if final_pred_idx == 1 else "REAL"
            
            return {
                "model_used": "Detectify_Audio_CNN_v2",
                "prediction": label,
                "confidence_score": round(avg_confidence, 2),
                "details": {
                    "segments_total": len(segments),
                    "segments_fake": vote_result[1],
                    "segments_real": vote_result[0]
                }
            }

        except Exception as e:
            return {"error": f"Audio prediction failed: {str(e)}"}
        
    
    def predict_text(self, raw_text, language='en'):
        """
        Melakukan prediksi Teks Deepfake. (ENGLSIH:en & INDONESIAN:id)
        Input: Raw String text.
        Output: Dictionary hasil prediksi.
        """
        if not self._is_loaded: self.load_assets()
        if not raw_text or len(raw_text.strip()) < 10:
            return {"error": "Teks terlalu pendek (Minimal 10 karakter)."}

        # Predict
        if language == 'en':
            if not getattr(self, 'en_text_model', None):
                return {"error": "Model Teks English tidak tersedia."}
            try:
                processed_text = clean_text(raw_text)
                
                # Pipeline expects an iterable (list), returns numpy array
                # self.en_text_model (Pipeline) handles vectorization internally
                prediction = self.en_text_model.predict([processed_text])[0]
                probabilities = self.en_text_model.predict_proba([processed_text])[0]
                
                # Mapping: 0 = Human/REAL, 1 = AI/FAKE
                label = "FAKE" if prediction == 1 else "REAL"
                confidence = probabilities[1] if prediction == 1 else probabilities[0]

                return {
                    "model_used": f"Detectify_Text_LogReg_v2 (MLflow)",
                    "prediction": label,
                    "confidence_score": float(confidence), 
                    "language": "English",
                    "probability_ai": float(probabilities[1]),
                    "probability_human": float(probabilities[0])
                }
            except Exception as e:
                return {"error": f"Text prediction failed: {str(e)}"}
        elif language == 'id':
            if not getattr(self, 'id_text_model', None) or not getattr(self, 'id_text_vectorizer', None):
                return {"error": "Model Teks Indonesia tidak tersedia."}
            try: 
                # 1. Preprocessing
                clean_txt = text_preprocessing_id(raw_text)
                words = simple_preprocess(clean_txt)

                # 2. Vectorization (Doc2Vec)
                vector = self.id_text_vectorizer.infer_vector(words, epochs=20)

                # 3. Reshape untuk LSTM (Batch, Seq_Len, Input_Dim) -> (1, 1000, 1)
                vector_tensor = torch.tensor(vector, dtype=torch.float32).view(1, 1000, 1).to(DEVICE)

                # 4. Inference
                with torch.no_grad():
                    prob_human = self.id_text_model(vector_tensor).item()
                
                prob_ai = 1.0 - prob_human

                # 5. Penentuan Label
                label = "FAKE" if prob_ai >= 0.5 else "REAL"
                
                # 6. Hitung Confidence Score (mengambil probabilitas tertinggi)
                confidence = prob_ai if label == "FAKE" else prob_human

                # Output disamakan persis dengan format English
                return {
                    "model_used": "Detectify_Text_BiLSTM_PyTorch",
                    "prediction": label,
                    "confidence_score": float(confidence), 
                    "language": "Indonesian",
                    "probability_ai": float(prob_ai),
                    "probability_human": float(prob_human)
                }
            except Exception as e:
                return {"error": f"Text prediction failed: {str(e)}"}
        else:
            return {"error": "Language not supported"}
                

    def predict_image(self, image_path):
        """
        Prediksi Image Deepfake (EfficientNetV2)
        """
        if not self._is_loaded: self.load_assets()
        if self.image_model is None: return {"error": "Model Image Not Found"}

        try:
            # Cek apakah input adalah path (str) atau sudah berupa objek Image
            if isinstance(image_path, str):
                # Jika String: Ini adalah alur S3/Image 
                img = Image.open(image_path).convert("RGB")
            else:
                # Jika bukan String: Ini adalah alur Video (Frame sudah di RAM)
                img = image_path.convert("RGB")

            # 1. Transformasi (Wajib sama dengan Training)
            transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
            ])

            # 2. Preprocess
            img_tensor = transform(img).unsqueeze(0).to(DEVICE)

            # 3. Predict
            with torch.no_grad():
                logit = self.image_model(img_tensor)
                prob = torch.sigmoid(logit).item() # 0.0 - 1.0

            # 4. Threshold Logic 
            FAKE_THRESHOLD = 0.40
            REAL_THRESHOLD = 0.25
            
            if prob >= FAKE_THRESHOLD:
                label = "FAKE"
                status = "High Confidence"
                final_conf = prob
            elif prob <= REAL_THRESHOLD:
                label = "REAL"
                status = "High Confidence"
                final_conf = 1 - prob 
            else:
                label = "SUSPICIOUS"
                status = "Uncertain"
                final_conf = 0.5 

            return {
                "prediction": label,
                "confidence": round(final_conf * 100, 2),
                "status": status,
                "raw_score": round(prob, 4)
            }
        except Exception as e:
            return {"error": f"Image Error: {str(e)}"}
        
    def predict_video_frame(self, frame_array):
        """
        Menerjemahkan array OpenCV menjadi PIL Image untuk predict_image.
        """
        # OpenCV (BGR) -> RGB
        frame_rgb = cv2.cvtColor(frame_array, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        
        # Kirim ke predict_image sebagai objek
        return self.predict_image(img)
    
    def humanize_text(self, text, language='en'):
        import requests
        OLLAMA_URL = "http://localhost:11434/api/generate" 
        
        # Penyesuaian instruksi agar hasil hanya berupa teks mentah
        if language == 'id':
            prompt = f"""
            Anda adalah editor profesional dan penulis berpengalaman.
            Tugas Anda adalah menulis ulang teks berikut agar terdengar alami, lancar, dan manusiawi dalam Bahasa Indonesia.
            Gunakan gaya bahasa yang natural (tidak kaku, tidak terkesan AI), pertahankan makna asli, dan jangan menambahkan informasi baru.

            PENTING: Tampilkan hasil tulis ulang saja secara langsung. Jangan sertakan kalimat pembuka, penjelasan, atau penutup apa pun.

            Teks:
            {text}
            """
        else:
            prompt = f"""
            You are a professional editor and experienced writer.
            Rewrite the following text so it sounds natural, fluent, and human-written in English.
            Avoid robotic or AI-like phrasing. Preserve the original meaning and do not add new information.

            IMPORTANT: Provide only the rewritten text directly. Do not include any introductory remarks, explanations, or conversational filler.

            Text:
            {text}
            """

        try:
            payload = {"model": "llama3", "prompt": prompt, "stream": False}
            response = requests.post(OLLAMA_URL, json=payload, timeout=120)
            result_text = response.json().get("response", "").strip()

            prefixes = ["Here is the rewritten text:", "Here's the rewritten version:", "Tentu, ini hasilnya:"]
            for p in prefixes:
                if result_text.lower().startswith(p.lower()):
                    result_text = result_text[len(p):].strip()
            
            # Mengembalikan dictionary agar konsisten dengan polling di console.html
            return {"humanized_text": result_text}
            
        except Exception as e:
            return {"error": f"Humanizer Error: {str(e)}", "humanized_text": "Gagal memproses teks."}

# Global Registry Instance  
ml_registry = ModelRegistry()