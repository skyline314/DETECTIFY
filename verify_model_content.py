import os
import mlflow
import mlflow.sklearn
from dotenv import load_dotenv

load_dotenv()

def verify_model():
    model_name = "detectify-text-en-logreg"
    version = "2"
    model_uri = f"models:/{model_name}/{version}"
    
    print(f"Attempting to load: {model_uri}")
    
    try:
        model = mlflow.sklearn.load_model(model_uri)
        print(f"[SUCCESS] Model loaded!")
        print(f"Type: {type(model)}")
        print(f"Model object: {model}")
        
        # Check if it has a vectorizer step if it's a pipeline
        if hasattr(model, 'steps'):
            print("It appears to be a Pipeline. Steps:")
            for name, step in model.steps:
                print(f"  - {name}: {type(step)}")
        else:
            print("It is NOT a Pipeline (likely just the classifier). We might still need the Vectorizer.")
            
    except Exception as e:
        print(f"[ERROR] Failed to load model: {e}")

if __name__ == "__main__":
    verify_model()
