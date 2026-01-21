import os
from app import create_app

# Muat konfigurasi dari env variable 'FLASK_ENV' (production/development)
config_name = os.getenv('FLASK_ENV', 'production')

# Panggil factory untuk membuat aplikasi
app = create_app(config_name)

app.config['SERVER_NAME'] = None
app.config['PREFERRED_URL_SCHEME'] = 'https'

if __name__ == '__main__':
    app.run()