"""
Core engine for the bulk certificate generator.
Handles spreadsheet loading, text rendering with auto-scaling,
and bulk export packaging (PNG zip, PDF zip, merged PDF).
"""

from __future__ import annotations

import io
import re
import zipfile
from typing import Callable, Sequence
import pandas as pd
from PIL import Image, ImageDraw, ImageFont


def sanitize_filename(name: str) -> str:
    """Produce a safe ASCII-friendly filename token from a participant name."""
    clean = re.sub(r'[\\/*?:"<>| ]', '_', name.strip())
    clean = re.sub(r'_+', '_', clean).strip('_')
    return clean or "participant"


def load_participants(
    file_or_path: str | io.BytesIO,
    column_name: str | None = None,
    transform: str = "none",
) -> tuple[list[str], list[str], str]:
    """
    Parse participant names from a CSV or Excel file.

    Returns:
        tuple: (list_of_names, available_columns, selected_column)
    """
    # Detect file type from name attribute if present
    filename = getattr(file_or_path, "name", str(file_or_path)).lower()
    if hasattr(file_or_path, "seek"):
        file_or_path.seek(0)

    # shortcut: assumes header on row 0, upgrade with multi-row header sniffing if non-standard sheets are uploaded
    if filename.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(file_or_path)
    else:
        # For CSV, try utf-8-sig first to cleanly strip BOM (\ufeff), fallback to latin-1
        try:
            df = pd.read_csv(file_or_path, encoding="utf-8-sig")
        except Exception:
            if hasattr(file_or_path, "seek"):
                file_or_path.seek(0)
            try:
                df = pd.read_excel(file_or_path)
            except Exception:
                if hasattr(file_or_path, "seek"):
                    file_or_path.seek(0)
                df = pd.read_csv(file_or_path, encoding="latin-1")

    # Clean DataFrame columns directly to prevent KeyError mismatches
    df.columns = [str(c).replace('\ufeff', '').strip() for c in df.columns]
    columns = [c for c in df.columns if c and not c.startswith("Unnamed:")]
    if not columns:
        columns = list(df.columns)
    if not columns:
        return [], [], ""

    # Determine which column to use
    selected = None
    if column_name and column_name in df.columns:
        selected = column_name
    else:
        # Auto-detect likely name columns (case-insensitive)
        common_candidates = [
            "name", "participant", "participant name", "participant's name",
            "full name", "student", "student name", "candidate", "recipient", "attendee"
        ]
        for cand in common_candidates:
            match = next((c for c in columns if c.lower() == cand), None)
            if match:
                selected = match
                break
        if not selected:
            selected = columns[0]

    # Safe series extraction with iloc fallback
    if selected in df.columns:
        series = df[selected].dropna().astype(str).str.strip()
    else:
        series = df.iloc[:, 0].dropna().astype(str).str.strip()

    # Filter out empty strings and string representations of nan
    raw_names = [n for n in series if n and n.lower() != "nan"]

    # Apply case transformation
    if transform == "title":
        names = [n.title() for n in raw_names]
    elif transform == "upper":
        names = [n.upper() for n in raw_names]
    else:
        names = raw_names

    return names, columns, selected


def render_certificate(
    template: Image.Image,
    name: str,
    font_path: str,
    font_size: int = 72,
    font_color: str = "#043539",
    y_pos: int = 750,
    max_width: int = 1500,
    mask_placeholder: bool = True,
) -> Image.Image:
    """
    Render a single certificate with dynamically centered and auto-scaled participant name.
    """
    cert = template.convert("RGB")
    draw = ImageDraw.Draw(cert)
    t_width, _ = cert.size

    # Mask pre-existing placeholder text from the template if present
    # shortcut: mask coordinates calibrated for 2000x1414 HackerRank template, upgrade to user-defined ROI if arbitrary templates have pre-printed text
    if mask_placeholder:
        draw.rectangle((250, 700, 1750, 802), fill=(255, 255, 255))

    # Auto-scale font size if name exceeds max_width
    current_size = max(font_size, 20)
    font = ImageFont.truetype(font_path, current_size)
    bbox = draw.textbbox((0, 0), name, font=font)
    text_width = bbox[2] - bbox[0]

    while text_width > max_width and current_size > 20:
        current_size -= 2
        font = ImageFont.truetype(font_path, current_size)
        bbox = draw.textbbox((0, 0), name, font=font)
        text_width = bbox[2] - bbox[0]

    text_height = bbox[3] - bbox[1]

    # Calculate centered position (accounting for font glyph bbox offsets)
    x = (t_width - text_width) / 2 - bbox[0]
    y = y_pos - (text_height / 2) - bbox[1]

    draw.text((x, y), name, font=font, fill=font_color)
    return cert


def export_batch(
    template: Image.Image,
    names: Sequence[str],
    font_path: str,
    font_size: int = 72,
    font_color: str = "#043539",
    y_pos: int = 750,
    max_width: int = 1500,
    mask_placeholder: bool = True,
    format_type: str = "png_zip",
    progress_callback: Callable[[int, int], None] | None = None,
) -> tuple[io.BytesIO, str, str]:
    """
    Generate certificates for all names and package them in the requested format.

    Returns:
        tuple: (BytesIO_buffer, default_filename, mime_type)
    """
    total = len(names)
    if total == 0:
        raise ValueError("No participant names provided for export.")

    if format_type == "pdf_merged":
        pdf_images: list[Image.Image] = []
        for idx, name in enumerate(names, 1):
            img = render_certificate(
                template=template,
                name=name,
                font_path=font_path,
                font_size=font_size,
                font_color=font_color,
                y_pos=y_pos,
                max_width=max_width,
                mask_placeholder=mask_placeholder,
            )
            pdf_images.append(img)
            if progress_callback:
                progress_callback(idx, total)

        buf = io.BytesIO()
        first, rest = pdf_images[0], pdf_images[1:]
        first.save(buf, format="PDF", save_all=True, append_images=rest, resolution=100.0)
        buf.seek(0)
        return buf, "certificates_merged.pdf", "application/pdf"

    # ZIP archives (png_zip or pdf_zip)
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for idx, name in enumerate(names, 1):
            img = render_certificate(
                template=template,
                name=name,
                font_path=font_path,
                font_size=font_size,
                font_color=font_color,
                y_pos=y_pos,
                max_width=max_width,
                mask_placeholder=mask_placeholder,
            )
            safe_name = sanitize_filename(name)

            if format_type == "pdf_zip":
                file_buf = io.BytesIO()
                img.save(file_buf, format="PDF", resolution=100.0)
                filename = f"{idx:03d}_{safe_name}.pdf"
                zf.writestr(filename, file_buf.getvalue())
            else:
                # Default: PNG with optimized compression
                file_buf = io.BytesIO()
                img.save(file_buf, format="PNG", optimize=True, compress_level=6)
                filename = f"{idx:03d}_{safe_name}.png"
                zf.writestr(filename, file_buf.getvalue())

            if progress_callback:
                progress_callback(idx, total)

    zip_buf.seek(0)
    out_name = "certificates_pdf.zip" if format_type == "pdf_zip" else "certificates_png.zip"
    return zip_buf, out_name, "application/zip"


def export_batch_in_parts(
    template: Image.Image,
    names: list[str],
    font_path: str,
    font_size: int = 72,
    font_color: str = "#043539",
    y_pos: int = 750,
    max_width: int = 1500,
    mask_placeholder: bool = True,
    format_type: str = "png_zip",
    max_names_per_part: int = 35,
    progress_callback: Callable[[int, int], None] | None = None,
) -> list[tuple[io.BytesIO, str, str]]:
    """
    Split participant list into safe sub-batches (<= max_names_per_part),
    and package each into a separate standalone zip buffer.
    Ensures no single upload archive exceeds cloud payload thresholds (~25 MB).
    
    Returns:
        list of (BytesIO_buffer, filename, mime_type)
    """
    total_names = len(names)
    if total_names == 0:
        raise ValueError("No participant names provided.")

    # Merged PDF is already compact (~13 MB for 95 certs), single part unless > 150
    if format_type == "pdf_merged" and total_names <= 150:
        buf, filename, mime = export_batch(
            template=template,
            names=names,
            font_path=font_path,
            font_size=font_size,
            font_color=font_color,
            y_pos=y_pos,
            max_width=max_width,
            mask_placeholder=mask_placeholder,
            format_type=format_type,
            progress_callback=progress_callback,
        )
        return [(buf, filename, mime)]

    # If small batch, return single file
    if total_names <= max_names_per_part:
        buf, filename, mime = export_batch(
            template=template,
            names=names,
            font_path=font_path,
            font_size=font_size,
            font_color=font_color,
            y_pos=y_pos,
            max_width=max_width,
            mask_placeholder=mask_placeholder,
            format_type=format_type,
            progress_callback=progress_callback,
        )
        return [(buf, filename, mime)]

    # Chunk names into sub-batches
    chunks = [names[i : i + max_names_per_part] for i in range(0, total_names, max_names_per_part)]
    num_parts = len(chunks)
    parts_output: list[tuple[io.BytesIO, str, str]] = []

    overall_rendered = 0
    ext = "pdf" if format_type == "pdf_zip" else "png"

    for part_idx, chunk in enumerate(chunks, 1):
        zip_buf = io.BytesIO()
        start_idx = (part_idx - 1) * max_names_per_part + 1
        end_idx = start_idx + len(chunk) - 1

        with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            for item_idx, name in enumerate(chunk):
                cert_number = start_idx + item_idx
                img = render_certificate(
                    template=template,
                    name=name,
                    font_path=font_path,
                    font_size=font_size,
                    font_color=font_color,
                    y_pos=y_pos,
                    max_width=max_width,
                    mask_placeholder=mask_placeholder,
                )
                safe_name = sanitize_filename(name)
                filename = f"{cert_number:03d}_{safe_name}.{ext}"

                file_buf = io.BytesIO()
                if format_type == "pdf_zip":
                    img.save(file_buf, format="PDF", resolution=100.0)
                else:
                    img.save(file_buf, format="PNG", optimize=True, compress_level=6)

                zf.writestr(filename, file_buf.getvalue())
                overall_rendered += 1
                if progress_callback:
                    progress_callback(overall_rendered, total_names)

        zip_buf.seek(0)
        part_filename = f"certificates_{ext}_part{part_idx}_of_{num_parts}_(certs_{start_idx}-{end_idx}).zip"
        parts_output.append((zip_buf, part_filename, "application/zip"))

    return parts_output
