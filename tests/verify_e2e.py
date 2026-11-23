"""
End-to-end integration verification using real assets.
"""

from pathlib import Path
from PIL import Image
from core.generator import load_participants, render_certificate, export_batch

def main():
    template_path = Path("assets/tech-start cert temp.png")
    assert template_path.exists(), f"Missing template at {template_path}"
    
    template = Image.open(template_path)
    print(f"[OK] Loaded template: {template.size}, mode: {template.mode}")

    sample_csv = Path("assets/sample_participants.csv")
    names, cols, sel = load_participants(str(sample_csv))
    print(f"[OK] Parsed {len(names)} participants from {sample_csv.name} using column '{sel}':")
    for n in names[:3]:
        print(f"     - {n}")
    assert len(names) == 8, f"Expected 8 names, got {len(names)}"

    font_path = "assets/fonts/SegoeUI-Bold.ttf"

    # Test single render
    sample_name = names[0]
    cert = render_certificate(
        template=template,
        name=sample_name,
        font_path=font_path,
        font_size=72,
        font_color="#043539",
        y_pos=745,
        mask_placeholder=True,
    )
    assert cert.size == (2000, 1414)
    # Save a sample preview to disk to visually inspect
    preview_output = Path("assets/test_preview.png")
    cert.save(preview_output)
    print(f"[OK] Rendered and saved test preview to {preview_output}")

    # Test PNG ZIP export
    png_buf, png_name, _ = export_batch(template, names, font_path, format_type="png_zip")
    assert png_buf.getbuffer().nbytes > 100000, "PNG ZIP unexpectedly small"
    print(f"[OK] PNG ZIP generated: {png_name} ({png_buf.getbuffer().nbytes / 1024:.1f} KB)")

    # Test PDF ZIP export
    pdf_zip_buf, pdf_zip_name, _ = export_batch(template, names, font_path, format_type="pdf_zip")
    assert pdf_zip_buf.getbuffer().nbytes > 100000, "PDF ZIP unexpectedly small"
    print(f"[OK] PDF ZIP generated: {pdf_zip_name} ({pdf_zip_buf.getbuffer().nbytes / 1024:.1f} KB)")

    # Test Merged PDF export
    merged_buf, merged_name, _ = export_batch(template, names, font_path, format_type="pdf_merged")
    assert merged_buf.getbuffer().nbytes > 100000, "Merged PDF unexpectedly small"
    print(f"[OK] Merged PDF generated: {merged_name} ({merged_buf.getbuffer().nbytes / 1024:.1f} KB)")

    print("\nALL END-TO-END CHECKS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
