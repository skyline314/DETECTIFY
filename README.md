# DetectiFy — Multi-Modal AI Detection & Text Humanizer

DetectiFy is a sophisticated web application designed to identify AI-generated content across various formats. Whether it's text, images, video, or audio, DetectiFy uses advanced machine learning models to provide transparent and reliable analysis. Additionally, it offers a "Text Humanizer" to refine AI-generated text for a more natural, human-like flow.

##  Features

- **Multi-Modal Detection**:
  - **Text Detection**: Specialized models for English and Indonesian text classification.
  - **Image Detection**: Analyzes visual patterns to distinguish AI-generated images.
  - **Video Detection**: Frame-level analysis for identifying deepfakes and AI video content.
  - **Audio Detection**: Detects synthesized speech and AI-generated audio signatures.
- **AI Text Humanizer**: Rewrites AI-generated text to improve readability and bypass detection.
- **Comprehensive Dashboard**:
  - **Analysis History**: View, sort, and filter your previous detection reports.
  - **Detailed Reports**: High-risk (AI) vs. Low-risk (Human) indicators with probability bars.
- **User Management**:
  - Secure JWT authentication.
  - Email verification and secure password reset.
  - Profile customization (Change Username).
- **Localized UI**: Support for English and Indonesian languages.

## Tech Stack

- **Backend**: Flask (Python)
- **Asynchronous Tasks**: Celery with Redis
- **Database**: SQLAlchemy (SQLite for development, PostgreSQL-ready)
- **Frontend**: Vanilla HTML/CSS/JavaScript with a modern, responsive design.
- **Machine Learning**: PyTorch, XGBoost, Scikit-learn, Timm, Librosa.
- **Mailing**: Resend API.

## Setup & Installation

### Prerequisites
- Python 3.9+
- Redis (for Celery broker)
- Ollama (running locally for the Text Humanizer feature)

### Steps
1. **Clone the repository**:
   ```bash
   git clone https://github.com/skyline314/DETECTIFY.git
   cd DETECTIFY
   ```

2. **Initialize Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Create a `.env` file in the root directory:
   ```env
   SECRET_KEY=your_secure_random_key
   DATABASE_URL=sqlite:///instance/app.db
   RESEND_API_KEY=your_resend_api_key
   LIMIT_DAILY=5
   ```

4. **Start the Celery Worker**:
   (Required for running ML inference tasks)
   ```bash
   celery -A celery_worker.celery_app.celery worker --loglevel=info --pool=solo
   ```

5. **Run the Flask App**:
   ```bash
   flask run
   ```
   Access the app at `http://127.0.0.1:5000`.

## How to Use

1. **Register**: Create an account and verify your email.
2. **Select a Model**: Use the navigation menu to choose between Text, Image, Video, or Audio detection.
3. **Upload/Paste**: Upload your file or paste the text you wish to analyze.
4. **Get Results**: Wait for the background task to complete and view your report.
5. **Humanize**: Use the Humanizer tool to refine your AI-generated text.

---
<<<<<<< HEAD
Developed by **[skyline314](https://github.com/skyline314)** and Team.
=======
title: Detectify
emoji: 🛡️
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

<div align="center">
  <img src="app/static/assets/dark-logo.png" alt="DetectiFy Logo" width="150" />
  <h1>DETECTIFY: Verify Reality, Faster.</h1>
  <p>An advanced, Open-Source deepfake detection application leveraging Machine Learning to uncover AI-generated text, images, video, and audio.</p>

  [![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/YOUR_RAILWAY_TEMPLATE)
  [![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)
</div>

<br />

## 🌟 Key Features
- 🎥 **Video & 🖼️ Image Detection**: Instantly spot AI-generated objects, visual glitches, and manipulation.
- 🔊 **Audio Detection**: Uncover cloned voices and deepfake speech audio.
- 📝 **Text Analysis**: Differentiate between human-written and LLM-generated texts.
- 🛠️ **Text Humanizer**: Refine AI-written text into natural, human-sounding writing.

---

## 🏗️ Architecture Overview
DETECTIFY is built with a robust, modern stack to ensure high performance and scalability:
- **Backend & API**: Flask (Python) powers the core routing and application logic.
- **Asynchronous Tasks**: Celery & Redis handle heavy machine learning inference tasks in the background without blocking the UI.
- **Machine Learning Tracking**: MLflow (DagsHub) tracks model experiments, weights, and parameters.
- **Monitoring**: Prometheus & Grafana provide real-time dashboards for system health and request rates.
- **Database**: PostgreSQL (via SQLAlchemy) stores user accounts, transaction histories, and analysis logs.
- **Payments**: Midtrans Snap integration handles premium subscriptions.

---

## 🚀 One-Click Deploy
Want to host your own instance of DetectiFy? You can deploy it instantly! 
Click one of the deployment buttons at the top of this README. Make sure you have your secrets ready. 
For *Hugging Face Spaces*, simply duplicate this space.

---

## 💻 Local Developer Setup

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

## 🐋 Docker Setup (Alternative)
If you prefer running everything via Docker:
1. Ensure your `.env` is fully populated.
2. Build and run the image:
```bash
docker build -t detectify .
docker run -p 5000:5000 --env-file .env detectify
```
*(Note: A full `docker-compose.yml` to spin up Redis & Postgres alongside the app is coming soon!)*

---

## 🤝 Contributing
Contributions are always welcome! Whether it's improving the UI, optimizing ML models, or fixing bugs:
1. Fork the Project.
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`).
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the Branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

## 📄 License
All rights reserved © 2026 DetectiFy.
>>>>>>> deploy-huggingface
