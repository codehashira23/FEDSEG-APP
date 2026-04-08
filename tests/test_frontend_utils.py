from pathlib import Path

import base64

import cv2
import numpy as np

from frontend.api_client import decode_mask_png_base64, parse_mask_payload
from frontend.clinical import build_clinical_summary, build_report_text, classify_confidence, classify_severity
from frontend.feedback import build_feedback_record, load_recent_feedback, save_feedback_record
from frontend.history import build_batch_row, load_recent_history, make_study_id, save_history_record
from frontend.image_utils import make_comparison_split, make_overlay, mask_to_rgb
from frontend.safety import assess_image_quality, build_safety_assessment


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


def test_history_save_and_load_returns_latest_records(tmp_path: Path):
    attrs = {
        "Filename": "scan-01.png",
        "Severity band": "Moderate",
        "Confidence status": "Review Recommended",
        "Area segmented (%)": 22.5,
        "Mean confidence": 0.61,
        "Inference time (ms)": 38.2,
        "Clinical summary": "Estimated segmented involvement is 22.5% of the image.",
    }
    save_history_record("study-a", attrs, tmp_path)
    attrs["Filename"] = "scan-02.png"
    save_history_record("study-b", attrs, tmp_path)

    records = load_recent_history(limit=2, base_dir=tmp_path)

    assert len(records) == 2
    filenames = {record["filename"] for record in records}
    assert filenames == {"scan-01.png", "scan-02.png"}


def test_make_study_id_is_stable():
    payload = b"sample-bytes"
    assert make_study_id(payload) == make_study_id(payload)


def test_build_batch_row_extracts_queue_fields():
    attrs = {
        "Severity band": "Mild",
        "Confidence status": "High Confidence",
        "Area segmented (%)": 12.4,
        "Mean confidence": 0.78,
        "Inference time (ms)": 41.2,
    }

    row = build_batch_row("scan.png", attrs)

    assert row["Filename"] == "scan.png"
    assert row["Status"] == "Completed"
    assert row["Severity"] == "Mild"


def test_feedback_save_and_load_round_trip(tmp_path: Path):
    attributes = {
        "Filename": "scan-01.png",
        "Severity band": "Moderate",
        "Confidence status": "Review Recommended",
        "Safety status": "Manual Review Recommended",
        "Area segmented (%)": 22.5,
    }
    save_feedback_record(
        "study-a",
        attributes,
        "Accepted with threshold adjustment",
        0.45,
        "Slightly lower threshold gives a cleaner contour.",
        base_dir=tmp_path,
    )

    records = load_recent_feedback(limit=1, base_dir=tmp_path)

    assert len(records) == 1
    assert records[0]["filename"] == "scan-01.png"
    assert records[0]["review_decision"] == "Accepted with threshold adjustment"


def test_build_feedback_record_captures_review_metadata():
    record = build_feedback_record(
        "study-a",
        {
            "Filename": "scan-02.png",
            "Severity band": "Mild",
            "Confidence status": "High Confidence",
            "Safety status": "Standard Review",
            "Area segmented (%)": 10.0,
        },
        "Accepted",
        0.5,
        "Looks consistent with expectations.",
    )

    assert record["study_id"] == "study-a"
    assert record["corrected_threshold"] == 0.5
    assert record["safety_status"] == "Standard Review"


def test_assess_image_quality_flags_dark_blurry_images():
    image = np.zeros((32, 32, 3), dtype=np.uint8)

    quality = assess_image_quality(image)

    assert quality["overall"] in {"review", "high_risk"}
    assert quality["issues"]


def test_build_safety_assessment_escalates_manual_review():
    quality = {
        "brightness": 10.0,
        "contrast": 5.0,
        "blur_variance": 1.0,
        "aspect_ratio": 1.0,
        "issues": ["Image is very dark", "Image appears blurry"],
        "overall": "review",
    }

    assessment = build_safety_assessment(quality, mean_conf=0.25, std_conf=0.31)

    assert assessment["status"] == "Manual Review Required"
    assert "Model confidence is very low" in assessment["reasons"]


def test_overlay_and_split_preserve_shape():
    original = np.zeros((4, 4, 3), dtype=np.uint8)
    mask = np.zeros((4, 4), dtype=np.float32)
    mask[:, 2:] = 1.0

    overlay = make_overlay(original, mask, threshold=0.5, alpha=0.5, tint=[255, 0, 0])
    compare = make_comparison_split(original, overlay, 0.5)

    assert overlay.shape == original.shape
    assert compare.shape == original.shape
