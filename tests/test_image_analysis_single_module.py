from unittest.mock import MagicMock, patch
import pytest
import torch
from celery_worker.core import ml_registry

# ========================================================================================
# FIXTURES
# ========================================================================================

@pytest.fixture
def mock_auth(app):
    """Mocks JWT Auth."""
    with patch("flask_jwt_extended.view_decorators.verify_jwt_in_request"):
        with patch("app.analysis.routes.get_jwt_identity") as mock_identity:
            mock_identity.return_value = "user_img_123"
            yield mock_identity

@pytest.fixture
def mock_db_user():
    """Mocks user."""
    user = MagicMock()
    user.user_id = "user_img_123"
    user.username = "testuser"
    user.is_premium_active.return_value = False
    with patch("app.extensions.db.session.get", return_value=user):
        yield user

@pytest.fixture
def setup_image_model():
    """Mocks the Image Model in ml_registry."""
    mock_model = MagicMock()
    ml_registry.image_model = mock_model
    ml_registry.image_transforms = MagicMock() # Mock transforms
    ml_registry._is_loaded = True
    
    # Mock torchvision
    with patch("torchvision.transforms.Compose") as mock_compose:
        yield mock_model

# ========================================================================================
# TEST CASES (TC-IMG-01 to TC-IMG-11)
# ========================================================================================

# --- TC-IMG-01: Auth Fail ---
def test_tc_img_01_auth_fail(client):
    response = client.post('/image', data={})
    assert response.status_code == 401

# --- TC-IMG-02: Premium Bypass ---
def test_tc_img_02_premium_bypass(client, mock_auth):
    user = MagicMock()
    user.user_id = "premium_user"
    user.is_premium_active.return_value = True
    with patch("app.extensions.db.session.get", return_value=user):
        with patch("app.analysis.services.AnalysisService._validate_file", return_value=("test.png", "png")):
            with patch("app.analysis.services.AnalysisService._handle_s3_upload", return_value="s3/path"):
                with patch("app.analysis.services.AnalysisService._dispatch_task"):
                    data = {'file': (open(__file__, 'rb'), 'test.png')}
                    response = client.post('/image', data=data, content_type='multipart/form-data')
                    assert response.status_code == 202

# --- TC-IMG-03: Quota Full ---
def test_tc_img_03_quota_full(client, mock_auth, mock_db_user):
    with patch("app.analysis.services.AnalysisService.get_daily_usage", return_value=5):
        data = {'file': (open(__file__, 'rb'), 'test.jpg')}
        response = client.post('/image', data=data, content_type='multipart/form-data')
        assert response.status_code == 403
        assert "Kuota harian habis" in response.get_json()['error']

# --- TC-IMG-04: Invalid Extension ---
def test_tc_img_04_invalid_ext(client, mock_auth, mock_db_user):
    with patch("app.analysis.services.AnalysisService.get_daily_usage", return_value=0):
        data = {'file': (open(__file__, 'rb'), 'test.gif')}
        response = client.post('/image', data=data, content_type='multipart/form-data')
        assert response.status_code == 400
        assert "Format tidak didukung" in response.get_json()['error']

# --- TC-IMG-05: Model Loading Trigger ---
def test_tc_img_05_model_loading():
    ml_registry._is_loaded = False
    ml_registry.image_model = None
    with patch.object(ml_registry, 'load_assets') as mock_load:
        try:
            ml_registry.predict_image("dummy.jpg")
        except: pass
        mock_load.assert_called_once()

# --- TC-IMG-06: Input Path (String) ---
def test_tc_img_06_input_path(setup_image_model):
    with patch("PIL.Image.open") as mock_open:
        mock_img = MagicMock()
        mock_open.return_value = mock_img
        mock_img.convert.return_value = mock_img
        
        setup_image_model.return_value = torch.tensor([-2.0])
        ml_registry.predict_image("test_path.jpg")
        mock_open.assert_called_with("test_path.jpg")

# --- TC-IMG-07: Input PIL Object ---
def test_tc_img_07_input_pil(setup_image_model):
    with patch("PIL.Image.open") as mock_open:
        mock_img = MagicMock()
        mock_img.convert.return_value = mock_img
        
        setup_image_model.return_value = torch.tensor([-2.0])
        ml_registry.predict_image(mock_img)
        mock_open.assert_not_called()

# --- TC-IMG-08: Decision High Prob (FAKE) ---
def test_tc_img_08_decision_fake(setup_image_model):
    setup_image_model.return_value = torch.tensor([0.0])
    mock_img = MagicMock()
    mock_img.convert.return_value = mock_img
    
    result = ml_registry.predict_image(mock_img)
    assert result['prediction'] == 'FAKE'

# --- TC-IMG-09: Decision Low Prob (REAL) ---
def test_tc_img_09_decision_real(setup_image_model):
    setup_image_model.return_value = torch.tensor([-2.0])
    mock_img = MagicMock()
    mock_img.convert.return_value = mock_img
    
    result = ml_registry.predict_image(mock_img)
    assert result['prediction'] == 'REAL'

# --- TC-IMG-10: Decision Mid Prob (SUSPICIOUS) ---
def test_tc_img_10_decision_susp(setup_image_model):
    setup_image_model.return_value = torch.tensor([-0.8])
    mock_img = MagicMock()
    mock_img.convert.return_value = mock_img
    
    result = ml_registry.predict_image(mock_img)
    assert result['prediction'] == 'SUSPICIOUS'

# --- TC-IMG-11: Image Corrupt / Error ---
def test_tc_img_11_image_error():
    # Setup mock so it bypasses loading check
    ml_registry.image_model = MagicMock()
    ml_registry._is_loaded = True

    with patch("PIL.Image.open", side_effect=RuntimeError("Corrupt Binary")):
        result = ml_registry.predict_image("broken.jpg")
        assert "error" in result
        assert "Image Error" in result['error']
