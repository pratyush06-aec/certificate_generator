"""
Bulk Certificate Generator — Streamlit Application.
Pure Python app for generating, previewing, and bulk-downloading personalized certificates.
Enhanced with interactive Light / Dark theme switching and high-contrast surfaces.
"""

from __future__ import annotations

import io
from pathlib import Path
import streamlit as st
from PIL import Image

from core.generator import (
    load_participants,
    render_certificate,
    export_batch,
)

# Page configuration
st.set_page_config(
    page_title="Bulk Certificate Generator",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize theme state if not set
if "theme_mode" not in st.session_state:
    st.session_state["theme_mode"] = "Light ☀️"

# Theme Selector in Sidebar header
with st.sidebar:
    st.markdown("## ⚙️ Certificate Generator")
    theme_choice = st.radio(
        "Interface Theme",
        options=["Light ☀️", "Dark 🌙"],
        index=0 if st.session_state["theme_mode"] == "Light ☀️" else 1,
        horizontal=True,
        label_visibility="collapsed",
    )
    st.session_state["theme_mode"] = theme_choice

is_dark = "Dark" in st.session_state["theme_mode"]

# Theme palette definition
if is_dark:
    bg_app = "#090d16"
    bg_card = "#131b2e"
    border_card = "#26354f"
    text_main = "#f1f5f9"
    text_muted = "#94a3b8"
    bg_sidebar = "#0f172a"
    border_sidebar = "#1e293b"
    bg_canvas = "#050811"
    border_canvas = "#1e293b"
    shadow_card = "0 1px 3px 0 rgba(0, 0, 0, 0.4)"
    shadow_cert = "0 14px 32px -4px rgba(0, 0, 0, 0.7), 0 4px 8px -2px rgba(0, 0, 0, 0.5)"
    border_cert = "1px solid rgba(255, 255, 255, 0.12)"
    bg_dropzone = "#101827"
    border_dropzone = "#334155"
    badge_bg = "#064e3b"
    badge_color = "#6ee7b7"
    badge_border = "#047857"
    sec_btn_bg = "#131b2e"
    sec_btn_color = "#2dd4bf"
    sec_btn_border = "#14b8a6"
    info_bg = "#131b2e"
    info_border = "#26354f"
    info_text = "#94a3b8"
    warn_bg = "#451a03"
    warn_border = "#78350f"
    warn_text = "#fde68a"
    subtext_color = "#94a3b8"
else:
    bg_app = "#f1f5f9"
    bg_card = "#ffffff"
    border_card = "#cbd5e1"
    text_main = "#0f172a"
    text_muted = "#475569"
    bg_sidebar = "#ffffff"
    border_sidebar = "#cbd5e1"
    bg_canvas = "#e2e8f0"
    border_canvas = "#cbd5e1"
    shadow_card = "0 1px 3px 0 rgba(15, 23, 42, 0.06), 0 1px 2px -1px rgba(15, 23, 42, 0.04)"
    shadow_cert = "0 10px 25px -4px rgba(15, 23, 42, 0.18), 0 4px 6px -2px rgba(15, 23, 42, 0.08)"
    border_cert = "1px solid rgba(15, 23, 42, 0.15)"
    bg_dropzone = "#f8fafc"
    border_dropzone = "#94a3b8"
    badge_bg = "#f0fdfa"
    badge_color = "#0f766e"
    badge_border = "#99f6e4"
    sec_btn_bg = "#ffffff"
    sec_btn_color = "#0f766e"
    sec_btn_border = "#0f766e"
    info_bg = "#f8fafc"
    info_border = "#e2e8f0"
    info_text = "#475569"
    warn_bg = "#fffbeb"
    warn_border = "#fde68a"
    warn_text = "#92400e"
    subtext_color = "#475569"

# Inject Dynamic High-Contrast CSS
st.markdown(
    f"""
    <style>
    /* Baseline typography & anti-aliasing */
    html, body, [class*="css"] {{
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        font-feature-settings: "cv02", "cv03", "cv04", "cv11";
    }}

    /* Overall page background */
    .stApp {{
        background-color: {bg_app} !important;
        color: {text_main} !important;
    }}

    /* Headings */
    h1, h2, h3, h4 {{
        color: {text_main} !important;
        letter-spacing: -0.02em;
        font-weight: 700 !important;
    }}
    p, span, label {{
        color: {text_main} !important;
    }}

    /* Bordered containers as elevated cards */
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: {bg_card} !important;
        border: 1px solid {border_card} !important;
        border-radius: 14px !important;
        box-shadow: {shadow_card} !important;
        padding: 6px !important;
        margin-bottom: 12px;
    }}

    /* Sidebar styling */
    [data-testid="stSidebar"] {{
        background-color: {bg_sidebar} !important;
        border-right: 1.5px solid {border_sidebar} !important;
    }}
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{
        color: {text_main} !important;
    }}
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span {{
        color: {text_main} !important;
    }}

    /* Certificate Preview Canvas Frame */
    .cert-canvas-frame {{
        background-color: {bg_canvas};
        border: 1.5px solid {border_canvas};
        border-radius: 12px;
        padding: 16px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin-top: 8px;
        margin-bottom: 8px;
    }}
    .cert-canvas-frame img {{
        border: {border_cert} !important;
        border-radius: 6px !important;
        box-shadow: {shadow_cert} !important;
    }}

    /* File Uploader Dropzone */
    [data-testid="stFileUploaderDropzone"] {{
        background-color: {bg_dropzone} !important;
        border: 2px dashed {border_dropzone} !important;
        border-radius: 10px !important;
        transition: border-color 0.15s ease, background-color 0.15s ease;
    }}
    [data-testid="stFileUploaderDropzone"]:hover {{
        border-color: #0f766e !important;
    }}
    [data-testid="stFileUploaderDropzone"] span, [data-testid="stFileUploaderDropzone"] small {{
        color: {text_muted} !important;
    }}

    /* Primary Buttons */
    button[kind="primary"] {{
        background-color: #0f766e !important;
        color: #ffffff !important;
        border: 1px solid #115e59 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 4px rgba(15, 118, 110, 0.25) !important;
        transition: transform 0.1s ease, background-color 0.15s ease !important;
    }}
    button[kind="primary"]:hover {{
        background-color: #115e59 !important;
    }}
    button[kind="primary"]:active {{
        transform: scale(0.97) !important;
    }}

    /* Secondary Buttons */
    button[kind="secondary"] {{
        background-color: {sec_btn_bg} !important;
        color: {sec_btn_color} !important;
        border: 1.5px solid {sec_btn_border} !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: transform 0.1s ease, background-color 0.15s ease !important;
    }}
    button[kind="secondary"]:hover {{
        background-color: {badge_bg} !important;
        color: #ffffff !important;
    }}
    button[kind="secondary"]:active {{
        transform: scale(0.97) !important;
    }}

    /* Inputs, Selectboxes & Dropdowns */
    .stSelectbox div[data-baseweb="select"] > div {{
        background-color: {bg_card} !important;
        border: 1.5px solid {border_card} !important;
        border-radius: 8px !important;
        color: {text_main} !important;
    }}
    .stSelectbox div[data-baseweb="select"]:hover > div {{
        border-color: #0f766e !important;
    }}
    .stSelectbox div[data-baseweb="select"] span {{
        color: {text_main} !important;
    }}

    /* Number / Tabular values */
    .tabular-badge {{
        font-variant-numeric: tabular-nums;
        background-color: {badge_bg};
        color: {badge_color};
        border: 1px solid {badge_border};
        border-radius: 6px;
        padding: 3px 10px;
        font-weight: 600;
        font-size: 0.875rem;
        display: inline-block;
    }}

    /* Radio button labels */
    [data-testid="stRadio"] label, [data-testid="stRadio"] span {{
        color: {text_main} !important;
        font-weight: 500 !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# Paths
BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
DEFAULT_TEMPLATE_PATH = ASSETS_DIR / "tech-start cert temp.png"
FONTS_DIR = ASSETS_DIR / "fonts"

# Font catalog
FONT_OPTIONS = {
    "Segoe UI (Bold) — Clean & Modern": str(FONTS_DIR / "SegoeUI-Bold.ttf"),
    "Segoe UI (Regular) — Light Modern": str(FONTS_DIR / "SegoeUI.ttf"),
    "Arial (Bold) — High Contrast Sans": str(FONTS_DIR / "Arial-Bold.ttf"),
    "Georgia (Bold) — Formal Serif": str(FONTS_DIR / "Georgia-Bold.ttf"),
}


def load_default_template() -> Image.Image:
    """Load the default certificate template from assets."""
    if DEFAULT_TEMPLATE_PATH.exists():
        return Image.open(DEFAULT_TEMPLATE_PATH)
    return Image.new("RGB", (2000, 1414), color=(255, 255, 255))


# --- SIDEBAR: Typography & Layout Controls ---
with st.sidebar:
    # Template selection
    with st.container(border=True):
        st.markdown("### 1. Template")
        use_custom_template = st.checkbox("Upload custom template", value=False)
        if use_custom_template:
            uploaded_template = st.file_uploader(
                "Upload image (PNG/JPG)", type=["png", "jpg", "jpeg"]
            )
            if uploaded_template:
                template_img = Image.open(uploaded_template)
            else:
                template_img = load_default_template()
        else:
            template_img = load_default_template()
            st.caption(f"Template: **{DEFAULT_TEMPLATE_PATH.name}** ({template_img.width}×{template_img.height}px)")

    # Typography controls
    with st.container(border=True):
        st.markdown("### 2. Typography")
        selected_font_label = st.selectbox(
            "Font Family",
            options=list(FONT_OPTIONS.keys()),
            index=0,
        )
        font_path = FONT_OPTIONS[selected_font_label]

        font_size = st.slider("Font Size (pt)", min_value=36, max_value=120, value=72, step=2)
        font_color = st.color_picker("Text Color", value="#043539", help="Hex color for participant name on the certificate")

        name_transform = st.selectbox(
            "Text Capitalization",
            options=["none", "title", "upper"],
            format_func=lambda x: {"none": "As in Sheet", "title": "Title Case", "upper": "UPPERCASE"}[x],
            index=0,
        )

    # Positioning & Masking
    with st.container(border=True):
        st.markdown("### 3. Alignment & Masking")
        y_pos = st.slider(
            "Vertical Position (Y-Offset)",
            min_value=650,
            max_value=850,
            value=745,
            step=5,
            help="Target vertical center for participant name in pixel coordinates",
        )

        mask_placeholder = st.checkbox(
            "Mask template placeholder text",
            value=True,
            help="Covers 'Participant's or Team's Name' with white background so new names render cleanly above the underline.",
        )

        max_width = st.slider(
            "Max Allowed Name Width (px)",
            min_value=800,
            max_value=1800,
            value=1500,
            step=50,
            help="Names wider than this threshold will automatically downscale in font size.",
        )


# --- MAIN CONTENT ---
st.title("🎓 Bulk Certificate Generator")
st.markdown(
    f"<p style='color: {subtext_color}; font-size: 1.05rem; margin-top: -10px; margin-bottom: 24px;'>"
    "Upload participant sheet, preview certificates in real-time, and download in bulk."
    "</p>",
    unsafe_allow_html=True,
)

col_upload, col_preview = st.columns([1, 1], gap="medium")

with col_upload:
    with st.container(border=True):
        st.markdown("### 📁 1. Participant Data")
        uploaded_file = st.file_uploader(
            "Upload participant spreadsheet (.csv or .xlsx)",
            type=["csv", "xlsx", "xls"],
            help="File should have a column containing participant names.",
        )

        sample_col1, sample_col2 = st.columns([1.2, 0.8])
        with sample_col1:
            use_sample = st.button("📄 Load Sample Participant List", use_container_width=True)

        names: list[str] = []
        columns: list[str] = []
        selected_column: str = ""

        # Handle file loading or sample data
        if uploaded_file is not None:
            names, columns, selected_column = load_participants(
                uploaded_file, transform=name_transform
            )
        elif use_sample or "use_sample_active" in st.session_state:
            st.session_state["use_sample_active"] = True
            sample_path = ASSETS_DIR / "sample_participants.csv"
            if sample_path.exists():
                names, columns, selected_column = load_participants(
                    str(sample_path), transform=name_transform
                )

        if names:
            st.markdown(
                f"<div style='margin-top: 12px; margin-bottom: 12px;'>"
                f"<span class='tabular-badge'>✓ {len(names)} Participants Loaded</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

            # Column selector if multiple columns exist
            if len(columns) > 1:
                chosen_col = st.selectbox(
                    "Select Column with Names:",
                    options=columns,
                    index=columns.index(selected_column) if selected_column in columns else 0,
                )
                if chosen_col != selected_column:
                    if uploaded_file is not None:
                        uploaded_file.seek(0)
                        names, _, selected_column = load_participants(
                            uploaded_file, column_name=chosen_col, transform=name_transform
                        )
                    else:
                        names, _, selected_column = load_participants(
                            str(ASSETS_DIR / "sample_participants.csv"),
                            column_name=chosen_col,
                            transform=name_transform,
                        )

            with st.expander("👁️ View Extracted Names", expanded=False):
                st.dataframe(
                    {"#": list(range(1, len(names) + 1)), "Participant Name": names},
                    use_container_width=True,
                    hide_index=True,
                )
        else:
            st.markdown(
                f"<div style='background-color: {info_bg}; border: 1px solid {info_border}; border-radius: 8px; padding: 12px; margin-top: 12px; color: {info_text};'>"
                "ℹ️ Upload a spreadsheet or click <b>'Load Sample Participant List'</b> to test."
                "</div>",
                unsafe_allow_html=True,
            )

with col_preview:
    with st.container(border=True):
        st.markdown("### 🔍 2. Live Certificate Preview")

        preview_name = "Participant Name"
        if names:
            preview_name = st.selectbox(
                "Previewing Participant:",
                options=names,
                index=0,
            )

        # Render preview
        preview_img = render_certificate(
            template=template_img,
            name=preview_name,
            font_path=font_path,
            font_size=font_size,
            font_color=font_color,
            y_pos=y_pos,
            max_width=max_width,
            mask_placeholder=mask_placeholder,
        )

        # Framed canvas container to ensure high contrast against the certificate's white background
        st.markdown('<div class="cert-canvas-frame">', unsafe_allow_html=True)
        st.image(
            preview_img,
            use_container_width=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)
        st.caption(f"Framed Canvas: **{preview_name}** ({preview_img.width}×{preview_img.height}px)")


# --- EXPORT SECTION ---
with st.container(border=True):
    st.markdown("### 📦 3. Bulk Generation & Export")

    if not names:
        st.markdown(
            f"<div style='background-color: {warn_bg}; border: 1.5px solid {warn_border}; border-radius: 8px; padding: 12px; color: {warn_text}; font-weight: 500;'>"
            "⚠️ Upload a participant list above to unlock bulk generation."
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        export_col1, export_col2 = st.columns([1, 1], gap="large")

        with export_col1:
            export_mode = st.radio(
                "Export Format:",
                options=["png_zip", "pdf_zip", "pdf_merged"],
                format_func=lambda x: {
                    "png_zip": "PNG Archive (.zip) — Individual high-resolution images (300 DPI)",
                    "pdf_zip": "PDF Archive (.zip) — Individual PDF files for each participant",
                    "pdf_merged": "Single Merged PDF (.pdf) — All certificates in one multi-page document",
                }[x],
                index=0,
            )

        with export_col2:
            st.markdown(f"**Total Ready to Generate:** <span class='tabular-badge'>{len(names)} Certificates</span>", unsafe_allow_html=True)
            st.write("")
            if st.button("🚀 Generate All Certificates Now", type="primary", use_container_width=True):
                progress_bar = st.progress(0, text="Generating certificates...")

                def update_progress(current: int, total: int):
                    pct = int((current / total) * 100)
                    progress_bar.progress(pct, text=f"Rendering {current} of {total} ({pct}%)...")

                buf, filename, mime_type = export_batch(
                    template=template_img,
                    names=names,
                    font_path=font_path,
                    font_size=font_size,
                    font_color=font_color,
                    y_pos=y_pos,
                    max_width=max_width,
                    mask_placeholder=mask_placeholder,
                    format_type=export_mode,
                    progress_callback=update_progress,
                )

                progress_bar.progress(100, text="Done! Ready for download.")
                st.success(f"Generated {len(names)} certificates successfully!")

                st.download_button(
                    label=f"⬇️ Download {filename} ({len(buf.getvalue()) / (1024 * 1024):.2f} MB)",
                    data=buf.getvalue(),
                    file_name=filename,
                    mime=mime_type,
                    type="primary",
                    use_container_width=True,
                )
