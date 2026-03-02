"""
DigiChefs Case Study Maker - Flask Application
"""

import os
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for
from dotenv import load_dotenv
from ai_generator import generate_case_study_content, get_brand_research, generate_clarifying_questions
from slides_builder import build_case_study_slides, get_google_credentials
from document_reader import read_google_doc

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

TEMPLATE_ID = os.getenv('GOOGLE_SLIDES_TEMPLATE_ID', '1TqBNcWKGJhkEhqsPJQQEHIsPQUEQN6Yg9K0n9u2O7oY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')


@app.route('/')
def index():
    """Serve the main case study input form."""
    return render_template('index.html')


@app.route('/clarify', methods=['POST'])
def clarify():
    """Endpoint for generating clarifying questions from AI before final generation."""
    try:
        data = request.json
        brand_name = data.get('brand_name', '').strip()
        industry = data.get('industry', '').strip()
        services_used = data.get('services_used', '').strip()
        what_we_did = data.get('what_we_did', '').strip()
        how_we_did_it = data.get('how_we_did_it', '').strip()
        impact = data.get('impact', '').strip()
        additional_context = data.get('additional_context', '').strip()
        drive_link = data.get('drive_link', '').strip()
        
        api_key = data.get('gemini_api_key', '').strip() or GEMINI_API_KEY
        
        rough_notes_content = ""
        if drive_link:
            rough_notes_content = read_google_doc(drive_link)
        
        if not rough_notes_content and (not brand_name or not what_we_did or not impact):
            return jsonify({'success': False, 'error': 'Either a Google Drive Link OR Brand Name, What We Did, and Impact are required.'}), 400
            
        questions = generate_clarifying_questions(
            brand_name=brand_name,
            industry=industry,
            services_used=services_used,
            what_we_did=what_we_did,
            how_we_did_it=how_we_did_it,
            impact=impact,
            additional_context=additional_context,
            rough_notes_content=rough_notes_content,
            api_key=api_key
        )
        
        return jsonify({
            'success': True,
            'questions': questions
        })
        
    except Exception as e:
        print(f"Error in clarify: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/generate', methods=['POST'])
def generate():
    """Generate case study content and create Google Slides."""
    try:
        data = request.get_json()
        
        brand_name = data.get('brand_name', '').strip()
        industry = data.get('industry', '').strip()
        services_used = data.get('services_used', '').strip()
        what_we_did = data.get('what_we_did', '').strip()
        how_we_did_it = data.get('how_we_did_it', '').strip()
        impact = data.get('impact', '').strip()
        media_link = data.get('media_link', '').strip()
        additional_context = data.get('additional_context', '').strip()
        drive_link = data.get('drive_link', '').strip()
        user_clarifications = data.get('user_clarifications', '')
        website_url = data.get('website_url', '').strip()
        
        api_key = data.get('gemini_api_key', '').strip() or GEMINI_API_KEY
        
        rough_notes_content = ""
        if drive_link:
            rough_notes_content = read_google_doc(drive_link)
            
        if not rough_notes_content and not all([brand_name, what_we_did, impact]):
            return jsonify({
                'error': 'Either a shared Google Drive Link OR Brand name, what we did, and impact are required fields.'
            }), 400
        
        if not api_key:
            return jsonify({
                'error': 'Gemini API key is required. Set it in .env or provide it in the form.'
            }), 400
        
        # Step 1: Generate content with AI
        content = generate_case_study_content(
            brand_name=brand_name,
            industry=industry,
            services_used=services_used,
            what_we_did=what_we_did,
            how_we_did_it=how_we_did_it,
            impact=impact,
            additional_context=additional_context,
            rough_notes_content=rough_notes_content,
            user_clarifications=user_clarifications,
            media_link=media_link,
            website_url=website_url,
            api_key=api_key
        )
        
        # Step 2: Try to build Google Slides
        slides_url = None
        slides_error = None
        try:
            slides_url = build_case_study_slides(TEMPLATE_ID, content)
        except FileNotFoundError as e:
            slides_error = str(e)
        except Exception as e:
            slides_error = f"Google Slides error: {str(e)}"
        
        return jsonify({
            'success': True,
            'content': content,
            'slides_url': slides_url,
            'slides_error': slides_error
        })
        
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON in request body.'}), 400
    except Exception as e:
        return jsonify({'error': f'Generation failed: {str(e)}'}), 500


@app.route('/auth/google')
def google_auth():
    """Trigger Google OAuth flow for Slides API access."""
    try:
        get_google_credentials()
        return redirect(url_for('index'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/auth/status')
def auth_status():
    """Check if Google credentials are available."""
    try:
        creds = get_google_credentials()
        return jsonify({'authenticated': creds is not None and creds.valid})
    except Exception:
        return jsonify({'authenticated': False})


if __name__ == '__main__':
    app.run(debug=False, port=5050)
