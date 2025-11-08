"""
CSSEF Competency 1 Tool: Topic Choice and Narrowing Evaluation

This tool evaluates how appropriately the speaker chose and narrowed their topic
for the audience and occasion, following CSSEF Competency 1 criteria.

Evaluation Criteria:
- Topic appropriateness for purpose, time constraints, and audience
- Evidence of audience analysis
- Topic focus and scope management
"""

import os
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from tools.base import BaseTool
from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE


class CSSEFIC1ToolInput(BaseModel):
    """Input schema for CSSEF Competency 1 evaluation"""
    
    transcript: str = Field(..., description="Full transcript of the speech")
    context: Optional[str] = Field(None, description="Speaking context (academic, persuasive, storytelling, etc.)")
    speech_duration: float = Field(..., description="Duration of speech in seconds")
    speech_title: Optional[str] = Field(None, description="Title of the speech")
    speech_goal: Optional[str] = Field(None, description="Goal/purpose of the speech")
    audience_description: Optional[str] = Field(None, description="Description of target audience")
    key_points: Optional[str] = Field(None, description="Key points speaker wanted to cover")


class CSSEFIC1ToolOutput(BaseModel):
    """Output schema for CSSEF Competency 1 evaluation"""
    
    score: float = Field(..., description="Score from 1-5 for topic choice appropriateness")
    justification: str = Field(..., description="Detailed justification with at least 2 examples")
    improvement_suggestions: str = Field(..., description="At least 2 specific improvement suggestions")


class CSSEFIC1Tool(BaseTool[CSSEFIC1ToolInput, CSSEFIC1ToolOutput]):
    """
    Tool for evaluating CSSEF Competency 1: Topic Choice and Narrowing
    
    Evaluates whether the speaker chose and narrowed a topic appropriately
    for the audience and occasion based on the CSSEF framework.
    """
    
    name = "cssef_c1_topic_choice_tool"
    description = "Evaluates topic choice and narrowing appropriateness (CSSEF Competency 1)"
    
    InputSchema = CSSEFIC1ToolInput
    OutputSchema = CSSEFIC1ToolOutput
    
    def __init__(self):
        """Initialize the tool with OpenAI client"""
        try:
            from openai import OpenAI
            self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
            self.openai_model = OPENAI_MODEL
            self.openai_temperature = OPENAI_TEMPERATURE
            print("OpenAI client initialized successfully for CSSEF C1 evaluation")
        except Exception as e:
            print(f"Warning: Failed to initialize OpenAI client: {e}")
            self.openai_client = None
    
    def run(self, inputs: CSSEFIC1ToolInput) -> CSSEFIC1ToolOutput:
        """
        Evaluate topic choice and narrowing appropriateness.
        
        Args:
            inputs: CSSEF C1 evaluation inputs
            
        Returns:
            CSSEF C1 evaluation output with score, justification, and improvements
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
                        "content": "You are an expert public speaking evaluator specializing in CSSEF Competency 1: Topic Choice and Narrowing. Provide detailed, evidence-based evaluations."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format=CSSEFIC1ToolOutput,
                temperature=self.openai_temperature
            )
            
            result = response.choices[0].message.parsed
            print(f"CSSEF C1 evaluation completed - Score: {result.score}")
            return result
            
        except Exception as e:
            print(f"Error in CSSEF C1 evaluation: {e}")
            return self._get_fallback_evaluation()
    
    def _create_evaluation_prompt(self, inputs: CSSEFIC1ToolInput) -> str:
        """Create the evaluation prompt for OpenAI"""
        
        # Calculate time constraints context
        duration_minutes = inputs.speech_duration / 60
        time_context = ""
        if duration_minutes < 3:
            time_context = "very short presentation (under 3 minutes)"
        elif duration_minutes < 7:
            time_context = "standard presentation (3-7 minutes)"
        else:
            time_context = "extended presentation (over 7 minutes)"
        
        return f"""
You are evaluating CSSEF Competency 1: "CHOOSES AND NARROWS A TOPIC APPROPRIATELY FOR THE AUDIENCE & OCCASION"

EVALUATION CRITERIA:
- EXCELLENT (5): Topic and focus are exceptionally appropriate for purpose, time constraints, and audience. Shows unusually insightful audience analysis.
- SATISFACTORY (3-4): Topic and focus are appropriate for purpose, time constraints, and audience. Shows adequate audience analysis.
- UNSATISFACTORY (1-2): Topic and focus are not appropriate for purpose, time constraints, or audience. Little/no evidence of audience analysis.

SPEECH DETAILS:
- Context: {inputs.context or 'General'}
- Duration: {duration_minutes:.1f} minutes ({time_context})
- Title: {inputs.speech_title or 'Not provided'}
- Stated Goal: {inputs.speech_goal or 'Not specified'}
- Target Audience: {inputs.audience_description or 'Not specified'}
- Key Points to Cover: {inputs.key_points or 'Not specified'}

TRANSCRIPT:
{inputs.transcript}

EVALUATION INSTRUCTIONS:
1. Analyze whether the topic is appropriate for:
   - The stated purpose/goal
   - The time constraints ({duration_minutes:.1f} minutes)
   - The target audience (if specified)
   - The speaking context ({inputs.context or 'general'})

2. Look for evidence of audience analysis in the content
3. Assess if the topic scope is well-narrowed for the time available
4. Identify specific examples from the transcript that support your evaluation

Provide your evaluation as a score (1-5), detailed justification with at least 2 specific examples from the transcript, and at least 2 concrete improvement suggestions.
"""
    
    def _get_fallback_evaluation(self) -> CSSEFIC1ToolOutput:
        """Return fallback evaluation when API fails"""
        return CSSEFIC1ToolOutput(
            score=3.0,
            justification="Unable to perform detailed evaluation due to technical issues. Topic appears generally appropriate for the context.",
            improvement_suggestions="Consider providing more specific audience analysis and ensure topic scope matches available time."
        )