"""
FeedbackGeneratorTool: Generates structured feedback based on speech analysis.

This tool creates personalized feedback with strengths, issues, suggestions,
exercises, and motivational content based on the speaking context and analysis results.
Uses OpenAI GPT-4o with structured outputs for reliable feedback generation.
"""

import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from utils.constants import CONTEXT_DATA
from tools.base import BaseTool

# Import configuration
from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE


class FeedbackGeneratorToolInput(BaseModel):
    """Input schema for FeedbackGeneratorTool"""

    context_label: Optional[str] = Field(
        None, description="Speaking context (Academic, Persuasive, Storytelling, etc.)"
    )

    speech_duration: float = Field(..., description="Duration of speech in seconds")

    words_per_minute: float = Field(
        ..., description="Speaking pace in words per minute"
    )
    transcript: Optional[str] = Field(
        None,
        description="Transcription of the speech content for LLM-based feedback generation",
    )
    filler_analysis: Optional[Dict[str, Any]] = Field(
        None, description="Detailed analysis of filler words from filler_detector"
    )
    prosody_results: Optional[Dict[str, Any]] = Field(
        None,
        description="Results from audio prosody analysis containing pitch, volume and pace data",
    )
    cssef_weights: Optional[Dict[str, float]] = Field(
        None, description="Weights for each CSSEF criterion based on speaking context"
    )
    speech_title: Optional[str] = Field(None, description="Title of the speech")
    speech_goal: Optional[str] = Field(None, description="Goal of the speech")
    speech_audience_description: Optional[str] = Field(
        None, description="Description of the audience for the speech"
    )
    speech_key_points: Optional[str] = Field(
        None, description="Key points of the speech"
    )
    speech_self_improvement_goal: Optional[str] = Field(
        None, description="Self-improvement goal for the speech"
    )


class FeedbackItem(BaseModel):
    """Schema for a specific feedback item"""

    title: str = Field(..., description="Short title/heading for this feedback")
    details: str = Field(..., description="Detailed explanation of the feedback")
    evidence: Optional[str] = Field(None, description="Specific evidence or examples")
    criterion: Optional[str] = Field(
        None, description="The CSSEF criterion this feedback relates to"
    )


class Exercise(BaseModel):
    """Schema for a practice exercise"""

    title: str = Field(..., description="Name of the exercise")
    description: str = Field(..., description="How to perform the exercise")
    duration: str = Field(..., description="Recommended duration/repetitions")
    focus_area: str = Field(..., description="Which skill this targets")


class CSSEFCompetencyEvaluation(BaseModel):
    """Evaluation for a single CSSEF competency"""

    score: float = Field(..., description="Score for this competency (1-5 scale)")
    comment: str = Field(..., description="Brief comment explaining the score reason")
    improvement: str = Field(
        ..., description="One specific point on how to improve this competency"
    )


class StructuredFeedbackSummary(BaseModel):
    """Structured summary with strengths and improvements"""

    strengths: List[str] = Field(..., description="Two good things about the speech")
    improvements: List[str] = Field(
        ..., description="Two points that should be improved"
    )


class LLMFeedbackSchema(BaseModel):
    """Schema for the LLM response"""

    revised_speech_text: str = Field(
        ..., description="Improved version of the speech incorporating all suggestions"
    )
    summary: StructuredFeedbackSummary = Field(
        ..., description="Structured summary with 2 strengths and 2 improvements"
    )
    cssef_evaluation: Optional[Dict[str, CSSEFCompetencyEvaluation]] = Field(
        None, description="Evaluation for each CSSEF competency (C1-C7)"
    )


class FeedbackGeneratorToolOutput(BaseModel):
    """Output schema for FeedbackGeneratorTool"""

    revised_speech_text: str = Field(..., description="Improved version of the speech")
    summary: StructuredFeedbackSummary = Field(
        ..., description="Structured summary with 2 strengths and 2 improvements"
    )
    cssef_evaluation: Optional[Dict[str, CSSEFCompetencyEvaluation]] = Field(
        None,
        description="Evaluation for each CSSEF competency (C1-C7) with score, comment, and improvement",
    )


class FeedbackGeneratorTool(
    BaseTool[FeedbackGeneratorToolInput, FeedbackGeneratorToolOutput]
):
    """
    Tool for generating structured feedback based on speech analysis using CSSEF criteria.

    The Communication and Speaking Structure Evaluation Framework (CSSEF) evaluates:
    - Content: Relevance, accuracy, depth, and value of the information
    - Structure: Organization, logical flow, transitions, and coherence
    - Style: Delivery approach, vocal variety, body language, and aids
    - Engagement: Audience connection, interaction, and maintaining interest
    - Fluency: Smoothness, handling of filler words, and confidence

    Uses LLM to generate personalized feedback based on these criteria,
    weighted according to the speaking context.
    """

    name = "feedback_generator_tool"
    description = "Generates structured feedback based on CSSEF criteria using LLM"

    # Define schemas for type checking
    InputSchema = FeedbackGeneratorToolInput
    OutputSchema = FeedbackGeneratorToolOutput

    def __init__(self):
        """Initialize the FeedbackGeneratorTool with OpenAI client"""
        try:
            from openai import OpenAI
            self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
            self.openai_model = OPENAI_MODEL
            self.openai_temperature = OPENAI_TEMPERATURE
            print("OpenAI client initialized successfully for feedback generation")
        except Exception as e:
            print(f"Warning: Failed to initialize OpenAI client: {e}")
            self.openai_client = None

        # Load CSSEF competencies and weights from context_weights.json
        self.context_weights_data = CONTEXT_DATA



    # Default CSSEF criteria descriptions (fallback if JSON can't be loaded)
    DEFAULT_CSSEF_CRITERIA = {
        "C1_topic_choice": "CHOOSES AND NARROWS A TOPIC APPROPRIATELY FOR THE AUDIENCE & OCCASION",
        "C2_purpose": "COMMUNICATES THE THESIS/SPECIFIC PURPOSE IN A MANNER APPROPRIATE FOR THE AUDIENCE & OCCASION",
        "C3_supporting_material": "PROVIDES SUPPORTING MATERIAL APPROPRIATE FOR THE AUDIENCE & OCCASION",
        "C4_organization": "USES AN ORGANIZATIONAL PATTERN APPROPRIATE TO THE TOPIC, AUDIENCE, OCCASION, & PURPOSE",
        "C5_language_use": "USES LANGUAGE APPROPRIATE TO THE AUDIENCE & OCCASION",
        "C6_vocal_variety": "USES VOCAL VARIETY IN RATE, PITCH, & INTENSITY TO HEIGHTEN & MAINTAIN INTEREST",
        "C7_pronunciation_and_grammar": "USES PRONUNCIATION, GRAMMAR, & ARTICULATION APPROPRIATE TO THE AUDIENCE & OCCASION",
        "C8_physical_behaviors": "USES PHYSICAL BEHAVIORS THAT SUPPORT THE VERBAL MESSAGE",
    }

    # Default context-specific CSSEF weights (fallback if JSON can't be loaded)
    DEFAULT_CONTEXT_SCORES = {
        "academic": {
            "C1_topic_choice": 0.15,
            "C2_purpose": 0.15,
            "C3_supporting_material": 0.15,
            "C4_organization": 0.15,
            "C5_language_use": 0.10,
            "C6_vocal_variety": 0.10,
            "C7_pronunciation_and_grammar": 0.10,
            "C8_physical_behaviors": 0.10,
        },
        "persuasive": {
            "C1_topic_choice": 0.10,
            "C2_purpose": 0.20,
            "C3_supporting_material": 0.20,
            "C4_organization": 0.15,
            "C5_language_use": 0.10,
            "C6_vocal_variety": 0.10,
            "C7_pronunciation_and_grammar": 0.10,
            "C8_physical_behaviors": 0.05,
        },
        "storytelling": {
            "C1_topic_choice": 0.10,
            "C2_purpose": 0.10,
            "C3_supporting_material": 0.20,
            "C4_organization": 0.20,
            "C5_language_use": 0.15,
            "C6_vocal_variety": 0.10,
            "C7_pronunciation_and_grammar": 0.10,
            "C8_physical_behaviors": 0.05,
        },
    }

    def run(self, inputs: FeedbackGeneratorToolInput) -> FeedbackGeneratorToolOutput:
        """
        Generate structured feedback based on speech analysis using CSSEF criteria.

        Args:
            inputs (FeedbackGeneratorToolInput): Input parameters with analysis results

        Returns:
            FeedbackGeneratorToolOutput: Structured feedback based on CSSEF evaluation
        """
        # Normalize context label
        context = None
        if inputs.context_label:
            context = inputs.context_label.strip().lower()

        # Generate LLM-based feedback if transcript is available
        llm_feedback = None
        print("inputs:", inputs)
        if inputs.transcript:
            llm_feedback = self._generate_llm_feedback(inputs)
            # if context == None:
            #     llm_feedback = self._generate_general_llm_feedback(inputs)
            # else:
            #     llm_feedback = self._generate_llm_feedback(inputs)

        print("llm_feedback:....", llm_feedback)
        # If LLM feedback isn't available, generate a basic response
        if not llm_feedback:
            print(
                "No transcript provided or LLM feedback generation failed. Using basic feedback template."
            )
            # return self._generate_basic_feedback(inputs)
            return

        try:
            # Extract the simplified response components
            revised_speech_text = llm_feedback.get(
                "revised_speech_text", "No revised speech text provided"
            )

            # Process summary
            summary_data = llm_feedback.get("summary", {})
            if isinstance(summary_data, dict):
                summary = StructuredFeedbackSummary(
                    strengths=summary_data.get("strengths", []),
                    improvements=summary_data.get("improvements", []),
                )
            else:
                # Fallback if summary is not structured
                summary = StructuredFeedbackSummary(
                    strengths=["Good overall presentation"],
                    improvements=["Practice more regularly"],
                )

            # Process CSSEF evaluation
            cssef_evaluation = {}
            if "cssef_evaluation" in llm_feedback and llm_feedback["cssef_evaluation"]:
                for criterion, eval_data in llm_feedback["cssef_evaluation"].items():
                    if isinstance(eval_data, dict):
                        try:
                            # Convert score to float and handle various formats
                            score = 3.0
                            if "score" in eval_data:
                                try:
                                    score = float(eval_data["score"])
                                except (ValueError, TypeError):
                                    score = 3.0

                            # Get comment and improvement strings
                            comment = eval_data.get("comment", "Good performance")
                            improvement = eval_data.get(
                                "improvement", "Keep practicing"
                            )

                            cssef_evaluation[criterion] = CSSEFCompetencyEvaluation(
                                score=score, comment=comment, improvement=improvement
                            )
                        except Exception as e:
                            print(f"Error processing evaluation for {criterion}: {e}")
                            # Add default evaluation for this criterion
                            cssef_evaluation[criterion] = CSSEFCompetencyEvaluation(
                                score=3.0,
                                comment="Good performance",
                                improvement="Keep practicing",
                            )

            return FeedbackGeneratorToolOutput(
                revised_speech_text=revised_speech_text,
                summary=summary,
                cssef_evaluation=cssef_evaluation or None,
            )

        except Exception as e:
            print(f"Error processing feedback: {e}")
            # Fall back to basic feedback if anything goes wrong
            return FeedbackGeneratorToolOutput(
                revised_speech_text="Keep practicing to improve your speech",
                summary=StructuredFeedbackSummary(
                    strengths=["Good effort"], improvements=["Practice more regularly"]
                ),
                cssef_evaluation={},
            )

    def _generate_llm_feedback(self, inputs: FeedbackGeneratorToolInput) -> Dict:
        """
        Generate personalized feedback using LLM based on transcript, prosody results,
        context, and CSSEF criteria weights.

        Args:
            inputs: FeedbackGeneratorToolInput containing transcript and analysis data

        Returns:
            Dict containing LLM-generated feedback sections based on CSSEF framework
        """
        if not inputs.transcript:
            return None

        # Get detailed filler analysis if not already provided
        filler_analysis = inputs.filler_analysis
        # if not filler_analysis and inputs.transcript:
        # filler_analysis = self._analyze_filler_words(inputs.transcript)
        print("Filler analysis:", filler_analysis)
        print(
            "Filler analysis: percentage", filler_analysis.get("filler_percentage", 0.0)
        )

        prosody_details = ""
        if inputs.prosody_results:
            prosody = inputs.prosody_results
            pitch_data = prosody.get("pitch", {})
            volume_data = prosody.get("volume", {})

            prosody_details = f"""
PROSODY ANALYSIS:
- Pitch variation: {pitch_data.get('std', 'N/A')} Hz (std deviation)
- Volume variation: {volume_data.get('std', 'N/A')} dB (std deviation)
- Pauses: {prosody.get('pause_count', 'N/A')} detected pauses
- Average pause duration: {prosody.get('average_pause_duration', 'N/A')} seconds
"""

        # Get CSSEF competencies and context weights from the loaded JSON file or use defaults
        cssef_competencies = self.DEFAULT_CSSEF_CRITERIA
        context_scores = self.DEFAULT_CONTEXT_SCORES

        if self.context_weights_data:
            cssef_competencies = self.context_weights_data.get(
                "CSSEF_COMPETENCIES", self.DEFAULT_CSSEF_CRITERIA
            )
            context_scores = self.context_weights_data.get(
                "CONTEXT_SCORES", self.DEFAULT_CONTEXT_SCORES
            )

        # Get the appropriate weights for the given context
        context = inputs.context_label.lower() if inputs.context_label else None

        # If context exists in context_scores, use those weights
        cssef_weights = {}
        if context and context in context_scores:
            print("context:", context)
            cssef_weights = context_scores[context]
            print("weights", cssef_weights)

        print(f"Using CSSEF weights for context '{context}': {cssef_weights}")

        # Prepare the prompt for LLM with CSSEF framework
        prompt = f"""
You are an expert **Public Speaking Coach and Evaluator** trained in the **Competent Speaker Speech Evaluation Form (CSSEF)** and **Toastmasters International** standards.

Your goal is to generate **highly specific, context-aware feedback** in valid JSON format.

---

### 🎯 SPEECH CONTEXT
- CONTEXT TYPE: {inputs.context_label or 'general'} presentation
- TITLE: {inputs.speech_title or 'N/A'}
- GOAL: {inputs.speech_goal or 'N/A'}
- AUDIENCE: {inputs.speech_audience_description or 'N/A'}
- KEY POINTS: {inputs.speech_key_points or 'N/A'}
- SELF-IMPROVEMENT GOAL: {inputs.speech_self_improvement_goal or 'N/A'}

Interpret “success” based on how well the speech meets its GOAL for this AUDIENCE.

---

### 🧮 CSSEF CONTEXT WEIGHTS
{cssef_weights}

Use weights to **prioritize comment depth**:
- ≥0.20 → detailed, 3–4 sentences
- 0.15–0.19 → medium, 2–3 sentences
- ≤0.10 → short, 1 sentence

---

### 🔊 DELIVERY ANALYSIS
- Duration: {int(inputs.speech_duration // 60)} min {int(inputs.speech_duration % 60)} sec
- Speaking Pace: {inputs.words_per_minute:.1f} WPM
- Filler Word %: {filler_analysis.get("filler_percentage", 0.0) if filler_analysis else 0.0}%
- Filler Details: {filler_analysis if filler_analysis else 'N/A'}
- Prosody Summary: {prosody_details}

Use this to evaluate:
- **C6 (Vocal Variety)** — pitch, pace, emotion
- **C7 (Pronunciation & Grammar)** — filler words, clarity, articulation
- **C4 (Organization)** — pauses for transitions

---

### 📜 TRANSCRIPT
{inputs.transcript[:2000]}   # Truncate long transcripts safely

Focus on:
- Logical flow (intro–body–conclusion)
- Alignment with key points and goal
- Evidence/supporting material
- Language tone and clarity

---

### 📋 SCORING RUBRIC (1–5)
1 = Poor / absent
2 = Weak or inconsistent
3 = Adequate / average
4 = Good / strong
5 = Excellent / exemplary

---

### 🧭 OUTPUT STRUCTURE
Respond ONLY in JSON:
{{
  "revised_speech_text": "Improved, more fluent version of the speech keeping the speaker’s voice",
  "summary": {{
    "summary": "1–2 sentence general overview of performance",
    "strengths": ["Two specific strengths"],
    "improvements": ["Two specific improvement suggestions"]
  }},
  "cssef_evaluation": {{
    "C1_topic_choice": {{"score": float, "comment": "Specific reason (context-aware)", "improvement": "How to fix"}},
    "C2_purpose": {{"score": float, "comment": "...", "improvement": "..."}},
    "C3_supporting_material": {{"score": float, "comment": "...", "improvement": "..."}},
    "C4_organization": {{"score": float, "comment": "...", "improvement": "..."}},
    "C5_language_use": {{"score": float, "comment": "...", "improvement": "..."}},
    "C6_vocal_variety": {{"score": float, "comment": "Based on prosody/filler metrics", "improvement": "..." }},
    "C7_pronunciation_and_grammar": {{"score": float, "comment": "Based on filler or clarity issues", "improvement": "..." }}
  }}
}}

---

### 🧩 EXAMPLE OF HIGH-QUALITY COMMENTS
Example good comment for C3 (Supporting Material, Persuasive):
- comment: "You gave emotional appeals but lacked specific data. In persuasive speeches, statistics or expert quotes would increase credibility."
- improvement: "Add one factual example or study to support your main argument."

---

### ⚙️ STYLE REQUIREMENTS
- Reference the **goal** and **audience** in at least two competency comments.
- When giving improvements, always say *what to do* (e.g., “Add an example of…” or “Pause longer after…”).
- Keep tone supportive but professional.
- Do not invent unrelated details.
- Output **only JSON**, nothing else.
"""

        print("prompt", prompt)

        # Use OpenAI for feedback generation
        if self.openai_client:
            return self._call_openai_api(prompt)
        else:
            print("OpenAI client not available")
            return None

    def _call_openai_api(self, prompt: str) -> Dict:
        """Call OpenAI API for feedback generation using structured outputs"""
        try:
            response = self.openai_client.beta.chat.completions.parse(
                model=self.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert public speaking coach. Provide detailed feedback based on CSSEF criteria.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format=LLMFeedbackSchema,
                temperature=self.openai_temperature,
            )

            feedback_data = response.choices[0].message.parsed
            llm_feedback = feedback_data.model_dump()
            print("Successfully generated OpenAI feedback with structured outputs")
            return llm_feedback

        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return self._get_fallback_feedback()

    def _get_fallback_feedback(self) -> Dict:
        """Return a basic feedback structure when API calls fail"""
        return {
            "revised_speech_text": "Keep practicing to improve your speech delivery.",
            "summary": {
                "strengths": ["Good effort in presenting"],
                "improvements": ["Practice more regularly", "Focus on clear delivery"]
            },
            "cssef_evaluation": {
                "C1_topic_choice": {
                    "score": 3.0,
                    "comment": "Topic was appropriate",
                    "improvement": "Consider narrowing focus for better impact"
                },
                "C2_purpose": {
                    "score": 3.0,
                    "comment": "Purpose was communicated",
                    "improvement": "Make purpose statement clearer"
                }
            }
        }
