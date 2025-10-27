"""
FeedbackGeneratorTool: Generates structured feedback based on speech analysis.

This tool creates personalized feedback with strengths, issues, suggestions,
exercises, and motivational content based on the speaking context and analysis results.
Uses LLM to generate more personalized and context-aware feedback.
"""

import os
import json
import re
import requests
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from tools.base import BaseTool

# Import configuration with fallback
try:
    from config import LLM_ENDPOINT, LLM_MODEL, LLM_TEMPERATURE
except ImportError:
    LLM_ENDPOINT = "http://localhost:11434/api/generate"
    LLM_MODEL = "llama3"
    LLM_TEMPERATURE = 0.3

# Import filler detector
from utils.filler_detector import count_filler_words


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


class CSSEFCriterionEvaluation(BaseModel):
    """Evaluation for a single CSSEF criterion"""

    score: float = Field(..., description="Score for this criterion (0-10)")
    strengths: List[str] = Field(
        default_factory=list, description="Strengths in this criterion"
    )
    improvements: List[str] = Field(
        default_factory=list, description="Areas to improve in this criterion"
    )


class LLMFeedbackSchema(BaseModel):
    """Schema for the LLM response"""

    summary: str = Field(
        ..., description="Brief summary of overall performance in 2-3 sentences"
    )
    cssef_evaluation: Dict[str, CSSEFCriterionEvaluation] = Field(
        default_factory=dict, description="Evaluation for each CSSEF criterion"
    )
    strengths: List[FeedbackItem] = Field(
        default_factory=list, description="Detailed breakdown of strengths"
    )
    issues: List[FeedbackItem] = Field(
        default_factory=list, description="Detailed breakdown of issues to address"
    )
    suggestions: List[str] = Field(
        default_factory=list, description="Actionable suggestions for improvement"
    )
    improved_excerpt: Optional[str] = Field(
        None, description="Recommended improved version of a speech excerpt"
    )
    exercises: List[Exercise] = Field(
        default_factory=list, description="Specific exercises to practice"
    )
    motivation: str = Field(
        ..., description="Motivational message tailored to the speaker's performance"
    )


class FeedbackGeneratorToolOutput(BaseModel):
    """Output schema for FeedbackGeneratorTool"""

    summary: str = Field(..., description="Brief summary of overall performance")
    cssef_evaluation: Dict[str, CSSEFCriterionEvaluation] = Field(
        default_factory=dict,
        description="Evaluation for each CSSEF criterion (Content, Structure, Style, Engagement, Fluency)",
    )
    strengths: List[FeedbackItem] = Field(
        default_factory=list, description="Detailed breakdown of strengths"
    )
    issues: List[FeedbackItem] = Field(
        default_factory=list, description="Detailed breakdown of issues to address"
    )
    suggestions: List[str] = Field(
        default_factory=list, description="Actionable suggestions for improvement"
    )
    improved_excerpt: Optional[str] = Field(
        None, description="Recommended improved version of a speech excerpt"
    )
    micro_exercises: List[Exercise] = Field(
        default_factory=list, description="Specific exercises to practice"
    )
    motivation: str = Field(
        ..., description="Motivational message tailored to the speaker's performance"
    )
    context_specific_tips: List[str] = Field(
        default_factory=list, description="Tips specific to the speaking context"
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
        """Initialize the FeedbackGeneratorTool with LLM config and context weights"""
        self.llm_endpoint = LLM_ENDPOINT
        self.llm_model = LLM_MODEL
        self.llm_temperature = LLM_TEMPERATURE

        # Load CSSEF competencies and weights from context_weights.json
        self.context_weights_data = self._load_context_weights()

    def _load_context_weights(self):
        """Load context weights from the JSON file"""
        weights_path = os.path.join(
            os.path.dirname(__file__), "../data/context_weights.json"
        )
        try:
            with open(weights_path, "r") as f:
                weights_data = json.load(f)
            print("Successfully loaded context weights data", weights_data)
            return weights_data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(
                f"Warning: Could not load context weights ({str(e)}). Using default weights."
            )
            return None

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
            if context == None:
                llm_feedback = self._generate_general_llm_feedback(inputs)
            else:
                llm_feedback = self._generate_llm_feedback(inputs)

        print("llm_feedback:....", llm_feedback)
        # If LLM feedback isn't available, generate a basic response
        if not llm_feedback:
            print(
                "No transcript provided or LLM feedback generation failed. Using basic feedback template."
            )
            # return self._generate_basic_feedback(inputs)
            return

        try:
            # Process CSSEF evaluation
            cssef_evaluation = {}
            if "cssef_evaluation" in llm_feedback:
                for criterion, eval_data in llm_feedback["cssef_evaluation"].items():
                    if isinstance(eval_data, dict):
                        try:
                            # Convert score to float and handle various formats
                            score = 5.0
                            if "score" in eval_data:
                                try:
                                    score = float(eval_data["score"])
                                except (ValueError, TypeError):
                                    score = 5.0

                            # Ensure strengths and improvements are lists
                            strengths = []
                            if "strengths" in eval_data:
                                if isinstance(eval_data["strengths"], list):
                                    strengths = eval_data["strengths"]
                                elif (
                                    isinstance(eval_data["strengths"], str)
                                    and eval_data["strengths"].strip()
                                ):
                                    strengths = [eval_data["strengths"]]

                            improvements = []
                            if "improvements" in eval_data:
                                if isinstance(eval_data["improvements"], list):
                                    improvements = eval_data["improvements"]
                                elif (
                                    isinstance(eval_data["improvements"], str)
                                    and eval_data["improvements"].strip()
                                ):
                                    improvements = [eval_data["improvements"]]

                            cssef_evaluation[criterion] = CSSEFCriterionEvaluation(
                                score=score,
                                strengths=strengths,
                                improvements=improvements,
                            )
                        except Exception as e:
                            print(f"Error processing evaluation for {criterion}: {e}")
                            # Add default evaluation for this criterion
                            cssef_evaluation[criterion] = CSSEFCriterionEvaluation(
                                score=5.0, strengths=[], improvements=[]
                            )

            # Process strengths
            strengths = []
            for strength in llm_feedback.get("strengths", []):
                try:
                    if isinstance(strength, dict):
                        strengths.append(
                            FeedbackItem(
                                title=strength.get("title", "Strength"),
                                details=strength.get("details", ""),
                                evidence=strength.get("evidence", None),
                            )
                        )
                    elif isinstance(strength, str) and strength.strip():
                        # Handle case where strength is just a string
                        strengths.append(
                            FeedbackItem(
                                title="Strength", details=strength, evidence=None
                            )
                        )
                except Exception as e:
                    print(f"Error processing strength: {e}")

            # Process issues
            issues = []
            for issue in llm_feedback.get("issues", []):
                try:
                    if isinstance(issue, dict):
                        issues.append(
                            FeedbackItem(
                                title=issue.get("title", "Area for Improvement"),
                                details=issue.get("details", ""),
                                evidence=issue.get("evidence", None),
                            )
                        )
                    elif isinstance(issue, str) and issue.strip():
                        # Handle case where issue is just a string
                        issues.append(
                            FeedbackItem(
                                title="Area for Improvement",
                                details=issue,
                                evidence=None,
                            )
                        )
                except Exception as e:
                    print(f"Error processing issue: {e}")

            # Process exercises
            exercises = []
            for exercise in llm_feedback.get("exercises", []):
                try:
                    if isinstance(exercise, dict):
                        # Ensure focus_area is properly formatted (no "and" expressions)
                        focus_area = exercise.get("focus_area", "C4_organization")
                        if isinstance(focus_area, str) and " and " in focus_area:
                            focus_area = focus_area.split(" and ")[0].strip()

                        exercises.append(
                            Exercise(
                                title=exercise.get("title", "Exercise"),
                                description=exercise.get("description", ""),
                                duration=exercise.get("duration", "5 minutes"),
                                focus_area=focus_area,
                            )
                        )
                    elif isinstance(exercise, str) and exercise.strip():
                        # Handle case where exercise is just a string
                        exercises.append(
                            Exercise(
                                title="Recommended Exercise",
                                description=exercise,
                                duration="5-10 minutes",
                                focus_area="C4_organization",
                            )
                        )
                except Exception as e:
                    print(f"Error processing exercise: {e}")

            # Extract other fields with defaults if missing
            summary = llm_feedback.get(
                "summary", f"Analysis of your {inputs.context_label} presentation"
            )

            # Handle suggestions - ensure they are strings
            suggestions = []
            for suggestion in llm_feedback.get(
                "suggestions", ["Practice more regularly", "Record yourself speaking"]
            ):
                if isinstance(suggestion, dict) and "title" in suggestion:
                    suggestions.append(suggestion["title"])
                elif isinstance(suggestion, dict) and "description" in suggestion:
                    suggestions.append(suggestion["description"])
                elif isinstance(suggestion, str):
                    suggestions.append(suggestion)

            # Handle improved_excerpt - could be string or object
            improved_excerpt = None
            raw_excerpt = llm_feedback.get("improved_excerpt")
            if isinstance(raw_excerpt, dict) and "text" in raw_excerpt:
                improved_excerpt = raw_excerpt["text"]
            elif isinstance(raw_excerpt, str):
                improved_excerpt = raw_excerpt

            motivation = llm_feedback.get(
                "motivation", "Keep practicing to improve your speaking skills!"
            )

            # Get context-specific tips based on the highest-weighted competencies for this context
            context_specific_tips = llm_feedback.get("context_specific_tips", [])

            return FeedbackGeneratorToolOutput(
                summary=summary,
                cssef_evaluation=cssef_evaluation,
                strengths=strengths,
                issues=issues,
                suggestions=suggestions,
                improved_excerpt=improved_excerpt,
                micro_exercises=exercises,
                motivation=motivation,
                context_specific_tips=context_specific_tips,
            )

        except Exception as e:
            print(f"Error processing feedback: {e}")
            # Fall back to basic feedback if anything goes wrong
            # return self._generate_basic_feedback(inputs)

    def _generate_general_llm_feedback(
        self, inputs: FeedbackGeneratorToolInput
    ) -> Dict:
        """
        Generate General feedback using LLM based on transcript, prosody results,
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

        # Prepare the prompt for LLM with CSSEF framework
        prompt = f"""
You are an expert public speaking coach and evaluator specializing in AI-driven feedback. 
You evaluate speeches according to the *Communication and Speaking Structure Evaluation Framework (CSSEF)* 
and *Toastmasters International* feedback principles.


SPEECH DURATION: {int(inputs.speech_duration // 60)} minutes {int(inputs.speech_duration % 60)} seconds
SPEAKING PACE: {inputs.words_per_minute:.1f} words per minute
FILLER WORD PERCENTAGE: {filler_analysis.get("filler_percentage")}%

## FILLER WORD ANALYSIS
{filler_analysis}

## AUDIO & PROSODY ANALYSIS

{prosody_details}
Examples of available metrics: pitch_mean, pitch_range, volume_stats, pause_events, speed_events, filler_words.

Interpret these to comment on:
- Vocal variety (C6)
- Fluency and pacing
- Pauses and expressiveness
- Clarity and pronunciation

TRANSCRIPT:
{inputs.transcript}


Feedback for high-weight competencies must include richer examples and actionable guidance.


## CSSEF COMPETENCIES
C1. Chooses and narrows a topic appropriately for the audience & occasion  
C2. Communicates the thesis/specific purpose appropriately for the audience & occasion  
C3. Provides supporting material appropriate for the audience & occasion  
C4. Uses an organizational pattern appropriate to the topic, audience, occasion, & purpose  
C5. Uses language appropriate to the audience & occasion  
C6. Uses vocal variety in rate, pitch, & intensity to heighten & maintain interest  
C7. Uses pronunciation, grammar, & articulation appropriate to the audience & occasion  
C8. Uses physical behaviors that support the verbal message 

Based on the transcript and analysis provided, evaluate the speech according to the CSSEF framework.


## YOUR TASK
Analyze the transcript and metrics to generate **feedback** according to CSSEF.

Your feedback must follow **Toastmasters principles**:
1. Begin with positive highlights.
2. Offer constructive suggestions for improvement.
3. End with an encouraging motivational note.

Provide the following:
1. A summary of overall performance (2-3 sentences)
2. For each CSSEF criterion:
   - Score (1-10)
   - Strengths identified
   - Areas for improvement
   - Specific examples from the transcript
3. Top 3-5 actionable suggestions
4. A recommended version of a short excerpt from the speech showing improvements
5. Two specific exercises

I need your response in structured JSON format with the following keys:
"summary", "cssef_evaluation", "strengths", "issues", "suggestions", "improved_excerpt", "exercises", "motivation"

IMPORTANT JSON FORMAT RULES:
1. For "cssef_evaluation", include each criterion as a key with an object containing "score" (number), "strengths" (array of strings), "improvements" (array of strings).
2. For "strengths" and "issues", each item should have "title", "details", and "criterion" fields.
3. For "criterion" fields, use exactly ONE criterion ID (e.g., "C1_topic_choice").
4. For "exercises", each item should have "title", "description", "duration", and "focus_area" fields.
5. Use empty arrays [] for lists with no items, not empty strings.
6. "improved_excerpt" should be a simple string, not an object.

Give response ONLY in the specified JSON format without any additional commentary or explanation.
"""
        print("prompt", prompt)
        # Call the LLM API with structured output format using Pydantic schema
        headers = {"Content-Type": "application/json"}
        data = {
            "model": self.llm_model,
            "prompt": prompt,
            "temperature": self.llm_temperature,
            "stream": False,
            "format": LLMFeedbackSchema.model_json_schema(),
        }

        try:
            response = requests.post(self.llm_endpoint, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            llm_response = result.get("response", "")
            print("LLM raw response:", llm_response)

            # Parse the LLM response using Pydantic model
            # Handle both dictionary and string responses from Ollama
            try:
                if isinstance(llm_response, dict):
                    # Response is already a dictionary - validate with Pydantic
                    feedback_data = LLMFeedbackSchema.model_validate(llm_response)
                    print("Successfully validated dictionary response with Pydantic")
                elif isinstance(llm_response, str):
                    # Response is a string - parse as JSON then validate
                    feedback_data = LLMFeedbackSchema.model_validate_json(llm_response)
                    print("Successfully validated string response with Pydantic")
                else:
                    raise ValueError(f"Unexpected response type: {type(llm_response)}")

                # Convert to dictionary for further processing
                llm_feedback = feedback_data.model_dump()
                print("Validated LLM response:", llm_feedback)
                return llm_feedback

            except (ValueError, TypeError) as e:
                print(f"Failed to validate LLM response: {e}")
                # Try to extract JSON from code blocks if needed
                if isinstance(llm_response, str):
                    # Try to find JSON content between code blocks
                    json_match = re.search(
                        r"```(?:json)?(.*?)```", llm_response, re.DOTALL
                    )
                    if json_match:
                        try:
                            json_str = json_match.group(1).strip()
                            feedback_data = LLMFeedbackSchema.model_validate_json(
                                json_str
                            )
                            llm_feedback = feedback_data.model_dump()
                            print(
                                "Successfully validated JSON from code block with Pydantic"
                            )
                            return llm_feedback
                        except Exception as e:
                            print(f"Failed to parse JSON from code block: {e}")

                # Create a basic feedback structure if all parsing attempts fail
                print("Using fallback feedback structure")
                return {
                    "summary": "The speaker's presentation needs improvement in several areas.",
                    "cssef_evaluation": {},
                    "strengths": [],
                    "issues": [],
                    "suggestions": [
                        "Practice more regularly",
                        "Focus on clear topic definition",
                    ],
                    "improved_excerpt": None,
                    "exercises": [],
                    "motivation": "Keep practicing to improve your speaking skills!",
                }

        except (requests.RequestException, KeyError) as e:
            print(f"Error calling LLM API: {e}")
            return None

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
You are an expert public speaking coach and evaluator specializing in AI-driven feedback.  
You evaluate speeches using the **Communication and Speaking Structure Evaluation Framework (CSSEF)**  
and **Toastmasters International** feedback principles.

---

## 🎯 SPEECH CONTEXT INFORMATION

- CONTEXT TYPE: {inputs.context_label} presentation  
- SPEECH TITLE: {inputs.speech_title or 'N/A'}  
- SPEECH GOAL: {inputs.speech_goal or 'N/A'}  
- AUDIENCE DESCRIPTION: {inputs.speech_audience_description or 'N/A'}  
- KEY POINTS: {inputs.speech_key_points or 'N/A'}  
- SELF-IMPROVEMENT GOAL: {inputs.speech_self_improvement_goal or 'N/A'}  

Use this contextual information to understand **what success means** for this specific speech.

When generating feedback:
- Always relate comments to the **title**, **goal**, **audience**, and **key points**.  
  Example: If the goal is “to inspire,” your feedback on purpose or delivery should discuss emotional connection.  
- Adjust tone and examples to fit the **audience type** (e.g., casual, academic, professional).  
- Connect all compliments, issues, and improvement areas to how well the speech achieved its stated goal.  

---

## 🧭 CSSEF COMPETENCY WEIGHTS (based on {inputs.context_label.upper()} context)
Use these weights to prioritize the **depth and emphasis** of your evaluation.  

{cssef_weights}

Weight guide:
- ≥0.20 → provide detailed, example-rich comments (3–4 sentences).  
- 0.15–0.19 → medium-depth comments (2–3 sentences).  
- ≤0.10 → brief mention or summary if relevant.

These weights define *which competencies matter most* for this context.  
For example:
- Academic → clarity, evidence, structure.  
- Persuasive → conviction, purpose, logical appeal.  
- Storytelling → emotional flow, language, vocal delivery.

---

## 🔊 AUDIO & PROSODY ANALYSIS
Speech Duration: {int(inputs.speech_duration // 60)} min {int(inputs.speech_duration % 60)} sec  
Speaking Pace: {inputs.words_per_minute:.1f} words per minute  
Filler Word %: {filler_analysis.get("filler_percentage")}%  

### Filler Word Analysis
{filler_analysis}

### Prosody Analysis
{prosody_details}

Interpret these values to comment on:
- **C6: Vocal Variety** — pitch, pace, and expressiveness.  
- **C7: Pronunciation & Grammar** — fluency, clarity, filler control.  
- **C4: Organization** — use of pauses or pacing to separate ideas.

Highlight where (in transcript time or phrasing) improvements could occur.

---

## 🧩 TRANSCRIPT
{inputs.transcript}

Use the transcript to:
- Identify story structure (opening, conflict, resolution, takeaway).  
- Compare to **key points** and evaluate alignment with the **stated goal**.  
- Locate disjointed transitions or unclear segments and suggest improvements.  
- Use prosody or pause timing to reference *when* improvements apply (e.g., “after the phrase ‘I love my cat…’ pause for emotional effect”).

---

## 🧩 CSSEF COMPETENCIES

C1. Chooses and narrows a topic appropriately for the audience & occasion  
C2. Communicates the thesis/specific purpose appropriately for the audience & occasion  
C3. Provides supporting material appropriate for the audience & occasion  
C4. Uses an organizational pattern appropriate to the topic, audience, occasion, & purpose  
C5. Uses language appropriate to the audience & occasion  
C6. Uses vocal variety in rate, pitch, & intensity to heighten & maintain interest  
C7. Uses pronunciation, grammar, & articulation appropriate to the audience & occasion  
C8. Uses physical behaviors that support the verbal message  

---

## 🧭 ANALYSIS STRATEGY

1. Evaluate how well the **speech achieves its goal** for the **intended audience**.  
2. Cross-reference **transcript structure** with the **key points** provided by the speaker.  
3. Use **prosody & filler data** to identify where delivery aids or distracts from the message.  
4. Apply **context-specific weights** to guide how much depth you devote to each competency.  
5. Tailor **feedback tone and content** to the speech’s **title**, **goal**, and **audience** — make it sound personally relevant.  
6. Follow the **Toastmasters evaluation model**:  
   - Start with positive highlights.  
   - Offer detailed, actionable improvement points.  
   - End with an encouraging, motivational summary aligned with the speaker’s goal.

---

## 🧱 REQUIRED JSON OUTPUT FORMAT
Respond **only** in valid JSON. No extra text, markdown, or commentary.

{{
  "summary": "2–3 sentence overall summary of the speech performance, clearly tied to the speech goal, title, and audience.",
  "cssef_evaluation": {{
    "C1_topic_choice": {{ "score": 1–10, "strengths": [], "improvements": [] }},
    "C2_purpose": {{ "score": 1–10, "strengths": [], "improvements": [] }},
    "C3_supporting_material": {{ "score": 1–10, "strengths": [], "improvements": [] }},
    "C4_organization": {{ "score": 1–10, "strengths": [], "improvements": [] }},
    "C5_language_use": {{ "score": 1–10, "strengths": [], "improvements": [] }},
    "C6_vocal_variety": {{ "score": 1–10, "strengths": [], "improvements": [] }},
    "C7_pronunciation_and_grammar": {{ "score": 1–10, "strengths": [], "improvements": [] }},
    "C8_physical_behaviors": {{ "score": 1–10, "strengths": [], "improvements": [] }}
  }},
  "strengths": [
    {{ "title": "Descriptive storytelling", "details": "Strong emotional connection aligned with goal ‘to inspire.’", "criterion": "C5_language_use" }}
  ],
  "issues": [
    {{ "title": "Unclear message transition", "details": "Between key points 1 and 2, connection to goal ‘to inspire joy’ could be clearer.", "criterion": "C4_organization" }}
  ],
  "suggestions": [
    "Add a reflective transition after describing your cat’s playfulness to link it back to your goal of finding joy in small moments."
  ],
  "improved_excerpt": "Example revised version of a key excerpt aligned with goal and audience.",
  "exercises": [
    {{ "title": "Pause & Emphasis Drill", "description": "Practice inserting 1-second pauses after emotional sentences to enhance impact.", "duration": "10 minutes", "focus_area": "C6_vocal_variety" }}
  ],
  "context_specific_tips": [
    "In storytelling, connect your personal experience directly to a universal lesson to engage listeners emotionally."
  ],
  "motivation": "Encouraging message tied to the speaker’s goal and title, e.g., 'Your story about your cat beautifully captures joy — keep refining your pacing to make it shine.'"
}}

---

## ⚙️ EVALUATION RULES
- **Tailor all feedback components** — summary, strengths, issues, suggestions, tips, and motivation — using the **speech title**, **goal**, **audience**, and **key points**.
- Always connect improvements to *where and how* they occur in the **transcript**.  
- Use **prosody data** to reinforce feedback on pacing, emotion, or clarity.
- Maintain a **constructive, positive coaching tone**.

"""
        print("prompt", prompt)
        # Call the LLM API with structured output format using Pydantic schema
        headers = {"Content-Type": "application/json"}
        data = {
            "model": self.llm_model,
            "prompt": prompt,
            "temperature": self.llm_temperature,
            "stream": False,
            "format": LLMFeedbackSchema.model_json_schema(),
        }

        try:
            response = requests.post(self.llm_endpoint, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            llm_response = result.get("response", "")

            # Parse the LLM response using Pydantic model
            # Handle both dictionary and string responses from Ollama
            try:
                if isinstance(llm_response, dict):
                    # Response is already a dictionary - validate with Pydantic
                    feedback_data = LLMFeedbackSchema.model_validate(llm_response)
                    print("Successfully validated dictionary response with Pydantic")
                elif isinstance(llm_response, str):
                    # Response is a string - parse as JSON then validate
                    feedback_data = LLMFeedbackSchema.model_validate_json(llm_response)
                    print("Successfully validated string response with Pydantic")
                else:
                    raise ValueError(f"Unexpected response type: {type(llm_response)}")

                # Convert to dictionary for further processing
                llm_feedback = feedback_data.model_dump()
                print("Validated LLM response:", llm_feedback)
                return llm_feedback

            except (ValueError, TypeError) as e:
                print(f"Failed to validate LLM response: {e}")
                # Try to extract JSON from code blocks if needed
                if isinstance(llm_response, str):
                    # Try to find JSON content between code blocks
                    json_match = re.search(
                        r"```(?:json)?(.*?)```", llm_response, re.DOTALL
                    )
                    if json_match:
                        try:
                            json_str = json_match.group(1).strip()
                            feedback_data = LLMFeedbackSchema.model_validate_json(
                                json_str
                            )
                            llm_feedback = feedback_data.model_dump()
                            print(
                                "Successfully validated JSON from code block with Pydantic"
                            )
                            return llm_feedback
                        except Exception as e:
                            print(f"Failed to parse JSON from code block: {e}")

                # Create a basic feedback structure if all parsing attempts fail
                print("Using fallback feedback structure")
                return {
                    "summary": "The speaker's presentation needs improvement in several areas.",
                    "cssef_evaluation": {},
                    "strengths": [],
                    "issues": [],
                    "suggestions": [
                        "Practice more regularly",
                        "Focus on clear topic definition",
                    ],
                    "improved_excerpt": None,
                    "exercises": [],
                    "motivation": "Keep practicing to improve your speaking skills!",
                }

        except (requests.RequestException, KeyError) as e:
            print(f"Error calling LLM API: {e}")
            return None
