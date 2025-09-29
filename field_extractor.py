import json
import re
from gemini_client import GeminiClient

class FieldExtractor:
    def __init__(self):
        self.gemini_client = GeminiClient()

    def extract_fields_from_transcript(self, transcript_text):
        """Extract names, patients, and branch information from transcript."""
        prompt = self._create_extraction_prompt(transcript_text)

        try:
            response = self.gemini_client.generate_response(prompt)
            extracted_data = self._parse_gemini_response(response)
            return extracted_data
        except Exception as e:
            raise Exception(f"Error extracting fields: {str(e)}")
    
    def _create_extraction_prompt(self, transcript_text):
        """Create the prompt for Gemini API."""
        return f"""
        Analyze this call transcript and extract the following information. ONLY extract information that is explicitly mentioned in the transcript:

        1. agent_names: Names of agents/staff (often introduced at beginning)
        2. patient_names: Patient names mentioned in the call
        3. test_centers: Medical centers, hospitals, diagnostic centers mentioned
        4. tests_mentioned: Specific tests, procedures, or reports mentioned (e.g. MRI, X-ray, blood test)
        5. doctors_mentioned: Doctor names if any are mentioned
        6. contact_info: Phone numbers, email addresses if mentioned
        7. appointment_dates: Dates or times mentioned for appointments/tests
        8. departments: Departments or branches mentioned
        9. sentiment: Sentiment observed in the call transcript(positive/neutral/negative)

        Return ONLY the JSON format below with actual extracted data. Do not make up or assume information:
        {{
            "agent_names": [],
            "patient_names": [],
            "test_centers": [],
            "tests_mentioned": [],
            "doctors_mentioned": [],
            "contact_info": [],
            "appointment_dates": [],
            "departments": [],
            "sentiment"' []
        }}

        Transcript:
        {transcript_text}
        """


    def _parse_gemini_response(self, response_text):
        """Parse the Gemini response and extract JSON."""
        try:
            # Find JSON in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1

            if start_idx == -1 or end_idx == 0:
                return self._create_empty_result("No JSON found in response")

            json_str = response_text[start_idx:end_idx]
            extracted_data = json.loads(json_str)

            # Validate structure
            required_fields = ['agent_names', 'patient_names', 'test_centers', 'tests_mentioned',
                             'doctors_mentioned', 'contact_info', 'appointment_dates', 'departments','sentiment']
            for field in required_fields:
                if field not in extracted_data:
                    extracted_data[field] = []

            return extracted_data

        except (json.JSONDecodeError, ValueError) as e:
            return self._create_empty_result(f"JSON parsing error: {str(e)}")

    def _create_empty_result(self, error_message):
        """Create an empty result structure with error information."""
        return {
            "agent_names": [],
            "patient_names": [],
            "test_centers": [],
            "tests_mentioned": [],
            "doctors_mentioned": [],
            "contact_info": [],
            "appointment_dates": [],
            "departments": [],
            "sentiment": [],
            "error": error_message
        }