"""
Core engine for the bulk certificate generator.
Handles spreadsheet loading, text rendering with auto-scaling,
and bulk export packaging (PNG zip, PDF zip, merged PDF).
"""

from __future__ import annotations

import functools
import io
import os
import re
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Sequence
import pandas as pd
from PIL import Image, ImageDraw, ImageFont


@functools.lru_cache(maxsize=128)
def get_font(font_path: str, size: int) -> ImageFont.FreeTypeFont:
    """Load and cache TrueType fonts by path and size to eliminate disk/parse overhead."""
    return ImageFont.truetype(font_path, size)


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
    if template.mode != "RGB":
        cert = template.convert("RGB")
    else:
        cert = template.copy()

    draw = ImageDraw.Draw(cert)
    t_width, _ = cert.size

    # Mask pre-existing placeholder text from the template if present
    # shortcut: mask coordinates calibrated for 2000x1414 HackerRank template, upgrade to user-defined ROI if arbitrary templates have pre-printed text
    if mask_placeholder:
        draw.rectangle((250, 700, 1750, 802), fill=(255, 255, 255))

    # Auto-scale font size if name exceeds max_width
    current_size = max(font_size, 20)
    font = get_font(font_path, current_size)
    bbox = draw.textbbox((0, 0), name, font=font)
    text_width = bbox[2] - bbox[0]

    while text_width > max_width and current_size > 20:
        current_size -= 2
        font = get_font(font_path, current_size)
        bbox = draw.textbbox((0, 0), name, font=font)
        text_width = bbox[2] - bbox[0]

    text_height = bbox[3] - bbox[1]

    # Calculate centered position (accounting for font glyph bbox offsets)
    x = (t_width - text_width) / 2 - bbox[0]
    y = y_pos - (text_height / 2) - bbox[1]

    draw.text((x, y), name, font=font, fill=font_color)
    return cert


def _render_and_encode_worker(
    item: tuple[int, str, Image.Image, str, int, str, int, int, bool, str]
) -> tuple[int, str, bytes, Image.Image | None]:
    """Worker task executed across thread pool for parallel rendering and compression."""
    idx, name, tmpl, font_path, font_size, font_color, y_pos, max_width, mask_placeholder, format_type = item
    cert = render_certificate(
        template=tmpl,
        name=name,
        font_path=font_path,
        font_size=font_size,
        font_color=font_color,
        y_pos=y_pos,
        max_width=max_width,
        mask_placeholder=mask_placeholder,
    )
    safe_name = sanitize_filename(name)

    if format_type == "pdf_merged":
        return idx, f"{idx:03d}_{safe_name}.pdf", b"", cert

    buf = io.BytesIO()
    if format_type == "pdf_zip":
        cert.save(buf, format="PDF", resolution=100.0)
        ext = "pdf"
    else:
        # PNG: compress_level=3, optimize=False gives 10x-30x speedup with 100% lossless fidelity
        cert.save(buf, format="PNG", optimize=False, compress_level=3)
        ext = "png"

    filename = f"{idx:03d}_{safe_name}.{ext}"
    return idx, filename, buf.getvalue(), None


def export_batch_unified(
    template: Image.Image,
    names: Sequence[str],
    font_path: str,
    font_size: int = 72,
    font_color: str = "#043539",
    y_pos: int = 750,
    max_width: int = 1500,
    mask_placeholder: bool = True,
    format_type: str = "png_zip",
    max_names_per_part: int = 30,
    progress_callback: Callable[[int, int], None] | None = None,
) -> tuple[tuple[io.BytesIO, str, str], list[tuple[io.BytesIO, str, str]]]:
    """
    High-performance single-pass certificate generation and packaging engine.
    Executes multithreaded rendering and returns both the master download archive
    and chunked safe parts for cloud sync without double-rendering.
    """
    total = len(names)
    if total == 0:
        raise ValueError("No participant names provided for export.")

    # Pre-load template into memory once to ensure multi-threaded thread-safety
    clean_template = template.convert("RGB")
    clean_template.load()

    max_workers = min(8, os.cpu_count() or 4)
    tasks = [
        (
            idx,
            name,
            clean_template,
            font_path,
            font_size,
            font_color,
            y_pos,
            max_width,
            mask_placeholder,
            format_type,
        )
        for idx, name in enumerate(names, 1)
    ]

    results: list[tuple[int, str, bytes, Image.Image | None]] = []
    completed_count = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_idx = {executor.submit(_render_and_encode_worker, it): it[0] for it in tasks}
        for future in as_completed(future_to_idx):
            res = future.result()
            results.append(res)
            completed_count += 1
            if progress_callback:
                progress_callback(completed_count, total)

    results.sort(key=lambda x: x[0])

    # Merged PDF output
    if format_type == "pdf_merged":
        buf = io.BytesIO()
        pdf_images = [r[3] for r in results if r[3] is not None]
        first, rest = pdf_images[0], pdf_images[1:]
        first.save(buf, format="PDF", save_all=True, append_images=rest, resolution=100.0)
        buf.seek(0)
        master_res = (buf, "certificates_merged.pdf", "application/pdf")
        return master_res, [master_res]

    # ZIP archives (png_zip or pdf_zip)
    ext = "pdf" if format_type == "pdf_zip" else "png"
    master_filename = f"certificates_{ext}.zip"
    mime_type = "application/zip"

    # Single part scenario
    if total <= max_names_per_part:
        master_buf = io.BytesIO()
        if format_type == "pdf_zip":
            zf_ctx = zipfile.ZipFile(master_buf, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=1)
        else:
            zf_ctx = zipfile.ZipFile(master_buf, mode="w", compression=zipfile.ZIP_STORED)

        with zf_ctx as zf:
            for _, fname, data, _ in results:
                zf.writestr(fname, data)

        master_buf.seek(0)
        master_res = (master_buf, master_filename, mime_type)
        return master_res, [master_res]

    # Multi-part chunked scenario (simultaneously packs master zip and parts in one pass)
    chunks = [names[i : i + max_names_per_part] for i in range(0, total, max_names_per_part)]
    num_parts = len(chunks)

    master_buf = io.BytesIO()
    part_bufs = [io.BytesIO() for _ in range(num_parts)]

    if format_type == "pdf_zip":
        master_zf = zipfile.ZipFile(master_buf, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=1)
        part_zfs = [
            zipfile.ZipFile(pb, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=1)
            for pb in part_bufs
        ]
    else:
        master_zf = zipfile.ZipFile(master_buf, mode="w", compression=zipfile.ZIP_STORED)
        part_zfs = [
            zipfile.ZipFile(pb, mode="w", compression=zipfile.ZIP_STORED)
            for pb in part_bufs
        ]

    try:
        for idx, fname, data, _ in results:
            master_zf.writestr(fname, data)
            part_idx = (idx - 1) // max_names_per_part
            part_zfs[part_idx].writestr(fname, data)
    finally:
        master_zf.close()
        for pz in part_zfs:
            pz.close()

    master_buf.seek(0)
    master_res = (master_buf, master_filename, mime_type)

    parts_output: list[tuple[io.BytesIO, str, str]] = []
    for p_idx, pb in enumerate(part_bufs):
        pb.seek(0)
        start_idx = p_idx * max_names_per_part + 1
        end_idx = min((p_idx + 1) * max_names_per_part, total)
        part_filename = f"certificates_{ext}_part{p_idx+1}_of_{num_parts}_(certs_{start_idx}-{end_idx}).zip"
        parts_output.append((pb, part_filename, mime_type))

    return master_res, parts_output


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
    """Generate certificates and package into a single master archive."""
    master_res, _ = export_batch_unified(
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
    return master_res


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
    """Split participants into chunked archive parts (<= max_names_per_part)."""
    _, parts = export_batch_unified(
        template=template,
        names=names,
        font_path=font_path,
        font_size=font_size,
        font_color=font_color,
        y_pos=y_pos,
        max_width=max_width,
        mask_placeholder=mask_placeholder,
        format_type=format_type,
        max_names_per_part=max_names_per_part,
        progress_callback=progress_callback,
    )
    return parts
