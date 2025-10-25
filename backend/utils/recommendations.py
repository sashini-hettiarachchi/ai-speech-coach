import requests
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# Import configuration with fallback
try:
    from config import LLM_ENDPOINT, LLM_MODEL, LLM_TEMPERATURE
except ImportError:
    LLM_ENDPOINT = "http://localhost:11434/api/generate"
    LLM_MODEL = "llama3"
    LLM_TEMPERATURE = 0.3


class FeedbackItem(BaseModel):
    """Schema for a specific feedback item"""
    title: str = Field(..., description="Short title/heading for this feedback")
    details: str = Field(..., description="Detailed explanation of the feedback")
    evidence: Optional[str] = Field(None, description="Specific evidence or examples")
    criterion: Optional[str] = Field(
        None, description="The criterion this feedback relates to"
    )


class Exercise(BaseModel):
    """Schema for a practice exercise"""
    title: str = Field(..., description="Name of the exercise")
    description: str = Field(..., description="How to perform the exercise")
    duration: str = Field(..., description="Recommended duration/repetitions")
    focus_area: str = Field(..., description="Which skill this targets")


class CriterionEvaluation(BaseModel):
    """Evaluation for a single criterion"""
    score: float = Field(..., description="Score for this criterion (0-10)")
    strengths: List[str] = Field(
        default_factory=list, description="Strengths in this criterion"
    )
    improvements: List[str] = Field(
        default_factory=list, description="Areas to improve in this criterion"
    )

class CSSEFCriterionEvaluation(BaseModel):
    """Evaluation for a single CSSEF criterion"""

    score: float = Field(..., description="Score for this criterion (0-10)")
    strengths: List[str] = Field(
        default_factory=list, description="Strengths in this criterion"
    )
    improvements: List[str] = Field(
        default_factory=list, description="Areas to improve in this criterion"
    )

class GeneralFeedbackSchema(BaseModel):
    """Schema for general feedback response"""
    summary: str = Field(
        ..., description="Brief summary of overall performance in 2-3 sentences"
    )
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
    exercises: List[Exercise] = Field(
        default_factory=list, description="Specific exercises to practice"
    )
    motivation: str = Field(
        ..., description="Motivational message tailored to the speaker's performance"
    )


def give_recommendations(transcript, prosody_result=None, filler_analysis=None):
    """
    Generate general recommendations for speech improvement without context-awareness.
    Returns structured feedback similar to the context-aware feedback generator.
    """
    
    # Prepare prosody details if available
    prosody_details = ""
    if prosody_result:
        try:
            prosody_details = f"""
## AUDIO & PROSODY ANALYSIS
Speaking pace: {prosody_result.get('words_per_minute', 'N/A')} words per minute
Pitch statistics: Mean={prosody_result.get('pitch_mean', 'N/A')}Hz, Std={prosody_result.get('pitch_std', 'N/A')}Hz
Volume statistics: Mean={prosody_result.get('volume_mean', 'N/A')}dB, Std={prosody_result.get('volume_std', 'N/A')}dB
Pause events: {len(prosody_result.get('pause_events', []))} pauses detected
Speed variations: {len(prosody_result.get('speed_events', []))} speed changes detected
"""
        except:
            prosody_details = "## AUDIO & PROSODY ANALYSIS\nBasic prosody data available"
    
    # Prepare filler analysis if available
    filler_details = ""
    if filler_analysis:
        try:
            filler_details = f"""
## FILLER WORD ANALYSIS
Total filler words: {filler_analysis.get('total_fillers', 0)}
Filler percentage: {filler_analysis.get('filler_percentage', 0):.1f}%
Detected fillers: {', '.join(filler_analysis.get('fillers', {}).keys())}
"""
        except:
            filler_details = "## FILLER WORD ANALYSIS\nBasic filler analysis available"

    # Create the prompt for general feedback
    prompt = f"""
You are an expert public speaking coach providing general feedback on speech performance.
Analyze the transcript and provide structured, actionable feedback focusing on universal speaking principles.

{prosody_details}
{filler_details}

TRANSCRIPT:
{transcript[:2000]}

## GENERAL SPEAKING CRITERIA
Evaluate the speech based on these universal criteria:
1. Content Quality - Clarity, relevance, and value of information
2. Organization - Logical structure and flow
3. Language Use - Appropriate word choice and grammar
4. Delivery - Vocal variety and pacing
5. Clarity - Pronunciation and articulation

## YOUR TASK
Analyze the transcript and provide general feedback focusing on fundamental speaking skills.
Follow these principles:
1. Begin with positive highlights
2. Offer constructive suggestions for improvement
3. End with encouraging motivation

Provide the following in JSON format:
1. A summary of overall performance (2-3 sentences)
2. For each general criterion:
   - Score (1-10)
   - Strengths identified
   - Areas for improvement
3. Top 3-5 actionable suggestions
4. A recommended improved version of a short excerpt
5. Two specific exercises for improvement

IMPORTANT JSON FORMAT RULES:
1. For "general_evaluation", include each criterion as a key with "score" (number), "strengths" (array), "improvements" (array)
2. For "strengths" and "issues", each item should have "title", "details", and optionally "criterion" fields
3. For "exercises", each item should have "title", "description", "duration", and "focus_area" fields
4. Use empty arrays [] for lists with no items
5. "improved_excerpt" should be a simple string

Give response ONLY in the specified JSON format without any additional commentary.
"""

    url = LLM_ENDPOINT
    headers = {"Content-Type": "application/json"}
    data = {
        "model": LLM_MODEL,
        "prompt": prompt,
        "temperature": LLM_TEMPERATURE,
        "stream": False,
        "format": GeneralFeedbackSchema.model_json_schema(),
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        # Parse the LLM response
        llm_response = result.get("response", "")
        if not llm_response:
            return None
        
        try:
            # Try to parse JSON response
            feedback_data = json.loads(llm_response)
            return _process_general_feedback(feedback_data)
            
        except json.JSONDecodeError:
            print("Failed to parse LLM JSON response, using fallback")
            return None
            
    except requests.RequestException as e:
        print("Error giving recommendations:", e)
        return None


def _process_general_feedback(feedback_data: Dict) -> str:
    """Process the structured feedback data into the expected format"""
    
    try:
        # Extract main components with defaults
        summary = feedback_data.get("summary", "General analysis of speech performance")
        
        # Process general evaluation
        general_evaluation = {}
        for criterion, eval_data in feedback_data.get("general_evaluation", {}).items():
            if isinstance(eval_data, dict):
                general_evaluation[criterion] = {
                    "score": eval_data.get("score", 5.0),
                    "strengths": eval_data.get("strengths", []),
                    "improvements": eval_data.get("improvements", [])
                }
        
        # Process strengths
        strengths = []
        for strength in feedback_data.get("strengths", []):
            if isinstance(strength, dict):
                strengths.append({
                    "title": strength.get("title", "Strength"),
                    "details": strength.get("details", ""),
                    "evidence": strength.get("evidence"),
                    "criterion": strength.get("criterion")
                })
        
        # Process issues
        issues = []
        for issue in feedback_data.get("issues", []):
            if isinstance(issue, dict):
                issues.append({
                    "title": issue.get("title", "Area for Improvement"),
                    "details": issue.get("details", ""),
                    "evidence": issue.get("evidence"),
                    "criterion": issue.get("criterion")
                })
        
        # Process exercises
        exercises = []
        for exercise in feedback_data.get("exercises", []):
            if isinstance(exercise, dict):
                exercises.append({
                    "title": exercise.get("title", "Exercise"),
                    "description": exercise.get("description", ""),
                    "duration": exercise.get("duration", "5 minutes"),
                    "focus_area": exercise.get("focus_area", "general")
                })
        
        cssef_evaluation = {}
        if "cssef_evaluation" in feedback_data:
            for criterion, eval_data in feedback_data["cssef_evaluation"].items():
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

        # Create structured response
        structured_feedback = {
            "summary": summary,
            "cssef_evaluation": cssef_evaluation,
            "strengths": strengths,
            "issues": issues,
            "suggestions": feedback_data.get("suggestions", []),
            "improved_excerpt": feedback_data.get("improved_excerpt"),
            "micro_exercises": exercises,
            "motivation": feedback_data.get("motivation", "Keep practicing to improve your speaking skills!"),
            "context_specific_tips": []  # Empty for general feedback
        }
        
        return json.dumps(structured_feedback, indent=2)
        
    except Exception as e:
        print(f"Error processing general feedback: {e}")
        return None


