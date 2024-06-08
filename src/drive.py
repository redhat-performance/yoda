import os
import logging
from typing import Any
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger(__name__)

def upload_image_to_drive(service: Any, image_path: str) -> str:
    """
    Function to upload an image to drive.

    Args:
        service (Any): google client service object
        image_path (int): source image_path that needs to be uploaded in drive

    Returns:
        image_url (str): url where the image is uploaded in google drive
    """
    drive_service = build('drive', 'v3', credentials=service._http.credentials)

    # File metadata
    file_metadata = {
        'name': os.path.basename(image_path),
        'mimeType': 'image/png'
    }
    media = MediaFileUpload(image_path, mimetype='image/png')

    # Upload the file
    uploaded_file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()

    # Set the permissions to make the file publicly accessible
    permission = {
        'type': 'anyone',
        'role': 'reader'
    }
    drive_service.permissions().create(fileId=uploaded_file['id'], body=permission).execute()

    image_url = f'https://drive.google.com/uc?id={uploaded_file["id"]}'
    logger.info(f"Uploaded image:{image_path} to url:{image_url}")
    return image_url
