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
        .create(body=metadata, fields="id, webViewLink", supportsAllDrives=True)
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
    Supports resumable chunked streaming (5MB slices) to prevent socket write timeouts.
    """
    file_bytes.seek(0)
    metadata = {
        "name": filename,
        "parents": [folder_id],
    }
    media = MediaIoBaseUpload(
        file_bytes,
        mimetype=mime_type,
        chunksize=5 * 1024 * 1024,
        resumable=True,
    )

    request = (
        service.files()
        .create(body=metadata, media_body=media, fields="id, webViewLink", supportsAllDrives=True)
    )

    try:
        response = None
        while response is None:
            status, response = request.next_chunk()
        return response.get("webViewLink", "") if isinstance(response, dict) else ""
    except (TypeError, ValueError, AttributeError):
        uploaded = request.execute()
        return uploaded.get("webViewLink", "") if isinstance(uploaded, dict) else ""


def automate_drive_export(
    file_bytes: io.BytesIO,
    filename: str,
    batch_folder_name: str,
    credentials_info: dict | None = None,
    parent_folder_id: str | None = None,
    mime_type: str = "application/zip",
    webhook_url: str | None = None,
) -> dict[str, str]:
    """
    End-to-end automation:
    1. If webhook_url is provided, uploads via Apps Script (personal Drive, 0 quota issues).
    2. Otherwise authenticates via Service Account with supportsAllDrives=True (Workspace Shared Drive).
    3. Automatically creates a new dedicated subfolder for this generation batch.
    4. Returns direct clickable Google Drive links to display on the UI.
    """
    if webhook_url:
        return upload_via_apps_script(file_bytes, filename, batch_folder_name, webhook_url)

    if not credentials_info:
        raise ValueError("Neither credentials_info nor webhook_url was provided.")

    service = get_drive_service(credentials_info)
    folder_id, folder_url = create_drive_folder(service, batch_folder_name, parent_folder_id)
    file_url = upload_file_to_folder(service, file_bytes, filename, folder_id, mime_type)

    return {
        "folder_id": folder_id,
        "folder_url": folder_url,
        "file_url": file_url,
        "folder_name": batch_folder_name,
    }


def upload_via_apps_script(
    file_bytes: io.BytesIO,
    filename: str,
    folder_name: str,
    webhook_url: str,
    folder_id: str | None = None,
) -> dict[str, str]:
    """
    Upload directly to a personal Google Drive account via a Google Apps Script Web App.
    Uses the user's personal Google Drive 15GB storage quota, completely bypassing
    GCP Service Account 0-byte storage restrictions.
    """
    import base64
    import requests

    file_bytes.seek(0)
    raw_data = file_bytes.read()
    raw_size_mb = len(raw_data) / (1024 * 1024)

    # Google Apps Script Web Apps have a hard 50 MB HTTP POST body limit.
    # Base64 encoding expands binary data by 33% (e.g. 35 MB raw becomes ~47 MB payload).
    if raw_size_mb > 35.0:
        raise TimeoutError(
            f"This individual file part is {raw_size_mb:.1f} MB, which exceeds Google Apps Script's "
            f"35 MB single-upload limit (expanding to {raw_size_mb * 1.33:.1f} MB in base64)."
        )

    b64_content = base64.b64encode(raw_data).decode("utf-8")
    payload = {
        "filename": filename,
        "folder": folder_name,
        "content": b64_content,
    }
    if folder_id:
        payload["folder_id"] = folder_id

    # Use a generous 5-minute timeout window (30s connect, 300s read/write) for large archives
    resp = requests.post(webhook_url, json=payload, timeout=(30, 300))
    resp.raise_for_status()
    data = resp.json()

    returned_folder_id = data.get("folder_id", folder_id or "")
    folder_url = data.get("folder_url", f"https://drive.google.com/drive/folders/{returned_folder_id}")

    return {
        "folder_id": returned_folder_id,
        "folder_url": folder_url,
        "file_url": data.get("file_url", ""),
        "folder_name": folder_name,
    }


def automate_chunked_drive_export(
    parts: list[tuple[io.BytesIO, str, str]],
    batch_folder_name: str,
    credentials_info: dict | None = None,
    parent_folder_id: str | None = None,
    webhook_url: str | None = None,
    progress_callback: object | None = None,
) -> dict[str, str]:
    """
    Sequential Gateway Uploader:
    Streams multiple file parts sequentially into the exact same Google Drive batch folder.
    Guarantees no single request exceeds cloud limits and eliminates timeouts.
    """
    total_parts = len(parts)
    if total_parts == 0:
        raise ValueError("No parts to upload.")

    folder_id: str | None = None
    folder_url: str = ""
    service = None

    if not webhook_url:
        if not credentials_info:
            raise ValueError("Neither credentials_info nor webhook_url was provided.")
        service = get_drive_service(credentials_info)
        folder_id, folder_url = create_drive_folder(service, batch_folder_name, parent_folder_id)

    last_file_url = ""

    for idx, (p_bytes, p_filename, p_mime) in enumerate(parts, 1):
        if progress_callback and callable(progress_callback):
            progress_callback(idx, total_parts, p_filename)

        if webhook_url:
            res = upload_via_apps_script(
                file_bytes=p_bytes,
                filename=p_filename,
                folder_name=batch_folder_name,
                webhook_url=webhook_url,
                folder_id=folder_id,
            )
            folder_id = res.get("folder_id") or folder_id
            folder_url = res.get("folder_url") or folder_url
            last_file_url = res.get("file_url") or last_file_url
        else:
            last_file_url = upload_file_to_folder(service, p_bytes, p_filename, folder_id, p_mime)

    return {
        "folder_id": folder_id or "",
        "folder_url": folder_url,
        "file_url": last_file_url,
        "folder_name": batch_folder_name,
        "total_parts": str(total_parts),
    }

