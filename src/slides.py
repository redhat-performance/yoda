import os
import csv
import json
import logging
from typing import Any
from tabulate import tabulate
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from src.drive import upload_image_to_drive

logger = logging.getLogger(__name__)

# If modifying these SCOPES, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/presentations',
    'https://www.googleapis.com/auth/drive.file'
]

def authenticate_google_slides(credentials_file: str) -> Any:
    """
    Function authenticate goole slides.

    Args:
        credentials_file (str): credentials file for authentication

    Returns:
        creds (Any): Updated credentials to build the service
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def get_slide_info(service: Any, presentation_id: str, expand: bool, csv_path="") -> dict:
    """
    Function to process a presentation and fetch slides information.

    Args:
        service (Any): service object for google apps
        presentation_id (str): presentation id to process
        expand (bool): flag to log the slides information into console
        csv_path (Optional[str]): csv path to store the slides preview

    Returns:
        slide_info (dict): dictionary that has all the slide information
    """
    presentation = service.presentations().get(presentationId=presentation_id).execute()
    slides = presentation.get('slides')

    slide_info = {}
    data = [['Slide Number', 'Slide ID', 'Slide Data']]
    for idx, slide in enumerate(slides):
        slide_id = slide.get('objectId')
        slide_data = {'images': {}, 'texts': {}}
        for element in slide.get('pageElements'):
            # Extract image information
            if element.get('image'):
                slide_data['images'][element['objectId']] = element['image'].get('contentUrl', None)
            
            # Extract text information
            if 'shape' in element and 'text' in element['shape']:
                text_elements = element['shape']['text'].get('textElements', [])
                text_runs = []
                for text_element in text_elements:
                    if 'textRun' in text_element:
                        text_runs.append(text_element['textRun']['content'])
                if text_runs:
                    slide_data['texts'][element['objectId']] = ''.join(text_runs)
        
        slide_info[slide_id] = slide_data
        data.append([idx + 1, slide_id, json.dumps(slide_data, indent=2)])
    if csv_path != "":
        with open(csv_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerows(data)
        logger.info(f"Slides preview writtern into file: {csv_path}")
    elif expand:
        heading_row = [["Presentation:", presentation_id]]
        full_table = heading_row + data
        table = tabulate(full_table, headers="firstrow", tablefmt="grid")
        logger.info("\n" + table)
    return slide_info

def replace_images_and_text(service, presentation_id, slide_info, slide_mapping) -> Any:
    """
    Function to replace images and text in the slides.

    Args:
        service (Any): service object for google apps
        presentation_id (str): presentation id to process
        slide_info (dict): dictionary containing existing slides information
        slide_mapping (dict): slide content mapping from the user provided input

    Returns:
        response (Any): consolidated object storing response for multiple requests
    """
    requests = []
    if "slide_info" not in slide_mapping:
        logger.info("Slide information not present in the mapping provided")
        return
    slide_content_mapping = slide_mapping["slide_info"]
    for slide in slide_content_mapping:
        if slide not in slide_info:
            logger.info(f"Slide: {slide} is not present in the presentation. Hence skipping it")
            continue
        else:
            if "images" in slide_content_mapping[slide]:
                for each_image in slide_content_mapping[slide]["images"]:
                    if each_image not in slide_info[slide]["images"]:
                        logger.info(f"Image: {each_image} is not found in slide: {slide}. Hence skipping it")
                        continue
                    else:
                        image_url = upload_image_to_drive(service, slide_content_mapping[slide]["images"][each_image])
                        requests.append({
                            'replaceImage': {
                                'imageObjectId': each_image,
                                'url': image_url,
                                'imageReplaceMethod': 'CENTER_INSIDE'
                            }
                        })
            if "texts" in slide_content_mapping[slide]:
                for each_text in slide_content_mapping[slide]["texts"]:
                    if each_text not in slide_info[slide]["texts"]:
                        logger.info(f"Text: {each_text} is not found in slide: {slide}. Hence skipping it")
                        continue
                    else:
                        # Create a request to delete the existing text
                        requests.append({
                            'deleteText': {
                                'objectId': each_text,
                                'textRange': {
                                    'type': 'ALL'
                                }
                            }
                        })
                        # Create a request to insert new text
                        requests.append({
                            'insertText': {
                                'objectId': each_text,
                                'insertionIndex': 0,
                                'text': slide_content_mapping[slide]["texts"][each_text]
                            }
                        })

    body = {
        'requests': requests
    }
    response = service.presentations().batchUpdate(presentationId=presentation_id, body=body).execute()
    return response
