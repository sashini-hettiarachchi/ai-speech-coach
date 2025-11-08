"""
FillerDetectorTool: Analyzes speech transcripts for filler words using OpenAI structured outputs.

This tool detects filler words in speech transcripts using GPT-4o with structured outputs
for reliable JSON parsing and consistent results.
"""

import re
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from tools.base import BaseTool

# Import configuration
from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE

# Comprehensive list of filler words and phrases
FILLERS = [
    # Basic fillers
    "um", "uh", "uhm", "ah", "er", "eh", "hmm", "mm",
    # Common verbal fillers
    "like", "you know", "basically", "actually", "literally", "so",
    "well", "okay", "right", "I mean", "sort of", "kind of",
    # Hesitation words
    "anyway", "whatever", "stuff", "thing", "things", "obviously",
    "totally", "really", "very", "just", "maybe", "probably",
    # Professional hesitations
    "let me see", "how do I put this", "what I'm trying to say",
    "if you will", "as it were", "per se", "you see"
]


class FillerDetectorToolInput(BaseModel):
    """Input schema for FillerDetectorTool"""
    transcript: str = Field(
        ...,
        description="The speech transcript to analyze for filler words"
    )

class FillerDetectorToolOutput(BaseModel):
    """Output schema for FillerDetectorTool"""
    total_fillers: int = Field(
        ..., 
        description="Total number of filler words/phrases detected"
    )
    filler_percentage: float = Field(
        ...,
        description="Percentage of filler words relative to total word count"
    )
    word_count: int = Field(
        ...,
        description="Total word count in the transcript"
    )
    fillers: Dict[str, int] = Field(
        default={},
        description="Dictionary of filler words with their counts"
    )

class FillerAnalysisResponse(BaseModel):
    """Structured response schema for OpenAI API"""
    filler_counts: Optional[Dict[str, int]] = Field(
        None,
        description="Dictionary of detected filler words with their counts"
    )

class FillerDetectorTool(BaseTool[FillerDetectorToolInput, FillerDetectorToolOutput]):
    """
    Tool for detecting and analyzing filler words in speech transcripts using OpenAI structured outputs.
    
    Uses GPT-4o with structured outputs for reliable and consistent filler word detection.
    """
    
    name = "filler_detector_tool"
    description = "Detects and analyzes filler words in speech transcripts using OpenAI structured outputs"
    
    InputSchema = FillerDetectorToolInput
    OutputSchema = FillerDetectorToolOutput
    
    def __init__(self):
        """Initialize the FillerDetectorTool with OpenAI client"""
        try:
            from openai import OpenAI
            self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
            self.openai_model = OPENAI_MODEL
            self.openai_temperature = OPENAI_TEMPERATURE
            print("OpenAI client initialized successfully for filler detection")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize OpenAI client: {e}")
    
    def run(self, inputs: FillerDetectorToolInput) -> FillerDetectorToolOutput:
        """
        Analyze transcript for filler words using OpenAI structured outputs.
        
        Args:
            inputs: FillerDetectorToolInput with transcript
        
        Returns:
            FillerDetectorToolOutput with detailed filler word analysis
        """
        transcript = inputs.transcript.strip()
        if not transcript:
            return FillerDetectorToolOutput(
                total_fillers=0,
                filler_percentage=0.0,
                word_count=0,
                fillers={}
            )

        return self._analyze_with_openai(transcript)

    def _analyze_with_openai(self, transcript: str) -> FillerDetectorToolOutput:
        """
        Use OpenAI structured outputs for filler word detection.
        
        Args:
            transcript: The speech transcript to analyze
            
        Returns:
            FillerDetectorToolOutput with analysis results
        """
        
        prompt = f"""You are a speech analysis expert. Analyze this transcript and count filler words precisely.

FILLER WORDS TO DETECT:
{', '.join(FILLERS)}

INSTRUCTIONS:
1. Count each filler word occurrence (case-insensitive)
2. Include multi-word phrases like "you know", "I mean"
3. Don't count words when they have semantic meaning
   Example: "I like cats" - here 'like' is NOT a filler
4. Only count words that are actually used as hesitations or fillers

TRANSCRIPT TO ANALYZE:
"{transcript}"

Count all instances of filler words and return the counts."""

        try:
            response = self.openai_client.beta.chat.completions.parse(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that analyzes speech transcripts for filler words."},
                    {"role": "user", "content": prompt}    
                ],
                response_format=FillerAnalysisResponse,
                temperature=self.openai_temperature,
            )
                
            analysis = response.choices[0].message.parsed
            
            # Calculate statistics
            filler_counts = analysis.filler_counts or {}
            total_fillers = sum(filler_counts.values())
            word_count = len(transcript.split())
            filler_percentage = (total_fillers / word_count * 100) if word_count > 0 else 0
            
            return FillerDetectorToolOutput(
                total_fillers=total_fillers,
                filler_percentage=round(filler_percentage, 2),
                word_count=word_count,
                fillers=filler_counts
            )
            
        except Exception as e:
            print(f"OpenAI filler analysis error: {e}")
            # Return empty result on error
            word_count = len(transcript.split()) if transcript else 0
            return FillerDetectorToolOutput(
                total_fillers=0,
                filler_percentage=0.0,
                word_count=word_count,
                fillers={}
            )
