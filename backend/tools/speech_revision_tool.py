"""
Speech Revision Tool: Generate Revised Speech Text and Audio

This tool creates an improved version of the speech text and generates
an audio version using text-to-speech, then saves it to Google Cloud Storage.

Features:
- Generates improved speech text based on analysis results
- Creates audio version using OpenAI TTS
- Uploads audio to Google Cloud Storage
- Returns GCS URL for storage in database
"""

import os
import tempfile
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from tools.base import BaseTool
from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE
from utils.gcs_storage import upload_speech_file


class SpeechRevisionToolInput(BaseModel):
    """Input schema for Speech Revision Tool"""
    
    original_transcript: str = Field(..., description="Original transcript of the speech")
    context: Optional[str] = Field(None, description="Speaking context (academic, persuasive, storytelling, etc.)")
    speech_goal: Optional[str] = Field(None, description="Goal/purpose of the speech")
    audience_description: Optional[str] = Field(None, description="Description of target audience")
    key_points: Optional[str] = Field(None, description="Key points to emphasize")
    cssef_feedback: Optional[Dict[str, Any]] = Field(None, description="CSSEF evaluation feedback for improvements")
    filler_analysis: Optional[Dict[str, Any]] = Field(None, description="Filler word analysis for fluency improvements")
    session_id: int = Field(..., description="Session ID for file naming")


class SpeechRevisionToolOutput(BaseModel):
    """Output schema for Speech Revision Tool"""
    
    revised_text: str = Field(..., description="Improved version of the speech text")
    audio_gcs_url: Optional[str] = Field(None, description="Google Cloud Storage URL for the audio file")
    improvements_made: str = Field(..., description="Summary of improvements made to the original speech")


class SpeechRevisionTool(BaseTool[SpeechRevisionToolInput, SpeechRevisionToolOutput]):
    """
    Tool for generating revised speech text and audio
    
    Creates an improved version of the speech based on analysis feedback,
    generates an audio version using TTS, and uploads to Google Cloud Storage.
    """
    
    name = "speech_revision_tool"
    description = "Generates revised speech text and audio version"
    
    InputSchema = SpeechRevisionToolInput
    OutputSchema = SpeechRevisionToolOutput
    
    def __init__(self):
        """Initialize the tool with OpenAI client"""
        try:
            from openai import OpenAI
            self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
            self.openai_model = OPENAI_MODEL
            self.openai_temperature = OPENAI_TEMPERATURE
            print("OpenAI client initialized successfully for Speech Revision")
        except Exception as e:
            print(f"Warning: Failed to initialize OpenAI client: {e}")
            self.openai_client = None
    
    def run(self, inputs: SpeechRevisionToolInput) -> SpeechRevisionToolOutput:
        """
        Generate revised speech text and audio.
        
        Args:
            inputs: Speech revision inputs
            
        Returns:
            Speech revision output with improved text and audio URL
        """
        if not self.openai_client:
            return self._get_fallback_revision(inputs)
        
        # Step 1: Generate revised text
        revised_text, improvements = self._generate_revised_text(inputs)
        
        # Step 2: Generate audio from revised text
        audio_gcs_url = self._generate_audio(revised_text, inputs.session_id)
        
        return SpeechRevisionToolOutput(
            revised_text=revised_text,
            audio_gcs_url=audio_gcs_url,
            improvements_made=improvements
        )
    
    def _generate_revised_text(self, inputs: SpeechRevisionToolInput) -> tuple[str, str]:
        """Generate improved speech text using OpenAI"""
        
        # Prepare feedback context
        feedback_context = ""
        if inputs.cssef_feedback:
            feedback_context = f"""
CSSEF EVALUATION FEEDBACK:
{self._format_cssef_feedback(inputs.cssef_feedback)}
"""
        
        filler_context = ""
        if inputs.filler_analysis:
            filler_percentage = inputs.filler_analysis.get('filler_percentage', 0)
            if filler_percentage > 2:
                filler_context = f"""
FLUENCY IMPROVEMENT NEEDED:
- Reduce filler words (currently {filler_percentage:.1f}%)
- Add strategic pauses instead of fillers
"""
        
        prompt = f"""
You are an expert speech coach tasked with revising and improving a speech transcript. 

ORIGINAL SPEECH DETAILS:
- Context: {inputs.context or 'General presentation'}
- Goal: {inputs.speech_goal or 'Not specified'}
- Target Audience: {inputs.audience_description or 'General audience'}
- Key Points: {inputs.key_points or 'Not specified'}

{feedback_context}

{filler_context}

ORIGINAL TRANSCRIPT:
{inputs.original_transcript}

REVISION INSTRUCTIONS:

1. IMPROVE STRUCTURE:
   - Add clear introduction with hook and preview
   - Organize body with logical flow and transitions
   - Create strong conclusion with summary and call to action

2. ENHANCE CONTENT:
   - Strengthen key points with better supporting evidence
   - Add engaging examples or analogies
   - Improve clarity and impact of message

3. REFINE LANGUAGE:
   - Use more vivid and precise language
   - Remove redundancy and filler phrases
   - Ensure appropriate tone for audience and context

4. OPTIMIZE FOR DELIVERY:
   - Add natural pause markers where helpful
   - Ensure smooth flow and rhythm
   - Keep conversational but polished tone

5. MAINTAIN AUTHENTICITY:
   - Preserve the speaker's voice and style
   - Keep personal elements that work well
   - Don't completely change the core message

CONTEXT-SPECIFIC IMPROVEMENTS:
- Academic: Add scholarly structure, precise terminology, formal transitions
- Persuasive: Strengthen arguments, add emotional appeals, clear call to action
- Storytelling: Enhance narrative flow, vivid descriptions, engaging pace

Please provide:
1. The revised speech text (well-formatted and ready for delivery)
2. A brief summary of the key improvements made

Format your response as:
REVISED SPEECH:
[Improved speech text here]

IMPROVEMENTS MADE:
[Summary of key changes and enhancements]
"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert speech coach specializing in speech revision and improvement. Provide clear, actionable improvements while maintaining the speaker's authentic voice."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=self.openai_temperature
            )
            
            content = response.choices[0].message.content
            
            # Parse the response
            parts = content.split("IMPROVEMENTS MADE:")
            if len(parts) >= 2:
                revised_text = parts[0].replace("REVISED SPEECH:", "").strip()
                improvements = parts[1].strip()
            else:
                # Fallback parsing
                revised_text = content
                improvements = "General improvements made to structure, clarity, and delivery."
            
            print("Speech revision completed successfully")
            return revised_text, improvements
            
        except Exception as e:
            print(f"Error generating revised text: {e}")
            return inputs.original_transcript, "Unable to generate improvements due to technical issues."
    
    def _generate_audio(self, text: str, session_id: int) -> Optional[str]:
        """Generate audio from text and upload to GCS"""
        
        if not self.openai_client:
            print("OpenAI client not available for audio generation")
            return None
            
        try:
            # Generate audio using OpenAI TTS
            response = self.openai_client.audio.speech.create(
                model="tts-1",  # Use tts-1 for faster generation
                voice="alloy",  # Default voice - could be made configurable
                input=text[:4000]  # Limit text length for TTS
            )
            
            # Create temporary file for audio
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                temp_file.write(response.content)
                temp_audio_path = temp_file.name
            
            # Upload to Google Cloud Storage
            filename = f"revised_speech_session_{session_id}.mp3"
            try:
                blob_name, gcs_signed_url = upload_speech_file(temp_audio_path, filename)
                print(f"Revised speech audio uploaded to GCS: {gcs_signed_url}")
                
                # Clean up temporary file
                os.unlink(temp_audio_path)
                
                return gcs_signed_url
                
            except Exception as gcs_error:
                print(f"Failed to upload audio to GCS: {gcs_error}")
                # Clean up temporary file
                try:
                    os.unlink(temp_audio_path)
                except:
                    pass
                return None
                
        except Exception as e:
            print(f"Error generating audio: {e}")
            return None
    
    def _format_cssef_feedback(self, cssef_feedback: Dict[str, Any]) -> str:
        """Format CSSEF feedback for inclusion in revision prompt"""
        
        feedback_lines = []
        for criterion, data in cssef_feedback.items():
            if isinstance(data, dict):
                score = data.get('score', 'N/A')
                improvement = data.get('improvement', '')
                if improvement:
                    feedback_lines.append(f"- {criterion}: Score {score} - {improvement}")
        
        return "\n".join(feedback_lines) if feedback_lines else "No specific CSSEF feedback available."
    
    def _get_fallback_revision(self, inputs: SpeechRevisionToolInput) -> SpeechRevisionToolOutput:
        """Return fallback revision when API fails"""
        return SpeechRevisionToolOutput(
            revised_text=inputs.original_transcript,
            audio_gcs_url=None,
            improvements_made="Unable to generate improvements due to technical issues. Original transcript preserved."
        )