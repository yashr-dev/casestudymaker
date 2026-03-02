import re
from googleapiclient.discovery import build
from slides_builder import get_google_credentials


def extract_doc_id(url: str) -> str:
    """Extract the Google Doc ID from a shared URL."""
    match = re.search(r'/document/d/([a-zA-Z0-9-_]+)', url)
    if match:
        return match.group(1)
    return ""


def read_google_doc(url: str) -> str:
    """
    Read text content from a Google Doc given its URL.
    Uses the Drive API export (which is already authorized) instead of
    requiring an additional Docs API scope.
    Returns the extracted text or an error message string.
    """
    if not url or 'docs.google.com/document' not in url:
        return ""

    doc_id = extract_doc_id(url)
    if not doc_id:
        return "Could not extract Document ID from the provided URL."

    try:
        creds = get_google_credentials()
        # Use Drive API to export the doc as plain text
        # This works with the existing 'drive' scope — no extra scope needed
        drive_service = build('drive', 'v3', credentials=creds)

        result = drive_service.files().export(
            fileId=doc_id,
            mimeType='text/plain'
        ).execute()

        # The result is bytes, decode to string
        if isinstance(result, bytes):
            return result.decode('utf-8').strip()
        return str(result).strip()
    except Exception as e:
        print(f"Error reading Google Doc: {e}")
        return f"Error reading document: {str(e)}\nMake sure the document is shared with 'Anyone with the link can view'."
