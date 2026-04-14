from pathlib import Path

import base64
import cv2
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from frontend.clinical import build_clinical_summary, build_report_text, classify_confidence, classify_severity


LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "logo.png"


def image_full_width(image, **kwargs):
    """Render images across Streamlit versions."""
    try:
        st.image(image, use_container_width=True, **kwargs)
    except TypeError:
        st.image(image, use_column_width=True, **kwargs)


def render_topbar(backend_ok: bool):
    status_color = "#10b981" if backend_ok else "#ef4444"
    status_text = "System Online" if backend_ok else "System Offline"
    st.markdown('<div class="topbar topbar-clean">', unsafe_allow_html=True)
    left_col, right_col = st.columns([6, 2], vertical_alignment="center")
    with left_col:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=900)
        st.markdown(
            """
            <p class="brand-title">FEDSEG AI Segmentation Console</p>
            <p class="brand-sub">Federated ResNet-UNet medical imaging dashboard with real-time inference insights.</p>
            <div class="topbar-badges">
                <span class="pill">Medical Imaging</span>
                <span class="pill">Federated Learning</span>
                <span class="pill">Real-time Inference</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right_col:
        st.markdown(
            f"""
            <div class="status-wrap">
                <span class="status-dot" style="background:{status_color};"></span>
                <span>{status_text}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def render_metric_card(label: str, value: str):
    st.markdown(
        f"""
        <div class="metric-card">
            <p class="metric-label">{label}</p>
            <p class="metric-value">{value}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state():
    st.markdown(
        """
        <div class="glass section-card">
            <div class="empty-state">
                <div class="empty-title">No study loaded</div>
                <p class="empty-sub">Upload a medical image from the left panel to run segmentation and unlock analytics.</p>
                <div class="step-row">
                    <span class="step-chip">1. Upload</span>
                    <span class="step-chip">2. Infer</span>
                    <span class="step-chip">3. Analyze</span>
                    <span class="step-chip">4. Export</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_model_info():
    st.markdown('<div class="glass section-card">', unsafe_allow_html=True)
    st.markdown('<p class="section-title">Model Info</p>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Core inference model and deployment metadata.</div>',
        unsafe_allow_html=True,
    )
    model_data = pd.DataFrame(
        [
            {"Property": "Model Family", "Value": "ResNet-UNet"},
            {"Property": "Training Setup", "Value": "Federated Learning (FSSS)"},
            {"Property": "Input Resolution", "Value": "224 x 224 (inference preprocess)"},
            {"Property": "Output", "Value": "Single-channel segmentation mask [0,1]"},
            {"Property": "Transport", "Value": "Compressed PNG mask payload"},
            {"Property": "Deployment", "Value": "FastAPI + Streamlit"},
            {"Property": "Clinical Status", "Value": "Research/Demo only"},
        ]
    )
    st.dataframe(model_data, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_recent_history(records: list[dict]):
    st.markdown('<div class="glass section-card">', unsafe_allow_html=True)
    st.markdown('<p class="section-title">Recent Studies</p>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Recently saved local prediction summaries for quick follow-up review.</div>',
        unsafe_allow_html=True,
    )
    if not records:
        st.caption("No saved prediction history yet. Process a study to populate this section.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    history_df = pd.DataFrame(records).rename(
        columns={
            "saved_at": "Saved At",
            "filename": "Filename",
            "severity_band": "Severity",
            "confidence_status": "Review Status",
            "area_segmented_pct": "Area Segmented (%)",
            "mean_confidence": "Mean Confidence",
            "inference_time_ms": "Inference Time (ms)",
            "clinical_summary": "Clinical Summary",
        }
    )
    st.dataframe(history_df, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_recent_feedback(records: list[dict]):
    st.markdown('<div class="glass section-card">', unsafe_allow_html=True)
    st.markdown('<p class="section-title">Recent Feedback</p>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Most recent clinician review decisions saved from this workstation.</div>',
        unsafe_allow_html=True,
    )
    if not records:
        st.caption("No feedback has been saved yet.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    feedback_df = pd.DataFrame(records).rename(
        columns={
            "saved_at": "Saved At",
            "filename": "Filename",
            "review_decision": "Decision",
            "corrected_threshold": "Corrected Threshold",
            "severity_band": "Severity",
            "confidence_status": "Confidence Status",
            "safety_status": "Safety Status",
            "area_segmented_pct": "Area Segmented (%)",
            "notes": "Notes",
        }
    )
    st.dataframe(feedback_df, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_batch_queue(batch_rows: list[dict]):
    st.markdown('<div class="glass section-card">', unsafe_allow_html=True)
    st.markdown('<p class="section-title">Batch Queue Summary</p>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Summary of files processed in the current run.</div>',
        unsafe_allow_html=True,
    )
    if not batch_rows:
        st.caption("Batch summary will appear here when multiple studies are processed.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    queue_df = pd.DataFrame(batch_rows)
    st.dataframe(queue_df, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_safety_panel(safety_assessment: dict):
    st.markdown('<div class="glass section-card">', unsafe_allow_html=True)
    st.markdown('<p class="section-title">Safety Review</p>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Pre-inference image checks and stronger manual-review guidance.</div>',
        unsafe_allow_html=True,
    )

    status = safety_assessment["status"]
    reasons = safety_assessment["reasons"]
    quality = safety_assessment["quality"]

    if status == "Manual Review Required":
        st.error(status)
    elif status == "Manual Review Recommended":
        st.warning(status)
    else:
        st.success(status)

    if reasons:
        st.write("Safety flags:")
        for reason in reasons:
            st.write(f"- {reason}")
    else:
        st.caption("No major image-quality or confidence safety flags were detected.")

    quality_df = pd.DataFrame(
        [
            {"Metric": "Brightness", "Value": quality["brightness"]},
            {"Metric": "Contrast", "Value": quality["contrast"]},
            {"Metric": "Blur Variance", "Value": quality["blur_variance"]},
            {"Metric": "Aspect Ratio", "Value": quality["aspect_ratio"]},
        ]
    )
    st.dataframe(quality_df, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_feedback_panel(study_id: str, filename: str, threshold: float):
    st.markdown('<div class="glass section-card">', unsafe_allow_html=True)
    st.markdown('<p class="section-title">Clinician Review</p>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Capture acceptance, threshold correction, and review notes for this study.</div>',
        unsafe_allow_html=True,
    )

    with st.form(key=f"feedback_form_{study_id}"):
        review_decision = st.radio(
            "Review decision",
            ["Accepted", "Accepted with threshold adjustment", "Needs correction", "Rejected"],
            horizontal=True,
        )
        corrected_threshold = st.slider(
            "Corrected threshold",
            min_value=0.20,
            max_value=0.80,
            value=float(threshold),
            step=0.05,
            help=f"Current threshold for {filename} is {threshold:.2f}. Save an adjusted threshold if needed.",
        )
        notes = st.text_area(
            "Review notes",
            placeholder="Example: Overlay acceptable but lower right region should be tighter.",
            height=100,
        )
        submitted = st.form_submit_button("Save Feedback", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)
    return {
        "submitted": submitted,
        "review_decision": review_decision,
        "corrected_threshold": corrected_threshold,
        "notes": notes,
    }


def build_attributes(filename, payload, width, height, area_pct, mean_conf, std_conf, threshold):
    severity = classify_severity(area_pct)
    confidence_label, confidence_note = classify_confidence(mean_conf, std_conf)
    return {
        "Filename": filename,
        "Image width (px)": payload.get("image_width", width),
        "Image height (px)": payload.get("image_height", height),
        "Area segmented (%)": round(area_pct, 2),
        "Severity band": severity,
        "Mean confidence": round(mean_conf, 4),
        "Confidence status": confidence_label,
        "Clinical summary": build_clinical_summary(area_pct, severity, confidence_label),
        "Review note": confidence_note,
        "Std confidence": round(std_conf, 4),
        "Mask min": round(payload.get("mask_min", 0.0), 4),
        "Mask max": round(payload.get("mask_max", 1.0), 4),
        "Threshold": threshold,
        "Inference time (ms)": payload.get("inference_time_ms"),
        "Mask transport": payload.get("mask_encoding", "png_base64"),
        "Model": "FEDSEG ResNet-UNet (FSSS)",
    }


def _array_to_base64_data_uri(arr, is_mask=False):
    if is_mask:
        arr_uint8 = (np.clip(arr, 0, 1) * 255).astype(np.uint8)
        _, buffer = cv2.imencode('.png', arr_uint8)
    else:
        # Assuming original is RGB, convert to BGR for cv2
        arr_bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        _, buffer = cv2.imencode('.png', arr_bgr)
    b64_str = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/png;base64,{b64_str}"


def render_results(original_rgb, mask_rgb, overlay, compare_view, mask_resized, attributes, threshold, show_3d):
    area_pct = attributes["Area segmented (%)"]
    mean_conf = attributes["Mean confidence"]
    inf_ms = attributes["Inference time (ms)"]
    severity = attributes["Severity band"]
    confidence_status = attributes["Confidence status"]
    review_note = attributes["Review note"]
    foreground_pixels = int((mask_resized > threshold).sum())
    total_pixels = int(mask_resized.size)
    height, width = original_rgb.shape[:2]

    st.markdown('<div class="glass section-card">', unsafe_allow_html=True)
    st.markdown('<p class="section-title">Results Section</p>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Key outputs and confidence indicators for current image.</div>',
        unsafe_allow_html=True,
    )

    if confidence_status == "Needs Manual Review":
        st.warning(f"{confidence_status}: {review_note}")
    elif confidence_status == "Review Recommended":
        st.info(f"{confidence_status}: {review_note}")
    else:
        st.success(f"{confidence_status}: {review_note}")

    st.markdown("### Clinical Snapshot")
    c1, c2 = st.columns(2)
    with c1:
        render_metric_card("Severity Band", severity)
    with c2:
        render_metric_card("Review Status", confidence_status)

    st.caption(attributes["Clinical summary"])

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_metric_card("Area Segmented", f"{area_pct:.1f}%")
    with m2:
        render_metric_card("Mean Confidence", f"{mean_conf:.3f}")
    with m3:
        render_metric_card("Inference Time", f"{inf_ms} ms" if inf_ms is not None else "N/A")
    with m4:
        render_metric_card("Threshold", f"{threshold:.2f}")

    s1, s2, s3 = st.columns(3)
    with s1:
        st.markdown(
            f"""
            <div class="mini-stat">
                <p class="mini-stat-label">Segmented Pixels</p>
                <p class="mini-stat-value">{foreground_pixels:,}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with s2:
        st.markdown(
            f"""
            <div class="mini-stat">
                <p class="mini-stat-label">Total Pixels</p>
                <p class="mini-stat-value">{total_pixels:,}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with s3:
        st.markdown(
            f"""
            <div class="mini-stat">
                <p class="mini-stat-label">Input Resolution</p>
                <p class="mini-stat-value">{width} x {height}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    tab_viz, tab_3d, tab_analytics, tab_table, tab_attrs = st.tabs(
        ["Visualization", "3D Topography", "Analytics", "Attributes Table", "Attribute Details"]
    )

    with tab_viz:
        st.markdown("### Image Comparison")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.caption("Original")
            image_full_width(original_rgb)
        with c2:
            st.caption("Thresholded Mask")
            image_full_width(mask_rgb)
        with c3:
            st.caption("Overlay")
            image_full_width(overlay)

        # st.markdown("### Before/After Split View")
        # st.caption("Left side: original image | Right side: overlay result")
        # image_full_width(compare_view)

        st.markdown("### Export")
        report_text = build_report_text(attributes)
        d1, d2, d3, d4 = st.columns(4)
        with d1:
            st.markdown('<div class="download-card">', unsafe_allow_html=True)
            mask_uint8 = (np.clip(mask_resized, 0, 1) * 255).astype(np.uint8)
            _, mask_buf = cv2.imencode(".png", mask_uint8)
            st.download_button(
                "Download Mask PNG",
                data=mask_buf.tobytes(),
                file_name="mask.png",
                mime="image/png",
                use_container_width=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)
        with d2:
            st.markdown('<div class="download-card">', unsafe_allow_html=True)
            export_df = pd.DataFrame([{"Attribute": k, "Value": v} for k, v in attributes.items()])
            st.download_button(
                "Download Attributes CSV",
                data=export_df.to_csv(index=False),
                file_name="attributes.csv",
                mime="text/csv",
                use_container_width=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)
        with d3:
            st.markdown('<div class="download-card">', unsafe_allow_html=True)
            overlay_bgr = cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR)
            _, overlay_buf = cv2.imencode(".png", overlay_bgr)
            st.download_button(
                "Download Overlay PNG",
                data=overlay_buf.tobytes(),
                file_name="overlay.png",
                mime="image/png",
                use_container_width=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)
        with d4:
            st.markdown('<div class="download-card">', unsafe_allow_html=True)
            st.download_button(
                "Download Report TXT",
                data=report_text,
                file_name="clinical-summary.txt",
                mime="text/plain",
                use_container_width=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### Report Preview")
        st.code(report_text, language="text")

    with tab_3d:
        st.markdown("### Interactive 3D X-Ray Topography")
        st.caption("Drag to rotate, scroll to zoom. The segmentation mask acts as a displacement map to lift the structure.")
        
        orig_uri = _array_to_base64_data_uri(original_rgb, is_mask=False)
        mask_uri = _array_to_base64_data_uri(mask_resized, is_mask=True)
        img_aspect = width / height
        plane_width = 5.0
        plane_height = 5.0 / img_aspect
        
        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ margin: 0; padding: 0; overflow: hidden; background-color: #f8fafc; border-radius: 8px; }}
                canvas {{ width: 100%; height: 100%; display: block; }}
            </style>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
        </head>
        <body>
            <script>
                const scene = new THREE.Scene();
                const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 100);
                
                const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
                renderer.setSize(window.innerWidth, window.innerHeight);
                renderer.setPixelRatio(window.devicePixelRatio);
                document.body.appendChild(renderer.domElement);
                
                const controls = new THREE.OrbitControls(camera, renderer.domElement);
                controls.enableDamping = true;
                controls.dampingFactor = 0.05;
                controls.maxPolarAngle = Math.PI / 2 - 0.05; 
                controls.minDistance = 2;
                controls.maxDistance = 15;
                
                const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
                scene.add(ambientLight);
                
                const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
                dirLight.position.set(5, 10, 7);
                scene.add(dirLight);
                
                const textureLoader = new THREE.TextureLoader();
                const colorMap = textureLoader.load("{orig_uri}");
                const dispMap = textureLoader.load("{mask_uri}");
                
                const geometry = new THREE.PlaneGeometry({plane_width}, {plane_height}, 256, 256);
                
                const material = new THREE.MeshStandardMaterial({{
                    map: colorMap,
                    displacementMap: dispMap,
                    displacementScale: 1.0,
                    displacementBias: 0.0,
                    side: THREE.DoubleSide,
                    wireframe: false
                }});
                
                const plane = new THREE.Mesh(geometry, material);
                plane.rotation.x = -Math.PI / 2;
                scene.add(plane);
                
                camera.position.set(0, 3, 5);
                controls.target.set(0, 0, 0);
                
                window.addEventListener('resize', () => {{
                    camera.aspect = window.innerWidth / window.innerHeight;
                    camera.updateProjectionMatrix();
                    renderer.setSize(window.innerWidth, window.innerHeight);
                }});
                
                const animate = function () {{
                    requestAnimationFrame(animate);
                    controls.update();
                    renderer.render(scene, camera);
                }};
                
                animate();
            </script>
        </body>
        </html>
        """
        components.html(html_code, height=500)

    with tab_analytics:
        st.markdown("### Confidence Analytics")
        g1, g2 = st.columns(2)

        with g1:
            hist_vals, bin_edges = np.histogram(mask_resized.flatten(), bins=50, range=(0, 1))
            fig_hist = go.Figure(
                data=[
                    go.Bar(
                        x=(bin_edges[:-1] + bin_edges[1:]) / 2,
                        y=hist_vals,
                        marker_color="#1e40af",
                        opacity=0.88,
                    )
                ]
            )
            fig_hist.add_vline(
                x=threshold,
                line_dash="dash",
                line_color="#0ea5e9",
                annotation_text="Threshold",
                annotation_position="top",
            )
            fig_hist.update_layout(
                title="Mask Confidence Distribution",
                xaxis_title="Confidence",
                yaxis_title="Pixel Count",
                template="plotly_white",
                margin=dict(t=48, b=32, l=30, r=18),
                height=350,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(255,255,255,0.68)",
            )
            st.plotly_chart(fig_hist, use_container_width=True)

        with g2:
            bins = [0.0, 0.25, 0.5, 0.75, 1.0]
            counts, _ = np.histogram(mask_resized.flatten(), bins=bins)
            labels = ["0-0.25", "0.25-0.5", "0.5-0.75", "0.75-1.0"]
            fig_band = go.Figure(
                data=[
                    go.Bar(
                        x=labels,
                        y=counts,
                        marker_color=["#dbeafe", "#93c5fd", "#3b82f6", "#1e40af"],
                        opacity=0.92,
                    )
                ]
            )
            fig_band.update_layout(
                title="Confidence Bands",
                xaxis_title="Range",
                yaxis_title="Pixels",
                template="plotly_white",
                margin=dict(t=48, b=32, l=30, r=18),
                height=350,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(255,255,255,0.68)",
            )
            st.plotly_chart(fig_band, use_container_width=True)

        if show_3d:
            st.markdown("### 3D Volume Projection")
            vol = np.repeat(mask_resized[np.newaxis, ...], 20, axis=0)
            zz, yy, xx = np.meshgrid(
                np.arange(vol.shape[0]),
                np.arange(vol.shape[1]),
                np.arange(vol.shape[2]),
                indexing="ij",
            )
            fig3d = go.Figure(
                data=go.Volume(
                    x=xx.flatten(),
                    y=yy.flatten(),
                    z=zz.flatten(),
                    value=vol.flatten(),
                    opacity=0.12,
                    surface_count=18,
                    colorscale=[
                        [0.0, "rgba(30,64,175,0.00)"],
                        [0.5, "rgba(30,64,175,0.45)"],
                        [1.0, "rgba(14,165,233,0.95)"],
                    ],
                )
            )
            fig3d.update_layout(
                margin=dict(l=0, r=0, b=0, t=10),
                height=430,
                scene=dict(
                    xaxis_title="X",
                    yaxis_title="Y",
                    zaxis_title="Z",
                    aspectmode="data",
                    bgcolor="rgb(248, 250, 252)",
                ),
            )
            st.plotly_chart(fig3d, use_container_width=True)
        else:
            st.info("3D volume rendering is disabled in the left panel.")

    with tab_table:
        # Force string values to avoid Arrow serialization issues with mixed object types.
        table_df = pd.DataFrame([{"Attribute": str(k), "Value": str(v)} for k, v in attributes.items()])
        st.dataframe(table_df, use_container_width=True, hide_index=True)

    with tab_attrs:
        for key, value in attributes.items():
            st.markdown(f"**{key}**  \n`{value}`")

    st.markdown("</div>", unsafe_allow_html=True)
