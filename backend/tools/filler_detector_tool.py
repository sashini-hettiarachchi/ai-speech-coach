"""
FillerDetectorTool: Analyzes speech transcripts for filler words.

This tool detects filler words in speech transcripts using LLM-based analysis 
with rule-based fallback. It provides detailed analysis of filler word usage,
including word counts, percentages, and patterns.
"""

import re
import json
import requests
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from tools.base import BaseTool

# Import configuration with fallback
try:
    from config import LLM_ENDPOINT, LLM_MODEL, LLM_TEMPERATURE
except ImportError:
    LLM_ENDPOINT = "http://localhost:11434/api/generate"
    LLM_MODEL = "llama3"
    LLM_TEMPERATURE = 0

# Import existing detector if available (for backward compatibility)
try:
    from utils.filler_detector import count_filler_words, FILLERS
except ImportError:
    # Comprehensive list of filler words and phrases if import fails
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


class FillerLocation(BaseModel):
    """Schema for a specific filler word location in text"""
    word: str = Field(..., description="The filler word/phrase detected")
    start_idx: Optional[int] = Field(None, description="Start index in the transcript")
    end_idx: Optional[int] = Field(None, description="End index in the transcript")


class FillerDetectorToolInput(BaseModel):
    """Input schema for FillerDetectorTool"""
    transcript: str = Field(
        ...,
        description="The speech transcript to analyze for filler words"
    )
    custom_fillers: List[str] = Field(
        default_factory=list,
        description="Optional additional filler words to detect beyond the default list"
    )
    use_llm: bool = Field(
        default=True,
        description="Whether to use LLM-based detection (falls back to rule-based if False or LLM fails)"
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
        default_factory=dict,
        description="Dictionary of filler words with their counts"
    )
    filler_details: List[FillerLocation] = Field(
        default_factory=list,
        description="Detailed list of filler words with positions"
    )
    most_common_filler: Optional[str] = Field(
        None,
        description="The most frequently used filler word/phrase"
    )
    analysis: str = Field(
        ...,
        description="Human-readable analysis of filler word usage"
    )
    improvement_tip: Optional[str] = Field(
        None,
        description="Specific tip for reducing the most common filler word"
    )
    analysis_method: str = Field(
        ...,
        description="Method used for analysis: 'llm' or 'rule_based'"
    )


class FillerDetectorTool(BaseTool[FillerDetectorToolInput, FillerDetectorToolOutput]):
    """
    Tool for detecting and analyzing filler words in speech transcripts.
    
    Provides detailed analysis of filler word usage, including word counts,
    percentages, patterns, and suggestions for improvement using either
    LLM-based analysis or rule-based fallback.
    """
    
    name = "filler_detector_tool"
    description = "Detects and analyzes filler words in speech transcripts"
    
    # Define schemas for type checking
    InputSchema = FillerDetectorToolInput
    OutputSchema = FillerDetectorToolOutput
    
    def __init__(self):
        """Initialize the FillerDetectorTool with LLM config"""
        self.llm_endpoint = LLM_ENDPOINT
        self.llm_model = LLM_MODEL
        self.llm_temperature = LLM_TEMPERATURE
        self.fillers = list(FILLERS)  # Copy default fillers
    
    def run(self, inputs: FillerDetectorToolInput) -> FillerDetectorToolOutput:
        """
        Analyze transcript for filler words and provide detailed analysis.
        
        Args:
            inputs: FillerDetectorToolInput with transcript and options
        
        Returns:
            FillerDetectorToolOutput with detailed filler word analysis
        """
        # Add any custom fillers to our detection list
        detection_fillers = list(self.fillers)
        if inputs.custom_fillers:
            for filler in inputs.custom_fillers:
                if filler and filler.strip() and filler not in detection_fillers:
                    detection_fillers.append(filler.strip())
        
        transcript = inputs.transcript.strip()
        if not transcript:
            return FillerDetectorToolOutput(
                total_fillers=0,
                filler_percentage=0.0,
                word_count=0,
                analysis="No transcript provided for analysis.",
                analysis_method="none"
            )
        
        # Try to use the existing utility function if available
        try:
            if "count_filler_words" in globals():
                result = count_filler_words(transcript)
                return self._format_result(result)
        except Exception as e:
            print(f"Error using existing filler detector: {e}")
        
        # Otherwise use our internal implementation
        if inputs.use_llm:
            try:
                llm_result = self._analyze_with_llm(transcript, detection_fillers)
                if llm_result:
                    return llm_result
            except Exception as e:
                print(f"LLM filler analysis failed: {e}")
        
        # Fallback to rule-based analysis
        print("Using rule-based filler word analysis...")
        return self._rule_based_analysis(transcript, detection_fillers)
    
    def _analyze_with_llm(self, transcript: str, fillers: List[str]) -> FillerDetectorToolOutput:
        """
        Use LLM for filler word detection with improved prompting.
        
        Args:
            transcript: The speech transcript to analyze
            fillers: List of filler words/phrases to detect
            
        Returns:
            FillerDetectorToolOutput with analysis results
        """
        
        enhanced_prompt = f"""You are a speech analysis expert. Analyze this transcript and count filler words precisely.

FILLER WORDS TO DETECT:
{', '.join(fillers)}

INSTRUCTIONS:
1. Count each filler word occurrence (case-insensitive)
2. Include multi-word phrases like "you know", "I mean"
3. Don't count words when they have semantic meaning
4. Return ONLY a valid JSON object in this exact format:
{{"filler_counts": {{"um": 3, "like": 5, "you know": 2}}, "total_fillers": 10}}

TRANSCRIPT TO ANALYZE:
"{transcript}"

RESPONSE (JSON only):"""

        try:
            response = requests.post(
                self.llm_endpoint,
                json={
                    "model": self.llm_model, 
                    "prompt": enhanced_prompt, 
                    "stream": False,
                    "options": {
                        "temperature": self.llm_temperature,
                        "top_p": 0.9,
                        "num_predict": 200
                    }
                },
                timeout=3000
            )
            
            if response.status_code != 200:
                raise requests.RequestException(f"HTTP {response.status_code}")
                
            data = response.json()
            result_text = data.get("response", "").strip()
            
            # Extract JSON from the response
            parsed_result = self._extract_json_from_llm_response(result_text)
            if parsed_result:
                return self._create_output_from_result(parsed_result, transcript, "llm")
                
        except requests.RequestException as e:
            print(f"LLM service error: {e}")
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
        except Exception as e:
            print(f"Unexpected LLM error: {e}")
        
        return None
    
    def _rule_based_analysis(self, transcript: str, fillers: List[str]) -> FillerDetectorToolOutput:
        """
        Analyze transcript using rule-based approach with pattern matching.
        
        Args:
            transcript: The speech transcript to analyze
            fillers: List of filler words/phrases to detect
            
        Returns:
            FillerDetectorToolOutput with analysis results
        """
        
        # Normalize transcript
        text = transcript.lower().strip()
        word_count = len(transcript.split())
        
        filler_counts = {}
        filler_details = []
        
        # Process single-word fillers
        single_word_fillers = [f for f in fillers if ' ' not in f]
        for filler in single_word_fillers:
            # Use word boundaries to avoid partial matches
            pattern = rf'\b{re.escape(filler)}\b'
            matches = list(re.finditer(pattern, text))
            count = len(matches)
            
            if count > 0:
                filler_counts[filler] = count
                for match in matches:
                    filler_details.append(FillerLocation(
                        word=filler,
                        start_idx=match.start(),
                        end_idx=match.end()
                    ))
        
        # Process multi-word fillers
        multi_word_fillers = [f for f in fillers if ' ' in f]
        for filler in multi_word_fillers:
            pattern = rf'\b{re.escape(filler)}\b'
            matches = list(re.finditer(pattern, text))
            count = len(matches)
            
            if count > 0:
                filler_counts[filler] = count
                for match in matches:
                    filler_details.append(FillerLocation(
                        word=filler,
                        start_idx=match.start(),
                        end_idx=match.end()
                    ))
        
        # Calculate total fillers and percentage
        total_fillers = sum(filler_counts.values())
        filler_percentage = (total_fillers / word_count * 100) if word_count > 0 else 0
        
        # Find most common filler
        most_common_filler = max(filler_counts, key=filler_counts.get) if filler_counts else None
        
        # Generate analysis and improvement tip
        analysis, improvement_tip = self._generate_analysis(total_fillers, filler_percentage, most_common_filler, filler_counts)
        
        return FillerDetectorToolOutput(
            total_fillers=total_fillers,
            filler_percentage=round(filler_percentage, 2),
            word_count=word_count,
            fillers=filler_counts,
            filler_details=filler_details,
            most_common_filler=most_common_filler,
            analysis=analysis,
            improvement_tip=improvement_tip,
            analysis_method="rule_based"
        )
    
    def _extract_json_from_llm_response(self, text: str) -> Dict[str, Any]:
        """
        Extract JSON from LLM response using multiple strategies.
        
        Args:
            text: The LLM response text
            
        Returns:
            Parsed JSON data or None if parsing fails
        """
        
        # Strategy 1: Direct JSON parsing
        try:
            result = json.loads(text.strip())
            if self._validate_json_structure(result):
                return result
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Find JSON block using regex
        json_patterns = [
            r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Nested braces
            r'\{.*?\}',  # Simple braces
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    result = json.loads(match.strip())
                    if self._validate_json_structure(result):
                        return result
                except json.JSONDecodeError:
                    continue
        
        # Strategy 3: Manual extraction of key-value pairs
        return self._extract_manual_counts(text)
    
    def _validate_json_structure(self, data: Dict[str, Any]) -> bool:
        """
        Validate that JSON has the expected structure.
        
        Args:
            data: Parsed JSON data
            
        Returns:
            True if valid structure, False otherwise
        """
        return (isinstance(data, dict) and 
                ("filler_counts" in data or "fillers" in data) and 
                isinstance(data.get("filler_counts", data.get("fillers", {})), dict))
    
    def _extract_manual_counts(self, text: str) -> Dict[str, Any]:
        """
        Manually extract filler counts when JSON parsing fails.
        
        Args:
            text: The LLM response text
            
        Returns:
            Dictionary with filler counts or None if extraction fails
        """
        filler_counts = {}
        
        # Look for filler word counts in various formats
        for filler in FILLERS:
            patterns = [
                rf'"{re.escape(filler)}":\s*(\d+)',
                rf"'{re.escape(filler)}':\s*(\d+)",
                rf'{re.escape(filler)}:\s*(\d+)',
                rf'{re.escape(filler)}\s*-\s*(\d+)',
                rf'{re.escape(filler)}\s*:\s*(\d+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    count = int(match.group(1))
                    if count > 0:
                        filler_counts[filler] = count
                    break
        
        if filler_counts:
            return {
                "filler_counts": filler_counts,
                "total_fillers": sum(filler_counts.values())
            }
        
        return None
    
    def _generate_analysis(self, total_fillers: int, filler_percentage: float, 
                          most_common: str = None, filler_counts: Dict[str, int] = None) -> tuple:
        """
        Generate contextual analysis and improvement tip based on filler word usage.
        
        Args:
            total_fillers: Total number of filler words detected
            filler_percentage: Percentage of words that are fillers
            most_common: Most common filler word (if any)
            filler_counts: Dictionary of filler words with their counts
            
        Returns:
            Tuple of (analysis, improvement_tip)
        """
        
        # Generate contextual analysis
        if total_fillers == 0:
            analysis = "Excellent! No filler words detected. Very clear and professional delivery."
            improvement_tip = None
        elif filler_percentage < 1:
            analysis = f"Outstanding delivery! Only {total_fillers} filler words ({filler_percentage:.1f}%) - extremely professional."
            improvement_tip = "Maintain this excellent level of clarity in future presentations."
        elif filler_percentage < 3:
            analysis = f"Great job! {total_fillers} filler words detected ({filler_percentage:.1f}%) - very good delivery with room for minor polish."
            improvement_tip = "Practice strategic pauses to maintain your already strong delivery."
        elif filler_percentage < 5:
            analysis = f"Good delivery with {total_fillers} filler words ({filler_percentage:.1f}%). Consider practicing pauses instead of fillers."
            improvement_tip = "Try the 'pause and breathe' technique: when tempted to use a filler word, take a breath instead."
        else:
            analysis = f"Focus area identified: {total_fillers} filler words ({filler_percentage:.1f}%). Practice reducing these for more professional delivery."
            improvement_tip = "Record yourself speaking and note when you use filler words. Practice replacing them with confident silence."
        
        # Add most common filler for targeted feedback
        if most_common and filler_counts:
            count = filler_counts[most_common]
            improvement_tip = f"Focus on reducing '{most_common}' - used {count} times. Try to replace it with a brief pause."
        
        return analysis, improvement_tip
    
    def _create_output_from_result(self, result: Dict[str, Any], transcript: str, method: str) -> FillerDetectorToolOutput:
        """
        Convert internal result format to FillerDetectorToolOutput.
        
        Args:
            result: Internal result dictionary
            transcript: Original transcript
            method: Analysis method used ('llm' or 'rule_based')
            
        Returns:
            FillerDetectorToolOutput with formatted results
        """
        
        # Extract data from result
        filler_counts = result.get("filler_counts", {})
        if not filler_counts and "fillers" in result:
            filler_counts = result["fillers"]
            
        total_fillers = result.get("total_fillers", sum(filler_counts.values()))
        word_count = result.get("word_count", len(transcript.split()))
        filler_percentage = result.get("filler_percentage", 
                                     (total_fillers / word_count * 100) if word_count > 0 else 0)
        
        # Create filler details list
        filler_details = []
        if "filler_details" in result and isinstance(result["filler_details"], list):
            for item in result["filler_details"]:
                if isinstance(item, str):
                    # Convert string to FillerLocation without position info
                    filler_details.append(FillerLocation(word=item))
                elif isinstance(item, dict):
                    # Convert dict to FillerLocation
                    filler_details.append(FillerLocation(**item))
        else:
            # Create from counts
            for filler, count in filler_counts.items():
                for _ in range(count):
                    filler_details.append(FillerLocation(word=filler))
        
        # Find most common filler
        most_common = result.get("most_common_filler")
        if not most_common and filler_counts:
            most_common = max(filler_counts, key=filler_counts.get)
            
        # Generate analysis and tip if not already provided
        analysis = result.get("analysis")
        improvement_tip = result.get("improvement_tip")
        
        if not analysis or not improvement_tip:
            new_analysis, new_tip = self._generate_analysis(
                total_fillers, filler_percentage, most_common, filler_counts
            )
            
            if not analysis:
                analysis = new_analysis
            if not improvement_tip:
                improvement_tip = new_tip
        
        return FillerDetectorToolOutput(
            total_fillers=total_fillers,
            filler_percentage=round(filler_percentage, 2),
            word_count=word_count,
            fillers=filler_counts,
            filler_details=filler_details,
            most_common_filler=most_common,
            analysis=analysis,
            improvement_tip=improvement_tip,
            analysis_method=method
        )
    
    def _format_result(self, result: Dict[str, Any]) -> FillerDetectorToolOutput:
        """
        Format result from external filler detector to match our schema.
        
        Args:
            result: Result from external filler detector
            
        Returns:
            FillerDetectorToolOutput with formatted results
        """
        
        # Extract values with defaults
        total_fillers = result.get("total_fillers", 0)
        filler_percentage = result.get("filler_percentage", 0.0)
        word_count = result.get("word_count", 0)
        fillers = result.get("fillers", {})
        most_common = result.get("most_common_filler")
        analysis = result.get("analysis", "Analysis not available.")
        improvement_tip = result.get("improvement_tip")
        analysis_method = result.get("analysis_method", "external")
        
        # Convert filler details
        filler_details = []
        if "filler_details" in result:
            for item in result["filler_details"]:
                if isinstance(item, str):
                    filler_details.append(FillerLocation(word=item))
        
        return FillerDetectorToolOutput(
            total_fillers=total_fillers,
            filler_percentage=filler_percentage,
            word_count=word_count,
            fillers=fillers,
            filler_details=filler_details,
            most_common_filler=most_common,
            analysis=analysis,
            improvement_tip=improvement_tip,
            analysis_method=analysis_method
        )
