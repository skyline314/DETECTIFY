from unittest.mock import MagicMock, patch
import pytest
import torch
from celery_worker.core import ml_registry

# ========================================================================================
# FIXTURES
# ========================================================================================

@pytest.fixture
def mock_auth(app):
    """Mocks JWT Auth to return a valid user ID."""
    with patch("flask_jwt_extended.view_decorators.verify_jwt_in_request"):
        with patch("app.analysis.routes.get_jwt_identity") as mock_identity:
            mock_identity.return_value = "user123"
            yield mock_identity

@pytest.fixture
def mock_db_user():
    """Mocks the DB User query (Legacy) and db.session.get (New)."""
    user = MagicMock()
    user.user_id = "user123"
    user.username = "testuser"
    user.is_premium_active.return_value = False
    
    with patch("app.models.User.query") as mock_query:
        mock_query.get.return_value = user
        with patch("app.extensions.db.session.get", return_value=user):
            yield user

@pytest.fixture
def setup_audio_model():
    """Mocks the internal Audio Model in ml_registry."""
    mock_model = MagicMock()
    ml_registry.audio_model = mock_model
    ml_registry._is_loaded = True
    return mock_model

# ========================================================================================
# TEST CASES (TC-SM-01 to TC-SM-10)
# ========================================================================================

# --- TC-SM-01: Authentication (User Not Logged In) ---
def test_tc_sm_01_auth_fail(client):
    response = client.post('/audio', data={})
    assert response.status_code == 401

# --- TC-SM-02: User Quota Exceeded ---
def test_tc_sm_02_quota_exceeded(client, mock_auth, mock_db_user):
    with patch("app.analysis.services.AnalysisService.get_daily_usage", return_value=5):
        data = {'file': (open(__file__, 'rb'), 'test.wav')} 
        response = client.post('/audio', data=data, content_type='multipart/form-data')
        assert response.status_code == 403
        assert "Kuota harian habis" in response.get_json()['error']

# --- TC-SM-03: File Extension Invalid ---
def test_tc_sm_03_invalid_extension(client, mock_auth, mock_db_user):
    with patch("app.analysis.services.AnalysisService.get_daily_usage", return_value=0):
        data = {'file': (open(__file__, 'rb'), 'test.midi')}
        response = client.post('/audio', data=data, content_type='multipart/form-data')
        assert response.status_code == 400
        assert "Format tidak didukung" in response.get_json()['error']

# --- TC-SM-04: Model Loading (Cold Start) ---
def test_tc_sm_04_model_loading():
    ml_registry._is_loaded = False
    ml_registry.audio_model = None
    with patch.object(ml_registry, 'load_assets') as mock_load:
        # Mock torchaudio to avoid errors
        import torchaudio
        with patch('torchaudio.load', return_value=(torch.randn(1, 16000), 16000)):
             ml_registry.predict_audio("dummy_path.wav")
             mock_load.assert_called_once()

# --- TC-SM-05: Resampling (44.1kHz -> 16kHz) ---
def test_tc_sm_05_resampling(setup_audio_model):
    import torchaudio
    mock_waveform = torch.randn(1, 44100) 
    with patch("torchaudio.load", return_value=(mock_waveform, 44100)):
        with patch("torchaudio.transforms.Resample") as mock_resample_cls:
            mock_resample_instance = MagicMock()
            mock_resample_cls.return_value = mock_resample_instance
            mock_resample_instance.return_value = torch.randn(1, 16000)
            
            ml_registry.predict_audio("test_44k.wav")
            mock_resample_cls.assert_called_with(44100, 16000)

# --- TC-SM-06: Mixing Mono (Stereo -> Mono) ---
def test_tc_sm_06_mixing_mono(setup_audio_model):
    import torchaudio
    mock_waveform = torch.randn(2, 16000) 
    with patch("torchaudio.load", return_value=(mock_waveform, 16000)):
        with patch("torch.mean") as mock_mean:
            mock_mean.return_value = torch.randn(1, 16000)
            ml_registry.predict_audio("stereo.wav")
            mock_mean.assert_called()

# --- TC-SM-07: Segmentation (Short File < 4s) ---
def test_tc_sm_07_segmentation_short(setup_audio_model):
    import torchaudio
    mock_waveform = torch.randn(1, 32000)
    with patch("torchaudio.load", return_value=(mock_waveform, 16000)):
        setup_audio_model.return_value = torch.randn(1, 2) 
        result = ml_registry.predict_audio("short.wav")
        assert result['details']['segments_total'] == 1

# --- TC-SM-08: Loop Logic (Long File > 4s) ---
def test_tc_sm_08_loop_logic(setup_audio_model):
    import torchaudio
    mock_waveform = torch.randn(1, 160000)
    with patch("torchaudio.load", return_value=(mock_waveform, 16000)):
        setup_audio_model.return_value = torch.randn(1, 2)
        result = ml_registry.predict_audio("long.wav")
        assert result['details']['segments_total'] == 3

# --- TC-SM-09: Voting Logic (Fake Majority) ---
def test_tc_sm_09_voting_fake(setup_audio_model):
    import torchaudio
    setup_audio_model.side_effect = [
        torch.tensor([[0.1, 0.9]]), # Fake
        torch.tensor([[0.2, 0.8]]), # Fake
        torch.tensor([[0.9, 0.1]])  # Real
    ]
    mock_waveform = torch.randn(1, 160000)
    with patch("torchaudio.load", return_value=(mock_waveform, 16000)):
        result = ml_registry.predict_audio("majority_fake.wav")
        assert result['prediction'] == 'FAKE'
        assert result['details']['segments_fake'] == 2

# --- TC-SM-10: Error Handler ---
def test_tc_sm_10_error_handler():
    # Setup mock model so it bypasses loading check
    ml_registry.audio_model = MagicMock()
    ml_registry._is_loaded = True

    import torchaudio
    with patch("torchaudio.load", side_effect=RuntimeError("Corrupt file")):
        result = ml_registry.predict_audio("corrupt.wav")
        assert "error" in result
        assert "Audio prediction failed" in result['error']
