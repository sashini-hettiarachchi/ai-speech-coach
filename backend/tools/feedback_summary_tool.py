"""
Feedback Summary Tool: Generate AI-powered feedback summary

This tool generates structured feedback summaries using AI, including:
- Overall summary of the speech performance
- Two key strengths identified from the speech
- Two specific improvement recommendations

Features:
- Uses OpenAI GPT-4o with structured outputs for reliable feedback generation
- Considers CSSEF competency scores and speech metrics
- Generates personalized feedback based on context and performance
- Compatible with Session model feedback_summary field
"""

import os
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from tools.base import BaseTool

# Import configuration
from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE


class FeedbackSummaryToolInput(BaseModel):
    """Input schema for Feedback Summary Tool"""

    cssef_scores: Dict[str, Dict[str, Any]] = Field(
        ..., description="CSSEF competency scores and feedback"
    )
    overall_score: float = Field(..., description="Overall performance score (1-5)")
    context: Optional[str] = Field(
        None, description="Speaking context for tailored feedback"
    )
    speech_duration: float = Field(..., description="Duration of speech in seconds")
    words_per_minute: float = Field(..., description="Speaking pace")
    filler_percentage: float = Field(..., description="Percentage of filler words")
    transcript: Optional[str] = Field(
        None, description="Speech transcript for content analysis"
    )
    speech_title: Optional[str] = Field(None, description="Title of the speech")
    speech_goal: Optional[str] = Field(None, description="Goal of the speech")


class StructuredFeedbackSummary(BaseModel):
    """Structured summary with overall summary, strengths and improvements"""

    summary: str = Field(..., description="Overall summary of the speech performance")
    strengths: List[str] = Field(
        ..., description="Two specific good things about the speech"
    )
    improvements: List[str] = Field(
        ..., description="Two specific points that should be improved"
    )


class FeedbackSummaryToolOutput(BaseModel):
    """Output schema for Feedback Summary Tool"""

    feedback_summary: StructuredFeedbackSummary = Field(
        ..., description="AI-generated structured feedback summary"
    )


class FeedbackSummaryTool(
    BaseTool[FeedbackSummaryToolInput, FeedbackSummaryToolOutput]
):
    """
    Tool for generating AI-powered feedback summaries

    Uses OpenAI to analyze speech performance data and generate personalized
    feedback including overall summary, strengths, and improvement suggestions.
    """

    name = "feedback_summary_tool"
    description = (
        "Generates AI-powered feedback summary with strengths and improvements"
    )

    InputSchema = FeedbackSummaryToolInput
    OutputSchema = FeedbackSummaryToolOutput

    def __init__(self):
        """Initialize the tool with OpenAI client"""
        try:
            from openai import OpenAI

            self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
            self.openai_model = OPENAI_MODEL
            self.openai_temperature = OPENAI_TEMPERATURE
            print("Feedback Summary Tool initialized successfully with OpenAI")
        except Exception as e:
            print(f"Warning: Failed to initialize OpenAI client: {e}")
            self.openai_client = None

    def run(self, inputs: FeedbackSummaryToolInput) -> FeedbackSummaryToolOutput:
        """
        Generate AI-powered feedback summary.

        Args:
            inputs: Feedback summary generation inputs

        Returns:
            Structured feedback summary output
        """
        if self.openai_client:
            feedback_summary = self._generate_ai_feedback_summary(inputs)
        else:
            print("OpenAI client not available, cannot generate feedback summary.")
            return FeedbackSummaryToolOutput(feedback_summary=None)
        return FeedbackSummaryToolOutput(feedback_summary=feedback_summary)

    def _generate_ai_feedback_summary(
        self, inputs: FeedbackSummaryToolInput
    ) -> StructuredFeedbackSummary:
        """Generate feedback summary using OpenAI"""

        # Prepare CSSEF scores summary for the prompt
        cssef_summary = []
        for competency, data in inputs.cssef_scores.items():
            if isinstance(data, dict):
                score = data.get("score", 3.0)
                comment = data.get("comment", "")
                improvement = data.get("improvement", "")
                cssef_summary.append(
                    f"- {competency.replace('_', ' ').title()}: {score}/5 - {comment}"
                )

        cssef_text = (
            "\n".join(cssef_summary) if cssef_summary else "No CSSEF scores available"
        )

        # Calculate performance metrics
        duration_minutes = inputs.speech_duration / 60
        performance_level = self._get_performance_level(inputs.overall_score)

        # Create comprehensive prompt for AI
        prompt = f"""
You are an expert public speaking coach providing feedback on a speech performance.

**SPEECH CONTEXT:**
- Type: {inputs.context or 'General'} presentation
- Title: {inputs.speech_title or 'N/A'}
- Goal: {inputs.speech_goal or 'N/A'}
- Duration: {duration_minutes:.1f} minutes
- Overall Score: {inputs.overall_score:.1f}/5 ({performance_level})

**PERFORMANCE METRICS:**
- Speaking pace: {inputs.words_per_minute:.1f} words per minute
- Filler words: {inputs.filler_percentage:.1f}% of speech
- Performance level: {performance_level}

**CSSEF COMPETENCY SCORES:**
{cssef_text}

**TRANSCRIPT SAMPLE:**
{inputs.transcript[:500] + '...' if inputs.transcript and len(inputs.transcript) > 500 else inputs.transcript or 'No transcript available'}

**TASK:**
Generate a comprehensive feedback summary with:

1. **Overall Summary (2-3 sentences)**: Describe the speaker's performance, mentioning the context, key strengths, and overall impression.

2. **Two Specific Strengths**: Identify two concrete positive aspects of the speech based on the CSSEF scores and performance data.

3. **Two Specific Improvements**: Provide two actionable improvement suggestions based on the weakest areas or areas with most potential for growth.

**GUIDELINES:**
- Be specific and constructive
- Reference actual performance data when possible
- Tailor feedback to the speech context and goals
- Focus on actionable advice for improvements
- Maintain an encouraging but honest tone
- Use the speaker's actual performance metrics in your assessment
"""

        try:
            response = self.openai_client.beta.chat.completions.parse(
                model=self.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert public speaking coach. Provide specific, constructive feedback based on performance data.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format=StructuredFeedbackSummary,
                temperature=self.openai_temperature,
            )

            feedback_data = response.choices[0].message.parsed
            print("Successfully generated AI feedback summary")
            return feedback_data

        except Exception as e:
            print(f"Error generating AI feedback: {e}")
            return self._generate_fallback_summary(inputs)

    def _get_performance_level(self, score: float) -> str:
        """Get performance level description from score"""
        if score >= 4.0:
            return "excellent"
        elif score > 2.0:
            return "satisfactory"
        else:
            return "unsatisfactory"
