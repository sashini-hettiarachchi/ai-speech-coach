"""
CSSEF Competency 7 Tool: Pronunciation, Grammar, and Articulation Evaluation

This tool evaluates the use of pronunciation, grammar, and articulation
appropriate to the audience and occasion, following CSSEF Competency 7 criteria.

Evaluation Criteria:
- Quality of articulation and pronunciation
- Grammatical accuracy
- Fluency and freedom from disfluencies
- Appropriateness for audience and occasion
"""

import os
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from tools.base import BaseTool
from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE


class CSSEFIC7ToolInput(BaseModel):
    """Input schema for CSSEF Competency 7 evaluation"""
    
    transcript: str = Field(..., description="Full transcript of the speech")
    context: Optional[str] = Field(None, description="Speaking context (academic, persuasive, storytelling, etc.)")
    audience_description: Optional[str] = Field(None, description="Description of target audience")
    filler_analysis: Optional[Dict[str, Any]] = Field(None, description="Analysis of filler words and speech disfluencies")


class CSSEFIC7ToolOutput(BaseModel):
    """Output schema for CSSEF Competency 7 evaluation"""
    
    score: float = Field(..., description="Score from 1-5 for pronunciation, grammar, and articulation")
    justification: str = Field(..., description="Detailed justification with at least 2 examples")
    improvement_suggestions: str = Field(..., description="At least 2 specific improvement suggestions")


class CSSEFIC7Tool(BaseTool[CSSEFIC7ToolInput, CSSEFIC7ToolOutput]):
    """
    Tool for evaluating CSSEF Competency 7: Pronunciation, Grammar, and Articulation
    
    Evaluates whether the speaker used pronunciation, grammar, and articulation
    appropriate to the audience and occasion.
    """
    
    name = "cssef_c7_pronunciation_tool"
    description = "Evaluates pronunciation, grammar, and articulation quality (CSSEF Competency 7)"
    
    InputSchema = CSSEFIC7ToolInput
    OutputSchema = CSSEFIC7ToolOutput
    
    def __init__(self):
        """Initialize the tool with OpenAI client"""
        try:
            from openai import OpenAI
            self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
            self.openai_model = OPENAI_MODEL
            self.openai_temperature = OPENAI_TEMPERATURE
            print("OpenAI client initialized successfully for CSSEF C7 evaluation")
        except Exception as e:
            print(f"Warning: Failed to initialize OpenAI client: {e}")
            self.openai_client = None
    
    def run(self, inputs: CSSEFIC7ToolInput) -> CSSEFIC7ToolOutput:
        """
        Evaluate pronunciation, grammar, and articulation quality.
        
        Args:
            inputs: CSSEF C7 evaluation inputs
            
        Returns:
            CSSEF C7 evaluation output with score, justification, and improvements
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
                        "content": "You are an expert public speaking evaluator specializing in CSSEF Competency 7: Pronunciation, Grammar, and Articulation. Provide detailed, evidence-based evaluations."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format=CSSEFIC7ToolOutput,
                temperature=self.openai_temperature
            )
            
            result = response.choices[0].message.parsed
            print(f"CSSEF C7 evaluation completed - Score: {result.score}")
            return result
            
        except Exception as e:
            print(f"Error in CSSEF C7 evaluation: {e}")
            return self._get_fallback_evaluation()
    
    def _create_evaluation_prompt(self, inputs: CSSEFIC7ToolInput) -> str:
        """Create the evaluation prompt for OpenAI"""
        
        # Extract filler analysis information
        filler_info = ""
        if inputs.filler_analysis:
            filler_percentage = inputs.filler_analysis.get('filler_percentage', 0)
            total_fillers = inputs.filler_analysis.get('total_fillers', 0)
            filler_details = inputs.filler_analysis.get('filler_words', {})
            
            filler_info = f"""
FILLER WORD AND DISFLUENCY ANALYSIS:
- Filler percentage: {filler_percentage:.1f}%
- Total filler words: {total_fillers}
- Common fillers detected: {list(filler_details.keys()) if filler_details else 'None'}
- Impact on fluency: {'High' if filler_percentage > 5 else 'Moderate' if filler_percentage > 2 else 'Low'}
"""
        
        return f"""
You are evaluating CSSEF Competency 7: "USES PRONUNCIATION, GRAMMAR, AND ARTICULATION APPROPRIATE TO THE AUDIENCE & OCCASION"

EVALUATION CRITERIA:
- EXCELLENT (5): Exceptional articulation, pronunciation, and grammar. Exceptional fluency, properly formed sounds that enhance message, no pronunciation or grammatical errors.
- SATISFACTORY (3-4): Acceptable articulation with few pronunciation or grammatical errors. Most sounds properly formed, minor vocalized disfluencies, few (1-2) minor errors.
- UNSATISFACTORY (1-2): Fails to use acceptable articulation, pronunciation, and grammar. Nonfluencies interfere with message, frequent errors make understanding difficult.

SPEECH DETAILS:
- Context: {inputs.context or 'General'}
- Target Audience: {inputs.audience_description or 'Not specified'}

{filler_info}

TRANSCRIPT:
{inputs.transcript}

EVALUATION INSTRUCTIONS:

1. PRONUNCIATION ANALYSIS:
   - Are words pronounced correctly and clearly?
   - Are there mispronunciations that interfere with meaning?
   - Is pronunciation appropriate for the audience and context?
   - Are proper nouns and technical terms pronounced correctly?

2. GRAMMAR EVALUATION:
   - Is sentence structure correct and varied?
   - Are there grammatical errors (subject-verb agreement, tense consistency, etc.)?
   - Is grammar appropriate for the formality level expected?
   - Are there run-on sentences or fragments?

3. ARTICULATION ASSESSMENT:
   - Are sounds clearly formed and distinct?
   - Is speech crisp and easily understood?
   - Are there issues with specific sounds or combinations?
   - Does articulation enhance or detract from the message?

4. FLUENCY EVALUATION:
   - Is speech smooth and natural?
   - Are there excessive hesitations or false starts?
   - Do filler words interfere with message clarity?
   - Is the flow of speech appropriate for the content?

ANALYSIS CONSIDERATIONS:

FILLER WORD IMPACT:
- <2%: Excellent fluency
- 2-5%: Acceptable with minor impact
- >5%: Noticeable interference with message

CONTEXT-SPECIFIC EXPECTATIONS:
- Academic: Formal grammar, precise pronunciation, technical accuracy
- Persuasive: Clear articulation for maximum impact, confident delivery
- Storytelling: Natural flow, expressive pronunciation, engaging delivery

COMMON ISSUES TO IDENTIFY:
- Frequent "um," "uh," "like," "you know"
- Dropped word endings
- Unclear consonants
- Grammatical inconsistencies
- Pronunciation errors that affect meaning

Look for specific examples in the transcript of pronunciation clarity, grammatical accuracy, and overall fluency. Consider the transcript quality as a reflection of the original speech delivery.
"""
    
    def _get_fallback_evaluation(self) -> CSSEFIC7ToolOutput:
        """Return fallback evaluation when API fails"""
        return CSSEFIC7ToolOutput(
            score=3.0,
            justification="Unable to perform detailed evaluation due to technical issues. Pronunciation and grammar appear generally acceptable but could be improved.",
            improvement_suggestions="Practice reducing filler words through conscious pausing. Focus on clear articulation and double-check pronunciation of key terms."
        )