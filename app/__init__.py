from flask import Flask, render_template
<<<<<<< HEAD
<<<<<<< HEAD

__version__ = '1.0.0'
=======
>>>>>>> 1a28d7f5a860d74198facd1c65210be6a133fa59
=======
>>>>>>> 45a07fcd43bd6fae16c3910ebcd43151321b3a1f
from .config import config
from .extensions import (
    db, 
    migrate, 
    jwt, 
    cors, 
    init_s3_client,
    mail
)
from flask_cors import CORS
import os

<<<<<<< HEAD
<<<<<<< HEAD
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))

def create_app(config_name='default'):
    app = Flask(__name__)
    
=======
=======
>>>>>>> 45a07fcd43bd6fae16c3910ebcd43151321b3a1f
def create_app(config_name='default'):
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
    app = Flask(__name__, template_folder=template_dir)

<<<<<<< HEAD
>>>>>>> 1a28d7f5a860d74198facd1c65210be6a133fa59
=======
>>>>>>> 45a07fcd43bd6fae16c3910ebcd43151321b3a1f
    CORS(app, resources={r"/*": {"origins": "*"}})
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app)
    mail.init_app(app)
    init_s3_client(app)

    with app.app_context():
        from . import models 
        
    # 1. Blueprint Auth
    from .auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # 2. Blueprint Analysis
    from .analysis import analysis_bp
<<<<<<< HEAD
<<<<<<< HEAD
    app.register_blueprint(analysis_bp, url_prefix='')
=======
    app.register_blueprint(analysis_bp, url_prefix='/api')
>>>>>>> 1a28d7f5a860d74198facd1c65210be6a133fa59
=======
    app.register_blueprint(analysis_bp, url_prefix='/api')
>>>>>>> 45a07fcd43bd6fae16c3910ebcd43151321b3a1f

    # 3. Blueprint Payment
    from app.payment.routes import payment_bp
    app.register_blueprint(payment_bp, url_prefix='/api/payment')

<<<<<<< HEAD
<<<<<<< HEAD
=======
=======
>>>>>>> 45a07fcd43bd6fae16c3910ebcd43151321b3a1f
    @app.route('/hello')
    def hello():
        return "Hello, World! Factory is working."
    
    @app.route('/')
    def index():
        # Ini akan mencari file app/templates/index.html
        return render_template('index.html')
    

<<<<<<< HEAD
>>>>>>> 1a28d7f5a860d74198facd1c65210be6a133fa59
=======
>>>>>>> 45a07fcd43bd6fae16c3910ebcd43151321b3a1f
    return app