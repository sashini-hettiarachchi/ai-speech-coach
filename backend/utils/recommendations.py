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
    micro_exercises: List[Exercise] = Field(
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

## CSSEF EVALUATION CRITERIA
You MUST evaluate the speech on these 5 criteria (score 0-10 for each):

1. **Content (C1)** - Quality, relevance, and value of information presented
2. **Structure (C2)** - Logical organization, flow, and coherence
3. **Style (C3)** - Language choice, tone, and appropriate register
4. **Engagement (C4)** - Ability to connect with audience and maintain interest
5. **Fluency (C5)** - Smoothness of delivery, pace, and vocal control

## YOUR TASK
Analyze the transcript and provide comprehensive general feedback. You MUST include:

1. **Summary**: 2-3 sentences about overall performance
2. **CSSEF Evaluation**: For EACH of the 5 criteria above, provide:
   - Numerical score (0-10)
   - At least 1 strength (what was done well)
   - At least 1 improvement area (what needs work)
3. **Strengths**: 2-3 detailed positive aspects with evidence
4. **Issues**: 2-3 areas needing improvement with specific details
5. **Suggestions**: 3-5 actionable recommendations
6. **Improved Excerpt**: Rewrite a portion of the speech to demonstrate improvement
7. **Micro Exercises**: 2-3 specific practice exercises
8. **Motivation**: Encouraging message for the speaker

CRITICAL REQUIREMENTS:
- cssef_evaluation MUST contain all 5 criteria: "Content", "Structure", "Style", "Engagement", "Fluency"
- Each criterion MUST have "score" (number 0-10), "strengths" (array), "improvements" (array)
- suggestions MUST contain 3-5 actionable items
- All arrays must contain actual items, not be empty

EXAMPLE CSSEF EVALUATION FORMAT:
```json
"cssef_evaluation": {{
  "Content": {{
    "score": 7.0,
    "strengths": ["Clear main topic", "Personal examples"],
    "improvements": ["Add more supporting details", "Include statistics"]
  }},
  "Structure": {{
    "score": 6.0,
    "strengths": ["Clear introduction"],
    "improvements": ["Add transitions", "Stronger conclusion"]
  }},
  "Style": {{
    "score": 5.0,
    "strengths": ["Conversational tone"],
    "improvements": ["Vary sentence length", "Reduce repetition"]
  }},
  "Engagement": {{
    "score": 6.0,
    "strengths": ["Enthusiasm evident"],
    "improvements": ["Use more questions", "Add stories"]
  }},
  "Fluency": {{
    "score": 4.0,
    "strengths": ["Good pace in parts"],
    "improvements": ["Reduce filler words", "Improve pausing"]
  }}
}}
```

Provide response ONLY in valid JSON format following the exact structure above. Ensure ALL required fields are present and populated.
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
        summary = feedback_data.get("summary", "Analysis of speech performance completed.")
        
        # Process CSSEF evaluation with defaults for missing criteria
        cssef_evaluation = {}
        default_criteria = {
            "Content": {"score": 5.0, "strengths": ["Content present"], "improvements": ["Enhance content quality"]},
            "Structure": {"score": 5.0, "strengths": ["Basic structure evident"], "improvements": ["Improve organization"]},
            "Style": {"score": 5.0, "strengths": ["Appropriate style"], "improvements": ["Refine language use"]},
            "Engagement": {"score": 5.0, "strengths": ["Shows engagement"], "improvements": ["Increase audience connection"]},
            "Fluency": {"score": 5.0, "strengths": ["Generally fluent"], "improvements": ["Enhance delivery smoothness"]}
        }
        
        # Start with defaults and update with actual data
        for criterion in default_criteria.keys():
            cssef_evaluation[criterion] = default_criteria[criterion].copy()
        
        # Update with actual evaluation data if present
        if "cssef_evaluation" in feedback_data and feedback_data["cssef_evaluation"]:
            for criterion, eval_data in feedback_data["cssef_evaluation"].items():
                if isinstance(eval_data, dict):
                    try:
                        # Convert score to float and handle various formats
                        score = 5.0
                        if "score" in eval_data:
                            try:
                                score = float(eval_data["score"])
                                # Ensure score is within valid range
                                score = max(0.0, min(10.0, score))
                            except (ValueError, TypeError):
                                score = 5.0

                        # Ensure strengths and improvements are lists
                        strengths = []
                        if "strengths" in eval_data:
                            if isinstance(eval_data["strengths"], list):
                                strengths = [s for s in eval_data["strengths"] if s and str(s).strip()]
                            elif isinstance(eval_data["strengths"], str) and eval_data["strengths"].strip():
                                strengths = [eval_data["strengths"]]
                        
                        # Provide default if empty
                        if not strengths:
                            strengths = [f"Shows {criterion.lower()} awareness"]

                        improvements = []
                        if "improvements" in eval_data:
                            if isinstance(eval_data["improvements"], list):
                                improvements = [i for i in eval_data["improvements"] if i and str(i).strip()]
                            elif isinstance(eval_data["improvements"], str) and eval_data["improvements"].strip():
                                improvements = [eval_data["improvements"]]
                        
                        # Provide default if empty
                        if not improvements:
                            improvements = [f"Continue developing {criterion.lower()} skills"]

                        cssef_evaluation[criterion] = {
                            "score": score,
                            "strengths": strengths,
                            "improvements": improvements
                        }
                    except Exception as e:
                        print(f"Error processing evaluation for {criterion}: {e}")
                        # Keep default for this criterion
        
        # Process strengths with better defaults
        strengths = []
        for strength in feedback_data.get("strengths", []):
            if isinstance(strength, dict):
                strengths.append({
                    "title": strength.get("title", "Strength Identified"),
                    "details": strength.get("details", "Positive aspect noted in your speech."),
                    "evidence": strength.get("evidence"),
                    "criterion": strength.get("criterion")
                })
        
        # Provide default strengths if none found
        if not strengths:
            strengths = [
                {
                    "title": "Communication Attempt",
                    "details": "You successfully communicated your message.",
                    "evidence": None,
                    "criterion": "Content"
                }
            ]
        
        # Process issues with better defaults
        issues = []
        for issue in feedback_data.get("issues", []):
            if isinstance(issue, dict):
                issues.append({
                    "title": issue.get("title", "Area for Improvement"),
                    "details": issue.get("details", "This area has potential for enhancement."),
                    "evidence": issue.get("evidence"),
                    "criterion": issue.get("criterion")
                })
        
        # Process suggestions with defaults
        suggestions = feedback_data.get("suggestions", [])
        if not suggestions or not isinstance(suggestions, list):
            suggestions = [
                "Practice your speech multiple times to improve fluency",
                "Focus on clear pronunciation and pacing",
                "Consider your audience when crafting your message",
                "Use more varied vocabulary to enhance engagement"
            ]
        
        # Process exercises with better structure
        exercises = []
        for exercise in feedback_data.get("micro_exercises", []):
            if isinstance(exercise, dict):
                exercises.append({
                    "title": exercise.get("title", "Speaking Exercise"),
                    "description": exercise.get("description", "Practice speaking skills."),
                    "duration": exercise.get("duration", "10 minutes"),
                    "focus_area": exercise.get("focus_area", "general speaking")
                })
        
        # Provide default exercises if none found
        if not exercises:
            exercises = [
                {
                    "title": "Filler Word Reduction",
                    "description": "Practice speaking slowly and deliberately, pausing instead of using filler words.",
                    "duration": "15 minutes",
                    "focus_area": "Fluency"
                },
                {
                    "title": "Voice Modulation Practice",
                    "description": "Read aloud varying your pitch, pace, and volume for emphasis.",
                    "duration": "10 minutes",
                    "focus_area": "Delivery"
                }
            ]

        # Create structured response
        structured_feedback = {
            "summary": summary,
            "cssef_evaluation": cssef_evaluation,
            "strengths": strengths,
            "issues": issues,
            "suggestions": suggestions,
            "improved_excerpt": feedback_data.get("improved_excerpt", "Consider restructuring your opening to be more engaging and clear."),
            "micro_exercises": exercises,
            "motivation": feedback_data.get("motivation", "Every great speaker started as a beginner. Keep practicing and you'll see improvement!")
        }
        
        return json.dumps(structured_feedback, indent=2)
        
    except Exception as e:
        print(f"Error processing general feedback: {e}")
        # Return a complete fallback response
        fallback_response = {
            "summary": "Speech analysis completed with basic evaluation.",
            "cssef_evaluation": {
                "Content": {"score": 5.0, "strengths": ["Content present"], "improvements": ["Enhance content depth"]},
                "Structure": {"score": 5.0, "strengths": ["Basic structure"], "improvements": ["Improve organization"]},
                "Style": {"score": 5.0, "strengths": ["Appropriate style"], "improvements": ["Refine language"]},
                "Engagement": {"score": 5.0, "strengths": ["Shows effort"], "improvements": ["Increase engagement"]},
                "Fluency": {"score": 5.0, "strengths": ["Generally fluent"], "improvements": ["Reduce hesitations"]}
            },
            "strengths": [{"title": "Communication", "details": "Message was communicated.", "evidence": None, "criterion": "Content"}],
            "issues": [{"title": "General Improvement", "details": "Continue developing speaking skills.", "evidence": None, "criterion": "General"}],
            "suggestions": ["Practice regularly", "Focus on clarity", "Engage your audience", "Reduce filler words"],
            "improved_excerpt": "Consider making your opening more direct and engaging.",
            "micro_exercises": [
                {"title": "Daily Practice", "description": "Practice speaking for 10 minutes daily.", "duration": "10 minutes", "focus_area": "General"},
                {"title": "Record and Review", "description": "Record yourself and listen for areas of improvement.", "duration": "15 minutes", "focus_area": "Self-Assessment"}
            ],
            "motivation": "Keep practicing and you'll see improvement in your speaking skills!"
        }
        return json.dumps(fallback_response, indent=2)


