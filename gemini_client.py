import os
import google.generativeai as genai
from dotenv import load_dotenv

class GeminiClient:
    def __init__(self):
        load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
        api_key = os.getenv('GEMINI_API_KEY')
        generation_config=genai.GenerationConfig(
            temperature=0
        )

        if not api_key:
            raise Exception("GEMINI_API_KEY not found in environment variables")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    def transcribe_audio(self, file_path ,prompt):
        """Transcribe Audio using Gemini"""
        try:
            uploaded_file=genai.upload_file(path=file_path)
            response=self.model.generate_content([prompt,uploaded_file])
            return response.text
        except Exception as e:
            raise Exception(f"Error transcribing audio from gemini :{str(e)}")
        
    def generate_response(self, prompt):
        """Generate response from Gemini API."""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            raise Exception(f"Error generating response from Gemini: {str(e)}")

    def test_connection(self):
        """Test the connection to Gemini API."""
        try:
            test_prompt = "Hello, respond with 'Connection successful'"
            response = self.generate_response(test_prompt)
            return "Connection successful" in response
        except Exception:
            return False