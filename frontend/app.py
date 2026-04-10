import hashlib
from pathlib import Path
import sys

import cv2
import numpy as np
import requests
import streamlit as st

# Ensure repo root is importable even when Streamlit runs this script from frontend/.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from frontend.api_client import check_backend_health, parse_mask_payload, request_prediction
    from frontend.clinical import classify_confidence, classify_severity
    from frontend.config import DEFAULT_API_URL
    from frontend.feedback import load_recent_feedback, save_feedback_record
    from frontend.history import build_batch_row, load_recent_history, make_study_id, save_history_record
    from frontend.image_utils import decode_uploaded_image, make_comparison_split, make_overlay, mask_to_rgb
    from frontend.safety import assess_image_quality, build_safety_assessment
    from frontend.styles import inject_styles
    from frontend.ui import (
        build_attributes,
        render_batch_queue,
        render_empty_state,
        render_feedback_panel,
        render_model_info,
        render_recent_feedback,
        render_recent_history,
        render_results,
        render_safety_panel,
        render_topbar,
    )
    from shared.api_contract import PREDICT_PATH
except ModuleNotFoundError:
    # Fallback for environments where Streamlit runs this file without repo root on sys.path.
    from api_client import check_backend_health, parse_mask_payload, request_prediction
    from clinical import classify_confidence, classify_severity
    from config import DEFAULT_API_URL
    from feedback import load_recent_feedback, save_feedback_record
    from history import build_batch_row, load_recent_history, make_study_id, save_history_record
    from image_utils import decode_uploaded_image, make_comparison_split, make_overlay, mask_to_rgb
    from safety import assess_image_quality, build_safety_assessment
    from styles import inject_styles
    from ui import (
        build_attributes,
        render_batch_queue,
        render_empty_state,
        render_feedback_panel,
        render_model_info,
        render_recent_feedback,
        render_recent_history,
        render_results,
        render_safety_panel,
        render_topbar,
    )
    PREDICT_PATH = "/predict"

st.set_page_config(
    page_title="FEDSEG AI Dashboard",
    page_icon=":stethoscope:",
    layout="wide",
    initial_sidebar_state="expanded",
)


def render_sidebar():
    with st.sidebar:
        st.markdown("## Control Panel")
        st.markdown("Configure endpoint, visualization, and output behavior.")
        api_base = st.text_input(
            "Backend API URL",
            value=DEFAULT_API_URL,
            help="Example: http://localhost:8000",
        )
        st.markdown("### Segmentation")
        threshold = st.slider(
            "Segmentation threshold",
            min_value=0.2,
            max_value=0.8,
            value=0.5,
            step=0.05,
            help="Pixels above this value are treated as segmented region.",
        )
        colormap = st.selectbox(
            "Mask colormap",
            ["Purple (medical)", "Green (medical)", "Viridis", "Plasma", "Grayscale"],
            index=0,
        )
        overlay_strength = st.slider(
            "Overlay intensity",
            min_value=0.20,
            max_value=0.80,
            value=0.45,
            step=0.05,
            help="Higher values make segmentation overlay stronger.",
        )
        overlay_tone = st.selectbox(
            "Overlay tone",
            ["Violet", "Cyan", "Emerald", "Amber"],
            index=0,
        )
        st.markdown("### Comparison")
        compare_split = st.slider(
            "Before/After split position",
            min_value=0.05,
            max_value=0.95,
            value=0.5,
            step=0.05,
            help="Controls split line in the comparison view.",
        )
        show_3d = st.toggle("Enable 3D volume rendering", value=True)
        st.markdown("---")
        st.caption("Guided flow: Upload -> Process -> Review -> Export")
        st.caption("For research/demo use only.")
    return {
        "api_base": api_base,
        "threshold": threshold,
        "colormap": colormap,
        "overlay_strength": overlay_strength,
        "overlay_tone": overlay_tone,
        "compare_split": compare_split,
        "show_3d": show_3d,
    }


def render_upload():
    st.markdown('<div class="glass section-card">', unsafe_allow_html=True)
    st.markdown('<p class="section-title">Upload Section</p>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Import one PNG or JPEG image to start segmentation inference.</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="upload-hint">Recommended: frontal chest X-ray PNG or JPEG for best visual consistency.</div>',
        unsafe_allow_html=True,
    )
    uploaded_files = st.file_uploader(
        "Upload image",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )
    st.markdown("</div>", unsafe_allow_html=True)
    return uploaded_files


def compute_upload_signature(uploaded_files) -> str:
    digest = hashlib.sha256()
    for uploaded_file in uploaded_files:
        file_bytes = uploaded_file.getvalue()
        digest.update((uploaded_file.name or "").encode("utf-8"))
        digest.update(file_bytes)
    return digest.hexdigest()


def process_uploaded_file(uploaded_file, file_bytes, controls):
    decoded = decode_uploaded_image(file_bytes)
    if decoded is None:
        raise ValueError("Could not decode image. Please upload a valid PNG or JPEG file.")

    quality_assessment = assess_image_quality(decoded)
    original_rgb = cv2.cvtColor(decoded, cv2.COLOR_BGR2RGB)
    h_orig, w_orig = original_rgb.shape[:2]
    filename = uploaded_file.name or "image.png"

    payload = request_prediction(controls["api_base"].rstrip("/") + PREDICT_PATH, file_bytes)
    probability_mask = parse_mask_payload(payload)
    probability_mask = cv2.resize(probability_mask, (w_orig, h_orig), interpolation=cv2.INTER_LINEAR)

    mean_conf = float(np.mean(probability_mask))
    std_conf = float(np.std(probability_mask))
    safety_assessment = build_safety_assessment(quality_assessment, mean_conf, std_conf)

    return {
        "file_bytes": file_bytes,
        "filename": filename,
        "original_rgb": original_rgb,
        "payload": payload,
        "probability_mask": probability_mask,
        "safety_assessment": safety_assessment,
    }


def build_display_result(base_result, controls):
    original_rgb = base_result["original_rgb"]
    probability_mask = base_result["probability_mask"]
    payload = base_result["payload"]
    filename = base_result["filename"]
    h_orig, w_orig = original_rgb.shape[:2]

    area_pct = 100.0 * (probability_mask > controls["threshold"]).sum() / (probability_mask.size or 1)
    mean_conf = float(np.mean(probability_mask))
    std_conf = float(np.std(probability_mask))
    severity = classify_severity(area_pct)
    confidence_status, _ = classify_confidence(mean_conf, std_conf)

    display_mask = (probability_mask > controls["threshold"]).astype(np.float32)
    mask_rgb = mask_to_rgb(display_mask, controls["colormap"])
    tone_map = {
        "Violet": [79, 70, 229],
        "Cyan": [14, 165, 233],
        "Emerald": [16, 185, 129],
        "Amber": [245, 158, 11],
    }
    overlay = make_overlay(
        original_rgb,
        probability_mask,
        controls["threshold"],
        alpha=controls["overlay_strength"],
        tint=tone_map[controls["overlay_tone"]],
    )
    compare_view = make_comparison_split(original_rgb, overlay, controls["compare_split"])

    attributes = build_attributes(
        filename,
        payload,
        w_orig,
        h_orig,
        area_pct,
        mean_conf,
        std_conf,
        controls["threshold"],
    )
    attributes["Severity band"] = severity
    attributes["Confidence status"] = confidence_status
    attributes["Safety status"] = base_result["safety_assessment"]["status"]
    attributes["Safety reasons"] = (
        "; ".join(base_result["safety_assessment"]["reasons"])
        if base_result["safety_assessment"]["reasons"]
        else "None"
    )

    return {
        **base_result,
        "mask_rgb": mask_rgb,
        "overlay": overlay,
        "compare_view": compare_view,
        "mask_resized": probability_mask,
        "attributes": attributes,
    }


def main():
    inject_styles()
    controls = render_sidebar()

    backend_ok = check_backend_health(controls["api_base"])
    render_topbar(backend_ok)
    render_recent_history(load_recent_history())
    render_recent_feedback(load_recent_feedback())

    uploaded_files = render_upload()
    if not uploaded_files:
        st.session_state.pop("processed_results", None)
        st.session_state.pop("processed_signature", None)
        render_empty_state()
        render_model_info()
        st.stop()

    run_requested = st.button("Run Inference", type="primary", use_container_width=True)
    upload_signature = compute_upload_signature(uploaded_files)
    if st.session_state.get("processed_signature") != upload_signature:
        st.session_state.pop("processed_results", None)
        st.session_state.pop("processed_signature", None)

    if not run_requested and "processed_results" not in st.session_state:
        st.info("Files are ready. Click `Run Inference` to generate masks.")
        render_model_info()
        st.stop()

    st.markdown('<div class="glass section-card">', unsafe_allow_html=True)
    st.markdown('<p class="section-title">Inference</p>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Model is processing the uploaded image set and generating confidence masks.</div>',
        unsafe_allow_html=True,
    )
    progress = st.progress(8, text="Preparing request...")

    if run_requested or "processed_results" not in st.session_state:
        processed_base = []
        try:
            with st.spinner("Running segmentation model..."):
                total_files = len(uploaded_files)
                for index, uploaded_file in enumerate(uploaded_files, start=1):
                    progress_value = int(10 + ((index - 1) / max(total_files, 1)) * 80)
                    progress.progress(progress_value, text=f"Processing {uploaded_file.name} ({index}/{total_files})...")
                    file_bytes = uploaded_file.getvalue()
                    processed_base.append(process_uploaded_file(uploaded_file, file_bytes, controls))
                progress.progress(100, text="Inference complete")
            st.session_state["processed_results"] = processed_base
            st.session_state["processed_signature"] = upload_signature
        except requests.exceptions.RequestException as exc:
            st.error(f"API error: {exc}")
            if hasattr(exc, "response") and exc.response is not None:
                try:
                    st.json(exc.response.json())
                except Exception:
                    st.code(exc.response.text)
            st.markdown("</div>", unsafe_allow_html=True)
            render_model_info()
            st.stop()
        except ValueError as exc:
            st.error(str(exc))
            st.markdown("</div>", unsafe_allow_html=True)
            render_model_info()
            st.stop()
    else:
        processed_base = st.session_state["processed_results"]
        progress.progress(100, text="Using cached inference results")

    st.success("Segmentation completed successfully.")
    st.markdown("</div>", unsafe_allow_html=True)

    processed = [build_display_result(item, controls) for item in processed_base]
    batch_rows = []
    for result in processed:
        study_id = make_study_id(result["file_bytes"])
        save_history_record(study_id, result["attributes"])
        batch_rows.append(build_batch_row(result["filename"], result["attributes"]))

    render_batch_queue(batch_rows)
    primary = processed[0]
    render_safety_panel(primary["safety_assessment"])
    primary_study_id = make_study_id(primary["file_bytes"])
    feedback_state = render_feedback_panel(primary_study_id, primary["filename"], controls["threshold"])
    if feedback_state["submitted"]:
        save_feedback_record(
            primary_study_id,
            primary["attributes"],
            feedback_state["review_decision"],
            feedback_state["corrected_threshold"],
            feedback_state["notes"],
        )
        st.success("Clinician feedback saved.")
    render_results(
        primary["original_rgb"],
        primary["mask_rgb"],
        primary["overlay"],
        primary["compare_view"],
        primary["mask_resized"],
        primary["attributes"],
        controls["threshold"],
        controls["show_3d"],
    )
    render_model_info()


if __name__ == "__main__":
    main()
