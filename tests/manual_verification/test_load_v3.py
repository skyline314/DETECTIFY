import mlflow.pytorch
import torch
import sys
import os
from dotenv import load_dotenv

load_dotenv()

try:
    print("Attempting to load models:/detectify-deepfake-audio-detector/3")
    m = mlflow.pytorch.load_model('models:/detectify-deepfake-audio-detector/3')
    print("Loaded successfully!")
    print(f"Type: {type(m)}")
    print(f"Has eval? {hasattr(m, 'eval')}")
    print(f"Has forward? {hasattr(m, 'forward')}")
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)
