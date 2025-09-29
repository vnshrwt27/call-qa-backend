from pydantic import BaseModel, Field, validator
from typing import Optional


class QAParameter(BaseModel):
    score: int = Field(..., description="Numeric score as per scoring scale")
    reason: Optional[str] = Field(None, description="Short justification for score")


class Greeting(BaseModel):
    greet_protocol: QAParameter = Field(..., description="Max 4: Excellent-4, Good-3, Average-1, Miss-0")
    offer_help: QAParameter = Field(..., description="Max 2: Yes-2, No-0, NA-2")

    @validator('greet_protocol')
    def validate_greet_protocol_score(cls, v):
        if v.score not in [0, 1, 3, 4]:
            raise ValueError('greet_protocol score must be 0, 1, 3, or 4')
        return v

    @validator('offer_help')
    def validate_offer_help_score(cls, v):
        if v.score not in [0, 2]:
            raise ValueError('offer_help score must be 0 or 2')
        return v


class Information(BaseModel):
    confirm_info: QAParameter = Field(..., description="Max 3: Complete-3, Partial-1, Missed-0")
    confirm_location: QAParameter = Field(..., description="Max 4: Yes-4, No-0")
    confirm_modality: QAParameter = Field(..., description="Max 4: Complete-4, Partial-2, Missed-0")
    complete_details: QAParameter = Field(..., description="Max 2: Yes-2, No-0")
    info_within_1min: QAParameter = Field(..., description="Max 2: Yes-2, No-0")

    @validator('confirm_info')
    def validate_confirm_info_score(cls, v):
        if v.score not in [0, 1, 3]:
            raise ValueError('confirm_info score must be 0, 1, or 3')
        return v

    @validator('confirm_location')
    def validate_confirm_location_score(cls, v):
        if v.score not in [0, 4]:
            raise ValueError('confirm_location score must be 0 or 4')
        return v

    @validator('confirm_modality')
    def validate_confirm_modality_score(cls, v):
        if v.score not in [0, 2, 4]:
            raise ValueError('confirm_modality score must be 0, 2, or 4')
        return v

    @validator('complete_details')
    def validate_complete_details_score(cls, v):
        if v.score not in [0, 2]:
            raise ValueError('complete_details score must be 0 or 2')
        return v

    @validator('info_within_1min')
    def validate_info_within_1min_score(cls, v):
        if v.score not in [0, 2]:
            raise ValueError('info_within_1min score must be 0 or 2')
        return v


class HoldProcedure(BaseModel):
    proper_hold_script: QAParameter = Field(..., description="Max 4: Yes-4, No-0, NA-4")
    extend_hold_disconnect: QAParameter = Field(..., description="Max 4: Yes-0, No-4, NA-4")
    reconnect_after_60s: QAParameter = Field(..., description="Max 4: Yes-4, No-0, NA-4")

    @validator('proper_hold_script')
    def validate_proper_hold_script_score(cls, v):
        if v.score not in [0, 4]:
            raise ValueError('proper_hold_script score must be 0 or 4')
        return v

    @validator('extend_hold_disconnect')
    def validate_extend_hold_disconnect_score(cls, v):
        if v.score not in [0, 4]:
            raise ValueError('extend_hold_disconnect score must be 0 or 4')
        return v

    @validator('reconnect_after_60s')
    def validate_reconnect_after_60s_score(cls, v):
        if v.score not in [0, 4]:
            raise ValueError('reconnect_after_60s score must be 0 or 4')
        return v


class QualityCheck(BaseModel):
    no_interrupt: QAParameter = Field(..., description="Max 2: Yes-0, No-2")
    attentive: QAParameter = Field(..., description="Max 3: Yes-3, No-0, Average-1")
    no_jargon: QAParameter = Field(..., description="Max 2: Yes-0, No-2")
    no_repetition: QAParameter = Field(..., description="Max 2: Yes-0, Average-1, No-2")
    polite_courteous: QAParameter = Field(..., description="Max 4: Excellent-4, Good-3, Average-1")
    tone_speed: QAParameter = Field(..., description="Max 5: Excellent-5, Good-3, Average-1")

    @validator('no_interrupt')
    def validate_no_interrupt_score(cls, v):
        if v.score not in [0, 2]:
            raise ValueError('no_interrupt score must be 0 or 2')
        return v

    @validator('attentive')
    def validate_attentive_score(cls, v):
        if v.score not in [0, 1, 3]:
            raise ValueError('attentive score must be 0, 1, or 3')
        return v

    @validator('no_jargon')
    def validate_no_jargon_score(cls, v):
        if v.score not in [0, 2]:
            raise ValueError('no_jargon score must be 0 or 2')
        return v

    @validator('no_repetition')
    def validate_no_repetition_score(cls, v):
        if v.score not in [0, 1, 2]:
            raise ValueError('no_repetition score must be 0, 1, or 2')
        return v

    @validator('polite_courteous')
    def validate_polite_courteous_score(cls, v):
        if v.score not in [1, 3, 4]:
            raise ValueError('polite_courteous score must be 1, 3, or 4')
        return v

    @validator('tone_speed')
    def validate_tone_speed_score(cls, v):
        if v.score not in [1, 3, 5]:
            raise ValueError('tone_speed score must be 1, 3, or 5')
        return v


class UnsureSituation(BaseModel):
    assure_callback: QAParameter = Field(..., description="Max 5: Yes-5, No-0, Partial-3")

    @validator('assure_callback')
    def validate_assure_callback_score(cls, v):
        if v.score not in [0, 3, 5]:
            raise ValueError('assure_callback score must be 0, 3, or 5')
        return v


class ClosingScript(BaseModel):
    ask_further_help: QAParameter = Field(..., description="Max 3: Yes-3, No-0")
    follow_closing: QAParameter = Field(..., description="Max 3: Yes-3, No-0")
    accurate_info: QAParameter = Field(..., description="Max 4: Yes-4, No-0")

    @validator('ask_further_help')
    def validate_ask_further_help_score(cls, v):
        if v.score not in [0, 3]:
            raise ValueError('ask_further_help score must be 0 or 3')
        return v

    @validator('follow_closing')
    def validate_follow_closing_score(cls, v):
        if v.score not in [0, 3]:
            raise ValueError('follow_closing score must be 0 or 3')
        return v

    @validator('accurate_info')
    def validate_accurate_info_score(cls, v):
        if v.score not in [0, 4]:
            raise ValueError('accurate_info score must be 0 or 4')
        return v


class SoundQuality(BaseModel):
    clear_confident: QAParameter = Field(..., description="Max 4: Excellent-4, Good-3, Average-1")

    @validator('clear_confident')
    def validate_clear_confident_score(cls, v):
        if v.score not in [1, 3, 4]:
            raise ValueError('clear_confident score must be 1, 3, or 4')
        return v


class RecordHandling(BaseModel):
    accurate_record: QAParameter = Field(..., description="Max 10: Yes-10, No-0")
    proper_disposition: QAParameter = Field(..., description="Max 10: Yes-10, No-0")
    spell_check: QAParameter = Field(..., description="Max 10: Yes-10, No-0")

    @validator('accurate_record')
    def validate_accurate_record_score(cls, v):
        # Allow any score from 0 to 10 for accurate_record
        if not (0 <= v.score <= 10):
            raise ValueError('accurate_record score must be between 0 and 10')
        return v

    @validator('proper_disposition')
    def validate_proper_disposition_score(cls, v):
        # Allow any score from 0 to 10 for proper_disposition
        if not (0 <= v.score <= 10):
            raise ValueError('proper_disposition score must be between 0 and 10')
        return v

    @validator('spell_check')
    def validate_spell_check_score(cls, v):
        # Allow any score from 0 to 10 for spell_check
        if not (0 <= v.score <= 10):
            raise ValueError('spell_check score must be between 0 and 10')
        return v


class QAEvaluation(BaseModel):
    transcript_summary: Optional[str] = Field(None, description="Short summary of call")
    greeting: Greeting
    information: Information
    hold_procedure: HoldProcedure
    quality_check: QualityCheck
    unsure_situation: UnsureSituation
    closing_script: ClosingScript
    sound_quality: SoundQuality
    record_handling: RecordHandling
    total_score: int = Field(..., description="Sum of all parameter scores (max 100)")

    @validator('total_score')
    def validate_total_score(cls, v, values):
        if 'greeting' not in values:
            return v

        calculated_total = 0

        # Greeting (max 6)
        greeting = values.get('greeting')
        if greeting:
            calculated_total += greeting.greet_protocol.score + greeting.offer_help.score

        # Information (max 15)
        information = values.get('information')
        if information:
            calculated_total += (information.confirm_info.score +
                               information.confirm_location.score +
                               information.confirm_modality.score +
                               information.complete_details.score +
                               information.info_within_1min.score)

        # Hold Procedure (max 12)
        hold_procedure = values.get('hold_procedure')
        if hold_procedure:
            calculated_total += (hold_procedure.proper_hold_script.score +
                               hold_procedure.extend_hold_disconnect.score +
                               hold_procedure.reconnect_after_60s.score)

        # Quality Check (max 18)
        quality_check = values.get('quality_check')
        if quality_check:
            calculated_total += (quality_check.no_interrupt.score +
                               quality_check.attentive.score +
                               quality_check.no_jargon.score +
                               quality_check.no_repetition.score +
                               quality_check.polite_courteous.score +
                               quality_check.tone_speed.score)

        # Unsure Situation (max 5)
        unsure_situation = values.get('unsure_situation')
        if unsure_situation:
            calculated_total += unsure_situation.assure_callback.score

        # Closing Script (max 10)
        closing_script = values.get('closing_script')
        if closing_script:
            calculated_total += (closing_script.ask_further_help.score +
                               closing_script.follow_closing.score +
                               closing_script.accurate_info.score)

        # Sound Quality (max 4)
        sound_quality = values.get('sound_quality')
        if sound_quality:
            calculated_total += sound_quality.clear_confident.score

        # Record Handling (max 30)
        record_handling = values.get('record_handling')
        if record_handling:
            calculated_total += (record_handling.accurate_record.score +
                               record_handling.proper_disposition.score +
                               record_handling.spell_check.score)

        if v != calculated_total:
            raise ValueError(f'total_score {v} does not match calculated total {calculated_total}')

        if v > 100:
            raise ValueError('total_score cannot exceed 100')

        return v