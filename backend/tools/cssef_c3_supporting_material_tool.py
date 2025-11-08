"""
CSSEF Competency 3 Tool: Supporting Material Evaluation

This tool evaluates the quality and variety of supporting material used in the speech,
including electronic and non-electronic presentational aids, following 
CSSEF Competency 3 criteria.

Evaluation Criteria:
- Quality and variety of supporting material
- Relevance and link to thesis
- Enhancement of credibility and clarity
- Appropriateness for audience and occasion
"""

import os
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from tools.base import BaseTool
from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE


class CSSEFIC3ToolInput(BaseModel):
    """Input schema for CSSEF Competency 3 evaluation"""
    
    transcript: str = Field(..., description="Full transcript of the speech")
    context: Optional[str] = Field(None, description="Speaking context (academic, persuasive, storytelling, etc.)")
    audience_description: Optional[str] = Field(None, description="Description of target audience")
    speech_title: Optional[str] = Field(None, description="Title of the speech")


class CSSEFIC3ToolOutput(BaseModel):
    """Output schema for CSSEF Competency 3 evaluation"""
    
    score: float = Field(..., description="Score from 1-5 for supporting material quality")
    justification: str = Field(..., description="Detailed justification with at least 2 examples")
    improvement_suggestions: str = Field(..., description="At least 2 specific improvement suggestions")


class CSSEFIC3Tool(BaseTool[CSSEFIC3ToolInput, CSSEFIC3ToolOutput]):
    """
    Tool for evaluating CSSEF Competency 3: Supporting Material
    
    Evaluates the quality, variety, and appropriateness of supporting material
    used in the speech for the audience and occasion.
    """
    
    name = "cssef_c3_supporting_material_tool"
    description = "Evaluates supporting material quality and variety (CSSEF Competency 3)"
    
    InputSchema = CSSEFIC3ToolInput
    OutputSchema = CSSEFIC3ToolOutput
    
    def __init__(self):
        """Initialize the tool with OpenAI client"""
        try:
            from openai import OpenAI
            self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
            self.openai_model = OPENAI_MODEL
            self.openai_temperature = OPENAI_TEMPERATURE
            print("OpenAI client initialized successfully for CSSEF C3 evaluation")
        except Exception as e:
            print(f"Warning: Failed to initialize OpenAI client: {e}")
            self.openai_client = None
    
    def run(self, inputs: CSSEFIC3ToolInput) -> CSSEFIC3ToolOutput:
        """
        Evaluate supporting material quality and variety.
        
        Args:
            inputs: CSSEF C3 evaluation inputs
            
        Returns:
            CSSEF C3 evaluation output with score, justification, and improvements
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
                        "content": "You are an expert public speaking evaluator specializing in CSSEF Competency 3: Supporting Material. Provide detailed, evidence-based evaluations."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format=CSSEFIC3ToolOutput,
                temperature=self.openai_temperature
            )
            
            result = response.choices[0].message.parsed
            print(f"CSSEF C3 evaluation completed - Score: {result.score}")
            return result
            
        except Exception as e:
            print(f"Error in CSSEF C3 evaluation: {e}")
            return self._get_fallback_evaluation()
    
    def _create_evaluation_prompt(self, inputs: CSSEFIC3ToolInput) -> str:
        """Create the evaluation prompt for OpenAI"""
        
        return f"""
You are evaluating CSSEF Competency 3: "PROVIDES SUPPORTING MATERIAL (INCLUDING ELECTRONIC AND NON-ELECTRONIC PRESENTATIONAL AIDS) APPROPRIATE TO THE AUDIENCE & OCCASION"

EVALUATION CRITERIA:
- EXCELLENT (5): Supporting material is exceptional in quality and variety. Unarguably linked to thesis, decidedly enhances credibility and clarity.
- SATISFACTORY (3-4): Supporting material is appropriate in quality and variety. Logically linked to thesis, adds measurable interest.
- UNSATISFACTORY (1-2): Supporting material is inappropriate in quality/variety. Only vaguely related to thesis, detracts from effectiveness.

SPEECH DETAILS:
- Context: {inputs.context or 'General'}
- Target Audience: {inputs.audience_description or 'Not specified'}
- Title: {inputs.speech_title or 'Not provided'}

TRANSCRIPT:
{inputs.transcript}

EVALUATION INSTRUCTIONS:
Analyze the transcript for types of supporting material used:

1. EXAMPLES & ILLUSTRATIONS:
   - Personal stories/anecdotes
   - Hypothetical scenarios
   - Case studies
   - Historical examples

2. STATISTICS & DATA:
   - Numerical data
   - Research findings
   - Surveys/polls
   - Quantitative evidence

3. EXPERT TESTIMONY:
   - Quotes from authorities
   - Expert opinions
   - Credible sources
   - Professional insights

4. ANALOGIES & COMPARISONS:
   - Metaphors
   - Similes
   - Comparisons to familiar concepts

5. DEFINITIONS & EXPLANATIONS:
   - Clear explanations of terms
   - Background information
   - Context setting

QUALITY ASSESSMENT:
- Are sources credible and appropriate for the audience?
- Is there good variety in types of supporting material?
- Do the materials clearly support the main points?
- Are they current and relevant?
- Do they enhance understanding rather than confuse?

CONTEXT CONSIDERATIONS:
- Academic: Expect scholarly sources, research, data
- Persuasive: Look for compelling evidence, statistics, expert testimony
- Storytelling: Focus on vivid examples, personal stories, descriptive details

Provide specific examples from the transcript of supporting materials used (or lacking), and suggest concrete improvements.
"""
    
    def _get_fallback_evaluation(self) -> CSSEFIC3ToolOutput:
        """Return fallback evaluation when API fails"""
        return CSSEFIC3ToolOutput(
            score=3.0,
            justification="Unable to perform detailed evaluation due to technical issues. Supporting material appears adequate but could benefit from more variety.",
            improvement_suggestions="Add more diverse types of supporting material such as statistics, expert quotes, and specific examples. Ensure all supporting material clearly links to your main points."
        )