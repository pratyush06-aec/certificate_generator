"""
Unit tests for certificate generator core module.
"""

import io
import unittest
import zipfile
import pandas as pd
from PIL import Image

from core.generator import (
    load_participants,
    render_certificate,
    export_batch,
    sanitize_filename,
)


class TestCertificateGenerator(unittest.TestCase):

    def setUp(self):
        # Create a lightweight dummy template (2000x1414 white canvas)
        self.template = Image.new("RGB", (2000, 1414), color=(255, 255, 255))
        self.font_path = "assets/fonts/SegoeUI-Bold.ttf"

    def test_sanitize_filename(self):
        self.assertEqual(sanitize_filename("John Doe"), "John_Doe")
        self.assertEqual(sanitize_filename("Jane / Doe: Spec*"), "Jane_Doe_Spec")
        self.assertEqual(sanitize_filename("   "), "participant")

    def test_load_participants_csv(self):
        csv_data = io.StringIO("ID,Participant Name,Score\n1, Alice Smith ,95\n2,Bob Jones,88\n3,,\n4, Charlie Brown,70\n")
        names, cols, sel = load_participants(csv_data)
        self.assertIn("Participant Name", cols)
        self.assertEqual(sel, "Participant Name")
        self.assertEqual(names, ["Alice Smith", "Bob Jones", "Charlie Brown"])

    def test_load_participants_with_trailing_spaces_and_bom(self):
        # Edge case: Column header has trailing space and BOM
        raw_bytes = io.BytesIO("\ufeffParticipant Name  ,Score\nAlice Smith,100\nBob Jones,90\n".encode("utf-8"))
        names, cols, sel = load_participants(raw_bytes)
        self.assertIn("Participant Name", cols)
        self.assertEqual(sel, "Participant Name")
        self.assertEqual(names, ["Alice Smith", "Bob Jones"])

    def test_load_participants_casing_transform(self):
        csv_data = io.StringIO("Name\njohn doe\nJANE ROE\n")
        title_names, _, _ = load_participants(csv_data, transform="title")
        self.assertEqual(title_names, ["John Doe", "Jane Roe"])

        csv_data.seek(0)
        upper_names, _, _ = load_participants(csv_data, transform="upper")
        self.assertEqual(upper_names, ["JOHN DOE", "JANE ROE"])

    def test_render_certificate_dimensions(self):
        cert = render_certificate(
            template=self.template,
            name="Alexander Supertramp",
            font_path=self.font_path,
            font_size=72,
            font_color="#043539",
            y_pos=750,
            mask_placeholder=True,
        )
        self.assertEqual(cert.size, (2000, 1414))
        self.assertEqual(cert.mode, "RGB")

    def test_render_certificate_long_name_auto_scaling(self):
        # A very long name should render without crashing or exceeding boundaries
        long_name = "Prof. Dr. Bartholomew Montgomery-Wellington the Third Esq."
        cert = render_certificate(
            template=self.template,
            name=long_name,
            font_path=self.font_path,
            font_size=90,
            max_width=1400,
        )
        self.assertEqual(cert.size, (2000, 1414))

    def test_export_batch_png_zip(self):
        names = ["Alice Smith", "Bob Jones"]
        buf, filename, mime = export_batch(
            template=self.template,
            names=names,
            font_path=self.font_path,
            format_type="png_zip",
        )
        self.assertEqual(filename, "certificates_png.zip")
        self.assertEqual(mime, "application/zip")
        
        # Verify ZIP contains 2 PNG files
        with zipfile.ZipFile(buf, "r") as zf:
            namelist = zf.namelist()
            self.assertEqual(len(namelist), 2)
            self.assertTrue(namelist[0].endswith(".png"))
            self.assertTrue(namelist[1].endswith(".png"))

    def test_export_batch_pdf_zip(self):
        names = ["Alice Smith", "Bob Jones"]
        buf, filename, mime = export_batch(
            template=self.template,
            names=names,
            font_path=self.font_path,
            format_type="pdf_zip",
        )
        self.assertEqual(filename, "certificates_pdf.zip")
        with zipfile.ZipFile(buf, "r") as zf:
            namelist = zf.namelist()
            self.assertEqual(len(namelist), 2)
            self.assertTrue(namelist[0].endswith(".pdf"))

    def test_export_batch_pdf_merged(self):
        names = ["Alice Smith", "Bob Jones"]
        buf, filename, mime = export_batch(
            template=self.template,
            names=names,
            font_path=self.font_path,
            format_type="pdf_merged",
        )
        self.assertEqual(filename, "certificates_merged.pdf")
        self.assertEqual(mime, "application/pdf")
        self.assertGreater(len(buf.getvalue()), 1000)

    def test_export_batch_empty_raises(self):
        with self.assertRaises(ValueError):
            export_batch(
                template=self.template,
                names=[],
                font_path=self.font_path,
            )


if __name__ == "__main__":
    unittest.main()
