import os
import sys
from googleapiclient.discovery import build
import json

# Adjust path to import get_google_credentials
from slides_builder import get_google_credentials

def dump_slides(presentation_id):
    creds = get_google_credentials()
    slides_service = build('slides', 'v1', credentials=creds)
    
    presentation = slides_service.presentations().get(
        presentationId=presentation_id
    ).execute()
    
    slides = presentation.get('slides', [])
    
    print(f"Presentation: {presentation_id}")
    for i, slide in enumerate(slides):
        print(f"\n--- Slide {i} ---")
        elements = slide.get('pageElements', [])
        for element in elements:
            if 'shape' in element and 'text' in element['shape']:
                text_content = element['shape']['text']
                full_text = ''
                for text_element in text_content.get('textElements', []):
                    if 'textRun' in text_element:
                        full_text += text_element['textRun'].get('content', '')
                print(f"[{element['objectId']}]\n{repr(full_text.strip())}\n")

if __name__ == '__main__':
    dump_slides('1TqBNcWKGJhkEhqsPJQQEHIsPQUEQN6Yg9K0n9u2O7oY')
