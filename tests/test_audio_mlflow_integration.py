import pytest
import os
import sys
from dotenv import load_dotenv

# Ensure we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from celery_worker.core import ml_registry
try:
    from tests.generate_dummy_audio import create_dummy_wav
except ImportError:
    # Handle if running from root
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tests'))
    from generate_dummy_audio import create_dummy_wav

def test_mlflow_audio_model_integration():
    """
    Test that the Audio model loads correctly from MLflow 
    and can perform prediction on a real (silent) wav file.
    """
    print("Testing MLflow Integration for Audio...")
    
    # 1. Generate Dummy Audio
    # Use absolute path to ensure proper creation/deletion
    base_dir = os.path.dirname(os.path.abspath(__file__))
    audio_path = os.path.join(base_dir, "test_audio.wav")
    
    create_dummy_wav(audio_path, duration=2.0)
    
    try:
        # 2. Trigger prediction
        # This should trigger _load_audio_model which downloads from MLflow
        # (Assuming ml_registry is singleton and might be already loaded, but _load_audio_model handles that?)
        # ml_registry.load_assets() checks self._is_loaded.
        # If running in same process as previous tests, it might be loaded.
        # But import reloads? No. 
        # If verify_model_content ran separately, this is a fresh process.
        
        result = ml_registry.predict_audio(audio_path)
        
        print("\n[INFO] Prediction Result:")
        print(result)
        
        # 3. Validation
        if "error" in result:
             pytest.fail(f"Model returned error: {result['error']}")
        
        # Check model loaded
        assert ml_registry.audio_model is not None, "Audio model was not loaded."
        
        # Check return structure
        assert "prediction" in result
        assert result["prediction"] in ["REAL", "FAKE"]
        assert "confidence_score" in result
        
        # Check if the file was actually downloaded?
        # Verify that we used MLflow path? We printed it in core.py.
        # Difficult to assert on stdout here without capsys, but functional test is key.
        
        print("[SUCCESS] Audio Model Integration Verified!")
        
    finally:
        # Cleanup
        if os.path.exists(audio_path):
            os.remove(audio_path)

if __name__ == "__main__":
    test_mlflow_audio_model_integration()
