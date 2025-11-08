"""
CSSEF Competency 4 Tool: Organizational Pattern Evaluation

This tool evaluates the organizational pattern used in the speech for
appropriateness to the topic, audience, occasion, and purpose, following 
CSSEF Competency 4 criteria.

Evaluation Criteria:
- Quality of introduction and conclusion
- Logical progression within and between ideas
- Clear structure and organization
- Appropriate pattern for topic and purpose
"""

import os
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from tools.base import BaseTool
from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE


class CSSEFIC4ToolInput(BaseModel):
    """Input schema for CSSEF Competency 4 evaluation"""
    
    transcript: str = Field(..., description="Full transcript of the speech")
    context: Optional[str] = Field(None, description="Speaking context (academic, persuasive, storytelling, etc.)")
    speech_goal: Optional[str] = Field(None, description="Stated goal/purpose of the speech")
    audience_description: Optional[str] = Field(None, description="Description of target audience")
    key_points: Optional[str] = Field(None, description="Key points speaker wanted to cover")


class CSSEFIC4ToolOutput(BaseModel):
    """Output schema for CSSEF Competency 4 evaluation"""
    
    score: float = Field(..., description="Score from 1-5 for organizational pattern appropriateness")
    justification: str = Field(..., description="Detailed justification with at least 2 examples")
    improvement_suggestions: str = Field(..., description="At least 2 specific improvement suggestions")


class CSSEFIC4Tool(BaseTool[CSSEFIC4ToolInput, CSSEFIC4ToolOutput]):
    """
    Tool for evaluating CSSEF Competency 4: Organizational Pattern
    
    Evaluates whether the speaker used an organizational pattern appropriate
    to the topic, audience, occasion, and purpose.
    """
    
    name = "cssef_c4_organization_tool"
    description = "Evaluates organizational pattern appropriateness (CSSEF Competency 4)"
    
    InputSchema = CSSEFIC4ToolInput
    OutputSchema = CSSEFIC4ToolOutput
    
    def __init__(self):
        """Initialize the tool with OpenAI client"""
        try:
            from openai import OpenAI
            self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
            self.openai_model = OPENAI_MODEL
            self.openai_temperature = OPENAI_TEMPERATURE
            print("OpenAI client initialized successfully for CSSEF C4 evaluation")
        except Exception as e:
            print(f"Warning: Failed to initialize OpenAI client: {e}")
            self.openai_client = None
    
    def run(self, inputs: CSSEFIC4ToolInput) -> CSSEFIC4ToolOutput:
        """
        Evaluate organizational pattern appropriateness.
        
        Args:
            inputs: CSSEF C4 evaluation inputs
            
        Returns:
            CSSEF C4 evaluation output with score, justification, and improvements
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
                        "content": "You are an expert public speaking evaluator specializing in CSSEF Competency 4: Organizational Pattern. Provide detailed, evidence-based evaluations."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format=CSSEFIC4ToolOutput,
                temperature=self.openai_temperature
            )
            
            result = response.choices[0].message.parsed
            print(f"CSSEF C4 evaluation completed - Score: {result.score}")
            return result
            
        except Exception as e:
            print(f"Error in CSSEF C4 evaluation: {e}")
            return self._get_fallback_evaluation()
    
    def _create_evaluation_prompt(self, inputs: CSSEFIC4ToolInput) -> str:
        """Create the evaluation prompt for OpenAI"""
        
        return f"""
You are evaluating CSSEF Competency 4: "USES AN ORGANIZATIONAL PATTERN APPROPRIATE TO THE TOPIC, AUDIENCE, OCCASION, & PURPOSE"

EVALUATION CRITERIA:
- EXCELLENT (5): Exceptional introduction and conclusion with exceptionally clear and logical progression. Introduction engages appropriately and creatively, body shows superior clarity, conclusion reflects content with undeniable message/call to action.
- SATISFACTORY (3-4): Appropriate introduction and conclusion with reasonably clear progression. Introduction engages majority appropriately, body shows adequate clarity, conclusion reflects content with clear message/call to action.
- UNSATISFACTORY (1-2): Fails to use proper introduction/conclusion and lacks clear progression. Introduction fails to engage, body lacks clarity, conclusion fails to reflect content or provide clear message.

SPEECH DETAILS:
- Context: {inputs.context or 'General'}
- Purpose/Goal: {inputs.speech_goal or 'Not specified'}
- Target Audience: {inputs.audience_description or 'Not specified'}
- Key Points: {inputs.key_points or 'Not specified'}

TRANSCRIPT:
{inputs.transcript}

EVALUATION INSTRUCTIONS:

1. INTRODUCTION ANALYSIS:
   - Does it grab attention effectively?
   - Is there a clear preview of main points?
   - Does it establish credibility and relevance?
   - Is it appropriate for the audience and occasion?

2. BODY ORGANIZATION:
   - Are main points clearly identifiable?
   - Is there logical flow between points?
   - Are transitions present and effective?
   - Does the pattern suit the topic and purpose?

3. CONCLUSION ANALYSIS:
   - Does it summarize key points?
   - Is there a memorable closing?
   - Does it call for action (if appropriate)?
   - Does it provide closure?

4. ORGANIZATIONAL PATTERNS TO CONSIDER:
   - Chronological (time-based)
   - Spatial (location-based)
   - Topical (by categories)
   - Problem-solution
   - Cause-effect
   - Compare-contrast
   - Narrative/story structure

CONTEXT-SPECIFIC EXPECTATIONS:
- Academic: Clear thesis, logical argument structure, formal organization
- Persuasive: Problem-solution, Monroe's motivated sequence, clear call to action
- Storytelling: Narrative arc, engaging opening, satisfying conclusion

Analyze the transcript for structural elements and organizational clarity. Provide specific examples of organizational strengths or weaknesses.
"""
    
    def _get_fallback_evaluation(self) -> CSSEFIC4ToolOutput:
        """Return fallback evaluation when API fails"""
        return CSSEFIC4ToolOutput(
            score=3.0,
            justification="Unable to perform detailed evaluation due to technical issues. Organization appears adequate but could be clearer.",
            improvement_suggestions="Add clear transitions between main points and ensure you have a strong introduction that previews your content and a conclusion that summarizes key points."
        )