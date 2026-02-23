<div align="center">
  <img src="app/static/assets/dark-logo.png" alt="DetectiFy Logo" width="150" />
  <h1>DETECTIFY: Verify Reality, Faster.</h1>
  <p>An advanced deepfake detection application leveraging Machine Learning to uncover AI-generated text, images, video, and audio.</p>

  [![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/YOUR_RAILWAY_TEMPLATE)
  [![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)
</div>

<br />

## Key Features
- **Video & Image Detection**: Instantly spot AI-generated objects, visual glitches, and manipulation.
- **Audio Detection**: Uncover cloned voices and deepfake speech audio.
- **Text Analysis**: Differentiate between human-written and LLM-generated texts.
- **Text Humanizer**: Refine AI-written text into natural, human-sounding writing.

---

## Architecture Overview
DETECTIFY is built with a robust, modern stack to ensure high performance and scalability:
- **Backend & API**: Flask (Python) powers the core routing and application logic.
- **Asynchronous Tasks**: Celery & Redis handle heavy machine learning inference tasks in the background without blocking the UI.
- **Machine Learning Tracking**: MLflow (DagsHub) tracks model experiments, weights, and parameters.
- **Monitoring**: Prometheus & Grafana provide real-time dashboards for system health and request rates.
- **Database**: PostgreSQL (via SQLAlchemy) stores user accounts, transaction histories, and analysis logs.
- **Payments**: Midtrans Snap integration handles premium subscriptions.

---

## One-Click Deploy
Want to host an instance of DetectiFy? You can deploy it instantly! 
Click one of the deployment buttons at the top of this README. Make sure you have your secrets ready. 
For *Hugging Face Spaces*, simply duplicate this space.

---

## Local Environment Setup

To run DetectiFy locally on your machine, follow these steps:

### 1. Prerequisites
- **Python 3.10+** installed
- **Redis Server** installed and running (for Celery background tasks)
- **PostgreSQL** database (or SQLite for quick local development)
- *(Optional)* **Docker** if you prefer containerized deployment

### 2. Installation
Clone the repository and install dependencies:
```bash
git clone https://github.com/skylined214/detectify.git
cd detectify

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory. You can copy the provided example:
```bash
cp .env.example .env
```
**Critical `.env` Variables to Configure:**
- `SECRET_KEY`: A random string for Flask cookie security.
- `DATABASE_URL`: Connection string. (e.g. `sqlite:///detectify.db` for local testing).
- `CELERY_BROKER_URL` / `REDIS_URL`: Your Redis connection string (`redis://localhost:6379/0`).
- `MLFLOW_TRACKING_URI`: Your DagsHub or MLflow server tracking URL to download model weights.
- `AWS_S3_BUCKET_NAME`: S3 credentials if you are storing large user uploads remotely.
- `RESEND_API_KEY`: For sending verification and password reset emails.

### 4. Running the Application
You will need to run two separate processes for the app to function fully:

**Terminal 1: Start the Celery Worker (Task Queue)**
```bash
# Windows
celery -A celery_worker.celery_app.celery worker --loglevel=info --pool=solo

# Linux / Mac
celery -A celery_worker.celery_app.celery worker --loglevel=info
```

**Terminal 2: Start the Flask App**
```bash
flask run
```
Your application should now be accessible at `http://127.0.0.1:5000`!

---

## Docker Setup (Alternative)
If you prefer running everything via Docker:
1. Ensure your `.env` is fully populated.
2. Build and run the image:
```bash
docker build -t detectify .
docker run -p 5000:5000 --env-file .env detectify
```
*(Note: A full `docker-compose.yml` to spin up Redis & Postgres alongside the app is coming soon!)*
