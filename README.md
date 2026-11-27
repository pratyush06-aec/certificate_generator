# Bulk Certificate Generator 🎓

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://bulkcertificate-generator.streamlit.app/)
![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)

> **Live Demo:** [bulkcertificate-generator.streamlit.app](https://bulkcertificate-generator.streamlit.app/)

A fast, pure-Python web application to generate, preview, and export personalized certificates in bulk from Excel or CSV files. Built with **Streamlit**, **Pillow**, **Pandas**, and **Google Drive API** automation.

![Preview](assets/test_preview.png)

---

## 🌟 Key Features

- **Spreadsheet Ingestion**: Supports `.csv`, `.xlsx`, and `.xls` files with automatic column header detection and whitespace/BOM normalization.
- **Interactive Live Preview**: Preview any participant's rendered certificate in real-time before bulk exporting.
- **Dynamic Centering & Auto-Scaling**: Long names automatically downscale in font size so they never exceed certificate borders.
- **Automated Placeholder Masking**: Automatically clears default template placeholder text while preserving the decorative underline and certificate layout.
- **100% Mobile & Aspect Ratio Responsive**:
  - Fully compatible with smartphones, tablets, and desktop displays across all aspect ratios (16:9, 18:9, 19.5:9, 20:9).
  - Touch-friendly 44px hit targets and safe area insets (`env(safe-area-inset-*)`).
  - Fluid certificate canvas scaling with no horizontal page clipping.
- **SEO & Social Share Ready**:
  - Search engine indexed with Open Graph social preview cards, Twitter cards, and Schema.org `WebApplication` JSON-LD structured data.
- **Automated Google Drive Sync**:
  - Automatically creates a dedicated batch subfolder in Google Drive and streams generated archives to the cloud.
  - Displays a 1-click copy-pastable public share link directly in the app.
- **Multi-Format Bulk Export**:
  - `PNG Archive (.zip)`: Individual high-resolution PNGs ($2000 \times 1414\text{ px}$, 300 DPI).
  - `PDF Archive (.zip)`: Individual PDF files for each participant.
  - `Single Merged PDF (.pdf)`: One multi-page printable document containing all certificates.
- **Customizable Typography**: Adjust font family, font size, text color, capitalization, and vertical position directly from the UI sidebar.
- **High-Contrast Light & Dark Theme**: Built-in theme toggle (Light ☀️ / Dark 🌙) engineered with WCAG AA compliance across all widgets, sliders, dropdowns, and input boxes.

---

## Quick Start

### 1. Activate Environment
```bash
# Windows
.\.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch the Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## Project Structure

```
certificate_generator/
├── assets/
│   ├── tech-start cert temp.png     # Default certificate template (2000x1414)
│   ├── sample_participants.csv      # Ready-to-use sample dataset
│   └── fonts/                       # TrueType fonts (Segoe UI, Arial, Georgia)
├── core/
│   ├── __init__.py
│   └── generator.py                 # Core text rendering, auto-scaling & export engine
├── tests/
│   ├── test_generator.py            # Unit tests for core functions
│   └── verify_e2e.py                # End-to-end integration check
├── app.py                           # Streamlit UI
├── requirements.txt
└── README.md
```

---

## Running Tests

```bash
python -m unittest tests/test_generator.py
python -m tests.verify_e2e
```
