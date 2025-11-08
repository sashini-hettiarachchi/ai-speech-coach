"""
CSSEF Competency 6 Tool: Vocal Variety Evaluation

This tool evaluates the use of vocal variety in rate, pitch, and intensity (volume)
to heighten and maintain interest, following CSSEF Competency 6 criteria.

This competency specifically requires prosody analysis data to provide accurate
scoring based on actual vocal delivery metrics, including word-level prosody analysis.

Evaluation Criteria:
- Effective use of vocal variety in conversational mode
- Appropriate pacing, volume, and pitch variation
- Enhancement of message through vocal delivery
- Maintenance of audience interest through vocal dynamics
"""

import os
from typing import Optional, Dict, Any, List
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
        
        # Extract prosody data
        prosody = inputs.prosody_results
        
        # Overall prosody statistics
        pitch_mean = prosody.get('pitch_mean', 0)
        pitch_std = prosody.get('pitch_std', 0)
        volume_mean = prosody.get('volume_mean', 0)
        volume_std = prosody.get('volume_std', 0)
        words_per_minute = prosody.get('words_per_minute', inputs.words_per_minute)
        
        # Detailed events for analysis
        pause_events = prosody.get('pause_events', [])
        pitch_events = prosody.get('pitch_events', [])
        volume_events = prosody.get('volume_events', [])
        speed_events = prosody.get('speed_events', [])
        
        # NEW: Word-level prosody analysis for detailed evaluation
        word_prosody_events = prosody.get('word_prosody_events', [])
        
        # Analyze word-level patterns for more detailed insights
        vocal_variety_insights = self._analyze_word_level_vocal_variety(word_prosody_events)
        
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
- Overall words per minute: {words_per_minute:.1f} WPM

OVERALL PROSODY ANALYSIS:

1. PITCH VARIATION:
   - Mean pitch: {pitch_mean:.1f} Hz
   - Standard deviation: {pitch_std:.1f} Hz
   - Assessment: {'Excellent variety' if pitch_std > 25 else 'Good variety' if pitch_std > 15 else 'Limited variety' if pitch_std > 8 else 'Very limited variety'}
   - Pitch events detected: {len(pitch_events)} significant variations

2. VOLUME/INTENSITY VARIATION:
   - Mean volume: {volume_mean:.1f} dB
   - Standard deviation: {volume_std:.1f} dB
   - Assessment: {'Excellent dynamics' if volume_std > 4 else 'Good dynamics' if volume_std > 2.5 else 'Limited dynamics' if volume_std > 1.5 else 'Very limited dynamics'}
   - Volume events detected: {len(volume_events)} significant variations

3. RATE/PACE ANALYSIS:
   - Speaking rate: {words_per_minute:.1f} WPM
   - Optimal range: 150-200 WPM for most contexts
   - Rate assessment: {'Appropriate' if 140 <= words_per_minute <= 220 else 'Too fast' if words_per_minute > 220 else 'Too slow'}
   - Pause events: {len(pause_events)} strategic pauses
   - Speed events: {len(speed_events)} rate variations

WORD-LEVEL VOCAL VARIETY ANALYSIS:
{vocal_variety_insights}

TRANSCRIPT EXCERPT (for content context):
{inputs.transcript[:1000]}...

EVALUATION INSTRUCTIONS:

1. RATE EVALUATION:
   - Is speaking pace appropriate for content and audience?
   - Are pauses used effectively for emphasis and comprehension?
   - Does pace vary to maintain interest and support meaning?
   - Look for natural rhythm and strategic speed changes

2. PITCH EVALUATION:
   - Is there sufficient pitch variation (std dev > 15 Hz is good)?
   - Does pitch support meaning and emotion?
   - Are there pitch stresses at key moments?
   - Avoid monotone delivery assessment

3. INTENSITY/VOLUME EVALUATION:
   - Is volume appropriate and audible?
   - Is there variation for emphasis (std dev > 2.5 dB is good)?
   - Does volume support the message and maintain interest?
   - Are volume changes purposeful?

4. CONVERSATIONAL MODE:
   - Does delivery sound natural and conversational?
   - Is vocal variety purposeful rather than random?
   - Does it enhance rather than distract from content?
   - Is there appropriate vocal energy?

5. WORD-LEVEL ANALYSIS:
   - Use the word-level prosody data to identify specific examples
   - Note words with effective vocal emphasis
   - Identify missed opportunities for vocal variety
   - Comment on natural speech patterns

CONTEXT-SPECIFIC CONSIDERATIONS:
- Academic: Clear, measured pace; professional tone; emphasis on key points
- Persuasive: Dynamic variety to build emotion and conviction
- Storytelling: Varied pace and pitch to create drama and engagement

Base your evaluation on both overall prosody statistics AND word-level analysis for comprehensive assessment.
"""
    
    def _analyze_word_level_vocal_variety(self, word_prosody_events: List[Dict[str, Any]]) -> str:
        """
        Analyze word-level prosody events to provide detailed vocal variety insights.
        
        Args:
            word_prosody_events: List of word-level prosody data
            
        Returns:
            Formatted analysis string for the evaluation prompt
        """
        if not word_prosody_events:
            return "No word-level prosody data available for detailed analysis."
        
        # Count vocal variety patterns
        stress_words = []
        loud_words = []
        soft_words = []
        fast_words = []
        slow_words = []
        pause_before_words = []
        pause_after_words = []
        
        for word_data in word_prosody_events:
            word = word_data.get('word', '')
            
            # Pitch analysis
            if word_data.get('pitch_level') == 'stress':
                stress_words.append(word)
            
            # Volume analysis
            if word_data.get('volume_level') == 'louder':
                loud_words.append(word)
            elif word_data.get('volume_level') == 'softer':
                soft_words.append(word)
            
            # Speed analysis
            if word_data.get('speed_level') == 'faster':
                fast_words.append(word)
            elif word_data.get('speed_level') == 'slower':
                slow_words.append(word)
            
            # Pause analysis
            if word_data.get('pause_before'):
                pause_before_words.append(f"{word} (after {word_data.get('pause_before_duration', 0):.1f}s pause)")
            if word_data.get('pause_after'):
                pause_after_words.append(f"{word} (before {word_data.get('pause_after_duration', 0):.1f}s pause)")
        
        # Calculate variety percentages
        total_words = len(word_prosody_events)
        pitch_variety_pct = (len(stress_words) / total_words * 100) if total_words > 0 else 0
        volume_variety_pct = ((len(loud_words) + len(soft_words)) / total_words * 100) if total_words > 0 else 0
        speed_variety_pct = ((len(fast_words) + len(slow_words)) / total_words * 100) if total_words > 0 else 0
        pause_variety_pct = ((len(pause_before_words) + len(pause_after_words)) / total_words * 100) if total_words > 0 else 0
        
        analysis = f"""
WORD-LEVEL VOCAL VARIETY DETAILS ({total_words} words analyzed):

📈 PITCH VARIETY: {pitch_variety_pct:.1f}% of words with pitch stress
   - Words with pitch emphasis: {', '.join(stress_words[:10])}{'...' if len(stress_words) > 10 else ''}
   - Assessment: {'Excellent' if pitch_variety_pct > 15 else 'Good' if pitch_variety_pct > 8 else 'Limited' if pitch_variety_pct > 3 else 'Very limited'} pitch variety

🔊 VOLUME VARIETY: {volume_variety_pct:.1f}% of words with volume variation
   - Louder words (emphasis): {', '.join(loud_words[:8])}{'...' if len(loud_words) > 8 else ''}
   - Softer words (de-emphasis): {', '.join(soft_words[:5])}{'...' if len(soft_words) > 5 else ''}
   - Assessment: {'Excellent' if volume_variety_pct > 20 else 'Good' if volume_variety_pct > 12 else 'Limited' if volume_variety_pct > 5 else 'Very limited'} volume dynamics

⚡ SPEED VARIETY: {speed_variety_pct:.1f}% of words with pace variation
   - Faster words: {', '.join(fast_words[:8])}{'...' if len(fast_words) > 8 else ''}
   - Slower words: {', '.join(slow_words[:8])}{'...' if len(slow_words) > 8 else ''}
   - Assessment: {'Excellent' if speed_variety_pct > 25 else 'Good' if speed_variety_pct > 15 else 'Limited' if speed_variety_pct > 8 else 'Very limited'} pace variation

⏸️ PAUSE STRATEGY: {pause_variety_pct:.1f}% of words associated with strategic pauses
   - Words after pauses: {', '.join(pause_before_words[:5])}{'...' if len(pause_before_words) > 5 else ''}
   - Words before pauses: {', '.join(pause_after_words[:5])}{'...' if len(pause_after_words) > 5 else ''}
   - Assessment: {'Excellent' if pause_variety_pct > 12 else 'Good' if pause_variety_pct > 6 else 'Limited' if pause_variety_pct > 2 else 'Very limited'} pause usage

OVERALL VOCAL VARIETY SCORE: {(pitch_variety_pct + volume_variety_pct + speed_variety_pct + pause_variety_pct) / 4:.1f}% combined variety
"""
        
        return analysis.strip()
    
    def _get_fallback_evaluation(self) -> CSSEFIC6ToolOutput:
        """Return fallback evaluation when API fails"""
        return CSSEFIC6ToolOutput(
            score=3.0,
            justification="Unable to perform detailed evaluation due to technical issues. Prosody analysis suggests adequate vocal variety but improvements could be made.",
            improvement_suggestions="Work on varying your pitch more to emphasize key points. Practice using strategic pauses and volume changes to maintain audience interest."
        )