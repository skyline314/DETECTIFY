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
            mock_identity.return_value = "user_txt_123"
            yield mock_identity

@pytest.fixture
def mock_db_user():
    """Mocks the DB User."""
    user = MagicMock()
    user.user_id = "user_txt_123"
    user.username = "testuser"
    user.is_premium_active.return_value = False
    
    with patch("app.extensions.db.session.get", return_value=user):
        yield user

@pytest.fixture
def setup_text_models():
    """Mocks all text-related models in ml_registry."""
    ml_registry._is_loaded = True
    
    # English Mocks
    mock_en_model = MagicMock()
    mock_en_vec = MagicMock()
    ml_registry.en_text_model = mock_en_model
    ml_registry.en_text_vectorizer = mock_en_vec
    
    # Indonesian Mocks
    mock_id_model = MagicMock()
    mock_id_vec = MagicMock()
    ml_registry.id_text_model = mock_id_model
    ml_registry.id_text_vectorizer = mock_id_vec
    
    return {
        "en_model": mock_en_model,
        "en_vec": mock_en_vec,
        "id_model": mock_id_model,
        "id_vec": mock_id_vec
    }

# ========================================================================================
# TEST CASES (TC-TXT-01 to TC-TXT-13)
# ========================================================================================

# --- TC-TXT-01: Auth Fail ---
def test_tc_txt_01_auth_fail(client):
    response = client.post('/text', data={})
    assert response.status_code == 401

# --- TC-TXT-02: Quota Full ---
def test_tc_txt_02_quota_full(client, mock_auth, mock_db_user):
    with patch("app.analysis.services.AnalysisService.get_daily_usage", return_value=5):
        data = {'file': (open(__file__, 'rb'), 'test.txt')}
        response = client.post('/text', data=data, content_type='multipart/form-data')
        assert response.status_code == 403
        assert "Kuota harian habis" in response.get_json()['error']

# --- TC-TXT-03: Invalid Extension ---
def test_tc_txt_03_invalid_ext(client, mock_auth, mock_db_user):
    with patch("app.analysis.services.AnalysisService.get_daily_usage", return_value=0):
        data = {'file': (open(__file__, 'rb'), 'test.exe')}
        response = client.post('/text', data=data, content_type='multipart/form-data')
        assert response.status_code == 400
        assert "Format tidak didukung" in response.get_json()['error']

# --- TC-TXT-04: Text Too Short ---
def test_tc_txt_04_text_short():
    from celery_worker.core import ml_registry
    result = ml_registry.predict_text("short")
    assert "error" in result
    assert "terlalu pendek" in result['error']

# --- TC-TXT-05: Cold Start Loading ---
def test_tc_txt_05_cold_start():
    ml_registry._is_loaded = False
    with patch.object(ml_registry, 'load_assets') as mock_load:
        # We don't need to finish prediction, just trigger it
        try:
            ml_registry.predict_text("this is a long enough text for test")
        except: pass
        mock_load.assert_called_once()

# --- TC-TXT-06: English FAKE ---
def test_tc_txt_06_en_fake(setup_text_models):
    setup_text_models['en_model'].predict.return_value = [1]
    setup_text_models['en_model'].predict_proba.return_value = [[0.1, 0.9]]
    
    with patch("celery_worker.core.clean_text", return_value="clean text"):
        result = ml_registry.predict_text("this is generated deepfake text for testing", language='en')
        assert result['prediction'] == 'FAKE'
        assert result['confidence_score'] == 0.9

# --- TC-TXT-07: English REAL ---
def test_tc_txt_07_en_real(setup_text_models):
    setup_text_models['en_model'].predict.return_value = [0]
    setup_text_models['en_model'].predict_proba.return_value = [[0.8, 0.2]]
    
    with patch("celery_worker.core.clean_text", return_value="clean text"):
        result = ml_registry.predict_text("this is a normal human written text for testing", language='en')
        assert result['prediction'] == 'REAL'
        assert result['confidence_score'] == 0.8

# --- TC-TXT-08: Indonesian FAKE ---
def test_tc_txt_08_id_fake(setup_text_models):
    # Mock predict_proba returned by ID model (Pipeline v2.1+)
    # Mapping: [prob_ai, prob_human] -> [0.75, 0.25] 
    setup_text_models['id_model'].predict_proba.return_value = [[0.75, 0.25]]
    
    # Mock vectorizer to avoid Doc2Vec logic
    setup_text_models['id_vec'].infer_vector.return_value = [0] * 1000
    
    with patch("celery_worker.core.text_preprocessing_id", return_value="teks bersih"):
        with patch("celery_worker.core.simple_preprocess", return_value=["teks", "bersih"]):
            result = ml_registry.predict_text("ini adalah teks palsu buatan AI", language='id')
            assert result['prediction'] == 'FAKE'
            assert result['probability_ai'] == 0.75

# --- TC-TXT-09: Indonesian REAL ---
def test_tc_txt_09_id_real(setup_text_models):
    # Mapping: [prob_ai, prob_human] -> [0.2, 0.8]
    setup_text_models['id_model'].predict_proba.return_value = [[0.2, 0.8]]
    setup_text_models['id_vec'].infer_vector.return_value = [0] * 1000
    
    with patch("celery_worker.core.text_preprocessing_id", return_value="teks bersih"):
        with patch("celery_worker.core.simple_preprocess", return_value=["teks", "bersih"]):
            result = ml_registry.predict_text("ini teks normal buatan manusia", language='id')
            assert result['prediction'] == 'REAL'
            assert result['probability_human'] == pytest.approx(0.8)
            assert result['probability_ai'] == pytest.approx(0.2)

# --- TC-TXT-10: Model Unavailable ---
def test_tc_txt_10_model_missing():
    ml_registry._is_loaded = True
    ml_registry.en_text_model = None
    result = ml_registry.predict_text("some long text here...", language='en')
    assert "error" in result
    assert "tidak tersedia" in result['error']

# --- TC-TXT-11: PDF Extraction ---
def test_tc_txt_11_pdf_success():
    from celery_worker.utils import extract_text_from_file
    with patch("builtins.open", MagicMock()):
        with patch("pypdf.PdfReader") as mock_pdf:
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "Extracted PDF text content"
            mock_pdf.return_value.pages = [mock_page]
            
            result = extract_text_from_file("dummy.pdf")
            assert "Extracted PDF" in result

# --- TC-TXT-12: DOCX Extraction ---
def test_tc_txt_12_docx_success():
    from celery_worker.utils import extract_text_from_file
    with patch("docx.Document") as mock_doc:
        mock_para = MagicMock()
        mock_para.text = "Extracted DOCX text content"
        mock_doc.return_value.paragraphs = [mock_para]
        
        result = extract_text_from_file("dummy.docx")
        assert "Extracted DOCX" in result

# --- TC-TXT-13: Extraction Fail ---
def test_tc_txt_13_extraction_fail():
    from celery_worker.utils import extract_text_from_file
    # Patch OPEN to fail
    with patch("builtins.open", side_effect=IOError("Locked")):
        with pytest.raises(RuntimeError) as exc:
            extract_text_from_file("locked.txt")
        assert "Gagal membaca dokumen" in str(exc.value)
