import base64

import cv2
import numpy as np
import requests

try:
    from shared.api_contract import HEALTH_PATH, MASK_ENCODING_PNG_BASE64
except ModuleNotFoundError:
    # Fallback constants for script execution modes where shared package is unresolved.
    HEALTH_PATH = "/health"
    MASK_ENCODING_PNG_BASE64 = "png_base64"


def check_backend_health(base_url: str, timeout: float = 2) -> bool:
    health_url = base_url.rstrip("/") + HEALTH_PATH
    try:
        response = requests.get(health_url, timeout=timeout)
        return response.status_code == 200
    except requests.RequestException:
        return False


def request_prediction(api_url: str, file_bytes: bytes, timeout: float = 60):
    response = requests.post(api_url, files={"file": file_bytes}, timeout=timeout)
    response.raise_for_status()
    return response.json()


def parse_mask_payload(payload: dict) -> np.ndarray:
    encoding = payload.get("mask_encoding", MASK_ENCODING_PNG_BASE64)
    if "mask_png_base64" in payload:
        if encoding != MASK_ENCODING_PNG_BASE64:
            raise ValueError(f"Unsupported mask encoding: {encoding}")
        return decode_mask_png_base64(payload["mask_png_base64"])
    if "mask" in payload:
        return np.array(payload["mask"], dtype=np.float32)
    raise ValueError("No mask payload found in backend response.")


def decode_mask_png_base64(mask_png_base64: str) -> np.ndarray:
    mask_bytes = base64.b64decode(mask_png_base64)
    np_arr = np.frombuffer(mask_bytes, np.uint8)
    mask = cv2.imdecode(np_arr, cv2.IMREAD_GRAYSCALE)
    if mask is None:
        raise ValueError("Could not decode mask payload from backend.")
    return mask.astype(np.float32) / 255.0
