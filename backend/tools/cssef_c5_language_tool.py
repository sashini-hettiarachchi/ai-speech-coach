"""
CSSEF Competency 5 Tool: Language Use Evaluation

This tool evaluates the appropriateness of language used in the speech
for the audience and occasion, following CSSEF Competency 5 criteria.

Evaluation Criteria:
- Clarity, vividness, and appropriateness of language
- Freedom from inappropriate jargon
- Inclusive and appropriate language choices
- Enhancement of audience comprehension and engagement
"""

import os
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from tools.base import BaseTool
from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE


class CSSEFIC5ToolInput(BaseModel):
    """Input schema for CSSEF Competency 5 evaluation"""
    
    transcript: str = Field(..., description="Full transcript of the speech")
    context: Optional[str] = Field(None, description="Speaking context (academic, persuasive, storytelling, etc.)")
    audience_description: Optional[str] = Field(None, description="Description of target audience")
    filler_analysis: Optional[Dict[str, Any]] = Field(None, description="Analysis of filler words and speech patterns")


class CSSEFIC5ToolOutput(BaseModel):
    """Output schema for CSSEF Competency 5 evaluation"""
    
    score: float = Field(..., description="Score from 1-5 for language appropriateness")
    justification: str = Field(..., description="Detailed justification with at least 2 examples")
    improvement_suggestions: str = Field(..., description="At least 2 specific improvement suggestions")


class CSSEFIC5Tool(BaseTool[CSSEFIC5ToolInput, CSSEFIC5ToolOutput]):
    """
    Tool for evaluating CSSEF Competency 5: Language Use
    
    Evaluates whether the speaker used language appropriate to the
    audience and occasion, including clarity, vividness, and inclusivity.
    """
    
    name = "cssef_c5_language_tool"
    description = "Evaluates language appropriateness and effectiveness (CSSEF Competency 5)"
    
    InputSchema = CSSEFIC5ToolInput
    OutputSchema = CSSEFIC5ToolOutput
    
    def __init__(self):
        """Initialize the tool with OpenAI client"""
        try:
            from openai import OpenAI
            self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
            self.openai_model = OPENAI_MODEL
            self.openai_temperature = OPENAI_TEMPERATURE
            print("OpenAI client initialized successfully for CSSEF C5 evaluation")
        except Exception as e:
            print(f"Warning: Failed to initialize OpenAI client: {e}")
            self.openai_client = None
    
    def run(self, inputs: CSSEFIC5ToolInput) -> CSSEFIC5ToolOutput:
        """
        Evaluate language appropriateness and effectiveness.
        
        Args:
            inputs: CSSEF C5 evaluation inputs
            
        Returns:
            CSSEF C5 evaluation output with score, justification, and improvements
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
                        "content": "You are an expert public speaking evaluator specializing in CSSEF Competency 5: Language Use. Provide detailed, evidence-based evaluations."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format=CSSEFIC5ToolOutput,
                temperature=self.openai_temperature
            )
            
            result = response.choices[0].message.parsed
            print(f"CSSEF C5 evaluation completed - Score: {result.score}")
            return result
            
        except Exception as e:
            print(f"Error in CSSEF C5 evaluation: {e}")
            return self._get_fallback_evaluation()
    
    def _create_evaluation_prompt(self, inputs: CSSEFIC5ToolInput) -> str:
        """Create the evaluation prompt for OpenAI"""
        
        # Extract filler information if available
        filler_info = ""
        if inputs.filler_analysis:
            filler_percentage = inputs.filler_analysis.get('filler_percentage', 0)
            filler_count = inputs.filler_analysis.get('total_fillers', 0)
            filler_info = f"""
FILLER WORD ANALYSIS:
- Filler percentage: {filler_percentage:.1f}%
- Total filler words: {filler_count}
- This affects language fluency and clarity
"""
        
        return f"""
You are evaluating CSSEF Competency 5: "USES LANGUAGE APPROPRIATE TO THE AUDIENCE & OCCASION"

EVALUATION CRITERIA:
- EXCELLENT (5): Language is exceptionally clear, vivid, and appropriate. Enhances comprehension and enthusiasm while showing exceptional sensitivity to meaning nuances.
- SATISFACTORY (3-4): Language is reasonably clear, vivid, and appropriate. Free of inappropriate jargon, nonsexist, nonracist, etc.
- UNSATISFACTORY (1-2): Uses unclear or inappropriate language. Contains inappropriate jargon, sexist, racist, or other problematic language.

SPEECH DETAILS:
- Context: {inputs.context or 'General'}
- Target Audience: {inputs.audience_description or 'Not specified'}

{filler_info}

TRANSCRIPT:
{inputs.transcript}

EVALUATION INSTRUCTIONS:

1. CLARITY AND PRECISION:
   - Are ideas expressed clearly and concisely?
   - Is vocabulary appropriate for the audience level?
   - Are technical terms explained when necessary?
   - Is sentence structure clear and varied?

2. VIVIDNESS AND ENGAGEMENT:
   - Does language paint clear mental pictures?
   - Are there effective metaphors, analogies, or descriptive phrases?
   - Is the language engaging and interesting?
   - Does word choice enhance emotional connection?

3. APPROPRIATENESS:
   - Is language suitable for the audience and occasion?
   - Are there any inappropriate terms or jargon?
   - Is the language inclusive and respectful?
   - Does formality level match the context?

4. FLUENCY AND FLOW:
   - Does language flow smoothly?
   - Are there excessive filler words that distract?
   - Is there good variety in sentence structure?
   - Are transitions smooth and natural?

CONTEXT CONSIDERATIONS:
- Academic: Expect scholarly vocabulary, precise terminology, formal tone
- Persuasive: Look for emotional language, strong action words, compelling phrases
- Storytelling: Focus on descriptive language, vivid imagery, engaging narrative voice

RED FLAGS TO IDENTIFY:
- Excessive jargon without explanation
- Inappropriate or exclusive language
- Unclear or confusing expressions
- Repetitive or monotonous word choices
- Language that doesn't match audience expectations

Provide specific examples from the transcript of effective or problematic language use.
"""
    
    def _get_fallback_evaluation(self) -> CSSEFIC5ToolOutput:
        """Return fallback evaluation when API fails"""
        return CSSEFIC5ToolOutput(
            score=3.0,
            justification="Unable to perform detailed evaluation due to technical issues. Language appears generally appropriate but could be more vivid and engaging.",
            improvement_suggestions="Use more descriptive and vivid language to enhance audience engagement. Avoid excessive jargon and ensure all terms are clear to your audience."
        )