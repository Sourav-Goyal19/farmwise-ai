# python -m venv .venv
# .venv/Scripts/activate
# ctrl+shift+p -> python: select interpretator -> Enter path -> .venv/Scripts/python.exe
# pip install -r requirements.txt
# pip freeze > requirements.txt
# python -m streamlit run scheme_summarizer.py

import streamlit as st
from dotenv import load_dotenv
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from PyPDF2 import PdfReader
from gtts import gTTS
import io
import tempfile
import base64
import re
import db_utils
import audio_utils

load_dotenv()

# Page configuration
st.set_page_config(page_title="FarmWise AI", page_icon="🌾", layout="wide")

# Initialize session state for user
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None
if 'scheme_title' not in st.session_state:
    st.session_state.scheme_title = None
if 'scheme_summary' not in st.session_state:
    st.session_state.scheme_summary = None
if 'scheme_eligibility' not in st.session_state:
    st.session_state.scheme_eligibility = None
if 'eligibility_result' not in st.session_state:
    st.session_state.eligibility_result = None
if 'document_text' not in st.session_state:
    st.session_state.document_text = None
if 'current_language' not in st.session_state:
    st.session_state.current_language = "en"

# API key validation
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("GOOGLE_API_KEY is not set in the .env file.")
    st.stop()

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

# Filter out unsupported languages
languages = {k: v for k, v in languages.items() if audio_utils.is_language_supported(v)}

# Create sidebar for language selection and user info
st.sidebar.title("Settings")

# Language selection with cache clearing on change
selected_language = st.sidebar.selectbox("Select Language", list(languages.keys()))
language_code = languages[selected_language]

# Check if language has changed and clear cache if needed
if st.session_state.current_language != language_code:
    # Clear all audio-related session state keys
    for key in list(st.session_state.keys()):
        if key.startswith('audio_data_') or key.startswith('download_btn_'):
            del st.session_state[key]
    
    # Force clear the audio cache
    audio_utils.clear_audio_cache(force=True)
    st.session_state.current_language = language_code

# User login/profile section in sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("User Profile")

# Simple login form
if st.session_state.user_id is None:
    with st.sidebar.form("login_form"):
        name = st.text_input("Your Name")
        phone = st.text_input("Phone Number")
        login_button = st.form_submit_button("Login / Register")
        
        if login_button and name and phone:
            # Validate phone number (basic validation)
            if re.match(r'^\d{10}$', phone):
                user_id = db_utils.get_or_create_user(name, phone, language_code)
                st.session_state.user_id = user_id
                st.session_state.user_name = name
                st.rerun()
            else:
                st.error("Please enter a valid 10-digit phone number")
else:
    st.sidebar.success(f"Logged in as: {st.session_state.user_name}")
    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.session_state.user_name = None
        st.rerun()

# Main app header
st.title("🌾 FarmWise AI")
st.markdown("### Helping farmers understand government schemes")

# Create tabs for different functionalities
tab1, tab2, tab3 = st.tabs(["Analyze Scheme", "My Schemes", "Help"])

with tab1:
    st.header("Upload Government Scheme Document")
    
    # File uploader 
    uploaded_file = st.file_uploader("Upload PDF file of the government scheme", type="pdf")
    
    if uploaded_file is not None:
        # Process the PDF
        st.success("Document uploaded successfully!")
        
        # Extract text from PDF
        try:
            pdf_reader = PdfReader(uploaded_file, strict=False)
            text = ""
            for page in pdf_reader.pages:
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text
                except Exception as e:
                    st.warning(f"Warning: Could not extract text from a page: {e}")
                    continue
            
            if not text.strip():
                st.error("Could not extract any text from the uploaded PDF. Please try another file.")
                st.stop()
        except Exception as e:
            st.error(f"Error processing PDF: {e}")
            st.info("Try converting your document to PDF using a different tool.")
            st.stop()
        
        # Store document text in session state
        st.session_state.document_text = text
        
        # Create collapsible section to show raw text if needed
        with st.expander("View Raw Document Text"):
            st.text(text)
        
        # Extract scheme title
        title_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert in government agricultural schemes. Extract the exact title of the scheme from the provided document. Return ONLY the title as a single line, without any additional text or explanation."),
            ("human", f"Extract the title from this document: {text[:5000]}")
        ])
        
        title_chain = title_prompt | llm
        title_response = title_chain.invoke({})
        scheme_title = title_response.content if hasattr(title_response, "content") else title_response
        scheme_title = scheme_title.strip()
        
        # Store scheme title in session state
        st.session_state.scheme_title = scheme_title
        
        # Analyze the scheme
        with st.spinner("Analyzing the scheme..."):
            summary_prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an expert in government agricultural schemes. Your task is to analyze the provided government scheme document and create a simple, easy-to-understand summary for farmers. Focus on the key benefits, eligibility criteria, and application process. Use simple language that a person with basic education can understand."),
                ("human", f"Please analyze this government agricultural scheme document and provide a summary in simple language: {text[:15000]}")
            ])
            
            summary_chain = summary_prompt | llm
            summary_response = summary_chain.invoke({})
            summary = summary_response.content if hasattr(summary_response, "content") else summary_response
            
            # Store summary in session state
            st.session_state.scheme_summary = summary
            
            # If not English, translate and display in selected language only
            if language_code != "en":
                with st.spinner(f"Translating to {selected_language}..."):
                    translation_prompt = ChatPromptTemplate.from_messages([
                        ("system", f"You are a translator. Translate the following text from English to {selected_language} maintaining the meaning and simplicity. Return ONLY the translated text without any additional explanations or notes."),
                        ("human", summary)
                    ])
                    translation_chain = translation_prompt | llm
                    translation_response = translation_chain.invoke({})
                    translated_summary = translation_response.content if hasattr(translation_response, "content") else translation_response
                    
                    # Display only the translated summary
                    st.subheader(f"Summary: {scheme_title}")
                    st.write(translated_summary)
                    tts_text = translated_summary
            else:
                # Display English summary
                st.subheader(f"Summary: {scheme_title}")
                st.write(summary)
                tts_text = summary
            
            # Generate audio summary
            try:
                with st.spinner(f"Generating audio in {selected_language}..."):
                    # Create audio using the utility function
                    audio_bytes, cache_path = audio_utils.generate_audio(tts_text, language_code)
                    
                    # Display audio player
                    if audio_bytes:
                        st.audio(audio_bytes, format="audio/mp3")
                        st.info("💡 Tip: Click the 3-dot menu in the audio player to download the audio file")
            except Exception as e:
                st.error(f"Error generating audio: {e}")
        
        # Eligibility checker
        st.subheader("Check Your Eligibility")
        st.write("Answer a few questions to check if you're eligible for this scheme:")
        
        # Extract eligibility criteria
        with st.spinner("Analyzing eligibility criteria..."):
            eligibility_prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an expert in government agricultural schemes. Extract the key eligibility criteria from the provided document. Then generate 5-7 simple yes/no questions that can determine if a farmer is eligible for the scheme. Return ONLY the questions, one per line, without any numbering or additional text."),
                ("human", f"Extract eligibility criteria questions from this scheme document: {text[:15000]}")
            ])
            
            eligibility_chain = eligibility_prompt | llm
            eligibility_response = eligibility_chain.invoke({})
            eligibility_questions = eligibility_response.content if hasattr(eligibility_response, "content") else eligibility_response
            
            # Store eligibility questions in session state
            st.session_state.scheme_eligibility = eligibility_questions
            
            # Keep original English questions for reference
            original_questions = [q.strip() for q in eligibility_questions.strip().split("\n") if q.strip()]
            
            # Translate eligibility questions if not in English
            if language_code != "en":
                with st.spinner(f"Translating eligibility questions to {selected_language}..."):
                    translation_prompt = ChatPromptTemplate.from_messages([
                        ("system", f"You are a translator. Translate the following questions from English to {selected_language} maintaining the meaning and simplicity. Keep the same format with one question per line."),
                        ("human", eligibility_questions)
                    ])
                    translation_chain = translation_prompt | llm
                    translation_response = translation_chain.invoke({})
                    translated_questions = translation_response.content if hasattr(translation_response, "content") else translation_response
                    
                    # Split translated questions
                    display_questions = [q.strip() for q in translated_questions.strip().split("\n") if q.strip()]
            else:
                # Use original questions for display
                display_questions = original_questions
            
            with st.form("eligibility_form"):
                responses = {}
                for i, question in enumerate(display_questions):
                    responses[f"q{i}"] = st.radio(question, ["Yes", "No"])
                
                submitted = st.form_submit_button("Check Eligibility")
                
                if submitted:
                    # Prepare responses for analysis using original English questions
                    formatted_responses = "\n".join([f"Q: {original_questions[i]}\nA: {responses[f'q{i}']}" for i in range(len(original_questions)) if i < len(display_questions)])
                    
                    eligibility_check_prompt = ChatPromptTemplate.from_messages([
                        ("system", "You are an expert in government agricultural schemes. Based on the scheme document and the farmer's responses to eligibility questions, determine if they are eligible for the scheme. Start your response with either 'ELIGIBLE: ' or 'NOT ELIGIBLE: ' followed by a clear explanation of your decision and any next steps they should take. If they are eligible, provide information on how to apply."),
                        ("human", f"Scheme document: {text[:5000]}\n\nFarmer's responses:\n{formatted_responses}\n\nIs the farmer eligible for this scheme? Explain why or why not, and provide next steps.")
                    ])
                    
                    eligibility_check_chain = eligibility_check_prompt | llm
                    eligibility_check_response = eligibility_check_chain.invoke({})
                    eligibility_result = eligibility_check_response.content if hasattr(eligibility_check_response, "content") else eligibility_check_response
                    
                    # Store eligibility result in session state
                    st.session_state.eligibility_result = eligibility_result
                    
                    # Determine if eligible from the response
                    is_eligible = eligibility_result.upper().startswith("ELIGIBLE:")
                    
                    st.subheader("Eligibility Result")
                    
                    if is_eligible:
                        st.success(eligibility_result)
                    else:
                        st.warning(eligibility_result)
                    
                    # Translate eligibility result if not in English
                    if language_code != "en":
                        with st.spinner(f"Translating eligibility result to {selected_language}..."):
                            translation_prompt = ChatPromptTemplate.from_messages([
                                ("system", f"You are a translator. Translate the following text from English to {selected_language} maintaining the meaning and simplicity. Return ONLY the translated text without any additional explanations or notes."),
                                ("human", eligibility_result)
                            ])
                            translation_chain = translation_prompt | llm
                            translation_response = translation_chain.invoke({})
                            translated_eligibility = translation_response.content if hasattr(translation_response, "content") else translation_response
                            
                            st.subheader(f"Eligibility Result in {selected_language}")
                            if is_eligible:
                                st.success(translated_eligibility)
                            else:
                                st.warning(translated_eligibility)
                    
                    # Option to save result (only if user is logged in)
                    if st.session_state.user_id:
                        if st.button("Save This Scheme to My List"):
                            # Save to database
                            scheme_id = db_utils.save_scheme(
                                title=scheme_title,
                                description=uploaded_file.name,
                                eligibility_criteria=eligibility_questions,
                                summary=summary,
                                document_text=text
                            )
                            
                            db_utils.save_user_scheme(
                                user_id=st.session_state.user_id,
                                scheme_id=scheme_id,
                                is_eligible=is_eligible,
                                eligibility_details=eligibility_result
                            )
                            
                            st.success("Scheme saved to your list!")
                    else:
                        st.info("Please log in to save this scheme to your list")

with tab2:
    st.header("My Saved Schemes")
    
    if st.session_state.user_id:
        # Get user's saved schemes
        user_schemes = db_utils.get_user_schemes(st.session_state.user_id)
        
        if user_schemes:
            for scheme in user_schemes:
                with st.expander(f"{scheme['title']} - {'Eligible' if scheme['is_eligible'] else 'Not Eligible'}"):
                    st.markdown(f"**Date Saved:** {scheme['saved_at']}")
                    
                    # If not English, translate and display only in the selected language
                    if language_code != "en":
                        # Translate summary
                        summary_text = scheme['summary']
                        with st.spinner(f"Translating to {selected_language}..."):
                            translation_prompt = ChatPromptTemplate.from_messages([
                                ("system", f"You are a translator. Translate the following text from English to {selected_language} maintaining the meaning and simplicity. Return ONLY the translated text without any additional explanations or notes."),
                                ("human", summary_text)
                            ])
                            translation_chain = translation_prompt | llm
                            translation_response = translation_chain.invoke({})
                            translated_summary = translation_response.content if hasattr(translation_response, "content") else translation_response
                            
                            st.markdown("### Summary")
                            st.write(translated_summary)
                            
                            # Translate eligibility details
                            eligibility_details = scheme['eligibility_details']
                            with st.spinner(f"Translating eligibility details..."):
                                translation_prompt = ChatPromptTemplate.from_messages([
                                    ("system", f"You are a translator. Translate the following text from English to {selected_language} maintaining the meaning and simplicity. Return ONLY the translated text without any additional explanations or notes."),
                                    ("human", eligibility_details)
                                ])
                                translation_chain = translation_prompt | llm
                                translation_response = translation_chain.invoke({})
                                translated_eligibility = translation_response.content if hasattr(translation_response, "content") else translation_response
                                
                                st.markdown("### Eligibility Details")
                                if scheme['is_eligible']:
                                    st.success(translated_eligibility)
                                else:
                                    st.warning(translated_eligibility)
                    else:
                        # Display in English
                        st.markdown("### Summary")
                        st.write(scheme['summary'])
                        
                        st.markdown("### Eligibility Details")
                        if scheme['is_eligible']:
                            st.success(scheme['eligibility_details'])
                        else:
                            st.warning(scheme['eligibility_details'])
                    
                    # Generate audio button that uses the current display language
                    if st.button(f"Generate Audio for {scheme['title']}", key=f"audio_{scheme['id']}"):
                        with st.spinner(f"Generating audio in {selected_language}..."):
                            # Get the correct text to convert to speech based on language
                            if language_code != "en":
                                # For non-English, use translated summary that was already generated above
                                # or generate it now if needed
                                if 'translated_summary' in locals():
                                    tts_text = translated_summary
                                else:
                                    # Translate if not done above
                                    summary_text = scheme['summary']
                                    translation_prompt = ChatPromptTemplate.from_messages([
                                        ("system", f"You are a translator. Translate the following text from English to {selected_language} maintaining the meaning and simplicity. Return ONLY the translated text without any additional explanations or notes."),
                                        ("human", summary_text)
                                    ])
                                    translation_chain = translation_prompt | llm
                                    translation_response = translation_chain.invoke({})
                                    tts_text = translation_response.content if hasattr(translation_response, "content") else translation_response
                            else:
                                # Use English
                                tts_text = scheme['summary']
                                
                            # Use audio utility function
                            audio_bytes, _ = audio_utils.generate_audio(tts_text, language_code)
                            if audio_bytes:
                                st.audio(audio_bytes, format="audio/mp3")
                                st.info("💡 Tip: Click the 3-dot menu in the audio player to download the audio file")
        else:
            st.info("You haven't saved any schemes yet. Go to the 'Analyze Scheme' tab to analyze and save schemes.")
    else:
        st.info("Please log in to view your saved schemes")

with tab3:
    st.header("Help & Instructions")
    st.markdown("""
    ### How to use FarmWise AI:
    
    1. **Upload a scheme document**: Go to the 'Analyze Scheme' tab and upload a PDF file of the government scheme you want to understand.
    
    2. **Read the summary**: The AI will create an easy-to-understand summary of the scheme, explaining benefits and requirements.
    
    3. **Listen to the audio**: If you prefer, you can listen to an audio summary in your chosen language.
    
    4. **Check eligibility**: Answer the questions to see if you qualify for the scheme.
    
    5. **Save schemes**: Save important schemes to your list for future reference.
    
    6. **Change language**: Use the sidebar to select your preferred language.
    
    ### Frequently Asked Questions:
    
    **Q: Is my personal information secure?**  
    A: Yes, we only collect your name and phone number to save your scheme preferences.
    
    **Q: Can I access my saved schemes from another device?**  
    A: Yes, just log in with the same phone number.
    
    **Q: How accurate are the eligibility checks?**  
    A: The eligibility check is based on the information provided in the scheme document and your answers. Always verify with official sources for final confirmation.
    
    **Q: Why do I need to log in?**  
    A: Logging in allows you to save schemes and access them later.
    
    **Q: Can I upload documents in languages other than English?**  
    A: Currently, we only support English documents for analysis, but summaries can be translated to multiple languages.
    """)
