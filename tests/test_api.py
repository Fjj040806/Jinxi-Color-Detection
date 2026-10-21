import io

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

from app import app


def test_health():
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    health = response.json()
    assert health["version"] == "0.6.0"
    assert health["reference_model"] == "ready"
    assert health["model_fingerprint"] == "25eb239bafb2bda1"
    assert health["reference_count"] == 13
    assert health["patchcore_implemented"] is False
    assert health["methods"] == [
        "SLIC",
        "CIELAB",
        "CIEDE2000",
        "MiniBatchKMeans",
        "leave-one-reference-out calibration",
    ]


def test_home_contains_camera_interface():
    response = TestClient(app).get("/")
    assert response.status_code == 200
    assert "captureButton" in response.text
    assert "JINXI / COLOR LENS" in response.text
    assert 'data-language="zh-CN"' in response.text
    assert 'data-language="en"' in response.text
    assert "translations" in response.text
    assert "/learning" in response.text
    assert 'id="networkGraph"' in response.text
    assert 'id="diagnosticPanel"' in response.text
    assert 'id="referenceNetworkPanel"' in response.text
    assert 'id="captureTimeline"' in response.text
    assert 'id="mapViewCone"' in response.text
    assert 'id="onboarding"' in response.text
    assert 'id="boundaryAck"' in response.text
    assert 'id="boundaryButton"' in response.text
    assert 'id="backendStatus"' in response.text
    assert 'data-i18n="networkExplainer"' in response.text
    assert "candidateCombined" in response.text
    assert "candidateLocal" in response.text
    assert "candidateReferenceScore" in response.text
    assert "prefers-reduced-motion" in response.text


def test_learning_page_and_reference_model_are_available():
    client = TestClient(app)
    page = client.get("/learning")
    assert page.status_code == 200
    assert "Learning & Evidence" in page.text
    assert "evidence_boundaries" in page.text
    assert "reference-card-inner" in page.text
    assert "reference-original" in page.text
    assert "reference-original-previews" in page.text
    assert "data-full-original" in page.text
    assert "repeat(5, minmax(0, 1fr))" in page.text
    assert "rotateY(180deg)" in page.text
    assert "Research precedent · not implemented" in page.text
    assert "研究先例 · 当前未实现" in page.text

    response = client.get("/api/reference-model")
    assert response.status_code == 200
    model = response.json()
    assert model["reference_count"] == 13
    assert model["prototype_count"] == 28
    assert len(model["prototype_colors"]) == 28
    assert model["calibration"]["q95_delta_e"] > 0
    assert all(item["original_image"].startswith("/static/reference-originals/") for item in model["references"])
    assert all("user-confirmed" in item["license"] for item in model["references"])
    for reference in model["references"]:
        asset = client.get(reference["original_image"])
        assert asset.status_code == 200
        assert asset.headers["content-type"] == "image/jpeg"
        preview_path = reference["original_image"].replace(
            "/reference-originals/", "/reference-original-previews/"
        )
        preview = client.get(preview_path)
        assert preview.status_code == 200
        assert preview.headers["content-type"] == "image/jpeg"


def test_analysis_returns_linked_network_masks():
    image = np.full((150, 220, 3), [108, 121, 106], dtype=np.uint8)
    image[45:110, 80:145] = [235, 55, 157]
    buffer = io.BytesIO()
    Image.fromarray(image).save(buffer, format="PNG")

    response = TestClient(app).post(
        "/api/analyze",
        files={"image": ("synthetic.png", buffer.getvalue(), "image/png")},
        data={"sensitivity": "80", "detail": "120", "top_k": "3", "language": "en"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["network"]["nodes"]
    assert payload["network"]["edges"]
    assert payload["network"]["hub_id"]
    assert payload["network"]["nodes"][0]["mask"].startswith("data:image/png;base64,")
    assert payload["candidates"]
    first = payload["candidates"][0]
    assert first["score"] == first["combined_review_score"]
    assert 0 <= first["local_contrast_score"] <= 100
    assert 0 <= first["reference_novelty_score"] <= 100
    assert payload["diagnostic_data"]["points"]
    assert payload["diagnostic_data"]["candidates"]
    assert "adjacency" in payload["method"]["network_definition"]
