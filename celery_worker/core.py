import os
import sys
os.environ['OMP_NUM_THREADS'] = '1'

import shutil
import json
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
        self.mlflow_client = None

    DEFAULT_MANIFEST_INFO = {
        "audio": {"name": "detectify-deepfake-audio-detector", "version": "0", "local_path": "assets/models/audio/AUDIO_MODEL.pth"},
        "text_en": {"name": "detectify-text-en-logreg", "version": "0", "local_path": "assets/models/text/English/mlflow_en_text_v2"},
        "text_id": {"name": "detectify-indo-text-bi-lstm", "version": "2", "local_path": "assets/models/text/Indonesia/mlflow_id_text"},
        "image": {"name": "Image_Deepfake_Detection_Model", "version": "3", "local_path": "assets/models/image/mlflow_image_model_v3.pth"}
    }

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
                print("[CORE] WARNING: MLFLOW_TRACKING_URI is not set.")

        # Load Manifest
        self.manifest_path = os.path.join(MODEL_DIR, "models_manifest.json")
        self.manifest = self._load_manifest()

        # Initialize global MLflow Client once
        try:
            self.mlflow_client = mlflow.tracking.MlflowClient()
        except Exception as e:
            print(f"[CORE] WARNING: Failed to initialize MlflowClient - {e}")

        print(f"[CORE] Syncing & Loading ML Models on {DEVICE}")
        self._load_audio_model()
        self._load_text_model()
        self._load_image_model()
        self._is_loaded = True
        print("[Core] All Assets Loaded & Synchronized.")

    def _load_manifest(self):
        if os.path.exists(self.manifest_path):
            try:
                with open(self.manifest_path, 'r') as f:
                    return json.load(f)
            except: pass
        return {}

    def _save_manifest(self):
        try:
            os.makedirs(os.path.dirname(self.manifest_path), exist_ok=True)
            with open(self.manifest_path, 'w') as f:
                json.dump(self.manifest, f, indent=4)
        except Exception as e:
            print(f"[Core] Failed to save manifest: {e}")

    def _get_latest_version(self, client, model_name):
        """Metadata-only check for latest version in MLflow"""
        try:
            versions = client.search_model_versions(f"name='{model_name}'")
            if not versions: return None
            versions.sort(key=lambda x: int(x.version), reverse=True)
            return versions[0].version
        except: return None

    # --- Loader Sub-methods ---
    def _load_audio_model(self):
        """Standardized Sync-then-Load for Audio Model."""
        model_info = self.manifest.get("audio", self.DEFAULT_MANIFEST_INFO["audio"])
        model_name = model_info["name"]
        local_version = model_info["version"]
        local_path = os.path.join(BASE_DIR, model_info["local_path"])
        client = self.mlflow_client

        # 1. Synchronize (MLflow -> Local)
        try:
            remote_version = self._get_latest_version(client, model_name) if client else None
            
            if remote_version and (remote_version != local_version or not os.path.exists(local_path)):
                print(f"[Core] Syncing Audio Model (v{local_version} -> v{remote_version})...")
                model_uri = f"models:/{model_name}/{remote_version}"
                
                # Download .pth artifact directly
                download_uri = client.get_model_version_download_uri(model_name, remote_version)
                tmp_dir = mlflow.artifacts.download_artifacts(artifact_uri=download_uri)
                audio_pth = os.path.join(tmp_dir, "data", "model.pth")
                
                if os.path.exists(audio_pth):
                    os.makedirs(os.path.dirname(local_path), exist_ok=True)
                    if os.path.exists(local_path): os.remove(local_path)
                    shutil.copy(audio_pth, local_path)
                    
                    # Update manifest
                    self.manifest["audio"] = {"name": model_name, "version": remote_version, "local_path": model_info["local_path"]}
                    self._save_manifest()
                    local_version = remote_version # For loading below
                    print(f"[Core] Audio Model Localized (v{remote_version})")
        except Exception as e:
            print(f"[Core] Audio Sync Warning: {e}")

        # 2. Force Load from Local Asset
        try:
            if os.path.exists(local_path):
                print(f"[Core] Initializing Audio Model from Asset: {local_path} (v{local_version})")
                checkpoint = torch.load(local_path, map_location=DEVICE, weights_only=False)
                
                if not isinstance(checkpoint, dict):
                    self.audio_model = checkpoint
                else:
                    self.audio_model = SimpleAudioCNN().to(DEVICE)
                    self.audio_model.load_state_dict(checkpoint.get("model_state_dict", checkpoint))
                
                self.audio_model.eval()
                self.audio_model.to(DEVICE)
                print(f"[Core] Audio Model Ready.")
            else:
                print(f"[Core] WARNING: Audio Model local asset missing at {local_path}")
        except Exception as e:
            print(f"[Core] Audio Initialization Failed: {e}")

    def _load_text_model(self):
        """Standardized Sync-then-Load for English & Indonesian Text Models."""
        client = self.mlflow_client
        
        for lang, key in [("English", "text_en"), ("Indonesian", "text_id")]:
            try:
                model_info = self.manifest.get(key, self.DEFAULT_MANIFEST_INFO[key])
                model_name = model_info["name"]
                local_version = model_info["version"]
                local_path = os.path.join(BASE_DIR, model_info["local_path"])
                
                # 1. Synchronize (MLflow -> Local)
                try:
                    remote_version = self._get_latest_version(client, model_name) if client else None
                    
                    # Robust check: Sync if update found OR folder missing OR folder empty
                    is_empty = not os.listdir(local_path) if os.path.exists(local_path) and os.path.isdir(local_path) else True
                    if remote_version and (remote_version != local_version or is_empty):
                        print(f"[Core] Syncing {lang} Text Model (v{local_version} -> v{remote_version})...")
                        model_uri = f"models:/{model_name}/{remote_version}"
                        
                        # Indonesian Run-Id workaround for sibling artifacts
                        if key == "text_id" and client:
                            versions = client.get_latest_versions(model_name)
                            target_v = next((v for v in versions if v.version == str(remote_version)), None)
                            if target_v and target_v.run_id:
                                # Re-create local dir and download run-root artifacts
                                if os.path.exists(local_path): shutil.rmtree(local_path)
                                os.makedirs(local_path, exist_ok=True)
                                # 2. Download everything from run root using modern API
                                print(f"[Core] Downloading run {target_v.run_id} artifacts...")
                                run_tmp = mlflow.artifacts.download_artifacts(run_id=target_v.run_id, artifact_path="")
                                
                                # 3. Copy items from run root
                                items = os.listdir(run_tmp)
                                print(f"[Core] Found {len(items)} items in run artifact root.")
                                for item in items:
                                    s, d = os.path.join(run_tmp, item), os.path.join(local_path, item)
                                    if os.path.isdir(s): shutil.copytree(s, d, dirs_exist_ok=True)
                                    else: shutil.copy2(s, d)
                            else:
                                raise ValueError(f"Run ID not found for {lang} v{remote_version}")
                        else:
                            # Standard MLflow artifact download
                            tmp_dir = mlflow.artifacts.download_artifacts(artifact_uri=model_uri)
                            if os.path.exists(local_path): shutil.rmtree(local_path)
                            shutil.copytree(tmp_dir, local_path)
                            
                        # Update Manifest
                        self.manifest[key] = {"name": model_name, "version": remote_version, "local_path": model_info["local_path"]}
                        self._save_manifest()
                        local_version = remote_version
                        print(f"[Core] {lang} Asset Localized (v{remote_version})")
                except Exception as sync_err:
                    print(f"[Core] {lang} Sync Warning: {sync_err}")

                # 2. Force Load from Local Asset
                if os.path.exists(local_path):
                    print(f"[Core] Initializing {lang} Text Model from Asset (v{local_version})")
                    
                    if key == "text_en":
                        # English (Sklearn Pipeline)
                        self.en_text_model = mlflow.sklearn.load_model(local_path)
                    else:
                        # Indonesian v2.1+ Logic (Standardized: artifacts/ and code/)
                        art_root = os.path.join(local_path, "artifacts")
                        code_root = os.path.join(local_path, "code")
                        
                        bi_lstm_pkl = os.path.join(art_root, "indo_text_pipeline_bi_lstm.pkl")
                        bi_lstm_vec = os.path.join(art_root, "doc2Vec.d2v")
                        bi_lstm_pth = os.path.join(art_root, "bi_lstm.pth")

                        if os.path.exists(bi_lstm_pkl):
                            # Add Code folder to sys.path for joblib wrapper resolution
                            if code_root not in sys.path: sys.path.append(code_root)
                            
                            self.id_text_model = joblib.load(bi_lstm_pkl)
                            
                            # Load Vectorizer Component
                            if os.path.exists(bi_lstm_vec):
                                self.id_text_vectorizer = Doc2Vec.load(bi_lstm_vec)
                            
                            # Patch pipeline paths (Handle hardcoded paths from training env)
                            if hasattr(self.id_text_model, 'named_steps'):
                                for step_name, step in self.id_text_model.named_steps.items():
                                    if hasattr(step, 'model_path'):
                                        old_path = str(step.model_path).lower()
                                        if 'doc2vec' in old_path:
                                            step.model_path = bi_lstm_vec
                                            if hasattr(step, 'model'): step.model = self.id_text_vectorizer
                                        elif 'bi_lstm.pth' in old_path:
                                            step.model_path = bi_lstm_pth
                        else:
                            print(f"[Core] Indonesian .pkl pipeline not found in {art_root}")
                    
                    print(f"[Core] {lang} Text Model Ready.")
                else:
                    print(f"[Core] WARNING: {lang} Text Model local asset missing.")
            except Exception as e:
                print(f"[Core] {lang} Initialization Failed: {e}")

    
    def _load_image_model(self):
        """Standardized Sync-then-Load for Image Model."""
        model_info = self.manifest.get("image", self.DEFAULT_MANIFEST_INFO["image"])
        model_name = model_info["name"]
        local_version = model_info["version"]
        local_path = os.path.join(BASE_DIR, model_info["local_path"])
        client = self.mlflow_client

        # 1. Synchronize (MLflow -> Local)
        try:
            remote_version = self._get_latest_version(client, model_name) if client else None
            
            if remote_version and (remote_version != local_version or not os.path.exists(local_path)):
                print(f"[Core] Syncing Image Model (v{local_version} -> v{remote_version})...")
                
                mv = client.get_model_version(model_name, remote_version)
                run_id = mv.run_id
                artifact_path = "raw_models/final_model.pth"
                
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                downloaded_file = mlflow.artifacts.download_artifacts(
                    run_id=run_id, 
                    artifact_path=artifact_path,
                    dst_path=os.path.dirname(local_path)
                )
                
                if os.path.exists(local_path): os.remove(local_path)
                shutil.move(downloaded_file, local_path)
                
                raw_dir = os.path.join(os.path.dirname(local_path), "raw_models")
                if os.path.exists(raw_dir): shutil.rmtree(raw_dir)
                
                self.manifest["image"] = {"name": model_name, "version": remote_version, "local_path": model_info["local_path"]}
                self._save_manifest()
                local_version = remote_version
                print(f"[Core] Image Model Localized (v{remote_version})")
        except Exception as e:
            print(f"[Core] Image Sync Warning: {e}")

        # 2. Force Load from Local Asset
        try:
            if os.path.exists(local_path):
                print(f"[Core] Initializing Image Model from Asset: {local_path} (v{local_version})")
                self.image_model = EfficientNetV2(pretrained=False).to(DEVICE)
                checkpoint = torch.load(local_path, map_location=DEVICE, weights_only=False)
                if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
                    self.image_model.load_state_dict(checkpoint["model_state_dict"])
                else:
                    self.image_model.load_state_dict(checkpoint)
                
                self.image_model.eval()
                print(f"[Core] Image Model Ready.")
            else:
                if os.path.exists(IMAGE_MODEL_PATH):
                    print(f"[Core] Initializing Image Model from Legacy Fallback: {IMAGE_MODEL_PATH}")
                    self.image_model = EfficientNetV2(pretrained=False).to(DEVICE)
                    checkpoint = torch.load(IMAGE_MODEL_PATH, map_location=DEVICE, weights_only=False)
                    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
                        self.image_model.load_state_dict(checkpoint["model_state_dict"])
                    else:
                        self.image_model.load_state_dict(checkpoint)
                    
                    self.image_model.eval()
                else:
                    print(f"[Core] WARNING: Image Model local asset missing.")
        except Exception as e:
            print(f"[Core] Image Initialization Failed: {e}")
    
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
                # Indonesian Inference (Standard v2.1 Pipeline)
                if hasattr(self.id_text_model, 'predict_proba'):
                    # Standard Pipeline with Probabilities
                    probabilities = self.id_text_model.predict_proba([raw_text])[0]
                    # Mapping: [prob_ai, prob_human] (Indo model: 0=AI, 1=Human)
                    prob_ai = probabilities[0]
                    prob_human = probabilities[1]
                elif hasattr(self.id_text_model, 'predict'):
                    # Pipeline with only binary output (0=AI, 1=Human)
                    prediction = self.id_text_model.predict([raw_text])[0]
                    prob_ai = 1.0 if prediction == 0 else 0.0
                    prob_human = 1.0 - prob_ai
                else:
                    return {"error": "Model Teks Indonesia format v2.1+ tidak terdeteksi (Missing predict/predict_proba)."}

                # 5. Penentuan Label
                label = "FAKE" if prob_ai >= 0.5 else "REAL"
                
                # 6. Hitung Confidence Score (mengambil probabilitas tertinggi)
                confidence = prob_ai if label == "FAKE" else prob_human

                # Model name detection for display
                model_display = "Detectify_Indo_BiLSTM_v2 (Pipeline)" if hasattr(self.id_text_model, 'predict_proba') else "Detectify_Indo_BiLSTM (Legacy)"

                # Output disamakan persis dengan format English
                return {
                    "model_used": model_display,
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
            # Explicitly set to eval mode to avoid BatchNorm error with batch_size=1
            self.image_model.eval()

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