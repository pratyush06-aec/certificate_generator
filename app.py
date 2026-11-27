"""
Bulk Certificate Generator — Streamlit Application.
Pure Python app for generating, previewing, and bulk-downloading personalized certificates.
Enhanced with interactive Light / Dark theme switching and high-contrast surfaces.
"""

from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path
import streamlit as st
from PIL import Image

from core.generator import (
    load_participants,
    render_certificate,
    export_batch,
)
from core.drive_uploader import automate_drive_export

# Page configuration & SEO Metadata
st.set_page_config(
    page_title="Bulk Certificate Generator — Free Online Certificate Maker & Google Drive Sync",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/pratyush06-aec/certificate_generator",
        "Report a bug": "https://github.com/pratyush06-aec/certificate_generator/issues",
        "About": (
            "### Bulk Certificate Generator\n"
            "Free open-source web application to generate, preview, and export hundreds of customized "
            "certificates in seconds from Excel/CSV with automated Google Drive integration.\n\n"
            "**Author:** Pratyush\n"
            "**Repo:** [GitHub](https://github.com/pratyush06-aec/certificate_generator)"
        ),
    },
)

# Inject Primary SEO Meta Tags, Social Cards (Open Graph / Twitter), and JSON-LD Schema
st.markdown(
    """
    <!-- Primary Meta Tags -->
    <meta name="title" content="Bulk Certificate Generator — Free Online Certificate Maker & Google Drive Sync" />
    <meta name="description" content="Generate hundreds of customized certificates in seconds from Excel/CSV sheets. Features real-time preview, automated template placeholder masking, 300 DPI PNG & PDF export, and 1-click Google Drive cloud sync. Free and mobile responsive." />
    <meta name="keywords" content="bulk certificate generator, certificate generator, free certificate maker, excel to certificate, csv certificate generator, certificate maker google drive, bulk pdf certificates, event certificate generator, appreciation certificate maker" />
    <meta name="author" content="Pratyush" />
    <meta name="robots" content="index, follow" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, viewport-fit=cover" />
    <link rel="canonical" href="https://bulkcertificate-generator.streamlit.app/" />

    <!-- Open Graph / Facebook / LinkedIn / WhatsApp -->
    <meta property="og:type" content="website" />
    <meta property="og:url" content="https://bulkcertificate-generator.streamlit.app/" />
    <meta property="og:title" content="Bulk Certificate Generator — Free Online Certificate Maker" />
    <meta property="og:description" content="Generate hundreds of customized certificates in seconds from Excel or CSV with real-time preview and Google Drive sync." />
    <meta property="og:image" content="https://raw.githubusercontent.com/pratyush06-aec/certificate_generator/main/assets/tech-start%20cert%20temp.png" />
    <meta property="og:site_name" content="Bulk Certificate Generator" />

    <!-- Twitter Cards -->
    <meta property="twitter:card" content="summary_large_image" />
    <meta property="twitter:url" content="https://bulkcertificate-generator.streamlit.app/" />
    <meta property="twitter:title" content="Bulk Certificate Generator — Free Online Certificate Maker" />
    <meta property="twitter:description" content="Generate customized certificates in bulk from Excel/CSV with live preview and Google Drive automation." />
    <meta property="twitter:image" content="https://raw.githubusercontent.com/pratyush06-aec/certificate_generator/main/assets/tech-start%20cert%20temp.png" />

    <!-- Schema.org JSON-LD Structured Data for Search Engines -->
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "WebApplication",
      "name": "Bulk Certificate Generator",
      "url": "https://bulkcertificate-generator.streamlit.app/",
      "description": "Generate high-resolution customized certificates in bulk from Excel/CSV spreadsheets with live preview, automated masking, and Google Drive upload.",
      "applicationCategory": "BusinessApplication",
      "operatingSystem": "All",
      "browserRequirements": "Requires JavaScript. Requires HTML5.",
      "offers": {
        "@type": "Offer",
        "price": "0",
        "priceCurrency": "USD"
      },
      "author": {
        "@type": "Person",
        "name": "Pratyush"
      },
      "featureList": [
        "Bulk certificate generation from CSV or Excel",
        "Live interactive certificate preview with custom typography",
        "Automated template placeholder masking",
        "Instant Google Drive folder creation and upload",
        "Export to 300 DPI PNG, individual PDFs, or merged multi-page PDF",
        "100% Mobile responsive layout across all aspect ratios"
      ]
    }
    </script>

    <!-- Attach tags to parent document.head for Streamlit Cloud iframe & direct bots -->
    <script>
      (function() {
        try {
          const targetDoc = window.parent.document !== document ? window.parent.document : document;
          const head = targetDoc.head || document.head;
          if (!head) return;

          if (!targetDoc.title || targetDoc.title === "Streamlit") {
            targetDoc.title = "Bulk Certificate Generator — Free Online Certificate Maker & Google Drive Sync";
          }

          const metaDefs = [
            { name: "description", content: "Generate hundreds of customized certificates in seconds from Excel/CSV sheets. High-resolution PNG & PDF export with automated Google Drive integration. 100% free and mobile responsive." },
            { name: "keywords", content: "bulk certificate generator, certificate maker, excel to certificate, free certificate generator, bulk pdf certificates, google drive certificate automation" },
            { name: "author", content: "Pratyush" },
            { name: "robots", content: "index, follow" },
            { property: "og:type", content: "website" },
            { property: "og:url", content: "https://bulkcertificate-generator.streamlit.app/" },
            { property: "og:title", content: "Bulk Certificate Generator — Free Online Certificate Maker" },
            { property: "og:description", content: "Generate hundreds of customized certificates in seconds from Excel or CSV with real-time preview and Google Drive sync." },
            { property: "og:image", content: "https://raw.githubusercontent.com/pratyush06-aec/certificate_generator/main/assets/tech-start%20cert%20temp.png" },
            { property: "twitter:card", content: "summary_large_image" },
            { property: "twitter:title", content: "Bulk Certificate Generator — Free Online Certificate Maker" },
            { property: "twitter:description", content: "Generate customized certificates in bulk from Excel/CSV with live preview and Google Drive automation." },
            { property: "twitter:image", content: "https://raw.githubusercontent.com/pratyush06-aec/certificate_generator/main/assets/tech-start%20cert%20temp.png" }
          ];

          metaDefs.forEach(def => {
            const key = def.name ? "name" : "property";
            const val = def[key];
            if (!head.querySelector(`meta[${key}="${val}"]`)) {
              const meta = targetDoc.createElement("meta");
              meta.setAttribute(key, val);
              meta.setAttribute("content", def.content);
              head.appendChild(meta);
            }
          });

          if (!head.querySelector('link[rel="canonical"]')) {
            const link = targetDoc.createElement("link");
            link.rel = "canonical";
            link.href = "https://bulkcertificate-generator.streamlit.app/";
            head.appendChild(link);
          }
        } catch (e) {
          // Cross-origin fallback
        }
      })();
    </script>
    """,
    unsafe_allow_html=True,
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
    input_bg = "#1e293b"
    input_border = "#334155"
    input_text = "#f8fafc"
    code_bg = "#0c1322"
    code_border = "#26354f"
    code_text = "#38bdf8"
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
    input_bg = "#ffffff"
    input_border = "#cbd5e1"
    input_text = "#0f172a"
    code_bg = "#f8fafc"
    code_border = "#e2e8f0"
    code_text = "#0f766e"

# Inject Dynamic High-Contrast CSS
st.markdown(
    f"""
    <style>
    /* Baseline typography & anti-aliasing */
    html {{
        -webkit-tap-highlight-color: transparent !important;
        scroll-behavior: smooth;
    }}
    html, body, [class*="css"] {{
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        font-feature-settings: "cv02", "cv03", "cv04", "cv11";
    }}

    /* Overall page background with dynamic viewport & safe areas */
    .stApp {{
        background-color: {bg_app} !important;
        color: {text_main} !important;
        min-height: 100dvh !important;
        padding-top: env(safe-area-inset-top, 0px) !important;
        padding-bottom: env(safe-area-inset-bottom, 0px) !important;
        padding-left: env(safe-area-inset-left, 0px) !important;
        padding-right: env(safe-area-inset-right, 0px) !important;
    }}

    /* Prevent mobile browser auto-zoom on input focus */
    input, select, textarea, div[data-baseweb="input"] input {{
        font-size: 16px !important;
    }}

    /* Mobile touch target minimum sizing (44px) & tap feedback */
    button, [role="button"], input[type="button"], input[type="submit"] {{
        touch-action: manipulation !important;
        user-select: none !important;
        -webkit-user-select: none !important;
        min-height: 44px !important;
    }}

    /* Headings */
    h1, h2, h3, h4, h5, h6 {{
        color: {text_main} !important;
        letter-spacing: -0.02em;
        font-weight: 700 !important;
    }}
    p, span, label {{
        color: {text_main} !important;
    }}

    /* All Streamlit widget labels */
    [data-testid="stWidgetLabel"] *,
    [data-testid="stWidgetLabel"] p,
    [data-testid="stWidgetLabel"] label,
    [data-testid="stWidgetLabel"] span {{
        color: {text_main} !important;
        font-weight: 600 !important;
    }}

    /* Helper captions & subtext */
    [data-testid="stCaptionContainer"] *,
    [data-testid="stCaptionContainer"] p,
    [data-testid="stCaptionContainer"] span,
    .stCaption {{
        color: {text_muted} !important;
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
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4 {{
        color: {text_main} !important;
    }}
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span {{
        color: {text_main} !important;
    }}

    /* Text Inputs & Number Inputs */
    div[data-baseweb="input"],
    div[data-baseweb="input"] > div,
    div[data-baseweb="base-input"] {{
        background-color: {input_bg} !important;
        border: 1.5px solid {input_border} !important;
        border-radius: 8px !important;
    }}
    div[data-baseweb="input"]:focus-within {{
        border-color: #2dd4bf !important;
    }}
    div[data-baseweb="input"] input,
    div[data-baseweb="base-input"] input {{
        background-color: transparent !important;
        color: {input_text} !important;
        -webkit-text-fill-color: {input_text} !important;
        font-weight: 500 !important;
    }}

    /* Sliders */
    [data-testid="stSlider"] div[data-testid="stSliderThumbValue"],
    [data-testid="stSliderTickBar"] *,
    [data-testid="stSlider"] div[data-baseweb="slider"] div {{
        color: {text_main} !important;
    }}
    [data-testid="stSliderTickBar"] div,
    [data-testid="stSliderTickBar"] span {{
        color: {text_muted} !important;
        font-weight: 600 !important;
    }}

    /* Selectboxes & Dropdowns */
    .stSelectbox div[data-baseweb="select"] > div {{
        background-color: {input_bg} !important;
        border: 1.5px solid {input_border} !important;
        border-radius: 8px !important;
        color: {text_main} !important;
    }}
    .stSelectbox div[data-baseweb="select"] * {{
        color: {text_main} !important;
    }}
    div[data-baseweb="select"] svg {{
        fill: {text_main} !important;
    }}

    /* Dropdown popover menu list */
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] ul,
    div[data-baseweb="menu"],
    ul[role="listbox"] {{
        background-color: {bg_card} !important;
        border: 1.5px solid {border_card} !important;
        border-radius: 8px !important;
    }}
    li[role="option"] {{
        background-color: {bg_card} !important;
        color: {text_main} !important;
    }}
    li[role="option"] * {{
        color: {text_main} !important;
    }}
    li[role="option"]:hover,
    li[role="option"]:hover *,
    li[aria-selected="true"],
    li[aria-selected="true"] * {{
        background-color: {border_card} !important;
        color: #2dd4bf !important;
    }}

    /* Certificate Preview Canvas Frame - Fluid Aspect Ratio Containment */
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
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
        overflow: hidden !important;
    }}
    .cert-canvas-frame img {{
        width: 100% !important;
        max-width: 100% !important;
        height: auto !important;
        object-fit: contain !important;
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
    [data-testid="stFileUploaderDropzoneInstructions"] * {{
        color: {text_main} !important;
    }}
    [data-testid="stFileUploaderDropzone"] small {{
        color: {text_muted} !important;
    }}
    [data-testid="stFileUploaderDropzone"] button {{
        background-color: {sec_btn_bg} !important;
        color: {sec_btn_color} !important;
        border: 1.5px solid {sec_btn_border} !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }}
    [data-testid="stFileUploaderFile"] {{
        background-color: {bg_card} !important;
        border: 1px solid {border_card} !important;
        border-radius: 8px !important;
    }}
    [data-testid="stFileUploaderFile"] * {{
        color: {text_main} !important;
    }}

    /* Expanders */
    [data-testid="stExpander"] details {{
        background-color: {bg_card} !important;
        border: 1px solid {border_card} !important;
        border-radius: 10px !important;
    }}
    [data-testid="stExpander"] summary {{
        background-color: {bg_card} !important;
        color: {text_main} !important;
        border-radius: 10px !important;
    }}
    [data-testid="stExpander"] summary * {{
        color: {text_main} !important;
        font-weight: 600 !important;
    }}
    [data-testid="stExpander"] summary svg {{
        fill: {text_main} !important;
        stroke: {text_main} !important;
    }}
    [data-testid="stExpander"] div[data-testid="stExpanderDetails"] {{
        background-color: {bg_card} !important;
        color: {text_main} !important;
    }}

    /* Code Blocks */
    [data-testid="stCodeBlock"] {{
        background-color: {code_bg} !important;
        border: 1.5px solid {code_border} !important;
        border-radius: 8px !important;
    }}
    [data-testid="stCodeBlock"] pre,
    [data-testid="stCodeBlock"] code {{
        background-color: transparent !important;
        color: {code_text} !important;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace !important;
        font-size: 0.95rem !important;
    }}
    [data-testid="stCodeBlock"] button {{
        color: {text_muted} !important;
    }}

    /* Inline Code */
    code {{
        color: {code_text} !important;
        background-color: {code_bg} !important;
        padding: 2px 6px !important;
        border-radius: 4px !important;
        font-size: 0.9em !important;
    }}

    /* Checkboxes & Radios */
    [data-testid="stCheckbox"] label,
    [data-testid="stCheckbox"] label span,
    [data-testid="stCheckbox"] label p,
    [data-testid="stRadio"] label,
    [data-testid="stRadio"] label span,
    [data-testid="stRadio"] label p {{
        color: {text_main} !important;
        font-weight: 500 !important;
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

    /* Secondary Buttons */
    button[kind="secondary"] {{
        background-color: {sec_btn_bg} !important;
        color: {sec_btn_color} !important;
        border: 1.5px solid {sec_btn_border} !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: transform 0.1s ease, background-color 0.15s ease !important;
    }}

    /* Gate hover states behind pointing device capability to prevent sticky hover on touch */
    @media (hover: hover) and (pointer: fine) {{
        button[kind="primary"]:hover {{
            background-color: #115e59 !important;
        }}
        button[kind="secondary"]:hover {{
            background-color: #0f766e !important;
            color: #ffffff !important;
        }}
        [data-testid="stFileUploaderDropzone"]:hover {{
            border-color: #2dd4bf !important;
        }}
        [data-testid="stFileUploaderDropzone"] button:hover {{
            background-color: #0f766e !important;
            color: #ffffff !important;
        }}
        .stSelectbox div[data-baseweb="select"]:hover > div {{
            border-color: #2dd4bf !important;
        }}
        [data-testid="stExpander"] summary:hover * {{
            color: #2dd4bf !important;
        }}
        [data-testid="stCodeBlock"] button:hover {{
            color: {text_main} !important;
        }}
    }}

    /* Snappy active press feedback across all devices */
    button:active, [role="button"]:active {{
        transform: scale(0.97) !important;
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

    /* Alerts */
    [data-testid="stAlert"] {{
        border-radius: 8px !important;
    }}
    [data-testid="stAlert"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stAlert"] [data-testid="stMarkdownContainer"] span {{
        color: {text_main} !important;
    }}

    /* Mobile & Tablet Responsive Breakpoints (handles all mobile aspect ratios) */
    @media (max-width: 768px) {{
        .block-container {{
            padding-left: 0.85rem !important;
            padding-right: 0.85rem !important;
            padding-top: 1rem !important;
            padding-bottom: 2rem !important;
            max-width: 100% !important;
        }}

        /* Seamless column stacking on mobile screens */
        [data-testid="column"] {{
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
            margin-bottom: 12px !important;
        }}

        /* Mobile responsive typography */
        h1 {{
            font-size: 1.65rem !important;
            line-height: 1.25 !important;
        }}
        h2 {{
            font-size: 1.35rem !important;
        }}
        h3 {{
            font-size: 1.15rem !important;
        }}

        .cert-canvas-frame {{
            padding: 8px !important;
            border-radius: 10px !important;
        }}

        [data-testid="stFileUploaderDropzone"] {{
            padding: 14px 10px !important;
        }}
    }}

    /* Small phone screens (<= 480px, tall aspect ratios like 19.5:9, 20:9) */
    @media (max-width: 480px) {{
        .block-container {{
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }}
        [data-testid="stVerticalBlockBorderWrapper"] {{
            padding: 8px 6px !important;
            border-radius: 10px !important;
        }}
        h1 {{
            font-size: 1.45rem !important;
        }}
        .tabular-badge {{
            font-size: 0.8rem !important;
            padding: 2px 8px !important;
        }}
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

            st.markdown("---")
            st.markdown("#### ☁️ Google Drive Automation")
            auto_upload_drive = st.checkbox(
                "Auto-create folder & upload to Google Drive",
                value=True,
                help="Automatically creates a new batch folder in Google Drive and uploads the certificates.",
            )

            drive_folder_name = ""
            parent_folder_id = ""
            if auto_upload_drive:
                default_name = f"Certificates_Batch_{datetime.now().strftime('%Y%m%d_%H%M')}"
                drive_folder_name = st.text_input(
                    "New Drive Folder Name:",
                    value=default_name,
                    help="Name of the dedicated folder to be created in Google Drive.",
                )
                default_parent = st.secrets.get("GDRIVE_PARENT_FOLDER_ID", "") if hasattr(st, "secrets") else ""
                parent_folder_id = st.text_input(
                    "Parent Drive Folder ID (Optional):",
                    value=default_parent,
                    help="Paste your shared Google Drive folder ID to keep certificates in a specific directory, or leave blank to create in root.",
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

                # --- Google Drive Automated Upload ---
                if auto_upload_drive:
                    webhook_url = st.secrets.get("GDRIVE_WEBHOOK_URL", "") if hasattr(st, "secrets") else ""
                    has_service_account = False
                    try:
                        has_service_account = "gdrive_service_account" in st.secrets
                    except Exception:
                        has_service_account = False

                    if webhook_url or has_service_account:
                        try:
                            with st.spinner("Creating Google Drive folder and uploading..."):
                                drive_result = automate_drive_export(
                                    file_bytes=buf,
                                    filename=filename,
                                    batch_folder_name=drive_folder_name or f"Certificates_{datetime.now().strftime('%Y%m%d')}",
                                    credentials_info=dict(st.secrets["gdrive_service_account"]) if has_service_account and not webhook_url else None,
                                    parent_folder_id=parent_folder_id or None,
                                    mime_type=mime_type,
                                    webhook_url=webhook_url or None,
                                )

                            st.markdown(
                                f"""
                                <div style="background-color: {badge_bg}; border: 1.5px solid {badge_border}; border-radius: 10px; padding: 16px; margin: 16px 0 12px 0;">
                                    <h4 style="margin: 0 0 8px 0; color: {badge_color};">☁️ Uploaded to Google Drive Successfully!</h4>
                                    <p style="margin: 0; color: {text_main}; font-size: 0.95rem;">
                                        📁 Created Folder: <b>{drive_result['folder_name']}</b> &nbsp;|&nbsp; 
                                        📄 File: <code>{filename}</code>
                                    </p>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                            st.markdown("##### 📋 Copy-Pastable Public Drive Link:")
                            st.code(drive_result["folder_url"], language="text")

                            if drive_result.get("file_url") and drive_result["file_url"] != drive_result["folder_url"]:
                                with st.expander("📄 Direct File Download Link", expanded=False):
                                    st.code(drive_result["file_url"], language="text")
                        except Exception as e:
                            st.error(f"Google Drive upload encountered an error: {e}")
                    else:
                        st.info(
                            "💡 **Google Drive Setup Required:** Add your Service Account credentials or Webhook URL into "
                            "`secrets.toml` to enable 1-click cloud sync."
                        )

                st.download_button(
                    label=f"⬇️ Download {filename} ({len(buf.getvalue()) / (1024 * 1024):.2f} MB)",
                    data=buf.getvalue(),
                    file_name=filename,
                    mime=mime_type,
                    type="secondary" if auto_upload_drive else "primary",
                    use_container_width=True,
                )


# --- SEO & FREQUENTLY ASKED QUESTIONS (FAQ) ---
with st.container(border=True):
    with st.expander("❓ Frequently Asked Questions (FAQ) & How to Use", expanded=False):
        st.markdown(
            f"""
            <div style="color: {text_main}; font-size: 0.95rem; line-height: 1.6;">
                <h4>🎓 About Bulk Certificate Generator</h4>
                <p>
                    <b>Bulk Certificate Generator</b> is an open-source, high-performance web tool designed to automate 
                    personalized certificate creation for events, workshops, hackathons, webinars, online courses, 
                    and academic programs.
                </p>
                <hr style="border: 0; border-top: 1px solid {border_card}; margin: 16px 0;" />
                <h5>⚡ How to generate certificates in bulk from Excel or CSV:</h5>
                <ol>
                    <li><b>Upload Spreadsheet:</b> Import an Excel (<code>.xlsx</code>, <code>.xls</code>) or CSV file with your participants' names.</li>
                    <li><b>Customize Typography & Alignment:</b> Adjust font style, size, color, and vertical offset in real-time on the preview canvas.</li>
                    <li><b>Automated Masking:</b> Automatically covers default placeholder names so new names render cleanly above the underline.</li>
                    <li><b>1-Click Export & Cloud Sync:</b> Download a <code>.zip</code> of 300 DPI PNG images, individual PDFs, or a single combined PDF, or sync directly to Google Drive.</li>
                </ol>
                <hr style="border: 0; border-top: 1px solid {border_card}; margin: 16px 0;" />
                <h5>📱 Mobile & Device Compatibility</h5>
                <p>
                    This app is optimized with fluid responsive styling for smartphones, tablets, foldables, and desktops 
                    across all screen aspect ratios (16:9, 18:9, 19.5:9, 20:9) with touch-friendly 44px tap targets and safe-area insets.
                </p>
                <hr style="border: 0; border-top: 1px solid {border_card}; margin: 16px 0;" />
                <h5>🔒 Privacy & Security</h5>
                <p>
                    Your participant data is processed in-memory during certificate generation and is never sold or permanently stored.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
