"""
Unit tests for core/drive_uploader.py using mocks.
"""

import io
import unittest
from unittest.mock import MagicMock, patch
import requests
from core.drive_uploader import (
    create_drive_folder,
    upload_file_to_folder,
    automate_drive_export,
)


class TestDriveUploader(unittest.TestCase):

    def test_create_drive_folder(self):
        mock_service = MagicMock()
        mock_create = mock_service.files().create
        mock_create.return_value.execute.return_value = {
            "id": "folder_123",
            "webViewLink": "https://drive.google.com/drive/folders/folder_123",
        }

        folder_id, link = create_drive_folder(mock_service, "Test_Folder", parent_id="parent_root")
        self.assertEqual(folder_id, "folder_123")
        self.assertIn("folder_123", link)

        # Verify parent passed in metadata
        call_kwargs = mock_create.call_args[1]
        self.assertEqual(call_kwargs["body"]["parents"], ["parent_root"])

    def test_upload_file_to_folder(self):
        mock_service = MagicMock()
        mock_create = mock_service.files().create
        mock_create.return_value.execute.return_value = {
            "id": "file_456",
            "webViewLink": "https://drive.google.com/file/d/file_456/view",
        }

        dummy_bytes = io.BytesIO(b"dummy zip content")
        file_link = upload_file_to_folder(
            mock_service, dummy_bytes, "certs.zip", "folder_123"
        )
        self.assertIn("file_456", file_link)

    @patch("core.drive_uploader.get_drive_service")
    @patch("core.drive_uploader.create_drive_folder")
    @patch("core.drive_uploader.upload_file_to_folder")
    def test_automate_drive_export(self, mock_upload, mock_create_folder, mock_get_service):
        mock_create_folder.return_value = ("new_f_id", "https://drive.google.com/folders/new_f_id")
        mock_upload.return_value = "https://drive.google.com/files/new_f_id"

        dummy_bytes = io.BytesIO(b"data")
        result = automate_drive_export(
            file_bytes=dummy_bytes,
            filename="batch.zip",
            batch_folder_name="Batch_2026",
            credentials_info={"type": "service_account"},
            parent_folder_id="root_id",
        )

        self.assertEqual(result["folder_id"], "new_f_id")
        self.assertEqual(result["folder_name"], "Batch_2026")
        self.assertEqual(result["folder_url"], "https://drive.google.com/folders/new_f_id")

    @patch("requests.post")
    def test_upload_via_apps_script_success(self, mock_post):
        from core.drive_uploader import upload_via_apps_script
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "folder_id": "f_123",
            "folder_url": "https://drive.google.com/drive/folders/f_123",
            "file_url": "https://drive.google.com/file/f_123",
        }
        mock_post.return_value = mock_resp

        buf = io.BytesIO(b"test certificate payload")
        res = upload_via_apps_script(buf, "certs.zip", "Batch_1", "https://script.google.com/macros/s/xyz/exec")
        self.assertEqual(res["folder_id"], "f_123")
        self.assertEqual(mock_post.call_args[1]["timeout"], (30, 300))

    def test_upload_via_apps_script_oversize_guard(self):
        from core.drive_uploader import upload_via_apps_script
        # Buffer simulating > 35 MB
        oversize_buf = io.BytesIO(b"0" * (36 * 1024 * 1024))
        with self.assertRaises(TimeoutError) as ctx:
            upload_via_apps_script(oversize_buf, "certs.zip", "Batch_1", "https://script.google.com/macros/s/xyz/exec")
        self.assertIn("exceeds Google Apps Script", str(ctx.exception))

    @patch.object(requests.Session, "post")
    def test_automate_chunked_drive_export(self, mock_post):
        from core.drive_uploader import automate_chunked_drive_export
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "folder_id": "batch_folder_99",
            "folder_url": "https://drive.google.com/drive/folders/batch_folder_99",
            "file_url": "https://drive.google.com/file/part.zip",
        }
        mock_post.return_value = mock_resp

        part1 = (io.BytesIO(b"part1"), "part1.zip", "application/zip")
        part2 = (io.BytesIO(b"part2"), "part2.zip", "application/zip")

        folder_created_called = []
        def on_folder(f_id, f_url):
            folder_created_called.append((f_id, f_url))

        res = automate_chunked_drive_export(
            parts=[part1, part2],
            batch_folder_name="Batch_99",
            webhook_url="https://script.google.com/macros/s/xyz/exec",
            on_folder_created=on_folder,
        )
        self.assertEqual(res["folder_id"], "batch_folder_99")
        self.assertEqual(res["total_parts"], "2")
        self.assertEqual(mock_post.call_count, 2)
        self.assertEqual(len(folder_created_called), 1)
        self.assertEqual(folder_created_called[0][0], "batch_folder_99")


if __name__ == "__main__":
    unittest.main()
