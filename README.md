# FarmWise AI

A smart assistant that helps farmers understand complex government schemes, check eligibility, and access benefits in their preferred language.

## 🌱 Project Overview

FarmWise AI is designed to bridge the gap between government agricultural schemes and farmers. It simplifies complex scheme documents, performs eligibility checks through interactive questions, and provides audio summaries in multiple Indian languages.

## 🚀 Features

- **Document Analysis**: Upload government scheme PDFs for AI analysis
- **Simplified Summaries**: Convert complex policy language into easy-to-understand explanations
- **Multilingual Support**: Access information in 10 Indian languages
- **Audio Summaries**: Listen to summaries in your preferred language
- **Eligibility Check**: Answer simple questions to determine if you qualify
- **Scheme Management**: Save and manage schemes that are relevant to you

## 🔧 Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/farmwise-ai.git
   cd farmwise-ai
   ```

2. Create a virtual environment:
   ```
   python -m venv .venv
   ```

3. Activate the virtual environment:
   - Windows:
     ```
     .venv\Scripts\activate
     ```
   - MacOS/Linux:
     ```
     source .venv/bin/activate
     ```

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Create a `.env` file in the project root with your Google API key:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```

6. Run the application:
   ```
   python -m streamlit run scheme_summarizer.py
   ```

## 📱 Usage

1. **Upload a scheme document**: Go to the 'Analyze Scheme' tab and upload a PDF file
2. **Read the summary**: The AI creates an easy-to-understand summary
3. **Listen to audio**: Play the audio summary in your language
4. **Check eligibility**: Answer questions to see if you qualify
5. **Save schemes**: Keep important schemes for future reference

## 🌐 Supported Languages

- English
- Hindi
- Tamil
- Telugu
- Bengali
- Marathi
- Gujarati
- Kannada
- Malayalam
- Punjabi

## 📋 Future Enhancements

- Database integration for saved schemes
- Mobile app for offline access
- SMS notifications for new schemes
- Integration with government APIs
- OCR for physical document scanning
- Voice input for farmers with limited literacy

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details. 