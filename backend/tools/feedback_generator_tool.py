"""
FeedbackGeneratorTool: Generates structured feedback based on speech analysis.

This tool creates personalized feedback with strengths, issues, suggestions,
exercises, and motivational content based on the speaking context and analysis results.
Uses LLM to generate more personalized and context-aware feedback.
"""

import os
import json
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

    context_label: str = Field(
        ..., description="Speaking context (Academic, Persuasive, Storytelling, etc.)"
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
        "Academic": {
            "C1_topic_choice": 0.15,
            "C2_purpose": 0.15,
            "C3_supporting_material": 0.15,
            "C4_organization": 0.15,
            "C5_language_use": 0.10,
            "C6_vocal_variety": 0.10,
            "C7_pronunciation_and_grammar": 0.10,
            "C8_physical_behaviors": 0.10,
        },
        "Persuasive": {
            "C1_topic_choice": 0.10,
            "C2_purpose": 0.20,
            "C3_supporting_material": 0.20,
            "C4_organization": 0.15,
            "C5_language_use": 0.10,
            "C6_vocal_variety": 0.10,
            "C7_pronunciation_and_grammar": 0.10,
            "C8_physical_behaviors": 0.05,
        },
        "Storytelling": {
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
        context = inputs.context_label.lower()

        # Generate LLM-based feedback if transcript is available
        llm_feedback = None
        print("inputs:", inputs)
        if inputs.transcript:
            llm_feedback = self._generate_llm_feedback(inputs)

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

            # If no CSSEF evaluation, create a basic one with default values
            if not cssef_evaluation:
                # Get CSSEF competencies from loaded JSON or use defaults
                cssef_competencies = self.DEFAULT_CSSEF_CRITERIA
                if (
                    self.context_weights_data
                    and "CSSEF_COMPETENCIES" in self.context_weights_data
                ):
                    cssef_competencies = self.context_weights_data["CSSEF_COMPETENCIES"]

                for comp_id in cssef_competencies:
                    cssef_evaluation[comp_id] = CSSEFCriterionEvaluation(
                        score=5.0,
                        strengths=[f"No specific strengths identified for {comp_id}"],
                        improvements=[
                            f"Consider working on {cssef_competencies[comp_id].lower()}"
                        ],
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
            # If we don't have any strengths/issues/exercises, create from CSSEF evaluation
            if not strengths and cssef_evaluation:
                for criterion, eval_data in cssef_evaluation.items():
                    for strength in eval_data.strengths[
                        :1
                    ]:  # Take just the first strength per criterion
                        strengths.append(
                            FeedbackItem(
                                title=f"Strong {criterion}",
                                details=strength,
                                evidence=None,
                            )
                        )

            if not issues and cssef_evaluation:
                for criterion, eval_data in cssef_evaluation.items():
                    for improvement in eval_data.improvements[
                        :1
                    ]:  # Take just the first improvement per criterion
                        issues.append(
                            FeedbackItem(
                                title=f"Improve your {criterion}",
                                details=improvement,
                                evidence=None,
                            )
                        )

            if not exercises:
                # Create basic exercises based on lowest scoring CSSEF criteria
                sorted_criteria = sorted(
                    cssef_evaluation.items(), key=lambda x: x[1].score
                )

                for criterion, eval_data in sorted_criteria[
                    :2
                ]:  # Take 2 lowest scoring criteria
                    exercises.append(
                        Exercise(
                            title=f"{criterion} Improvement",
                            description=f"Practice focusing on {criterion.lower()} elements in your speech",
                            duration="10 minutes daily",
                            focus_area=criterion,
                        )
                    )

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
            context = inputs.context_label.capitalize()
            context_weights = {}
            if (
                self.context_weights_data
                and "CONTEXT_SCORES" in self.context_weights_data
            ):
                context_weights = self.context_weights_data["CONTEXT_SCORES"].get(
                    context, {}
                )

            context_specific_tips = []

            if context_weights:
                # Sort competencies by their weight in this context
                sorted_comps = sorted(
                    context_weights.items(), key=lambda x: x[1], reverse=True
                )
                # Add improvement tips from the most important competencies for this context
                for comp_id, weight in sorted_comps[
                    :3
                ]:  # Use the top 3 most important competencies
                    if (
                        comp_id in cssef_evaluation
                        and cssef_evaluation[comp_id].improvements
                    ):
                        context_specific_tips.append(
                            cssef_evaluation[comp_id].improvements[0]
                        )

            # If we couldn't get context-specific tips, use generic ones
            if not context_specific_tips:
                for criterion in cssef_evaluation:
                    if cssef_evaluation[criterion].improvements:
                        context_specific_tips.extend(
                            cssef_evaluation[criterion].improvements[:1]
                        )

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
        context = inputs.context_label.capitalize()

        # If context exists in context_scores, use those weights
        cssef_weights = {}
        if context in context_scores:
            cssef_weights = context_scores[context]
        # Otherwise use the default weights for "Academic" or fall back to equal weights
        else:
            cssef_weights = context_scores.get(
                "Academic", {k: 0.125 for k in cssef_competencies}
            )

        # Allow explicit overriding of weights if provided in input
        if inputs.cssef_weights:
            cssef_weights = inputs.cssef_weights

        # Format CSSEF weights for prompt
        cssef_weights_str = "\n".join(
            [
                f"- {comp} ({cssef_competencies.get(comp, comp)[:40]}...): {weight:.2f}"
                for comp, weight in cssef_weights.items()
            ]
        )

        # Prepare the prompt for LLM with CSSEF framework
        prompt = f"""
You are an expert public speaking coach using the Communication and Speaking Structure Evaluation Framework (CSSEF) to provide feedback.

CONTEXT: {inputs.context_label} presentation
SPEECH DURATION: {int(inputs.speech_duration // 60)} minutes {int(inputs.speech_duration % 60)} seconds
SPEAKING PACE: {inputs.words_per_minute:.1f} words per minute
FILLER WORD PERCENTAGE: {filler_analysis.get("filler_percentage")}%

{filler_analysis}

{prosody_details}

TRANSCRIPT:
{inputs.transcript[:2000]}

## CSSEF COMPETENCY WEIGHTS FOR {inputs.context_label.upper()} PRESENTATION:
{cssef_weights_str}

## CSSEF FRAMEWORK COMPETENCIES:
C1. TOPIC CHOICE: CHOOSES AND NARROWS A TOPIC APPROPRIATELY FOR THE AUDIENCE & OCCASION
C2. PURPOSE/THESIS: COMMUNICATES THE THESIS/SPECIFIC PURPOSE IN A MANNER APPROPRIATE FOR THE AUDIENCE & OCCASION
C3. SUPPORTING MATERIAL: PROVIDES SUPPORTING MATERIAL APPROPRIATE FOR THE AUDIENCE & OCCASION
C4. ORGANIZATION: USES AN ORGANIZATIONAL PATTERN APPROPRIATE TO THE TOPIC, AUDIENCE, OCCASION, & PURPOSE
C5. LANGUAGE USE: USES LANGUAGE APPROPRIATE TO THE AUDIENCE & OCCASION
C6. VOCAL VARIETY: USES VOCAL VARIETY IN RATE, PITCH, & INTENSITY TO HEIGHTEN & MAINTAIN INTEREST
C7. PRONUNCIATION & GRAMMAR: USES PRONUNCIATION, GRAMMAR, & ARTICULATION APPROPRIATE TO THE AUDIENCE & OCCASION
C8. PHYSICAL BEHAVIORS: USES PHYSICAL BEHAVIORS THAT SUPPORT THE VERBAL MESSAGE

Based on the transcript and analysis provided, evaluate the speech according to the CSSEF framework.
Focus your feedback on the criteria with higher weights for this context.

Provide the following:
1. A summary of overall performance (2-3 sentences)
2. For each CSSEF criterion:
   - Score (1-10)
   - Strengths identified
   - Areas for improvement
   - Specific examples from the transcript
3. Top 3-5 actionable suggestions prioritized based on CSSEF weights
4. A recommended version of a short excerpt from the speech showing improvements
5. Two specific exercises tailored to the highest priority improvement areas

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
            print("result:", result)
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
