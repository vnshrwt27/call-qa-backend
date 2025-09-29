import json
import re
import logging
from typing import Dict, Any
from gemini_client import GeminiClient
from qa_models import QAEvaluation

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QAEvaluator:
    def __init__(self):
        self.gemini_client = GeminiClient()

    def evaluate_transcript_qa(self, transcript_text: str) -> QAEvaluation:
        """Evaluate a transcript against QA parameters."""
        logger.info(f"Starting QA evaluation for transcript (length: {len(transcript_text)} chars)")

        prompt = self._create_qa_evaluation_prompt(transcript_text)
        logger.info("Generated QA evaluation prompt")

        try:
            response = self.gemini_client.generate_response(prompt)
            logger.info(f"Received response from Gemini (length: {len(response)} chars)")

            qa_data = self._parse_qa_response(response)
            logger.info(f"Parsed QA data, total_score: {qa_data.get('total_score', 'unknown')}")

            # Validate and create QAEvaluation object
            qa_evaluation = QAEvaluation(**qa_data)
            logger.info(f"Successfully created QAEvaluation with score: {qa_evaluation.total_score}")
            return qa_evaluation

        except Exception as e:
            logger.error(f"Error evaluating QA: {str(e)}")
            raise Exception(f"Error evaluating QA: {str(e)}")

    def _create_qa_evaluation_prompt(self, transcript_text: str) -> str:
        """Create comprehensive QA evaluation prompt for Gemini."""
        return f"""
You are a STRICT QA evaluator for customer support calls. Be critical and look for real issues.
Note:Deducting points without a reason is not encouraged 
### Scoring Guidelines (EXACT values only):

**GREETING (max 6 points):**
- Greeting protocol: Excellent-4 (perfect greeting + company name), Good-3 (good greeting), Average-1 (basic greeting), Miss-0 (no greeting)
- Offer help: Yes-2 (explicitly offered), No-0 (no offer), NA-2 (not needed)

**INFORMATION (max 15 points) - USE EXACT SCORES ONLY:**
- Confirming info: Complete-3, Partial-1, Missed-0 (ONLY these values)
- Confirming location: Yes-4, No-0 (ONLY 4 or 0)
- Confirming modality: Complete-4, Partial-2, Missed-0 (ONLY 4, 2, or 0)
- Complete patient details: Yes-2, No-0 (ONLY 2 or 0)
- Info within 1 min: Yes-2, No-0 (ONLY 2 or 0)

**HOLD PROCEDURE (max 12 points) - BE CRITICAL:**
- Hold script: Yes-4 (proper hold script used), No-0 (improper/no script), NA-4 (no hold needed AND none occurred)
- Extended hold disconnect: Yes-0 (disconnected during hold - BAD), No-4 (no disconnect), NA-4 (no extended hold)
- Reconnect after 60s: Yes-4 (reconnected properly), No-0 (failed to reconnect), NA-4 (no disconnection occurred)

**QUALITY CHECK (max 18 points) - LOOK FOR REAL ISSUES:**
- Interrupt caller: Yes-0 (agent interrupted - BAD), No-2 (did not interrupt)
- Attentive: Yes-3 (fully attentive), No-0 (inattentive), Average-1 (somewhat attentive)
- Jargon: Yes-0 (used confusing jargon - BAD), No-2 (clear language)
- Repetition: Yes-0 (unnecessary repetition - BAD), Average-1 (some repetition), No-2 (clear communication)
- Polite & courteous: Excellent-4 (exceptional), Good-3 (good), Average-1 (basic politeness)
- Tone & speed: Excellent-5 (perfect), Good-3 (good), Average-1 (acceptable)

**UNSURE SITUATION (max 5 points):**
- Assure callback: Yes-5 (properly assured customer,if needed callback), No-0 (no assurance given), Partial-3 (some assurance)

**CLOSING SCRIPT (max 10 points):**
- Ask further help: Yes-3 (explicitly asked), No-0 (forgot to ask)
- Closing script: Yes-3 (proper closing), No-0 (abrupt/improper ending)
- Accurate info: Yes-4 (all info accurate), No-0 (inaccurate information provided)

**SOUND QUALITY (max 4 points):**
- Clear & confident: Excellent-4 (crystal clear), Good-3 (mostly clear), Average-1 (acceptable)

**RECORD HANDLING (max 30 points) - EVALUATE BASED ON TRANSCRIPT:**
- Accurate record: 0-10 points (estimate based on how well agent captured details)
- Proper disposition: 0-10 points (estimate if call was handled according to procedure)
- Spell check: 0-10 points (based on accuracy of names/details in transcript)

---

### CRITICAL EVALUATION RULES:
1. READ THE TRANSCRIPT CAREFULLY - look for actual problems
2. Agent confusion, multiple transfers, incorrect information = DEDUCT POINTS
3. Missing standard procedures = DEDUCT POINTS
4. Communication issues, unclear responses = DEDUCT POINTS
5. Perfect scores (100) should be RARE - most calls have issues
6. Look for: interruptions, confusion, multiple agents, unclear procedures

---

### Transcript:
{transcript_text}

---

### Required JSON Output Format - INCLUDE SPECIFIC EVIDENCE:
```json
{{
  "transcript_summary": "Brief summary of the call",
  "greeting": {{
    "greet_protocol": {{"score": X, "reason": "EVIDENCE: Quote the actual greeting used, e.g. 'Agent said [exact quote]' - then explain scoring"}},
    "offer_help": {{"score": X, "reason": "EVIDENCE: Quote where help was offered or state 'No evidence of help being offered'"}}
  }},
  "information": {{
    "confirm_info": {{"score": X, "reason": "EVIDENCE: Quote specific confirmation attempts or lack thereof"}},
    "confirm_location": {{"score": X, "reason": "EVIDENCE: Quote location confirmation or state none occurred"}},
    "confirm_modality": {{"score": X, "reason": "EVIDENCE: Quote service/test confirmation or state missing"}},
    "complete_details": {{"score": X, "reason": "EVIDENCE: List what details were/weren't collected"}},
    "info_within_1min": {{"score": X, "reason": "EVIDENCE: Describe actual timing of information gathering"}}
  }},
  "hold_procedure": {{
    "proper_hold_script": {{"score": X, "reason": "EVIDENCE: Quote hold script used or state 'No hold script observed'"}},
    "extend_hold_disconnect": {{"score": X, "reason": "EVIDENCE: State if disconnection occurred during hold"}},
    "reconnect_after_60s": {{"score": X, "reason": "EVIDENCE: State if reconnection was needed and occurred"}}
  }},
  "quality_check": {{
    "no_interrupt": {{"score": X, "reason": "EVIDENCE: Quote interruptions or state 'No interruptions observed'"}},
    "attentive": {{"score": X, "reason": "EVIDENCE: Provide examples of attention or inattention"}},
    "no_jargon": {{"score": X, "reason": "EVIDENCE: Quote any jargon used or state 'Clear language used'"}},
    "no_repetition": {{"score": X, "reason": "EVIDENCE: Quote repetitive phrases or state 'No unnecessary repetition'"}},
    "polite_courteous": {{"score": X, "reason": "EVIDENCE: Quote polite/impolite language used"}},
    "tone_speed": {{"score": X, "reason": "EVIDENCE: Describe observed communication pace and tone"}}
  }},
  "unsure_situation": {{
    "assure_callback": {{"score": X, "reason": "EVIDENCE: Quote assurance given or state 'No assurance provided'"}}
  }},
  "closing_script": {{
    "ask_further_help": {{"score": X, "reason": "EVIDENCE: Quote request for further help or state it was missing"}},
    "follow_closing": {{"score": X, "reason": "EVIDENCE: Quote closing used or describe how call ended"}},
    "accurate_info": {{"score": X, "reason": "EVIDENCE: List accurate/inaccurate information provided"}}
  }},
  "sound_quality": {{
    "clear_confident": {{"score": X, "reason": "EVIDENCE: Describe clarity issues or confirm clear communication"}}
  }},
  "record_handling": {{
    "accurate_record": {{"score": X, "reason": "EVIDENCE: List what details were accurately/inaccurately captured"}},
    "proper_disposition": {{"score": X, "reason": "EVIDENCE: Describe how call was handled according to procedure"}},
    "spell_check": {{"score": X, "reason": "EVIDENCE: List any spelling errors in names or confirm accuracy"}}
  }},
  "total_score": X
}}
```

CRITICAL:
- BE STRICT AND REALISTIC
- Look for actual problems in the transcript
- Most real calls score 60-80, not 95-100
- USE ONLY THE EXACT SCORE VALUES SPECIFIED ABOVE
- If unsure between two scores, pick the LOWER one
- Return ONLY the JSON, no other text
"""

    def _parse_qa_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini response and extract QA evaluation JSON."""
        try:
            # Find JSON in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1

            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")

            json_str = response_text[start_idx:end_idx]
            qa_data = json.loads(json_str)

            # Validate structure
            required_sections = [
                'greeting', 'information', 'hold_procedure', 'quality_check',
                'unsure_situation', 'closing_script', 'sound_quality', 'record_handling'
            ]

            for section in required_sections:
                if section not in qa_data:
                    raise ValueError(f"Missing required section: {section}")

            # Always calculate total_score to ensure accuracy
            qa_data['total_score'] = self._calculate_total_score(qa_data)

            return qa_data

        except (json.JSONDecodeError, ValueError) as e:
            raise Exception(f"Failed to parse QA response: {str(e)}")

    def _calculate_total_score(self, qa_data: Dict[str, Any]) -> int:
        """Calculate total score from all parameters."""
        total = 0

        # Greeting
        greeting = qa_data.get('greeting', {})
        total += greeting.get('greet_protocol', {}).get('score', 0)
        total += greeting.get('offer_help', {}).get('score', 0)

        # Information
        information = qa_data.get('information', {})
        total += information.get('confirm_info', {}).get('score', 0)
        total += information.get('confirm_location', {}).get('score', 0)
        total += information.get('confirm_modality', {}).get('score', 0)
        total += information.get('complete_details', {}).get('score', 0)
        total += information.get('info_within_1min', {}).get('score', 0)

        # Hold Procedure
        hold_procedure = qa_data.get('hold_procedure', {})
        total += hold_procedure.get('proper_hold_script', {}).get('score', 0)
        total += hold_procedure.get('extend_hold_disconnect', {}).get('score', 0)
        total += hold_procedure.get('reconnect_after_60s', {}).get('score', 0)

        # Quality Check
        quality_check = qa_data.get('quality_check', {})
        total += quality_check.get('no_interrupt', {}).get('score', 0)
        total += quality_check.get('attentive', {}).get('score', 0)
        total += quality_check.get('no_jargon', {}).get('score', 0)
        total += quality_check.get('no_repetition', {}).get('score', 0)
        total += quality_check.get('polite_courteous', {}).get('score', 0)
        total += quality_check.get('tone_speed', {}).get('score', 0)

        # Unsure Situation
        unsure_situation = qa_data.get('unsure_situation', {})
        total += unsure_situation.get('assure_callback', {}).get('score', 0)

        # Closing Script
        closing_script = qa_data.get('closing_script', {})
        total += closing_script.get('ask_further_help', {}).get('score', 0)
        total += closing_script.get('follow_closing', {}).get('score', 0)
        total += closing_script.get('accurate_info', {}).get('score', 0)

        # Sound Quality
        sound_quality = qa_data.get('sound_quality', {})
        total += sound_quality.get('clear_confident', {}).get('score', 0)

        # Record Handling
        record_handling = qa_data.get('record_handling', {})
        total += record_handling.get('accurate_record', {}).get('score', 0)
        total += record_handling.get('proper_disposition', {}).get('score', 0)
        total += record_handling.get('spell_check', {}).get('score', 0)

        return total

    def create_fallback_evaluation(self, error_message: str) -> Dict[str, Any]:
        """Create a fallback evaluation when AI parsing fails."""
        return {
            "transcript_summary": f"Evaluation failed: {error_message}",
            "greeting": {
                "greet_protocol": {"score": 0, "reason": "Unable to evaluate"},
                "offer_help": {"score": 0, "reason": "Unable to evaluate"}
            },
            "information": {
                "confirm_info": {"score": 0, "reason": "Unable to evaluate"},
                "confirm_location": {"score": 0, "reason": "Unable to evaluate"},
                "confirm_modality": {"score": 0, "reason": "Unable to evaluate"},
                "complete_details": {"score": 0, "reason": "Unable to evaluate"},
                "info_within_1min": {"score": 0, "reason": "Unable to evaluate"}
            },
            "hold_procedure": {
                "proper_hold_script": {"score": 4, "reason": "NA - default"},
                "extend_hold_disconnect": {"score": 4, "reason": "NA - default"},
                "reconnect_after_60s": {"score": 4, "reason": "NA - default"}
            },
            "quality_check": {
                "no_interrupt": {"score": 0, "reason": "Unable to evaluate"},
                "attentive": {"score": 0, "reason": "Unable to evaluate"},
                "no_jargon": {"score": 0, "reason": "Unable to evaluate"},
                "no_repetition": {"score": 0, "reason": "Unable to evaluate"},
                "polite_courteous": {"score": 1, "reason": "Unable to evaluate"},
                "tone_speed": {"score": 1, "reason": "Unable to evaluate"}
            },
            "unsure_situation": {
                "assure_callback": {"score": 0, "reason": "Unable to evaluate"}
            },
            "closing_script": {
                "ask_further_help": {"score": 0, "reason": "Unable to evaluate"},
                "follow_closing": {"score": 0, "reason": "Unable to evaluate"},
                "accurate_info": {"score": 0, "reason": "Unable to evaluate"}
            },
            "sound_quality": {
                "clear_confident": {"score": 1, "reason": "Unable to evaluate"}
            },
            "record_handling": {
                "accurate_record": {"score": 0, "reason": "Unable to evaluate"},
                "proper_disposition": {"score": 0, "reason": "Unable to evaluate"},
                "spell_check": {"score": 0, "reason": "Unable to evaluate"}
            },
            "total_score": 14,
            "error": error_message
        }