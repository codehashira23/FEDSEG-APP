import cv2
import numpy as np
from fastapi.testclient import TestClient

from backend.api import app
from frontend.api_client import parse_mask_payload
from shared.api_contract import PREDICT_PATH


def _encode_test_image() -> bytes:
    image = np.full((2, 2, 3), 127, dtype=np.uint8)
    ok, buffer = cv2.imencode(".png", image)
    assert ok
    return buffer.tobytes()


def test_backend_predict_payload_is_accepted_by_frontend_parser(monkeypatch):
    client = TestClient(app)
    expected_mask = np.array([[0.0, 0.2], [0.8, 1.0]], dtype=np.float32)

    def fake_predict(_image):
        return expected_mask

    monkeypatch.setattr("backend.api.predict", fake_predict)

    response = client.post(
        PREDICT_PATH,
        files={"file": ("test.png", _encode_test_image(), "image/png")},
    )

    assert response.status_code == 200
    parsed_mask = parse_mask_payload(response.json())
    assert parsed_mask.shape == expected_mask.shape
    assert np.isclose(parsed_mask[1, 1], 1.0, atol=1e-2)
