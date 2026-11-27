"""
Google Drive automated folder creation and file upload module.
Uses Google Service Account credentials to dynamically create folders
and upload generated certificate archives without manual user sign-in.
"""

from __future__ import annotations

import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

SCOPES = ["https://www.googleapis.com/auth/drive"]


def get_drive_service(credentials_info: dict):
    """Build and return an authorized Google Drive v3 service instance."""
    creds = service_account.Credentials.from_service_account_info(
        credentials_info, scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds)


def create_drive_folder(
    service, folder_name: str, parent_id: str | None = None
) -> tuple[str, str]:
    """
    Create a new folder in Google Drive.
    
    Args:
        service: Authenticated Drive API client
        folder_name: Display name for the new folder
        parent_id: Optional ID of the parent folder (e.g. shared root)
        
    Returns:
        tuple[str, str]: (folder_id, web_view_link)
    """
    metadata: dict = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_id and parent_id.strip():
        metadata["parents"] = [parent_id.strip()]

    folder = (
        service.files()
        .create(body=metadata, fields="id, webViewLink")
        .execute()
    )
    folder_id = folder.get("id")
    web_link = folder.get("webViewLink", f"https://drive.google.com/drive/folders/{folder_id}")

    # Ensure anyone with the link can view if parent isn't already shared
    try:
        service.permissions().create(
            fileId=folder_id,
            body={"role": "reader", "type": "anyone"},
        ).execute()
    except Exception:
        # Permission change may be restricted by workspace domain policy
        pass

    return folder_id, web_link


def upload_file_to_folder(
    service,
    file_bytes: io.BytesIO,
    filename: str,
    folder_id: str,
    mime_type: str = "application/zip",
) -> str:
    """
    Upload an in-memory file buffer directly to a target Google Drive folder.
    """
    file_bytes.seek(0)
    metadata = {
        "name": filename,
        "parents": [folder_id],
    }
    media = MediaIoBaseUpload(file_bytes, mimetype=mime_type, resumable=True)

    uploaded = (
        service.files()
        .create(body=metadata, media_body=media, fields="id, webViewLink")
        .execute()
    )
    return uploaded.get("webViewLink", "")


def automate_drive_export(
    file_bytes: io.BytesIO,
    filename: str,
    batch_folder_name: str,
    credentials_info: dict,
    parent_folder_id: str | None = None,
    mime_type: str = "application/zip",
) -> dict[str, str]:
    """
    End-to-end automation:
    1. Authenticate with Service Account.
    2. Automatically creates a new dedicated subfolder for this generation batch.
    3. Streams the certificate archive directly into the newly created folder.
    4. Returns direct clickable Google Drive links to display on the UI.
    
    Returns:
        dict with keys: 'folder_id', 'folder_url', 'file_url', 'folder_name'
    """
    service = get_drive_service(credentials_info)
    folder_id, folder_url = create_drive_folder(service, batch_folder_name, parent_folder_id)
    file_url = upload_file_to_folder(service, file_bytes, filename, folder_id, mime_type)

    return {
        "folder_id": folder_id,
        "folder_url": folder_url,
        "file_url": file_url,
        "folder_name": batch_folder_name,
    }
