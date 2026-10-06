from fastapi.testclient import TestClient

from app import app


def test_health():
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["version"] == "0.3.0"
    assert response.json()["reference_model"] == "ready"


def test_home_contains_camera_interface():
    response = TestClient(app).get("/")
    assert response.status_code == 200
    assert "captureButton" in response.text
    assert "JINXI / COLOR LENS" in response.text
    assert 'data-language="zh-CN"' in response.text
    assert 'data-language="en"' in response.text
    assert "translations" in response.text
    assert "/learning" in response.text


def test_learning_page_and_reference_model_are_available():
    client = TestClient(app)
    page = client.get("/learning")
    assert page.status_code == 200
    assert "Learning & Evidence" in page.text
    assert "evidence_boundaries" in page.text

    response = client.get("/api/reference-model")
    assert response.status_code == 200
    model = response.json()
    assert model["reference_count"] == 13
    assert model["prototype_count"] == 28
    assert len(model["prototype_colors"]) == 28
    assert model["calibration"]["q95_delta_e"] > 0
