import sys
import os

# Ensure the app directory is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from slides_builder import get_google_credentials

try:
    print("Attempting to get Google credentials...")
    creds = get_google_credentials()
    if creds:
        print(f"Success! Credentials valid: {creds.valid}, Expired: {creds.expired}")
    else:
        print("Returned None for credentials.")
except Exception as e:
    print(f"Error getting credentials: {type(e).__name__}: {str(e)}")
