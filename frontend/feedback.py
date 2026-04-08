import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_FEEDBACK_DIR = Path("outputs") / "feedback"


def feedback_dir(base_dir: Path | None = None) -> Path:
    target = base_dir or DEFAULT_FEEDBACK_DIR
    target.mkdir(parents=True, exist_ok=True)
    return target


def build_feedback_record(
    study_id: str,
    attributes: dict,
    review_decision: str,
    corrected_threshold: float,
    notes: str,
) -> dict:
    return {
        "study_id": study_id,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "filename": attributes["Filename"],
        "review_decision": review_decision,
        "corrected_threshold": round(float(corrected_threshold), 2),
        "notes": notes.strip(),
        "severity_band": attributes["Severity band"],
        "confidence_status": attributes["Confidence status"],
        "safety_status": attributes.get("Safety status", "Unknown"),
        "area_segmented_pct": attributes["Area segmented (%)"],
    }


def save_feedback_record(
    study_id: str,
    attributes: dict,
    review_decision: str,
    corrected_threshold: float,
    notes: str,
    base_dir: Path | None = None,
) -> Path:
    output_path = feedback_dir(base_dir) / f"{study_id}.json"
    record = build_feedback_record(study_id, attributes, review_decision, corrected_threshold, notes)
    output_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return output_path


def load_recent_feedback(limit: int = 5, base_dir: Path | None = None) -> list[dict]:
    target_dir = feedback_dir(base_dir)
    records = []
    for path in sorted(target_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            records.append(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
        if len(records) >= limit:
            break
    return records
