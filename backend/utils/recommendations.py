import requests
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# Import the existing feedback generator tool
from tools.feedback_generator_tool import FeedbackGeneratorTool, FeedbackGeneratorToolInput

# Import configuration with fallback
try:
    from config import LLM_ENDPOINT, LLM_MODEL, LLM_TEMPERATURE
except ImportError:
    LLM_ENDPOINT = "http://localhost:11434/api/generate"
    LLM_MODEL = "llama3"
    LLM_TEMPERATURE = 0.3


# Remove the old schemas and processing functions since we're using the FeedbackGeneratorTool


def give_recommendations(transcript, prosody_result=None, filler_analysis=None):
    """
    Generate general recommendations for speech improvement without context-awareness.
    Uses the existing FeedbackGeneratorTool but without context weights and user-specific data.
    """
    
    try:
        # Initialize the feedback generator tool
        feedback_tool = FeedbackGeneratorTool()
        
        # Calculate basic speech metrics
        word_count = len(transcript.split()) if transcript else 0
        
        # Try to get duration from prosody_result, otherwise estimate
        duration_seconds = 60.0  # default
        if prosody_result:
            # Try different possible field names for duration
            duration_seconds = prosody_result.get('duration_seconds') or \
                             prosody_result.get('duration') or \
                             prosody_result.get('total_duration') or \
                             60.0
        
        words_per_minute = (word_count / duration_seconds * 60) if duration_seconds > 0 else 120.0
        
        # Create input for the feedback generator tool
        # For general feedback, we use "General" as context and don't provide user-specific data
        tool_input = FeedbackGeneratorToolInput(
            context_label=None,
            speech_duration=duration_seconds,
            words_per_minute=words_per_minute,
            transcript=transcript,
            filler_analysis=filler_analysis,
            prosody_results=prosody_result,
            cssef_weights=None,  # No context-specific weights for general feedback
            speech_title=None,   # No user-provided title
            speech_goal=None,    # No user-provided goal
            speech_audience_description=None,  # No user-provided audience description
            speech_key_points=None,  # No user-provided key points
            speech_self_improvement_goal=None  # No user-provided improvement goal
        )
        
        # Generate feedback using the tool
        feedback_output = feedback_tool.run(tool_input)
        
        if feedback_output is None:
            print("FeedbackGeneratorTool returned None, using fallback")
            return None
            
        # Convert the tool output to the expected format using the new simplified schema
        structured_feedback = {
            "revised_speech_text": feedback_output.revised_speech_text,
            "summary": {
                "strengths": feedback_output.summary.strengths,
                "improvements": feedback_output.summary.improvements
            },
            "cssef_evaluation": {
                criterion: {
                    "score": eval_data.score,
                    "comment": eval_data.comment,
                    "improvement": eval_data.improvement
                }
                for criterion, eval_data in feedback_output.cssef_evaluation.items()
            }
        }
        
        return json.dumps(structured_feedback, indent=2)
        
    except Exception as e:
        print(f"Error generating general recommendations: {e}")
        return None



