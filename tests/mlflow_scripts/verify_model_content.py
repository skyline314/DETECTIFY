import os
import mlflow
import mlflow.sklearn
import mlflow.pytorch
from dotenv import load_dotenv

load_dotenv()

def verify_models():
    log_file = "verify_model_content.log"
    client = mlflow.tracking.MlflowClient()
    
    with open(log_file, "w", encoding="utf-8") as f:
        # 1. Check Indonesian Text Pipeline
        model_name = "Indo_Text_Pipeline_BILSTM"
        version = "2"
        
        try:
             msg = f"\n[INFO] Inspecting {model_name} v{version}...\n"
             print(msg)
             f.write(msg)
             
             model_uri = f"models:/{model_name}/{version}"
             # Get run_id from version
             mv = client.get_model_version(model_name, version)
             run_id = mv.run_id
             msg = f"Run ID: {run_id}\n"
             print(msg)
             f.write(msg)
             
             # List artifacts
             artifacts = client.list_artifacts(run_id)
             msg = "Artifacts root:\n"
             for art in artifacts:
                 msg += f" - {art.path} ({art.file_size} bytes)\n"
                 if art.is_dir:
                     sub_arts = client.list_artifacts(run_id, art.path)
                     for sub in sub_arts:
                         msg += f"   - {sub.path} ({sub.file_size} bytes)\n"
             print(msg)
             f.write(msg)

             # Check flavors
             info = mlflow.models.get_model_info(model_uri)
             flavors = info.flavors
             msg = f"Flavors: {flavors}\n"
             print(msg)
             f.write(msg)
             
             if 'python_function' in flavors:
                  try:
                      print("Attempting PyFunc load...")
                      model = mlflow.pyfunc.load_model(model_uri)
                      print("[SUCCESS] Loaded as PyFunc!")
                      f.write("[SUCCESS] Loaded as PyFunc!\n")
                  except Exception as e:
                      f.write(f"PyFunc load failed: {e}\n")
                      print(f"PyFunc load failed: {e}")

        except Exception as e:
            err = f"[ERROR] Failed to verify {model_name}: {e}\n"
            print(err)
            f.write(err)

        # 2. Check Audio Model
        model_name = "Audio_Deepfake_Detection_Model"
        version = "1"
        
        try:
            msg = f"\n[INFO] Inspecting {model_name} v{version}...\n"
            print(msg)
            f.write(msg)
            
            model_uri = f"models:/{model_name}/{version}"
            mv = client.get_model_version(model_name, version)
            run_id = mv.run_id
            
            # List artifacts
            artifacts = client.list_artifacts(run_id)
            msg = "Artifacts root:\n"
            for art in artifacts:
                msg += f" - {art.path} ({art.file_size} bytes)\n"
                if art.is_dir:
                     sub_arts = client.list_artifacts(run_id, art.path)
                     for sub in sub_arts:
                         msg += f"   - {sub.path} ({sub.file_size} bytes)\n"
            print(msg)
            f.write(msg)

            info = mlflow.models.get_model_info(model_uri)
            flavors = info.flavors
            msg = f"Flavors: {flavors}\n"
            print(msg)
            f.write(msg)
            
            if 'python_function' in flavors:
                  try:
                      print("Attempting PyFunc load...")
                      model = mlflow.pyfunc.load_model(model_uri)
                      print("[SUCCESS] Loaded as PyFunc!")
                      f.write("[SUCCESS] Loaded as PyFunc!\n")
                  except Exception as e:
                      f.write(f"PyFunc load failed: {e}\n")
                      print(f"PyFunc load failed: {e}")

        except Exception as e:
            f.write(f"[ERROR] Failed to verify {model_name}: {e}\n")
            print(e)

if __name__ == "__main__":
    verify_models()
