import os
import base64

def generate():
    print('=============================================')
    print('  RENDER ENVIRONMENT VARIABLES GENERATOR')
    print('=============================================')
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    token_file = os.path.join(base_dir, 'token.json')
    creds_file = os.path.join(base_dir, 'credentials.json')
    
    if os.path.exists(creds_file):
        with open(creds_file, 'rb') as f:
            creds_b64 = base64.b64encode(f.read()).decode('utf-8')
            print("\n1. Copy this value for GOOGLE_CREDENTIALS_B64:\n")
            print(creds_b64)
    else:
        print("\n[!] credentials.json not found!")
        
    if os.path.exists(token_file):
        with open(token_file, 'rb') as f:
            token_b64 = base64.b64encode(f.read()).decode('utf-8')
            print("\n\n2. Copy this value for GOOGLE_TOKEN_B64:\n")
            print(token_b64)
    else:
        print("\n\n[!] token.json not found!")

    print('\n=============================================')
    print('Paste these into your Render Dashboard under "Environment".')

if __name__ == '__main__':
    generate()
