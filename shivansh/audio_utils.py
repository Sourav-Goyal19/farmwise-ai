import os
import hashlib
from gtts import gTTS
from gtts.lang import tts_langs
import io
from pathlib import Path
from dotenv import load_dotenv
import re
import shutil
import streamlit as st

load_dotenv()

# Set up audio cache directory
AUDIO_CACHE_DIR = os.getenv("AUDIO_CACHE_DIR", "./audio_cache")
os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)

# Get a dictionary of supported languages by gTTS
SUPPORTED_LANGUAGES = tts_langs()

def get_supported_languages():
    """Return a dictionary of supported languages by gTTS"""
    return SUPPORTED_LANGUAGES

def is_language_supported(lang_code):
    """Check if a language is supported by gTTS"""
    return lang_code in SUPPORTED_LANGUAGES

def clear_audio_cache(force=True):
    """Clear all audio files from the cache directory
    
    Args:
        force (bool): If True, will use stronger methods to ensure files are deleted
    
    Returns:
        bool: True if cache was cleared successfully, False otherwise
    """
    try:
        cache_dir = Path(AUDIO_CACHE_DIR)
        if not cache_dir.exists():
            os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)
            return True
            
        # Clear the session states that might be holding references to these files
        for key in list(st.session_state.keys()):
            if key.startswith('audio_data_'):
                del st.session_state[key]
                
        # Delete each file
        deleted_count = 0
        for file in cache_dir.glob("*.mp3"):
            try:
                # First try normal deletion
                os.unlink(file)
                deleted_count += 1
            except Exception as e:
                if force:
                    try:
                        # If normal deletion fails and force=True, try with file handling
                        with open(file, 'w') as f:
                            # Truncate the file
                            pass
                        # Then delete the empty file
                        os.unlink(file)
                        deleted_count += 1
                    except Exception as inner_e:
                        print(f"Could not delete file even with force: {file}, error: {inner_e}")
                else:
                    print(f"Error deleting file: {file}, error: {e}")
        
        # If force=True and files still exist, recreate the directory
        if force and list(cache_dir.glob("*.mp3")):
            try:
                # Remove the entire directory and recreate it
                shutil.rmtree(AUDIO_CACHE_DIR, ignore_errors=True)
                os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)
                print(f"Recreated audio cache directory: {AUDIO_CACHE_DIR}")
                deleted_count = -1  # Special flag indicating directory was recreated
            except Exception as e:
                print(f"Error recreating cache directory: {e}")
        
        print(f"Cleared audio cache in {AUDIO_CACHE_DIR}: {deleted_count} files deleted")
        return True
    except Exception as e:
        print(f"Error clearing audio cache: {e}")
        return False

def clean_text_for_audio(text):
    """
    Clean text to make it more suitable for audio generation
    by removing non-informational characters and formatting
    
    Args:
        text (str): The text to clean
        
    Returns:
        str: Cleaned text optimized for audio generation
    """
    if not text:
        return ""
    
    # Replace multiple newlines with a single space
    text = re.sub(r'\n+', ' ', text)
    
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters that don't add value in speech
    text = re.sub(r'[*_#~`<>{}[\]\\|]', '', text)
    
    # Convert bullet points to sentence structure
    text = re.sub(r'•\s*', '. ', text)
    text = re.sub(r'-\s*', '. ', text)
    
    # Add periods after numeric lists for better speech pacing
    text = re.sub(r'(\d+)\.\s+', r'\1. ', text)
    
    # Fix consecutive periods
    text = re.sub(r'\.{2,}', '.', text)
    
    # Add a space after periods if missing
    text = re.sub(r'\.(?!\s|$)', '. ', text)
    
    return text.strip()

def get_audio_hash(text, lang_code):
    """Generate a unique hash for the text and language combination"""
    content = f"{text}_{lang_code}".encode('utf-8')
    return hashlib.md5(content).hexdigest()

def generate_audio(text, lang_code="en", use_cache=True):
    """
    Generate audio from text using gTTS
    
    Args:
        text (str): Text to convert to speech
        lang_code (str): Language code (default: "en")
        use_cache (bool): Whether to use caching (default: True)
        
    Returns:
        tuple: (audio_bytes, cache_path) - audio data as bytes and cache path if cached
    """
    if not text:
        return None, None
    
    # Check if language is supported
    if not is_language_supported(lang_code):
        print(f"Language not supported: {lang_code}")
        return None, None
    
    # Clean the text for better audio quality
    cleaned_text = clean_text_for_audio(text)
    if not cleaned_text:
        return None, None
    
    # Generate hash for caching
    text_hash = get_audio_hash(cleaned_text, lang_code)
    cache_path = os.path.join(AUDIO_CACHE_DIR, f"{text_hash}.mp3")
    
    # Check if cached version exists
    if use_cache and os.path.exists(cache_path):
        with open(cache_path, 'rb') as f:
            audio_data = f.read()
        return io.BytesIO(audio_data), cache_path
    
    # Generate new audio
    try:
        tts = gTTS(text=cleaned_text, lang=lang_code, slow=False)
        
        # Save to BytesIO for streaming
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        
        # Cache the audio if caching is enabled
        if use_cache:
            tts.save(cache_path)
        
        return audio_bytes, cache_path
    except Exception as e:
        print(f"Error generating audio: {e}")
        return None, None

def clean_cache(max_age_days=7):
    """Remove audio cache files older than the specified number of days"""
    import time
    from datetime import datetime, timedelta
    
    cache_dir = Path(AUDIO_CACHE_DIR)
    cutoff_time = time.time() - (max_age_days * 86400)
    
    for cache_file in cache_dir.glob("*.mp3"):
        file_stat = cache_file.stat()
        if file_stat.st_mtime < cutoff_time:
            try:
                os.remove(cache_file)
                print(f"Removed old cache file: {cache_file}")
            except Exception as e:
                print(f"Error removing cache file {cache_file}: {e}")
                
# Run cache cleanup on import (once per app startup)
clean_cache() 