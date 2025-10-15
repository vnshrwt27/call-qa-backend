import os
import time
import base64
import mimetypes
import google.generativeai as genai
from dotenv import load_dotenv

class GeminiClient:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv('GEMINI_API_KEY')
        generation_config = genai.GenerationConfig(
            temperature=0,
            response_mime_type="application/json"
        )

        if not api_key:
            raise Exception("GEMINI_API_KEY not found in environment variables")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name='gemini-2.0-flash-001',
            generation_config=generation_config
        )

    def transcribe_audio(self, file_path ,prompt):
        """Transcribe Audio using Gemini (inline data to avoid RAG file paths)."""
        try:
            # Determine mime type
            mime_type, _ = mimetypes.guess_type(file_path)
            mime_type = mime_type or 'audio/mpeg'

            # Read and base64-encode the audio
            with open(file_path, 'rb') as f:
                data_b64 = base64.b64encode(f.read()).decode('utf-8')

            # Send prompt + audio via inline_data to fully bypass RAG storage
            contents = [{
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": mime_type, "data": data_b64}}
                ]
            }]

            response = self.model.generate_content(contents=contents)
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