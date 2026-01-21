import os
from app import create_app, db

# Muat konfigurasi dari env variable 'FLASK_ENV' (production/development)
config_name = os.getenv('FLASK_ENV', 'production')

# Panggil factory untuk membuat aplikasi
app = create_app(config_name)

app.config['SERVER_NAME'] = None
app.config['PREFERRED_URL_SCHEME'] = 'https'

with app.app_context():
    try:
        from app.models import User, Transaction, AnalysisHistory
        db.create_all()
        print(" [DATABASE] Connection successful and tables verified/created.")
    except Exception as e:
        print(f" [DATABASE] Error initializing database: {e}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 7860))
    app.run(host="0.0.0.0", port=port)