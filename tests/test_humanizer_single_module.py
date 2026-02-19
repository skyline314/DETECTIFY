from unittest.mock import MagicMock, patch
import pytest
from celery_worker.core import ml_registry

# ========================================================================================
# FIXTURES
# ========================================================================================

@pytest.fixture
def mock_auth(app):
    """Mocks JWT Auth."""
    with patch("flask_jwt_extended.view_decorators.verify_jwt_in_request"):
        with patch("app.analysis.routes.get_jwt_identity") as mock_identity:
            mock_identity.return_value = "user_hum_123"
            yield mock_identity

@pytest.fixture
def mock_db_user():
    """Mocks the DB User."""
    user = MagicMock()
    user.user_id = "user_hum_123"
    user.username = "testuser"
    user.is_premium_active.return_value = False
    with patch("app.extensions.db.session.get", return_value=user):
        yield user

# ========================================================================================
# TEST CASES (TC-HUM-01 to TC-HUM-10)
# ========================================================================================

# --- TC-HUM-01: Auth Fail ---
def test_tc_hum_01_auth_fail(client):
    response = client.post('/humanize', data={})
    assert response.status_code == 401

# --- TC-HUM-02: Premium Bypass ---
def test_tc_hum_02_premium_bypass(client, mock_auth):
    user = MagicMock()
    user.is_premium_active.return_value = True
    with patch("app.extensions.db.session.get", return_value=user):
        with patch("app.analysis.services.AnalysisService._validate_file", return_value=("test.txt", "txt")):
            with patch("app.analysis.services.AnalysisService._handle_s3_upload", return_value="path/to/s3"):
                with patch("app.analysis.services.AnalysisService._dispatch_task"):
                    response = client.post('/humanize', json={'text': 'Mock text', 'language': 'en'})
                    assert response.status_code == 202

# --- TC-HUM-03: Quota Full ---
def test_tc_hum_03_quota_full(client, mock_auth, mock_db_user):
    with patch("app.analysis.services.AnalysisService.get_daily_usage", return_value=5):
        response = client.post('/humanize', json={'text': 'Mock text'})
        assert response.status_code == 403
        assert "Kuota harian habis" in response.get_json()['error']

# --- TC-HUM-04: Invalid Ext (Note: Humanizer bypasses ext check but we test logic) ---
def test_tc_hum_04_any_text_allowed(client, mock_auth, mock_db_user):
    # Humanizer actually doesn't have an extension check because it takes raw text.
    # But it wraps it in a .txt filename.
    with patch("app.analysis.services.AnalysisService.get_daily_usage", return_value=0):
        with patch("app.analysis.services.AnalysisService._handle_s3_upload", return_value="ok"):
            with patch("app.analysis.services.AnalysisService._dispatch_task"):
                response = client.post('/humanize', json={'text': 'Some valid text content'})
                assert response.status_code == 202

# --- TC-HUM-05: Lang: English ---
@patch("requests.post")
def test_tc_hum_05_lang_en(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "Humanized English Text"}
    mock_post.return_value = mock_response
    
    result = ml_registry.humanize_text("Robotic English text here", language='en')
    assert "Humanized English Text" in result['humanized_text']
    # Verify prompt contains English instructions
    args, kwargs = mock_post.call_args
    assert "professional editor" in kwargs['json']['prompt']

# --- TC-HUM-06: Lang: Indonesian ---
@patch("requests.post")
def test_tc_hum_06_lang_id(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "Teks Bahasa Indonesia yang manusiawi"}
    mock_post.return_value = mock_response
    
    result = ml_registry.humanize_text("Teks kaku AI di sini", language='id')
    assert "Teks Bahasa Indonesia" in result['humanized_text']
    # Verify prompt contains Indonesian instructions
    args, kwargs = mock_post.call_args
    assert "editor profesional" in kwargs['json']['prompt']

# --- TC-HUM-07: Ollama Down ---
@patch("requests.post", side_effect=Exception("Connection Refused"))
def test_tc_hum_07_ollama_down(mock_post):
    result = ml_registry.humanize_text("Some text")
    assert "error" in result
    assert "Gagal memproses teks" in result['humanized_text']

# --- TC-HUM-08: Prefix Cleaning ---
@patch("requests.post")
def test_tc_hum_08_prefix_cleaning(mock_post):
    mock_response = MagicMock()
    # Simulate LLM adding conversational filler
    mock_response.json.return_value = {"response": "Here is the rewritten text: This is the clean version."}
    mock_post.return_value = mock_response
    
    result = ml_registry.humanize_text("Robotic text")
    assert result['humanized_text'] == "This is the clean version."

# --- TC-HUM-09: Extraction Error Handling (Worker Context) ---
def test_tc_hum_09_worker_context():
    from celery_worker.tasks_humanize import process_humanize_task
    with patch("app.models.AnalysisHistory.query") as mock_query:
        job = MagicMock()
        job.file_location = "test.txt"
        mock_query.filter_by.return_value.first.return_value = job
        
        with patch("celery_worker.tasks_humanize.s3_temp_file") as mock_s3:
            mock_s3.return_value.__enter__.return_value = "dummy.txt"
            # Simulate extraction finding no text
            with patch("celery_worker.tasks_humanize.extract_text_from_file", return_value=""):
                process_humanize_task("job123")
                assert job.status == 'FAILED'
                assert "short" in job.error_message.lower()

# --- TC-HUM-10: Global Exception in ML Registry ---
@patch("requests.post")
def test_tc_hum_10_registry_exception(mock_post):
    # Simulate response.json() failing
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_post.return_value = mock_response
    
    result = ml_registry.humanize_text("Some text")
    assert "error" in result
    assert "Humanizer Error" in result['error']
