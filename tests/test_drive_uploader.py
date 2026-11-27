"""
Unit tests for core/drive_uploader.py using mocks.
"""

import io
import unittest
from unittest.mock import MagicMock, patch
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


if __name__ == "__main__":
    unittest.main()
