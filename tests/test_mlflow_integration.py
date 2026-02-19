import pytest
import os
import sys
from dotenv import load_dotenv

# Ensure we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from celery_worker.core import ml_registry

@pytest.mark.integration
def test_mlflow_english_model_integration():
    """
    Test that the English Text model loads correctly from MLflow 
    and can perform prediction.
    """
    print("Testing MLflow Integration for English Text...")
    
    # Text to predict
    text = "This is a test message to verify the model integration."
    
    # Trigger prediction
    result = ml_registry.predict_text(text, language='en')
    
    # Assertions
    assert "error" not in result, f"Model returned error: {result.get('error')}"
    assert "prediction" in result, "Result missing prediction key"
    assert result["prediction"] in ["REAL", "FAKE"], "Invalid prediction label"
    
    # Verify metadata indicates MLflow usage
    model_used = result.get("model_used", "")
    assert "MLflow" in model_used, f"Expected model name to contain 'MLflow', got: {model_used}"

    print(f"\n[SUCCESS] Prediction: {result['prediction']} (Conf: {result['confidence_score']})")
