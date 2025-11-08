"""
TranscribeTool: Transcribes speech from audio/video files.

This tool uses Whisper to convert speech to text and generates timestamps for segments.
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field
import whisper
import os
from tools.base import BaseTool

class TranscribeToolInput(BaseModel):
    """Input schema for TranscribeTool"""
    file_path: str = Field(
        ..., 
        description="Absolute path to the audio/video file to transcribe"
    )

class WordTimestamp(BaseModel):
    """Schema for individual word with precise timestamps"""
    word: str = Field(..., description="The transcribed word")
    start: float = Field(..., description="Start time of word in seconds")
    end: float = Field(..., description="End time of word in seconds")
    probability: float = Field(..., description="Confidence score for this word")

class TranscribeSegment(BaseModel):
    """Schema for a transcribed segment with timestamps"""
    start: float = Field(..., description="Start time of segment in seconds")
    end: float = Field(..., description="End time of segment in seconds")
    text: str = Field(..., description="Transcribed text for this segment")
    words: List[WordTimestamp] = Field(default_factory=list, description="Word-level timestamps within this segment")

class TranscribeToolOutput(BaseModel):
    """Output schema for TranscribeTool"""
    transcript: str = Field(
        ..., 
        description="Full transcript of the audio/video file"
    )
    segments: List[TranscribeSegment] = Field(
        default_factory=list,
        description="List of transcript segments with timing information"
    )
    words: List[WordTimestamp] = Field(
        default_factory=list,
        description="List of all words with precise timing information"
    )

class TranscribeTool(BaseTool[TranscribeToolInput, TranscribeToolOutput]):
    """
    Tool for transcribing speech from audio/video files.
    
    Uses OpenAI's Whisper model to generate accurate transcriptions
    with timestamps for each segment.
    """
    
    name = "transcribe_tool"
    description = "Transcribes speech from audio/video files with segment timestamps"
    
    # Define schemas for type checking
    InputSchema = TranscribeToolInput
    OutputSchema = TranscribeToolOutput
    
    def __init__(self, model_size: str = "tiny"):
        """
        Initialize the TranscribeTool.
        
        Args:
            model_size (str): Whisper model size ("tiny", "base", "small", "medium", "large")
        """
        self.model_size = model_size
        self.model = None  # Lazy loading for efficiency
    
    def _load_model(self):
        """Load the Whisper model if not already loaded"""
        if self.model is None:
            self.model = whisper.load_model(self.model_size)
    
    def run(self, inputs: TranscribeToolInput) -> TranscribeToolOutput:
        """
        Transcribe the audio/video file at the specified path.
        
        Args:
            inputs (TranscribeToolInput): Input parameters with file path
        
        Returns:
            TranscribeToolOutput: Transcription results with full text and segments
        """
        file_path = inputs.file_path
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found at {file_path}")
        
        # Load model (if not already loaded)
        self._load_model()
        
        # Configure transcription for better handling of filler words
        prompt = (
            "I was like, was like, I'm like, you know what I mean, kind of, "
            "um, ah, huh, and so, so um, uh, and um, like um, so like, like it's, "
            "it's like, i mean, yeah, ok so, uh so, so uh, yeah so, you know, it's uh"
        )
        
        # Run transcription with word-level timestamps
        result = self.model.transcribe(
            file_path,
            initial_prompt=prompt,
            verbose=False,
            word_timestamps=True  # Enable word-level timestamps
        )
        
        # Process segments and extract word-level data
        segments = []
        all_words = []
        
        for segment in result.get("segments", []):
            # Extract word-level timestamps for this segment
            segment_words = []
            if "words" in segment:
                for word_data in segment["words"]:
                    word_timestamp = WordTimestamp(
                        word=word_data["word"].strip(),
                        start=word_data["start"],
                        end=word_data["end"],
                        probability=word_data.get("probability", 1.0)
                    )
                    segment_words.append(word_timestamp)
                    all_words.append(word_timestamp)
            
            # Create segment with words
            segments.append(
                TranscribeSegment(
                    start=segment["start"],
                    end=segment["end"],
                    text=segment["text"].strip(),
                    words=segment_words
                )
            )
        
        return TranscribeToolOutput(
            transcript=result["text"],
            segments=segments,
            words=all_words
        )
