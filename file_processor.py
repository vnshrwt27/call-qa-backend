import os
import json
import time
from gemini_client import GeminiClient

def read_transcript_file(file_path):
    """Read and return the content of a transcript file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        raise Exception(f"File not found: {file_path}")
    except UnicodeDecodeError:
        raise Exception(f"Unable to decode file: {file_path}")
    except Exception as e:
        raise Exception(f"Error reading file: {str(e)}")

def validate_file_type(filename):
    """Validate if the uploaded file is a text or JSON file."""
    allowed_extensions = ['.wav', '.mp3', '.m4a', '.flac']
    file_extension = os.path.splitext(filename)[1].lower()
    return file_extension in allowed_extensions

def save_uploaded_file(file_content, filename, upload_dir="uploads"):
    """Save uploaded file content to disk."""
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    file_path = os.path.join(upload_dir, filename)

    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(file_content)
        return file_path
    except Exception as e:
        raise Exception(f"Error saving file: {str(e)}")

def transcribe_audio_file(file_path, max_retries=2):
    """Transcribe Audio File with basic retries for transient failures."""
    client = GeminiClient()
    prompt = """
    You are trnacribing this audio file you must be accurate and specfic
Analyze the provided audio file. Your response **must be a single, complete JSON object** and nothing else.

The JSON object must provide a comprehensive analysis with four top-level keys: `metadata`, `conversation_summary`, `participants`, and `transcript`. The goal is to create a file that is highly useful for automated systems while also being easily understood at a glance by a human.

Transcribe the calls in English,strictly follow the json schema the transcript should have agents and caller entities and then separated by \n (Look at the Format in example)
Use the following JSON structure and content as a template for your response:

{{
  "metadata": {{
    "audio_source": "{file_path}",
    "timestamp_utc": "2025-09-26T12:15:00Z",
    "detected_language": "English"
  }},
  "conversation_summary": {{
    "topic": "Inquiry about high electricity bill",
    "caller_intent": "To understand the reason for an unusually high bill and check for potential errors.",
    "outcome": "Agent identified a one-time installation fee from a recent smart meter upgrade, resolving the customer's concern. No billing error was found.",
    "sentiment": "Positive"
    }}
  }},
  "participants": [
    {{
      "speaker_id": "SPK_0",
      "role": "Caller",
      "name": "Priya Sharma"
    }},
    {{
      "speaker_id": "SPK_1",
      "role": "Agent",
      "name": "Anil Roy"
    }}
  ],
  "transcript": [
    AGENT:Hello how are you i am Anil roy speaking \n CALLER:hi i am Priya sharma  \n AGENT:..... so on 
  ]
}}
```
"""
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            transcription_text = client.transcribe_audio(file_path, prompt)
            return transcription_text
        except Exception as e:
            last_error = e
            backoff_seconds = 1 * (2 ** attempt)
            print(f"[transcribe_audio_file] attempt {attempt + 1} failed: {e}")
            if attempt < max_retries:
                time.sleep(backoff_seconds)
    raise Exception(f"Transcription failed after {max_retries + 1} attempts: {last_error}")

def extract_transcript_text(file_content, filename):
    """Extract transcript text from file content (supports .txt and .json files)."""
    file_extension = os.path.splitext(filename)[1].lower()

    try:
        if file_extension == '.json':
            # Parse JSON and extract transcript text
            json_data = json.loads(file_content)

            # Common JSON fields that might contain transcript text (prioritize English)
            possible_fields = [
                'englishTranscript', 'english_transcript', 'transcript', 'text',
                'content', 'conversation', 'dialogue', 'call_transcript', 'transcript_text'
            ]

            transcript_text = ""

            # Try to find transcript in common fields
            for field in possible_fields:
                if field in json_data:
                    if isinstance(json_data[field], str):
                        transcript_text = json_data[field]
                        break
                    elif isinstance(json_data[field], list):
                        # If it's a list, join the items
                        transcript_text = "\n".join(str(item) for item in json_data[field])
                        break

            # If no standard field found, try to extract text from the structure
            if not transcript_text:
                if isinstance(json_data, dict):
                    # Look for any field containing substantial text
                    for key, value in json_data.items():
                        if isinstance(value, str) and len(value) > 50:
                            transcript_text = value
                            break
                        elif isinstance(value, list) and len(value) > 0:
                            # Join list items
                            transcript_text = "\n".join(str(item) for item in value)
                            break

                # Last resort: convert entire JSON to string
                if not transcript_text:
                    transcript_text = json.dumps(json_data, indent=2)

            return transcript_text.strip()

        else:
            # For .txt files, return content as-is
            return file_content.strip()

    except json.JSONDecodeError:
        raise Exception("Invalid JSON file format")
    except Exception as e:
        raise Exception(f"Error extracting transcript text: {str(e)}")