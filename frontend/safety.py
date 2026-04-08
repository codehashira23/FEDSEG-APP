import cv2
import numpy as np


def assess_image_quality(image_bgr: np.ndarray) -> dict:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    brightness = float(np.mean(gray))
    contrast = float(np.std(gray))
    blur_variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    height, width = gray.shape
    aspect_ratio = width / max(height, 1)

    issues = []
    if brightness < 35:
        issues.append("Image is very dark")
    elif brightness > 220:
        issues.append("Image is very bright")

    if contrast < 18:
        issues.append("Image contrast is low")

    if blur_variance < 45:
        issues.append("Image appears blurry")

    if aspect_ratio < 0.6 or aspect_ratio > 1.8:
        issues.append("Image aspect ratio is unusual for a chest X-ray")

    overall = "pass"
    if len(issues) >= 3:
        overall = "high_risk"
    elif issues:
        overall = "review"

    return {
        "brightness": round(brightness, 2),
        "contrast": round(contrast, 2),
        "blur_variance": round(blur_variance, 2),
        "aspect_ratio": round(aspect_ratio, 3),
        "issues": issues,
        "overall": overall,
    }


def build_safety_assessment(quality: dict, mean_conf: float, std_conf: float) -> dict:
    reasons = list(quality["issues"])
    review_required = quality["overall"] != "pass"

    if mean_conf < 0.3:
        reasons.append("Model confidence is very low")
        review_required = True
    if std_conf > 0.3:
        reasons.append("Prediction confidence is unstable")
        review_required = True

    status = "Standard Review"
    if review_required:
        status = "Manual Review Required"
    elif mean_conf < 0.55 or std_conf > 0.2:
        status = "Manual Review Recommended"

    return {
        "status": status,
        "reasons": reasons,
        "quality": quality,
    }
