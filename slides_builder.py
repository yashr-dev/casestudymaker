"""
Google Slides Builder for DigiChefs Case Studies.
Duplicates the template presentation and populates it with generated content.
"""

import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import json

SCOPES = [
    'https://www.googleapis.com/auth/presentations',
    'https://www.googleapis.com/auth/drive'
]

TOKEN_FILE = 'token.json'
CREDENTIALS_FILE = 'credentials.json'


def get_google_credentials():
    """Get or refresh Google API credentials."""
    creds = None
    
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"'{CREDENTIALS_FILE}' not found. Download OAuth 2.0 Client ID credentials "
                    "from Google Cloud Console and save as 'credentials.json'."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=8090)
        
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    
    return creds


def duplicate_template(template_id: str, new_title: str) -> str:
    """
    Duplicate the template Google Slides presentation.
    
    Args:
        template_id: The ID of the template presentation
        new_title: Title for the new presentation
    
    Returns:
        The ID of the newly created presentation
    """
    creds = get_google_credentials()
    drive_service = build('drive', 'v3', credentials=creds)
    
    copy_body = {
        'name': new_title
    }
    
    response = drive_service.files().copy(
        fileId=template_id,
        body=copy_body
    ).execute()
    
    new_presentation_id = response.get('id')
    
    # Make it accessible via link
    drive_service.permissions().create(
        fileId=new_presentation_id,
        body={
            'type': 'anyone',
            'role': 'writer'
        }
    ).execute()
    
    return new_presentation_id


def populate_slides(presentation_id: str, content: dict) -> str:
    """
    Populate the duplicated presentation with generated content.
    
    Args:
        presentation_id: ID of the new presentation
        content: Dict with all case study content sections
    
    Returns:
        URL to the populated presentation
    """
    creds = get_google_credentials()
    slides_service = build('slides', 'v1', credentials=creds)
    
    # First, get the presentation to understand its structure
    presentation = slides_service.presentations().get(
        presentationId=presentation_id
    ).execute()
    
    # First pass: analyze content length and duplicate slides if necessary
    # We will track the original slides and create a new list of slides
    # along with their mapped "template index" so we know what content goes where
    
    slides = presentation.get('slides', [])
    slide_mapping = []  # List of tuples: (actual_slide_id, logical_slide_index, is_continuation)
    
    for i, slide in enumerate(slides):
        slide_id = slide['objectId']
        slide_mapping.append((slide_id, i, False))
        
        # Check if this slide needs duplication (e.g., Deliverables/Solutions or Results)
        # We estimate this by checking the combined length of bullet points
        
        # Slide 5 is Solution/Delivery, Slide 7 is Results
        if i == 5:
            steps_text = content.get('delivery_steps', '')
            # If there are more than 4 bullets or it's very long, split it
            if steps_text.count('•') > 4 or len(steps_text) > 400:
                print(f"Duplicating Solution slide {i} due to length.")
                new_slide_id = f"duplicated_slide_{i}_{len(slide_mapping)}"
                
                # Request to duplicate the slide
                duplicate_req = {
                    'duplicateObject': {
                        'objectId': slide_id,
                        'objectIds': {
                            slide_id: new_slide_id
                        }
                    }
                }
                slides_service.presentations().batchUpdate(
                    presentationId=presentation_id,
                    body={'requests': [duplicate_req]}
                ).execute()
                
                # Add the new slide to our processing map
                slide_mapping.append((new_slide_id, i, True))
                
        elif i == 7:
            impact_text = content.get('impact_metrics', '')
            if impact_text.count('•') > 4 or len(impact_text) > 400:
                print(f"Duplicating Results slide {i} due to length.")
                new_slide_id = f"duplicated_slide_{i}_{len(slide_mapping)}"
                
                duplicate_req = {
                    'duplicateObject': {
                        'objectId': slide_id,
                        'objectIds': {
                            slide_id: new_slide_id
                        }
                    }
                }
                slides_service.presentations().batchUpdate(
                    presentationId=presentation_id,
                    body={'requests': [duplicate_req]}
                ).execute()
                
                slide_mapping.append((new_slide_id, i, True))

    # Re-fetch the presentation to get the new slide shapes and object IDs
    presentation = slides_service.presentations().get(
        presentationId=presentation_id
    ).execute()
    
    updated_slides = presentation.get('slides', [])
    
    # Create a quick lookup for slides by ID
    slide_by_id = {s['objectId']: s for s in updated_slides}

    requests = []
    
    # Process each slide based on its logical template mapping
    for slide_id, logical_index, is_continuation in slide_mapping:
        if slide_id not in slide_by_id:
            continue
            
        current_slide = slide_by_id[slide_id]
        slide_requests = _build_slide_requests(current_slide, logical_index, content, is_continuation)
        requests.extend(slide_requests)
    
    # Execute all text updates in one batch
    if requests:
        slides_service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={'requests': requests}
        ).execute()
    
    return f"https://docs.google.com/presentation/d/{presentation_id}/edit"


def _build_slide_requests(slide: dict, slide_index: int, content: dict, is_continuation: bool = False) -> list:
    """Build replacement requests for a specific slide."""
    requests = []
    
    # Get all text elements in this slide
    elements = slide.get('pageElements', [])
    
    for element in elements:
        if 'shape' not in element:
            continue
        
        shape = element['shape']
        if 'text' not in shape:
            continue
        
        text_content = shape['text']
        full_text = ''
        for text_element in text_content.get('textElements', []):
            if 'textRun' in text_element:
                full_text += text_element['textRun'].get('content', '')
        
        full_text = full_text.strip()
        object_id = element['objectId']
        
        # Map slide content based on index and placeholder text
        replacement = _get_replacement_text(slide_index, full_text, content, is_continuation)
        
        if replacement is not None:
            # First insert new text at index 0
            requests.append({
                'insertText': {
                    'objectId': object_id,
                    'insertionIndex': 0,
                    'text': replacement
                }
            })
            # Then delete the original text which was pushed down
            requests.append({
                'deleteText': {
                    'objectId': object_id,
                    'textRange': {
                        'type': 'FIXED_RANGE',
                        'startIndex': len(replacement),
                        'endIndex': len(replacement) + len(full_text)
                    }
                }
            })
    
    return requests


def _get_replacement_text(slide_index: int, current_text: str, content: dict, is_continuation: bool = False) -> str:
    """
    Determine what replacement text to use based on slide index and current text.
    Handles splitting content if 'is_continuation' is True.
    Returns None if no replacement needed.
    """
    current_lower = current_text.lower().strip()
    
    # Slide 1 (index 0): Title slide - update title
    if slide_index == 0:
        if 'multi' in current_lower and 'case study' in current_lower:
            # You usually leave the internal separator labels as-is, or optionally set the brand here.
            # But earlier it was wrongly pulling case_study_title here.
            return current_text
        if 'award' in current_lower or 'website' in current_lower:
            return current_text
    
    # Slide 2 (index 1): Snapshot / KPI Overview
    if slide_index == 1:
        if 'jio' in current_lower or 'tessarct' in current_lower or 'clear and descriptive' in current_lower:
            return content.get('case_study_title', current_text)
        if '34k' in current_lower or 'video views' in current_lower:
            return f"{content.get('kpi_1_number', '')}\n{content.get('kpi_1_label', '')}"
        if '15k' in current_lower or 'impressions' in current_lower:
            return f"{content.get('kpi_2_number', '')}\n{content.get('kpi_2_label', '')}"
        if '2.5k' in current_lower or 'shares' in current_lower:
            return f"{content.get('kpi_3_number', '')}\n{content.get('kpi_3_label', '')}"
    
    # Slide 3 (index 2): About the Brand + Challenge
    if slide_index == 2:
        if "client logo" in current_lower or "client description" in current_lower or "brief description" in current_lower:
            return content.get('about_brand', current_text)
        if 'clearly describe the problem' in current_lower or 'relevant quote' in current_lower:
            return content.get('challenge', current_text)
        if 'add points in bullets' in current_lower:
            return ''  # Clear placeholder text
    
    # Slide 4 (index 3): Core Insight
    if slide_index == 3:
        if 'lorem ipsum' in current_lower or 'add points' in current_lower:
            return content.get('core_insight', current_text)
    
    # Slide 5 (index 4): Strategy
    if slide_index == 4:
        if 'lorem ipsum' in current_lower or 'add points' in current_lower:
            return content.get('strategy', current_text)
    
    # Slide 6 (index 5): Delivery Overview / Solution
    if slide_index == 5:
        if 'heading: solution' in current_lower or 'explain the solution' in current_lower:
            solution = content.get('delivery_solution', '')
            steps = content.get('delivery_steps', '')
            tools = content.get('tools_used', '')
            
            # Split logic if the slide was duplicated
            if steps.count('•') > 4 or len(steps) > 400:
                step_lines = steps.split('\n')
                mid_point = len(step_lines) // 2
                
                if not is_continuation:
                    # First slide gets the solution text and first half of steps
                    first_half = '\n'.join(step_lines[:mid_point])
                    return f"{solution}\n\nKey Actions (Part 1):\n{first_half}"
                else:
                    # Second slide gets second half of steps and tools
                    second_half = '\n'.join(step_lines[mid_point:])
                    return f"Key Actions (Continued):\n{second_half}\n\nTools Used: {tools}"
            else:
                return f"{solution}\n\nKey Actions:\n{steps}\n\nTools Used: {tools}"
                
        # Handle individual step placeholders
        if '[step' in current_lower:
            return ''
        if 'additional steps' in current_lower:
            return ''
        if 'visuals' in current_lower and 'insert' in current_lower:
            return ''
        if 'tools used' in current_lower and 'mention' in current_lower:
            return content.get('tools_used', '') if not is_continuation else ''
    
    # Slide 7 (index 6): Campaign Creatives
    if slide_index == 6:
        media_link = content.get('media_link', '')
        if media_link:
            return f"{current_text}\n\nMedia Assets Link (Google Drive):\n{media_link}"
        return current_text
    
    # Slide 8 (index 7): Impact — METRICS ONLY (no testimonials, no learnings)
    if slide_index == 7:
        has_results = 'heading: results' in current_lower or 'key metric' in current_lower
        has_explanation = 'explanation' in current_lower or 'highlight the key results' in current_lower
        
        if has_results or has_explanation:
            metrics = content.get('impact_metrics', '')
            
            # Split logic if duplicated
            if metrics.count('•') > 4 or len(metrics) > 400:
                metric_lines = metrics.split('\n')
                mid_point = len(metric_lines) // 2
                
                if not is_continuation:
                    first_half = '\n'.join(metric_lines[:mid_point])
                    return first_half
                else:
                    second_half = '\n'.join(metric_lines[mid_point:])
                    return second_half
            else:
                return metrics
    
    # Slide 9 (index 8): Single-slide title - skip
    if slide_index == 8:
        if 'single' in current_lower:
            return f"Case Study: {content.get('brand_name', '')}"
    
    # Slide 10 (index 9): Single-slide compact layout
    if slide_index == 9:
        if 'challenge' in current_lower:
            return content.get('challenge', current_text)[:200]
        if 'solution' in current_lower:
            return content.get('delivery_solution', current_text)[:200]
        if 'outcome' in current_lower:
            return content.get('impact_metrics', current_text)[:200]
    
    return None


def build_case_study_slides(template_id: str, content: dict) -> str:
    """
    Full pipeline: duplicate template and populate with content.
    
    Args:
        template_id: Google Slides template presentation ID
        content: Generated case study content dict
    
    Returns:
        URL to the completed presentation
    """
    title = f"DigiChefs Case Study - {content.get('brand_name', 'New')} - {content.get('industry', '')}"
    
    # Step 1: Duplicate template
    new_id = duplicate_template(template_id, title)
    
    # Step 2: Populate with content
    url = populate_slides(new_id, content)
    
    return url
