import sys
from unittest.mock import MagicMock

# ========================================================================================
# GLOBAL MOCKS (Applied before any test collection)
# ========================================================================================

# List of libraries that are heavy or might not be in the test environment
MOCKED_LIBS = [
    'gensim', 'gensim.models.doc2vec', 'gensim.utils',
    'librosa', 'timm', 'cv2', 'boto3', 'soundfile', 
    'PIL', 'PIL.Image', 'pypdf', 'docx',
    'torchvision', 'torchvision.transforms'
]

def setup_global_mocks():
    """Applied at the very beginning to prevent real imports of ML libs."""
    for lib in MOCKED_LIBS:
        if lib not in sys.modules:
            m = MagicMock()
            m.__spec__ = MagicMock()
            if lib == 'PIL':
                m.__version__ = '9.4.0'
            sys.modules[lib] = m

# Execute immediately upon import by pytest
# setup_global_mocks()

# ========================================================================================
# SHARED FIXTURES
# ========================================================================================
import pytest
from app import create_app
from app.extensions import db

@pytest.fixture(scope="session")
def app():
    """Session-wide application fixture."""
    _app = create_app('testing')
    _app.config['LIMIT_DAILY'] = 5
    _app.config['AWS_S3_BUCKET_NAME'] = 'test-bucket'
    
    with _app.app_context():
        db.create_all()
        yield _app
        db.drop_all()

@pytest.fixture(scope="session")
def client(app):
    return app.test_client()

@pytest.fixture(autouse=True)
def reset_ml_registry():
    """Reset ML Registry state before each test to prevent pollution."""
    from celery_worker.core import ml_registry
    
    # Backup original state if needed, here we just reset to None/False
    ml_registry.audio_model = None
    ml_registry.en_text_model = None
    ml_registry.id_text_model = None
    ml_registry.id_text_vectorizer = None
    ml_registry.image_model = None
    ml_registry._is_loaded = False
    
    # Also clear any mocks attached to it
    if hasattr(ml_registry, 'image_transforms'):
        del ml_registry.image_transforms
    
    yield
