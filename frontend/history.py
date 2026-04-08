import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_HISTORY_DIR = Path("outputs") / "history"


def make_study_id(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()[:16]


def history_dir(base_dir: Path | None = None) -> Path:
    target = base_dir or DEFAULT_HISTORY_DIR
    target.mkdir(parents=True, exist_ok=True)
    return target


def build_history_record(study_id: str, attributes: dict) -> dict:
    return {
        "study_id": study_id,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "filename": attributes["Filename"],
        "severity_band": attributes["Severity band"],
        "confidence_status": attributes["Confidence status"],
        "area_segmented_pct": attributes["Area segmented (%)"],
        "mean_confidence": attributes["Mean confidence"],
        "inference_time_ms": attributes["Inference time (ms)"],
        "clinical_summary": attributes["Clinical summary"],
    }


def save_history_record(study_id: str, attributes: dict, base_dir: Path | None = None) -> Path:
    target_dir = history_dir(base_dir)
    output_path = target_dir / f"{study_id}.json"
    output_path.write_text(json.dumps(build_history_record(study_id, attributes), indent=2), encoding="utf-8")
    return output_path


def load_recent_history(limit: int = 5, base_dir: Path | None = None) -> list[dict]:
    target_dir = history_dir(base_dir)
    records = []
    for path in sorted(target_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            records.append(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
        if len(records) >= limit:
            break
    return records


def build_batch_row(filename: str, attributes: dict, status: str = "Completed") -> dict:
    return {
        "Filename": filename,
        "Status": status,
        "Severity": attributes["Severity band"],
        "Review Status": attributes["Confidence status"],
        "Area Segmented (%)": attributes["Area segmented (%)"],
        "Mean Confidence": attributes["Mean confidence"],
        "Inference Time (ms)": attributes["Inference time (ms)"],
    }
