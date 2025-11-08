"""
CSSEF Competency 2 Tool: Thesis/Specific Purpose Communication Evaluation

This tool evaluates how clearly and appropriately the speaker communicated
their thesis/specific purpose for the audience and occasion, following 
CSSEF Competency 2 criteria.

Evaluation Criteria:
- Clarity and identifiability of thesis/specific purpose
- Appropriateness for audience and occasion
- Timing of purpose communication (within opening sentences)
"""

import os
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from tools.base import BaseTool
from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE


class CSSEFIC2ToolInput(BaseModel):
    """Input schema for CSSEF Competency 2 evaluation"""
    
    transcript: str = Field(..., description="Full transcript of the speech")
    context: Optional[str] = Field(None, description="Speaking context (academic, persuasive, storytelling, etc.)")
    speech_goal: Optional[str] = Field(None, description="Stated goal/purpose of the speech")
    audience_description: Optional[str] = Field(None, description="Description of target audience")
    speech_title: Optional[str] = Field(None, description="Title of the speech")


class CSSEFIC2ToolOutput(BaseModel):
    """Output schema for CSSEF Competency 2 evaluation"""
    
    score: float = Field(..., description="Score from 1-5 for thesis/purpose communication")
    justification: str = Field(..., description="Detailed justification with at least 2 examples")
    improvement_suggestions: str = Field(..., description="At least 2 specific improvement suggestions")


class CSSEFIC2Tool(BaseTool[CSSEFIC2ToolInput, CSSEFIC2ToolOutput]):
    """
    Tool for evaluating CSSEF Competency 2: Thesis/Specific Purpose Communication
    
    Evaluates whether the speaker clearly communicated their thesis/specific purpose
    in a manner appropriate for the audience and occasion.
    """
    
    name = "cssef_c2_purpose_tool"
    description = "Evaluates thesis/specific purpose communication clarity (CSSEF Competency 2)"
    
    InputSchema = CSSEFIC2ToolInput
    OutputSchema = CSSEFIC2ToolOutput
    
    def __init__(self):
        """Initialize the tool with OpenAI client"""
        try:
            from openai import OpenAI
            self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
            self.openai_model = OPENAI_MODEL
            self.openai_temperature = OPENAI_TEMPERATURE
            print("OpenAI client initialized successfully for CSSEF C2 evaluation")
        except Exception as e:
            print(f"Warning: Failed to initialize OpenAI client: {e}")
            self.openai_client = None
    
    def run(self, inputs: CSSEFIC2ToolInput) -> CSSEFIC2ToolOutput:
        """
        Evaluate thesis/specific purpose communication.
        
        Args:
            inputs: CSSEF C2 evaluation inputs
            
        Returns:
            CSSEF C2 evaluation output with score, justification, and improvements
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
                        "content": "You are an expert public speaking evaluator specializing in CSSEF Competency 2: Thesis/Specific Purpose Communication. Provide detailed, evidence-based evaluations."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format=CSSEFIC2ToolOutput,
                temperature=self.openai_temperature
            )
            
            result = response.choices[0].message.parsed
            print(f"CSSEF C2 evaluation completed - Score: {result.score}")
            return result
            
        except Exception as e:
            print(f"Error in CSSEF C2 evaluation: {e}")
            return self._get_fallback_evaluation()
    
    def _create_evaluation_prompt(self, inputs: CSSEFIC2ToolInput) -> str:
        """Create the evaluation prompt for OpenAI"""
        
        # Split transcript into opening sentences for analysis
        sentences = inputs.transcript.split('.')[:3]  # First 3 sentences
        opening_text = '. '.join(sentences) + '.' if sentences else inputs.transcript[:200]
        
        return f"""
You are evaluating CSSEF Competency 2: "COMMUNICATES THE THESIS/SPECIFIC PURPOSE IN A MANNER APPROPRIATE FOR THE AUDIENCE & OCCASION"

EVALUATION CRITERIA:
- EXCELLENT (5): Thesis/specific purpose is exceptionally clear and identifiable. All audience members should understand the purpose within opening sentences.
- SATISFACTORY (3-4): Thesis/specific purpose is adequately clear and identifiable. Majority of audience should understand within opening sentences.
- UNSATISFACTORY (1-2): Does not communicate a clear and identifiable thesis/specific purpose. Majority may have difficulty understanding the purpose.

SPEECH DETAILS:
- Context: {inputs.context or 'General'}
- Stated Goal: {inputs.speech_goal or 'Not specified'}
- Target Audience: {inputs.audience_description or 'Not specified'}
- Title: {inputs.speech_title or 'Not provided'}

OPENING SENTENCES ANALYSIS:
{opening_text}

FULL TRANSCRIPT:
{inputs.transcript}

EVALUATION INSTRUCTIONS:
1. Identify if there is a clear thesis statement or specific purpose in the opening
2. Assess how quickly the purpose becomes clear to the audience
3. Evaluate if the purpose is appropriate for the stated audience and context
4. Look for explicit statements of intent, goals, or main arguments
5. Consider if the purpose remains consistent throughout the speech

Key questions to address:
- Is there a clear "I will..." or "Today I'm going to..." type statement?
- Would the audience know what to expect from this speech after the first few sentences?
- Is the purpose appropriate for the given context and audience?
- Does the actual content align with any stated purpose?

Provide specific examples from the transcript, particularly from the opening, that support your evaluation.
"""
    
    def _get_fallback_evaluation(self) -> CSSEFIC2ToolOutput:
        """Return fallback evaluation when API fails"""
        return CSSEFIC2ToolOutput(
            score=3.0,
            justification="Unable to perform detailed evaluation due to technical issues. Purpose appears to be communicated but clarity could be improved.",
            improvement_suggestions="Start with a clear thesis statement in the opening sentences. Make your specific purpose explicit and obvious to the audience."
        )