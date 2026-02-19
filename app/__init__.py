from flask import Flask, render_template

__version__ = '1.0.0'
from .config import config
from .extensions import (
    db, 
    migrate, 
    jwt, 
    cors, 
    init_s3_client,
    mail,
    metrics
)
from flask_cors import CORS
import os

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))

def create_app(config_name='default'):
    app = Flask(__name__)
    
    CORS(app, resources={r"/*": {"origins": "*"}})
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app)
    mail.init_app(app)
    init_s3_client(app)
    
    # Initialize Metrics
    metrics.init_app(app)
    # Set static info (optional)
    # Set static info (optional)
    try:
        metrics.info('app_info', 'Application info', version='1.0.0')
    except ValueError:
        pass # Metric already registered

    with app.app_context():
        from . import models 
        
    # 1. Blueprint Auth
    from .auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # 2. Blueprint Analysis
    from .analysis import analysis_bp
    app.register_blueprint(analysis_bp, url_prefix='')

    # 3. Blueprint Payment
    from app.payment.routes import payment_bp
    app.register_blueprint(payment_bp, url_prefix='/api/payment')

    return app