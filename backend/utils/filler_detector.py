import requests
import json
import re
from typing import Dict, List

# Import configuration with fallback
try:
    from config import LLM_ENDPOINT, LLM_MODEL, LLM_TEMPERATURE
except ImportError:
    LLM_ENDPOINT = "http://localhost:11434/api/generate"
    LLM_MODEL = "llama3"
    LLM_TEMPERATURE = 0

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

def count_filler_words(transcript: str) -> dict:
    """
    Analyzes transcript for filler words using LLM with enhanced fallback.
    Returns detailed analysis with counts, percentages, and insights.
    """
    
    if not transcript or not transcript.strip():
        return {
            "total_fillers": 0,
            "filler_percentage": 0.0,
            "fillers": {},
            "filler_details": [],
            "word_count": 0,
            "analysis": "No transcript provided for analysis."
        }

    # Try LLM analysis first
    try:
        llm_result = _analyze_with_llm(transcript)
        if llm_result:
            return llm_result
    except Exception as e:
        print(f"LLM analysis failed: {e}")
    
    # Fallback to enhanced rule-based analysis
    print("Using enhanced rule-based filler analysis...")
    return _enhanced_rule_based_analysis(transcript)

def _analyze_with_llm(transcript: str) -> dict:
    """
    Use LLM for filler word detection with improved prompting.
    """
    
    enhanced_prompt = f"""You are a speech analysis expert. Analyze this transcript and count filler words precisely.

FILLER WORDS TO DETECT:
{', '.join(FILLERS)}

INSTRUCTIONS:
1. Count each filler word occurrence (case-insensitive)
2. Include multi-word phrases like "you know", "I mean"
3. Don't count words when they have semantic meaning
4. Return ONLY a valid JSON object in this exact format in json
example response:
{{"filler_counts": {{"um": 3, "like": 5, "you know": 2}}, "total_fillers": 10}}

TRANSCRIPT TO ANALYZE:
"{transcript}"

RESPONSE (JSON only):"""

    try:
        response = requests.post(
            LLM_ENDPOINT,
            json={
                "model": LLM_MODEL, 
                "prompt": enhanced_prompt, 
                "stream": False,
                "options": {
                    "temperature": LLM_TEMPERATURE,
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
        
        # Extract and validate JSON
        parsed_result = _extract_and_validate_json(result_text)
        if parsed_result:
            return _format_analysis_result(parsed_result, transcript, "llm")
            
    except requests.RequestException as e:
        print(f"LLM service error: {e}")
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
    except Exception as e:
        print(f"Unexpected LLM error: {e}")
    
    return None

def _extract_and_validate_json(text: str) -> dict:
    """
    Extract JSON from LLM response using multiple strategies.
    """
    
    # Strategy 1: Direct JSON parsing
    try:
        result = json.loads(text.strip())
        if _validate_json_structure(result):
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
                if _validate_json_structure(result):
                    return result
            except json.JSONDecodeError:
                continue
    
    # Strategy 3: Manual extraction of key-value pairs
    return _extract_manual_counts(text)

def _validate_json_structure(data: dict) -> bool:
    """
    Validate that JSON has expected structure.
    """
    return (isinstance(data, dict) and 
            "filler_counts" in data and 
            isinstance(data["filler_counts"], dict))

def _extract_manual_counts(text: str) -> dict:
    """
    Manually extract filler counts from text when JSON parsing fails.
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

def _enhanced_rule_based_analysis(transcript: str) -> dict:
    """
    Enhanced rule-based filler word detection with pattern matching.
    """
    
    # Normalize transcript
    text = transcript.lower().strip()
    word_count = len(transcript.split())
    
    filler_counts = {}
    filler_details = []
    
    # Process single-word fillers
    single_word_fillers = [f for f in FILLERS if ' ' not in f]
    for filler in single_word_fillers:
        # Use word boundaries to avoid partial matches
        pattern = rf'\b{re.escape(filler)}\b'
        matches = re.findall(pattern, text)
        count = len(matches)
        if count > 0:
            filler_counts[filler] = count
            filler_details.extend([filler] * count)
    
    # Process multi-word fillers
    multi_word_fillers = [f for f in FILLERS if ' ' in f]
    for filler in multi_word_fillers:
        pattern = rf'\b{re.escape(filler)}\b'
        matches = re.findall(pattern, text)
        count = len(matches)
        if count > 0:
            filler_counts[filler] = count
            filler_details.extend([filler] * count)
    
    return _format_analysis_result(
        {"filler_counts": filler_counts, "total_fillers": sum(filler_counts.values())},
        transcript,
        "rule_based"
    )

def _format_analysis_result(parsed_result: dict, transcript: str, method: str) -> dict:
    """
    Format analysis result into standardized response.
    """
    
    filler_counts = parsed_result.get("filler_counts", {})
    total_fillers = parsed_result.get("total_fillers", sum(filler_counts.values()))
    
    word_count = len(transcript.split())
    filler_percentage = (total_fillers / word_count * 100) if word_count > 0 else 0
    
    # Create detailed list of found fillers
    filler_details = []
    for filler, count in filler_counts.items():
        if count > 0:
            filler_details.extend([filler] * count)
    
    # Generate contextual analysis
    if total_fillers == 0:
        analysis = "Excellent! No filler words detected. Very clear and professional delivery."
    elif filler_percentage < 1:
        analysis = f"Outstanding delivery! Only {total_fillers} filler words ({filler_percentage:.1f}%) - extremely professional."
    elif filler_percentage < 3:
        analysis = f"Great job! {total_fillers} filler words detected ({filler_percentage:.1f}%) - very good delivery with room for minor polish."
    elif filler_percentage < 5:
        analysis = f"Good delivery with {total_fillers} filler words ({filler_percentage:.1f}%). Consider practicing pauses instead of fillers."
    else:
        analysis = f"Focus area identified: {total_fillers} filler words ({filler_percentage:.1f}%). Practice reducing these for more professional delivery."
    
    # Find most common filler for targeted feedback
    most_common_filler = max(filler_counts, key=filler_counts.get) if filler_counts else None
    
    result = {
        "total_fillers": total_fillers,
        "filler_percentage": round(filler_percentage, 2),
        "fillers": filler_counts,
        "filler_details": filler_details,
        "word_count": word_count,
        "analysis": analysis,
        "analysis_method": method
    }
    
    if most_common_filler:
        result["most_common_filler"] = most_common_filler
        result["improvement_tip"] = f"Focus on reducing '{most_common_filler}' - used {filler_counts[most_common_filler]} times."
    
    return result
