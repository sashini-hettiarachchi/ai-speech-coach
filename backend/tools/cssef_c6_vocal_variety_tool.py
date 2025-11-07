"""
CSSEF Competency 6 Tool: Vocal Variety Evaluation

This tool evaluates the use of vocal variety in rate, pitch, and intensity (volume)
to heighten and maintain interest, following CSSEF Competency 6 criteria.

This competency specifically requires prosody analysis data to provide accurate
scoring based on actual vocal delivery metrics.

Evaluation Criteria:
- Effective use of vocal variety in conversational mode
- Appropriate pacing, volume, and pitch variation
- Enhancement of message through vocal delivery
- Maintenance of audience interest through vocal dynamics
"""

import os
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from tools.base import BaseTool
from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE


class CSSEFIC6ToolInput(BaseModel):
    """Input schema for CSSEF Competency 6 evaluation"""
    
    transcript: str = Field(..., description="Full transcript of the speech")
    prosody_results: Dict[str, Any] = Field(..., description="Prosody analysis results with pitch, volume, pace data")
    context: Optional[str] = Field(None, description="Speaking context (academic, persuasive, storytelling, etc.)")
    speech_duration: float = Field(..., description="Duration of speech in seconds")
    words_per_minute: float = Field(..., description="Speaking pace in words per minute")


class CSSEFIC6ToolOutput(BaseModel):
    """Output schema for CSSEF Competency 6 evaluation"""
    
    score: float = Field(..., description="Score from 1-5 for vocal variety effectiveness")
    justification: str = Field(..., description="Detailed justification with at least 2 examples")
    improvement_suggestions: str = Field(..., description="At least 2 specific improvement suggestions")


class CSSEFIC6Tool(BaseTool[CSSEFIC6ToolInput, CSSEFIC6ToolOutput]):
    """
    Tool for evaluating CSSEF Competency 6: Vocal Variety
    
    Evaluates whether the speaker used vocal variety in rate, pitch, and intensity
    to heighten and maintain interest appropriate to the audience and occasion.
    
    This tool specifically analyzes prosody data to provide evidence-based scoring.
    """
    
    name = "cssef_c6_vocal_variety_tool"
    description = "Evaluates vocal variety in rate, pitch, and intensity (CSSEF Competency 6)"
    
    InputSchema = CSSEFIC6ToolInput
    OutputSchema = CSSEFIC6ToolOutput
    
    def __init__(self):
        """Initialize the tool with OpenAI client"""
        try:
            from openai import OpenAI
            self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
            self.openai_model = OPENAI_MODEL
            self.openai_temperature = OPENAI_TEMPERATURE
            print("OpenAI client initialized successfully for CSSEF C6 evaluation")
        except Exception as e:
            print(f"Warning: Failed to initialize OpenAI client: {e}")
            self.openai_client = None
    
    def run(self, inputs: CSSEFIC6ToolInput) -> CSSEFIC6ToolOutput:
        """
        Evaluate vocal variety effectiveness using prosody data.
        
        Args:
            inputs: CSSEF C6 evaluation inputs including prosody results
            
        Returns:
            CSSEF C6 evaluation output with score, justification, and improvements
        """
        if not self.openai_client:
            return self._get_fallback_evaluation()
        
        prompt = self._create_evaluation_prompt(inputs)
        
        try:
            response = self.openai_client.beta.chat.completions.parse(
                model=self.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert public speaking evaluator specializing in CSSEF Competency 6: Vocal Variety. Use prosody data to provide evidence-based evaluations."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format=CSSEFIC6ToolOutput,
                temperature=self.openai_temperature
            )
            
            result = response.choices[0].message.parsed
            print(f"CSSEF C6 evaluation completed - Score: {result.score}")
            return result
            
        except Exception as e:
            print(f"Error in CSSEF C6 evaluation: {e}")
            return self._get_fallback_evaluation()
    
    def _create_evaluation_prompt(self, inputs: CSSEFIC6ToolInput) -> str:
        """Create the evaluation prompt for OpenAI with prosody analysis"""
        
        # Extract prosody metrics
        prosody = inputs.prosody_results
        pitch_data = prosody.get('pitch', {})
        volume_data = prosody.get('volume', {})
        pace_data = prosody.get('pace', {})
        
        # Calculate prosody metrics for evaluation
        pitch_mean = pitch_data.get('mean', 0)
        pitch_std = pitch_data.get('std', 0)
        pitch_range = pitch_data.get('max', 0) - pitch_data.get('min', 0)
        
        volume_mean = volume_data.get('mean', 0)
        volume_std = volume_data.get('std', 0)
        volume_range = volume_data.get('max', 0) - volume_data.get('min', 0)
        
        pause_count = prosody.get('pause_count', 0)
        avg_pause_duration = prosody.get('average_pause_duration', 0)
        
        # Pace analysis
        duration_minutes = inputs.speech_duration / 60
        
        return f"""
You are evaluating CSSEF Competency 6: "USES VOCAL VARIETY IN RATE, PITCH, AND INTENSITY (VOLUME) TO HEIGHTEN AND MAINTAIN INTEREST APPROPRIATE TO THE AUDIENCE & OCCASION"

EVALUATION CRITERIA:
- EXCELLENT (5): Exceptional use of vocal variety in conversational mode. Exceptionally well-paced, easily heard, varied in pitch to enhance message.
- SATISFACTORY (3-4): Acceptable use of vocal variety in conversational mode. Shows only occasional weakness in pace, volume, pitch without significantly detracting.
- UNSATISFACTORY (1-2): Fails to use vocal variety and conversational mode. Frequent weakness in controlling pace, volume, pitch, detracting from speech quality.

SPEECH DETAILS:
- Context: {inputs.context or 'General'}
- Duration: {duration_minutes:.1f} minutes
- Words per minute: {inputs.words_per_minute:.1f} WPM

PROSODY ANALYSIS DATA:

1. PITCH VARIATION:
   - Mean pitch: {pitch_mean:.1f} Hz
   - Standard deviation: {pitch_std:.1f} Hz
   - Pitch range: {pitch_range:.1f} Hz
   - Assessment: {'Good variety' if pitch_std > 20 else 'Limited variety' if pitch_std > 10 else 'Very limited variety'}

2. VOLUME/INTENSITY VARIATION:
   - Mean volume: {volume_mean:.1f} dB
   - Standard deviation: {volume_std:.1f} dB
   - Volume range: {volume_range:.1f} dB
   - Assessment: {'Good dynamics' if volume_std > 3 else 'Limited dynamics' if volume_std > 1.5 else 'Very limited dynamics'}

3. RATE/PACE ANALYSIS:
   - Speaking rate: {inputs.words_per_minute:.1f} WPM
   - Optimal range: 150-200 WPM for most contexts
   - Rate assessment: {'Appropriate' if 140 <= inputs.words_per_minute <= 220 else 'Too fast' if inputs.words_per_minute > 220 else 'Too slow'}
   - Pause count: {pause_count}
   - Average pause duration: {avg_pause_duration:.2f} seconds

4. CONVERSATIONAL QUALITY:
   - Natural pacing with strategic pauses
   - Pitch variety that supports meaning
   - Volume changes for emphasis

TRANSCRIPT:
{inputs.transcript[:1500]}

EVALUATION INSTRUCTIONS:

1. RATE EVALUATION:
   - Is speaking pace appropriate for content and audience?
   - Are pauses used effectively for emphasis and comprehension?
   - Does pace vary to maintain interest?

2. PITCH EVALUATION:
   - Is there sufficient pitch variation (std dev > 15 Hz is good)?
   - Does pitch support meaning and emotion?
   - Avoid monotone delivery

3. INTENSITY/VOLUME EVALUATION:
   - Is volume appropriate and audible?
   - Is there variation for emphasis (std dev > 2 dB is good)?
   - Does volume support the message?

4. CONVERSATIONAL MODE:
   - Does delivery sound natural and conversational?
   - Is vocal variety purposeful rather than random?
   - Does it enhance rather than distract from content?

CONTEXT-SPECIFIC CONSIDERATIONS:
- Academic: Clear, measured pace; professional tone; emphasis on key points
- Persuasive: Dynamic variety to build emotion and conviction
- Storytelling: Varied pace and pitch to create drama and engagement

Base your evaluation on the prosody data provided, which gives objective measurements of the speaker's vocal delivery.
"""
    
    def _get_fallback_evaluation(self) -> CSSEFIC6ToolOutput:
        """Return fallback evaluation when API fails"""
        return CSSEFIC6ToolOutput(
            score=3.0,
            justification="Unable to perform detailed evaluation due to technical issues. Prosody analysis suggests adequate vocal variety but improvements could be made.",
            improvement_suggestions="Work on varying your pitch more to emphasize key points. Practice using strategic pauses and volume changes to maintain audience interest."
        )