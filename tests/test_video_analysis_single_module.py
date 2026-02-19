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
def setup_image_model():
    """Mocks the internal Image Model in ml_registry used for video frames."""
    mock_model = MagicMock()
    ml_registry.image_model = mock_model
    ml_registry._is_loaded = True
    return mock_model

# ========================================================================================
# TEST CASES (TC-VID-01 to TC-VID-11)
# ========================================================================================

# --- TC-VID-01: Authentication Fail ---
def test_tc_vid_01_auth_fail(client):
    response = client.post('/video', data={})
    assert response.status_code == 401

# --- TC-VID-02: User Quota Exceeded ---
def test_tc_vid_02_quota_exceeded(client, mock_auth, mock_db_user):
    with patch("app.analysis.services.AnalysisService.get_daily_usage", return_value=5):
        data = {'file': (open(__file__, 'rb'), 'test.mp4')}
        response = client.post('/video', data=data, content_type='multipart/form-data')
        assert response.status_code == 403
        assert "Kuota harian habis" in response.get_json()['error']

# --- TC-VID-03: Invalid Extension ---
def test_tc_vid_03_invalid_extension(client, mock_auth, mock_db_user):
    with patch("app.analysis.services.AnalysisService.get_daily_usage", return_value=0):
        data = {'file': (open(__file__, 'rb'), 'test.mkv')}
        response = client.post('/video', data=data, content_type='multipart/form-data')
        assert response.status_code == 400
        assert "Format tidak didukung" in response.get_json()['error']

# --- TC-VID-04: Model Loading (Cold Start) ---
def test_tc_vid_04_model_loading():
    ml_registry._is_loaded = False
    ml_registry.image_model = None
    with patch.object(ml_registry, 'load_assets') as mock_load:
        try:
            ml_registry.predict_image("dummy.jpg")
        except:
            pass 
        mock_load.assert_called_once()

# --- TC-VID-05: Extract Loop (Short Video) ---
@patch("celery_worker.tasks_video.cv2.VideoCapture")
def test_tc_vid_05_short_video(mock_vc, setup_image_model):
    cap = MagicMock()
    cap.isOpened.side_effect = [True, False]
    cap.read.return_value = (True, "frame_data")
    mock_vc.return_value = cap
    
    from celery_worker.tasks_video import process_video_task
    with patch("app.models.AnalysisHistory.query") as mock_query:
        job = MagicMock()
        job.file_location = "test.mp4"
        mock_query.filter_by.return_value.first.return_value = job
        
        with patch("celery_worker.tasks_video.s3_temp_file") as mock_s3:
            mock_s3.return_value.__enter__.return_value = "dummy.mp4"
            with patch.object(ml_registry, 'predict_video_frame', return_value={"prediction": "REAL", "confidence": 90}):
                process_video_task("job123")
                assert job.status == 'COMPLETED'
                assert job.result_summary['details']['total_frames_analyzed'] == 1

# --- TC-VID-06: Skip Logic (Many Frames) ---
@patch("celery_worker.tasks_video.cv2.VideoCapture")
def test_tc_vid_06_skip_logic(mock_vc, setup_image_model):
    cap = MagicMock()
    cap.isOpened.return_value = True
    cap.read.side_effect = [(True, f"f{i}") for i in range(61)] + [(False, None)]
    mock_vc.return_value = cap
    
    from celery_worker.tasks_video import process_video_task
    with patch("app.models.AnalysisHistory.query") as mock_query:
        job = MagicMock()
        mock_query.filter_by.return_value.first.return_value = job
        with patch("celery_worker.tasks_video.s3_temp_file") as mock_s3:
            mock_s3.return_value.__enter__.return_value = "dummy.mp4"
            with patch.object(ml_registry, 'predict_video_frame', return_value={"prediction": "REAL", "confidence": 90}):
                process_video_task("job123")
                assert job.result_summary['details']['total_frames_analyzed'] == 3

# --- TC-VID-07: Max Frames Limit ---
@patch("celery_worker.tasks_video.cv2.VideoCapture")
def test_tc_vid_07_max_frames(mock_vc, setup_image_model):
    cap = MagicMock()
    cap.isOpened.return_value = True
    cap.read.return_value = (True, "frame")
    mock_vc.return_value = cap
    
    from celery_worker.tasks_video import process_video_task
    with patch("app.models.AnalysisHistory.query") as mock_query:
        job = MagicMock()
        mock_query.filter_by.return_value.first.return_value = job
        with patch("celery_worker.tasks_video.s3_temp_file") as mock_s3:
            mock_s3.return_value.__enter__.return_value = "dummy.mp4"
            with patch.object(ml_registry, 'predict_video_frame', return_value={"prediction": "REAL", "confidence": 90}):
                process_video_task("job123")
                assert job.result_summary['details']['total_frames_analyzed'] == 20

# --- TC-VID-08: Frame Error Handling ---
@patch("celery_worker.tasks_video.cv2.VideoCapture")
def test_tc_vid_08_frame_error(mock_vc, setup_image_model):
    cap = MagicMock()
    cap.isOpened.side_effect = [True, True, False]
    cap.read.side_effect = [(True, "f1"), (True, "f2")]
    mock_vc.return_value = cap
    
    from celery_worker.tasks_video import process_video_task
    with patch("app.models.AnalysisHistory.query") as mock_query:
        job = MagicMock()
        mock_query.filter_by.return_value.first.return_value = job
        with patch("celery_worker.tasks_video.s3_temp_file") as mock_s3:
            mock_s3.return_value.__enter__.return_value = "dummy.mp4"
            with patch.object(ml_registry, 'predict_video_frame') as mock_predict:
                mock_predict.side_effect = [{"prediction": "REAL", "confidence": 90}, {"error": "fail"}]
                process_video_task("job123")
                assert job.result_summary['details']['total_frames_analyzed'] == 1

# --- TC-VID-09: No Valid Frames ---
@patch("celery_worker.tasks_video.cv2.VideoCapture")
def test_tc_vid_09_no_valid_frames(mock_vc, setup_image_model):
    cap = MagicMock()
    cap.isOpened.return_value = False
    mock_vc.return_value = cap
    
    from celery_worker.tasks_video import process_video_task
    with patch("app.models.AnalysisHistory.query") as mock_query:
        job = MagicMock()
        mock_query.filter_by.return_value.first.return_value = job
        with patch("celery_worker.tasks_video.s3_temp_file") as mock_s3:
            mock_s3.return_value.__enter__.return_value = "dummy.mp4"
            process_video_task("job123")
            assert job.status == 'FAILED'
            assert "Gagal mengekstrak frame" in job.error_message

# --- TC-VID-10: Voting Logic (FAKE Majority) ---
@patch("celery_worker.tasks_video.cv2.VideoCapture")
def test_tc_vid_10_voting_fake(mock_vc, setup_image_model):
    cap = MagicMock()
    cap.isOpened.return_value = True
    cap.read.side_effect = [(True, "f")] * 61 + [(False, None)]
    mock_vc.return_value = cap
    
    from celery_worker.tasks_video import process_video_task
    with patch("app.models.AnalysisHistory.query") as mock_query:
        job = MagicMock()
        mock_query.filter_by.return_value.first.return_value = job
        with patch("celery_worker.tasks_video.s3_temp_file") as mock_s3:
            mock_s3.return_value.__enter__.return_value = "dummy.mp4"
            with patch.object(ml_registry, 'predict_video_frame') as mock_predict:
                mock_predict.side_effect = [
                    {"prediction": "FAKE", "confidence": 90}, 
                    {"prediction": "FAKE", "confidence": 80},
                    {"prediction": "REAL", "confidence": 70}
                ]
                process_video_task("job123")
                assert job.result_summary['prediction'] == 'FAKE'
                assert job.result_summary['details']['vote_distribution']['FAKE'] == 2

# --- TC-VID-11: Voting Logic (REAL Majority) ---
@patch("celery_worker.tasks_video.cv2.VideoCapture")
def test_tc_vid_11_voting_real(mock_vc, setup_image_model):
    cap = MagicMock()
    cap.isOpened.return_value = True
    cap.read.side_effect = [(True, "f")] * 61 + [(False, None)]
    mock_vc.return_value = cap
    
    from celery_worker.tasks_video import process_video_task
    with patch("app.models.AnalysisHistory.query") as mock_query:
        job = MagicMock()
        mock_query.filter_by.return_value.first.return_value = job
        with patch("celery_worker.tasks_video.s3_temp_file") as mock_s3:
            mock_s3.return_value.__enter__.return_value = "dummy.mp4"
            with patch.object(ml_registry, 'predict_video_frame') as mock_predict:
                mock_predict.side_effect = [
                    {"prediction": "REAL", "confidence": 95}, 
                    {"prediction": "REAL", "confidence": 85},
                    {"prediction": "FAKE", "confidence": 60}
                ]
                process_video_task("job123")
                assert job.result_summary['prediction'] == 'REAL'
                assert job.result_summary['details']['vote_distribution']['REAL'] == 2
