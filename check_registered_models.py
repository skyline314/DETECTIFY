import os
import mlflow
from dotenv import load_dotenv
from pprint import pprint

load_dotenv()

def list_registered_models():
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI"))
    client = mlflow.tracking.MlflowClient()
    
    print(f"Connecting to: {mlflow.get_tracking_uri()}")
    print("Fetching registered models...")
    
    try:
        models = client.search_registered_models()
        if not models:
            print("\n[INFO] No registered models found.")
            print("You (or your friend) haven't registered any models yet.")
        else:
            print(f"\n[SUCCESS] Found {len(models)} models:")
            for m in models:
                print(f"\n- Name: {m.name}")
                print(f"  Description: {m.description}")
                print(f"  Latest Versions:")
                for v in m.latest_versions:
                    print(f"    - Version: {v.version}, Stage: {v.current_stage}")
    except Exception as e:
        print(f"[ERROR] Failed to fetch models: {e}")

if __name__ == "__main__":
    list_registered_models()
