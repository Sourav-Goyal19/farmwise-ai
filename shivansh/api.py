from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from PyPDF2 import PdfReader
import io
import base64
import re
import db_utils
import audio_utils
import sqlite3
import time

# Load environment variables
load_dotenv()

# Initialize Flask app
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
app.secret_key = os.urandom(24)  # For session management

# API key validation
api_key = os.getenv("GOOGLE_API_KEY")
# if not api_key:
#     raise ValueError("GOOGLE_API_KEY is not set in the .env file.")

# Initialize LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    api_key=api_key
)

# Get supported languages
supported_langs = audio_utils.get_supported_languages()

# Filter the language dictionary to only include supported languages
languages = {
    "English": "en",
    "Hindi": "hi",
    "Tamil": "ta",
    "Telugu": "te",
    "Bengali": "bn",
    "Marathi": "mr",
    "Gujarati": "gu",
    "Kannada": "kn",
    "Malayalam": "ml"
}

languages = {k: v for k, v in languages.items() if audio_utils.is_language_supported(v)}


@app.route('/set_language', methods=['POST'])
def set_language():
    data = request.get_json()
    language = data.get('language', 'en') if data else 'en'
    if language not in languages.values():
        return jsonify({'error': f'Unsupported language code: {language}'}), 400
    session['language'] = language
    return jsonify({'success': True, 'language': language}), 200


@app.route('/upload_scheme', methods=['POST'])
def upload_scheme():
    if 'scheme_file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['scheme_file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Get language from form data
    language_code = request.form.get('language', 'en')
    if language_code not in languages.values():
        return jsonify({'error': f'Unsupported language code: {language_code}'}), 400
    
    if file and file.filename.endswith('.pdf'):
        try:
            pdf_reader = PdfReader(file, strict=False)
            text = ""
            for page in pdf_reader.pages:
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text
                except Exception as e:
                    return jsonify({'error': f'Warning: Could not extract text from a page: {e}'}), 400
            
            if not text.strip():
                return jsonify({'error': 'Could not extract any text from the uploaded PDF'}), 400
            
            # Extract scheme title
            title_prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an expert in government agricultural schemes. Extract the exact title of the scheme from the provided document. Return ONLY the title as a single line, without any additional text or explanation."),
                ("human", f"Extract the title from this document: {text[:5000]}")
            ])
            
            title_chain = title_prompt | llm
            title_response = title_chain.invoke({})
            scheme_title = title_response.content if hasattr(title_response, "content") else title_response
            scheme_title = scheme_title.strip()
            
            # Analyze the scheme
            summary_prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an expert in government agricultural schemes. Your task is to analyze the provided government scheme document and create a simple, easy-to-understand summary for farmers. Focus on the key benefits, eligibility criteria, and application process. Use simple language that a person with basic education can understand."),
                ("human", f"Please analyze this government agricultural scheme document and provide a summary in simple language: {text[:15000]}")
            ])
            
            summary_chain = summary_prompt | llm
            summary_response = summary_chain.invoke({})
            summary = summary_response.content if hasattr(summary_response, "content") else summary_response
            
            # Generate eligibility questions
            eligibility_prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an expert in government agricultural schemes. Extract the key eligibility criteria from the provided document. Then generate 5-7 simple yes/no questions that can determine if a farmer is eligible for the scheme. Return ONLY the questions, one per line, without any numbering or additional text."),
                ("human", f"Extract eligibility criteria questions from this scheme document: {text[:15000]}")
            ])
            
            eligibility_chain = eligibility_prompt | llm
            eligibility_response = eligibility_chain.invoke({})
            eligibility_questions = eligibility_response.content if hasattr(eligibility_response, "content") else eligibility_response
            
            # Get selected language name
            selected_language = [k for k, v in languages.items() if v == language_code][0]
            
            # Translate summary if not English
            display_summary = summary
            if language_code != "en":
                translation_prompt = ChatPromptTemplate.from_messages([
                    ("system", f"You are a translator. Translate the following text from English to {selected_language} maintaining the meaning and simplicity. Return ONLY the translated text without any additional explanations or notes."),
                    ("human", summary)
                ])
                translation_chain = translation_prompt | llm
                translation_response = translation_chain.invoke({})
                display_summary = translation_response.content if hasattr(translation_response, "content") else translation_response
            
            # Translate eligibility questions if not English
            display_eligibility_questions = eligibility_questions
            if language_code != "en":
                translation_prompt = ChatPromptTemplate.from_messages([
                    ("system", f"You are a translator. Translate the following questions from English to {selected_language} maintaining the meaning and simplicity. Keep the format with one question per line, no numbering or extra text."),
                    ("human", eligibility_questions)
                ])
                translation_chain = translation_prompt | llm
                translation_response = translation_chain.invoke({})
                display_eligibility_questions = translation_response.content if hasattr(translation_response, "content") else translation_response
            
            # Generate audio for the summary
            try:
                tts_text = display_summary  # Use translated summary for non-English
                audio_bytes, _ = audio_utils.generate_audio(tts_text, language_code)
                if not audio_bytes:
                    return jsonify({'error': 'Failed to generate audio'}), 500
                
                # Convert audio to base64 for response
                audio_bytes.seek(0)
                audio_base64 = base64.b64encode(audio_bytes.read()).decode('utf-8')
                
                # Optionally save audio to temp file for future use
                timestamp = int(time.time())
                filename = f"scheme_{scheme_title.lower().replace(' ', '_')}_{timestamp}.mp3"
                temp_dir = os.path.join(os.getcwd(), 'static', 'temp_audio')
                os.makedirs(temp_dir, exist_ok=True)
                temp_file = os.path.join(temp_dir, filename)
                audio_bytes.seek(0)
                with open(temp_file, 'wb') as f:
                    f.write(audio_bytes.read())
                audio_url = url_for('static', filename=f'temp_audio/{filename}', _external=True)
            except Exception as e:
                return jsonify({'error': f'Error generating audio: {e}'}), 500
            
            # Store in session
            session['document_text'] = text
            session['scheme_title'] = scheme_title
            session['scheme_summary'] = summary  # Original English
            session['scheme_summary_translated'] = display_summary  # Translated
            session['scheme_eligibility'] = eligibility_questions  # Original English
            session['scheme_eligibility_translated'] = display_eligibility_questions  # Translated
            session['original_questions'] = [q.strip() for q in eligibility_questions.strip().split("\n") if q.strip()]
            session['translated_questions'] = [q.strip() for q in display_eligibility_questions.strip().split("\n") if q.strip()]
            session['language'] = language_code  # For other endpoints
            
            return jsonify({
                'success': True,
                'summary': display_summary,
                'raw': text,
                'summary_title': scheme_title,
                'eligibility_questions': display_eligibility_questions,  # Translated
                'language': selected_language,
                'language_code': language_code,
                'audio_base64': audio_base64,
                'audio_url': audio_url
            })
        
        except Exception as e:
            return jsonify({'error': f'Error processing PDF: {e}'}), 500
    
    return jsonify({'error': 'Invalid file type, please upload a PDF'}), 400
@app.route('/view_scheme/<scheme_id>')
def view_scheme(scheme_id):
    scheme = db_utils.get_scheme_by_id(scheme_id)
    
    if not scheme:
        return jsonify({'error': 'Scheme not found'}), 404
    
    language_code = session.get('language', 'en')
    selected_language = [k for k, v in languages.items() if v == language_code][0]
    
    # If not English, translate the summary
    if language_code != "en":
        translation_prompt = ChatPromptTemplate.from_messages([
            ("system", f"You are a translator. Translate the following text from English to {selected_language} maintaining the meaning and simplicity. Return ONLY the translated text without any additional explanations or notes."),
            ("human", scheme['summary'])
        ])
        translation_chain = translation_prompt | llm
        translation_response = translation_chain.invoke({})
        translated_summary = translation_response.content if hasattr(translation_response, "content") else translation_response
        display_summary = translated_summary
    else:
        display_summary = scheme['summary']
    
    # Translate eligibility questions if not in English
    if language_code != "en":
        translation_prompt = ChatPromptTemplate.from_messages([
            ("system", f"You are a translator. Translate the following questions from English to {selected_language} maintaining the meaning and simplicity. Keep the same format with one question per line."),
            ("human", scheme['eligibility_criteria'])
        ])
        translation_chain = translation_prompt | llm
        translation_response = translation_chain.invoke({})
        translated_questions = translation_response.content if hasattr(translation_response, "content") else translation_response
        
        # Split translated questions
        display_questions = [q.strip() for q in translated_questions.strip().split("\n") if q.strip()]
    else:
        # Use original questions for display
        display_questions = [q.strip() for q in scheme['eligibility_criteria'].strip().split("\n") if q.strip()]
    
    return jsonify({
        'title': scheme['title'],
        'summary': display_summary,
        'questions': display_questions,
        'language': selected_language,
        'language_code': language_code,
        'scheme_id': scheme_id
    })


@app.route('/generate_audio', methods=['POST'])
def generate_audio():
    # Get JSON data from the request
    data = request.get_json()
    if not data or 'summary' not in data:
        return jsonify({'error': 'No summary provided in the request'}), 400
    
    summary = data['summary']
    language_code = data.get('language', 'en')  # Default to English if not provided
    
    # Validate language code
    if language_code not in languages.values():
        return jsonify({'error': f'Unsupported language code: {language_code}'}), 400
    
    try:
        # If not English, translate
        if language_code != "en":
            selected_language = [k for k, v in languages.items() if v == language_code][0]
            translation_prompt = ChatPromptTemplate.from_messages([
                ("system", f"You are a translator. Translate the following text from English to {selected_language} maintaining the meaning and simplicity. Return ONLY the translated text without any additional explanations or notes."),
                ("human", summary)
            ])
            translation_chain = translation_prompt | llm
            translation_response = translation_chain.invoke({})
            tts_text = translation_response.content if hasattr(translation_response, "content") else translation_response
        else:
            tts_text = summary
        
        # Generate audio
        audio_bytes, _ = audio_utils.generate_audio(tts_text, language_code)
        if audio_bytes:
            audio_bytes.seek(0)
            return send_file(
                audio_bytes,
                mimetype='audio/mp3',
                as_attachment=True,
                download_name=f"scheme_summary_{language_code}.mp3"
            )
        else:
            return jsonify({'error': 'Failed to generate audio'}), 500
    except Exception as e:
        return jsonify({'error': f'Error generating audio: {e}'}), 500


@app.route('/check_eligibility', methods=['POST'])
def check_eligibility():
    # Get JSON data from the request
    data = request.get_json()
    if not data or 'questions' not in data or 'responses' not in data:
        return jsonify({'error': 'Questions and responses must be provided'}), 400

    questions = data['questions']
    responses = data['responses']
    language_code = data.get('language', 'en')

    # Validate inputs
    if not isinstance(questions, list) or not isinstance(responses, list):
        return jsonify({'error': 'Questions and responses must be arrays'}), 400
    if len(questions) != len(responses):
        return jsonify({'error': 'Number of questions and responses must match'}), 400
    if not all(r in ['Yes', 'No'] for r in responses):
        return jsonify({'error': 'Responses must be "Yes" or "No"'}), 400
    if language_code not in languages.values():
        return jsonify({'error': f'Unsupported language code: {language_code}'}), 400

    try:
        # Prepare responses for analysis
        formatted_responses = "\n".join(
            [f"Q: {questions[i]}\nA: {responses[i]}" for i in range(len(questions))]
        )

        # Check eligibility (no document_text, using questions as context)
        eligibility_check_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert in government agricultural schemes. Based on the eligibility questions and the farmer's responses, determine if they are eligible for the scheme. IMPORTANT: Start your response with exactly 'ELIGIBLE: ' (if they qualify) or 'NOT ELIGIBLE: ' (if they don't qualify) followed by a clear explanation of your decision and any next steps they should take. If they are eligible, provide information on how to apply."),
            ("human", f"Eligibility questions and responses:\n{formatted_responses}\n\nBased on these responses, is the farmer eligible for the scheme? Start with ELIGIBLE: or NOT ELIGIBLE: followed by your explanation.")
        ])

        eligibility_check_chain = eligibility_check_prompt | llm
        eligibility_check_response = eligibility_check_chain.invoke({})
        eligibility_result = eligibility_check_response.content if hasattr(eligibility_check_response, "content") else eligibility_check_response

        # Determine if eligible
        is_eligible = eligibility_result.upper().startswith("ELIGIBLE:") and not eligibility_result.upper().startswith("NOT ELIGIBLE:")

        # Translate eligibility result if not in English
        display_result = eligibility_result
        if language_code != "en":
            selected_language = [k for k, v in languages.items() if v == language_code][0]
            translation_prompt = ChatPromptTemplate.from_messages([
                ("system", f"You are a translator. Translate the following text from English to {selected_language} maintaining the meaning and simplicity. Return ONLY the translated text without any additional explanations or notes."),
                ("human", eligibility_result)
            ])
            translation_chain = translation_prompt | llm
            translation_response = translation_chain.invoke({})
            display_result = translation_response.content if hasattr(translation_response, "content") else translation_response

        return jsonify({
            'success': True,
            'is_eligible': is_eligible,
            'result': display_result
        })
    except Exception as e:
        return jsonify({'error': f'Error checking eligibility: {str(e)}'}), 500


@app.route('/save_scheme', methods=['POST'])
def save_scheme():
    if 'user_id' not in session:
        return jsonify({'error': 'Please log in to save this scheme'}), 401
    
    if ('scheme_title' not in session or 'scheme_summary' not in session or 
        'scheme_eligibility' not in session):
        return jsonify({'error': 'No scheme data available to save'}), 400
    
    scheme_title = session['scheme_title']
    scheme_summary = session['scheme_summary']  # Original English
    eligibility_questions = session['scheme_eligibility']
    document_text = session.get('document_text', '')
    
    try:
        # Save to database
        scheme_id = db_utils.save_scheme(
            title=scheme_title,
            description="Uploaded scheme",
            eligibility_criteria=eligibility_questions,
            summary=scheme_summary,
            document_text=document_text
        )
        
        # Save user scheme without eligibility result if not checked
        db_utils.save_user_scheme(
            user_id=session['user_id'],
            scheme_id=scheme_id,
            is_eligible=None,
            eligibility_details=None
        )
        
        return jsonify({'success': True, 'message': 'Scheme saved to your list!'})
    
    except Exception as e:
        return jsonify({'error': f'Error saving scheme: {e}'}), 500


@app.route('/translate_scheme_summary')
def translate_scheme_summary():
    if 'user_id' not in session:
        return jsonify({'error': 'Please log in to view translations'}), 401
    
    scheme_id = request.args.get('scheme_id')
    if not scheme_id:
        return jsonify({'error': 'No scheme ID provided'}), 400
    
    language_code = session.get('language', 'en')
    if language_code == 'en':
        return jsonify({'error': 'Translation not needed for English'}), 400
    
    # Get the scheme from the database
    try:
        conn = sqlite3.connect(db_utils.DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT summary FROM schemes WHERE id = ?", (scheme_id,))
        scheme = cursor.fetchone()
        conn.close()
        
        if not scheme:
            return jsonify({'error': 'Scheme not found'}), 404
        
        summary = scheme['summary']
        selected_language = [k for k, v in languages.items() if v == language_code][0]
        
        # Translate the summary
        translation_prompt = ChatPromptTemplate.from_messages([
            ("system", f"You are a translator. Translate the following text from English to {selected_language} maintaining the meaning and simplicity. Return ONLY the translated text without any additional explanations or notes."),
            ("human", summary)
        ])
        translation_chain = translation_prompt | llm
        translation_response = translation_chain.invoke({})
        translated_text = translation_response.content if hasattr(translation_response, "content") else translation_response
        
        return jsonify({'translated_text': translated_text})
    except Exception as e:
        return jsonify({'error': f'Error translating text: {e}'}), 500


@app.route('/translate_eligibility_details')
def translate_eligibility_details():
    if 'user_id' not in session:
        return jsonify({'error': 'Please log in to view translations'}), 401
    
    scheme_id = request.args.get('scheme_id')
    if not scheme_id:
        return jsonify({'error': 'No scheme ID provided'}), 400
    
    language_code = session.get('language', 'en')
    if language_code == 'en':
        return jsonify({'error': 'Translation not needed for English'}), 400
    
    # Get the eligibility details from the database
    try:
        conn = sqlite3.connect(db_utils.DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT eligibility_details FROM user_schemes WHERE user_id = ? AND scheme_id = ?", 
            (session['user_id'], scheme_id)
        )
        user_scheme = cursor.fetchone()
        conn.close()
        
        if not user_scheme:
            return jsonify({'error': 'Scheme not found'}), 404
        
        eligibility_details = user_scheme['eligibility_details']
        selected_language = [k for k, v in languages.items() if v == language_code][0]
        
        # Translate the eligibility details
        translation_prompt = ChatPromptTemplate.from_messages([
            ("system", f"You are a translator. Translate the following text from English to {selected_language} maintaining the meaning and simplicity. Return ONLY the translated text without any additional explanations or notes."),
            ("human", eligibility_details)
        ])
        translation_chain = translation_prompt | llm
        translation_response = translation_chain.invoke({})
        translated_text = translation_response.content if hasattr(translation_response, "content") else translation_response
        
        return jsonify({'translated_text': translated_text})
    except Exception as e:
        return jsonify({'error': f'Error translating text: {e}'}), 500


@app.route('/generate_scheme_audio')
def generate_scheme_audio():
    if 'user_id' not in session:
        return jsonify({'error': 'Please log in to generate audio'}), 401
    
    scheme_id = request.args.get('scheme_id')
    if not scheme_id:
        return jsonify({'error': 'No scheme ID provided'}), 400
    
    # Get the scheme from the database
    try:
        conn = sqlite3.connect(db_utils.DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT summary FROM schemes WHERE id = ?", (scheme_id,))
        scheme = cursor.fetchone()
        conn.close()
        
        if not scheme:
            return jsonify({'error': 'Scheme not found'}), 404
        
        summary = scheme['summary']
        language_code = session.get('language', 'en')
        
        # If not English, translate
        if language_code != "en":
            selected_language = [k for k, v in languages.items() if v == language_code][0]
            translation_prompt = ChatPromptTemplate.from_messages([
                ("system", f"You are a translator. Translate the following text from English to {selected_language} maintaining the meaning and simplicity. Return ONLY the translated text without any additional explanations or notes."),
                ("human", summary)
            ])
            translation_chain = translation_prompt | llm
            translation_response = translation_chain.invoke({})
            tts_text = translation_response.content if hasattr(translation_response, "content") else translation_response
        else:
            tts_text = summary
        
        # Create a temporary audio file
        audio_bytes, _ = audio_utils.generate_audio(tts_text, language_code)
        if audio_bytes:
            timestamp = int(time.time())
            filename = f"scheme_{scheme_id}_{timestamp}.mp3"
            
            # Create temporary file
            temp_dir = os.path.join(os.getcwd(), 'static', 'temp_audio')
            os.makedirs(temp_dir, exist_ok=True)
            temp_file = os.path.join(temp_dir, filename)
            
            audio_bytes.seek(0)
            with open(temp_file, 'wb') as f:
                f.write(audio_bytes.read())
            
            # Return URL to the audio file
            audio_url = url_for('static', filename=f'temp_audio/{filename}')
            return jsonify({'audio_url': audio_url})
        else:
            return jsonify({'error': 'Failed to generate audio'}), 500
    except Exception as e:
        return jsonify({'error': f'Error generating audio: {e}'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)