import base64

import cv2
import numpy as np

from frontend.api_client import decode_mask_png_base64, parse_mask_payload
from frontend.clinical import build_clinical_summary, build_report_text, classify_confidence, classify_severity
from frontend.image_utils import make_comparison_split, make_overlay, mask_to_rgb


def test_decode_mask_png_base64_round_trip():
    original = np.array([[0, 127], [255, 64]], dtype=np.uint8)
    ok, buffer = cv2.imencode(".png", original)
    assert ok

    decoded = decode_mask_png_base64(base64.b64encode(buffer.tobytes()).decode("ascii"))

    assert decoded.shape == (2, 2)
    assert np.isclose(decoded[0, 0], 0.0)
    assert np.isclose(decoded[1, 0], 1.0)


def test_mask_to_rgb_returns_three_channels():
    mask = np.array([[0.1, 0.9], [0.5, 0.7]], dtype=np.float32)

    rgb = mask_to_rgb(mask, "Viridis")

    assert rgb.shape == (2, 2, 3)
    assert rgb.dtype == np.uint8


def test_parse_mask_payload_supports_legacy_mask_arrays():
    payload = {"mask": [[0.0, 0.5], [1.0, 0.25]]}

    mask = parse_mask_payload(payload)

    assert mask.shape == (2, 2)
    assert np.isclose(mask[1, 0], 1.0)


def test_clinical_classifiers_cover_low_and_high_risk_cases():
    assert classify_severity(2.0) == "Minimal"
    assert classify_severity(25.0) == "Moderate"
    assert classify_severity(55.0) == "Severe"

    low_conf_label, _ = classify_confidence(0.2, 0.35)
    high_conf_label, _ = classify_confidence(0.8, 0.05)
    assert low_conf_label == "Needs Manual Review"
    assert high_conf_label == "High Confidence"


def test_clinical_summary_mentions_severity_and_confidence():
    summary = build_clinical_summary(18.4, "Mild", "Review Recommended")

    assert "18.4%" in summary
    assert "mild" in summary.lower()
    assert "review recommended" in summary.lower()


def test_report_text_contains_core_doctor_facing_fields():
    report = build_report_text(
        {
            "Filename": "scan-01.png",
            "Image width (px)": 512,
            "Image height (px)": 512,
            "Severity band": "Moderate",
            "Confidence status": "Review Recommended",
            "Area segmented (%)": 22.5,
            "Mean confidence": 0.61,
            "Std confidence": 0.14,
            "Inference time (ms)": 38.2,
            "Clinical summary": "Estimated segmented involvement is 22.5% of the image.",
            "Review note": "Prediction is usable for screening, but a clinician should confirm the result.",
            "Model": "FEDSEG ResNet-UNet (FSSS)",
            "Mask transport": "png_base64",
            "Threshold": 0.5,
        }
    )

    assert "FEDSEG AI Clinical Summary" in report
    assert "scan-01.png" in report
    assert "Severity Band: Moderate" in report
    assert "Confidence Status: Review Recommended" in report
    assert "Disclaimer:" in report


def test_overlay_and_split_preserve_shape():
    original = np.zeros((4, 4, 3), dtype=np.uint8)
    mask = np.zeros((4, 4), dtype=np.float32)
    mask[:, 2:] = 1.0

    overlay = make_overlay(original, mask, threshold=0.5, alpha=0.5, tint=[255, 0, 0])
    compare = make_comparison_split(original, overlay, 0.5)

    assert overlay.shape == original.shape
    assert compare.shape == original.shape
