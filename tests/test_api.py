from fastapi.testclient import TestClient

from app import app


def test_health():
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_home_contains_camera_interface():
    response = TestClient(app).get("/")
    assert response.status_code == 200
    assert "captureButton" in response.text
    assert "JINXI / COLOR LENS" in response.text
