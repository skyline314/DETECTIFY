import os
os.environ['OMP_NUM_THREADS'] = '1'

import joblib
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
import tensorflow as tf
from gensim.models.doc2vec import Doc2Vec

###########################################################################################################
# GLOBAL CONFIGURATION & PATHS

# CONFIG & PATHS 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
MODEL_DIR = os.path.join(ASSETS_DIR, 'models')

# AUDIO
AUDIO_MODEL_PATH = os.path.join(MODEL_DIR, 'audio', 'AUDIO_MODEL.pth')
AUDIO_MODEL = None
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# TEXT
TEXT_MODEL_DIR = os.path.join(MODEL_DIR, 'text') 
ENGLISH_TEXT_MODEL_PATH = os.path.join(TEXT_MODEL_DIR, 'English', 'logistic_regression' ,'log_reg_model.pkl')
ENGLISH_TEXT_VECTORIZER_PATH = os.path.join(TEXT_MODEL_DIR, 'English', 'logistic_regression' ,'tfidf_vectorizer.pkl')
INDONESIAN_TEXT_MODEL_PATH = os.path.join(TEXT_MODEL_DIR, 'Indonesia', 'bi_lstm.h5')
INDONESIAN_TEXT_VECTORIZER_PATH = os.path.join(TEXT_MODEL_DIR, 'Indonesia', 'doc2Vec.d2v')

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
        self.en_text_vectorizer = None
        self.id_text_model = None
        self.id_text_vectorizer = None

        # Image Assets
        self.image_model = None
        
        self._is_loaded = False

    def load_assets(self):
        """Metode utama pemuatan aset (Entry Point)."""
        if self._is_loaded:
            return
        
        print(f"[CORE] Loading ML Models on {DEVICE}")
        self._load_audio_model()
        self._load_text_model()
        self._load_image_model()
        self._is_loaded = True
        print("[Core] All Assets Loaded.")

    # --- Loader Sub-methods ---
    def _load_audio_model(self):
        try:
            if os.path.exists(AUDIO_MODEL_PATH):
                print(f"[Core] Loading Audio Model from: {AUDIO_MODEL_PATH}")
                self.audio_model = SimpleAudioCNN().to(DEVICE)
                self.audio_model.load_state_dict(torch.load(AUDIO_MODEL_PATH, map_location=DEVICE, weights_only=True))
                self.audio_model.eval()
        except Exception as e:
            print(f"[Core]  Error loading Audio Model: {e}")

    def _load_text_model(self):
        # Load englsih model
        try:
            if os.path.exists(ENGLISH_TEXT_MODEL_PATH) and os.path.exists(ENGLISH_TEXT_VECTORIZER_PATH):
                    self.en_text_model = joblib.load(ENGLISH_TEXT_MODEL_PATH)
                    self.en_text_vectorizer = joblib.load(ENGLISH_TEXT_VECTORIZER_PATH)
                    print(f"[Core] Loaded Text Model: Englsih Text Detection")
        except Exception as e:
            print(f"[Core] Error loading Text Models: {e}")

        # Load indonesia model
        try:
            if os.path.exists(INDONESIAN_TEXT_MODEL_PATH) and os.path.exists(INDONESIAN_TEXT_VECTORIZER_PATH):
                    self.id_text_model = tf.keras.models.load_model(INDONESIAN_TEXT_MODEL_PATH)
                    self.id_text_vectorizer = Doc2Vec.load(INDONESIAN_TEXT_VECTORIZER_PATH)
                    print(f"[Core] Loaded Text Model: Indonesian Text Detection")
        except Exception as e:
            print(f"[Core] Error loading Text Models: {e}")

    
    def _load_image_model(self):
        try:
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
        if not self.text_model or not self.text_vectorizer: return {"error": "Model Teks tidak tersedia."}

        # Predict
        if language == 'en':
            try:
                processed_text = clean_text(raw_text)
                text_vectorized = self.en_text_vectorizer.transform([processed_text])
                prediction = self.en_text_model.predict(text_vectorized)[0]
                probabilities = self.en_text_model.predict_proba(text_vectorized)[0]
                
                # Mapping: 0 = Human/REAL, 1 = AI/FAKE
                label = "FAKE" if prediction == 1 else "REAL"
                confidence = probabilities[1] if prediction == 1 else probabilities[0]

                return {
                    "model_used": f"Detectify_Text_Logistic_Regression",
                    "prediction": label,
                    "confidence_score": float(confidence), 
                    "probability_ai": float(probabilities[1]),
                    "probability_human": float(probabilities[0])
                }
            except Exception as e:
                return {"error": f"Text prediction failed: {str(e)}"}
        elif language == 'id':
            try: 
                vector = self.id_text_vectorizer.infer_vector(raw_text.split())
                vector = np.expand_dims(vector, axis=0)
                
                prediction = self.id_text_model.predict(vector)[0][0]
                label = "FAKE" if prediction >= 0.5 else "REAL"
                confidence = prediction if label == "FAKE" else 1 - prediction
                
                return {
                    "prediction": label,
                    "confidence_score": round(float(confidence) * 100, 2),
                    "model_used": "Indo_BiLSTM_Doc2Vec",
                    "language": "Indonesian"
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