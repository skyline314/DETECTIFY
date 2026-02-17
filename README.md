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
Developed by **[skyline314](https://github.com/skyline314)** and Team.