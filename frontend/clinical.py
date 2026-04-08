def classify_severity(area_pct: float) -> str:
    if area_pct < 5:
        return "Minimal"
    if area_pct < 20:
        return "Mild"
    if area_pct < 40:
        return "Moderate"
    return "Severe"


def classify_confidence(mean_conf: float, std_conf: float) -> tuple[str, str]:
    if mean_conf < 0.35 or std_conf > 0.30:
        return "Needs Manual Review", "Prediction confidence is unstable or low. Review carefully before use."
    if mean_conf < 0.55 or std_conf > 0.20:
        return "Review Recommended", "Prediction is usable for screening, but a clinician should confirm the result."
    return "High Confidence", "Prediction confidence is relatively stable for this image."


def build_clinical_summary(area_pct: float, severity: str, confidence_label: str) -> str:
    return (
        f"Estimated segmented involvement is {area_pct:.1f}% of the image, "
        f"which falls in the {severity.lower()} range. "
        f"Current model confidence status: {confidence_label.lower()}."
    )


def build_report_text(attributes: dict) -> str:
    lines = [
        "FEDSEG AI Clinical Summary",
        "",
        f"Filename: {attributes['Filename']}",
        f"Image Size: {attributes['Image width (px)']} x {attributes['Image height (px)']} px",
        f"Severity Band: {attributes['Severity band']}",
        f"Confidence Status: {attributes['Confidence status']}",
        f"Area Segmented: {attributes['Area segmented (%)']}%",
        f"Mean Confidence: {attributes['Mean confidence']}",
        f"Confidence Std: {attributes['Std confidence']}",
        f"Inference Time (ms): {attributes['Inference time (ms)']}",
        "",
        "Clinical Summary:",
        attributes["Clinical summary"],
        "",
        "Review Note:",
        attributes["Review note"],
        "",
        "System Metadata:",
        f"Model: {attributes['Model']}",
        f"Mask Transport: {attributes['Mask transport']}",
        f"Threshold: {attributes['Threshold']}",
        "",
        "Disclaimer: Research/demo output only. Clinical decisions require qualified physician review.",
    ]
    return "\n".join(str(line) for line in lines)
