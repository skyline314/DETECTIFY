import pytest
import os
import sys
from dotenv import load_dotenv
from PIL import Image
import torch

# Ensure we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from celery_worker.core import ml_registry

@pytest.mark.integration
def test_mlflow_image_model_integration():
    """
    Test that the Image model loads correctly from MLflow (via artifact download)
    and can perform prediction.
    """
    if not os.getenv("MLFLOW_TRACKING_URI"):
        pytest.skip("Skipping MLflow integration test: MLFLOW_TRACKING_URI not set.")

    print("Testing MLflow Integration for Image...")
    
    # 1. Create Dummy Image
    base_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(base_dir, "test_image.jpg")
    
    # Create a random image
    img = Image.new('RGB', (224, 224), color = 'red')
    img.save(image_path)
    
    try:
        # 2. Trigger prediction
        # The reset_ml_registry fixture in conftest.py matches this file location?
        # Yes, tests/conftest.py applies to tests/.
        
        result = ml_registry.predict_image(image_path)
        
        print("\n[INFO] Prediction Result:")
        print(result)
        
        # 3. Validation
        if "error" in result:
             pytest.fail(f"Model returned error: {result['error']}")
        
        # Check model loaded
        assert ml_registry.image_model is not None, "Image model was not loaded."
        
        # Check return structure
        assert "prediction" in result
        assert result["prediction"] in ["REAL", "FAKE", "SUSPICIOUS"]
        assert "confidence" in result
        
        print("[SUCCESS] Image Model Integration Verified!")
        
    finally:
        # Cleanup
        if os.path.exists(image_path):
            os.remove(image_path)

if __name__ == "__main__":
    test_mlflow_image_model_integration()
