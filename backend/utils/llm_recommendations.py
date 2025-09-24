import requests
import json
import re
from typing import Dict, List, Optional

# Import configuration
try:
    from config import LLM_ENDPOINT, LLM_MODEL, LLM_TEMPERATURE
except ImportError:
    # Fallback values if config not available
    LLM_ENDPOINT = "http://localhost:11434/api/generate"
    LLM_MODEL = "llama3"
    LLM_TEMPERATURE = 0.3

class LLMRecommendationGenerator:
    """
    Enhanced LLM-based recommendation generator that integrates with knowledge servers
    """
    
    def __init__(self, llm_endpoint=LLM_ENDPOINT, model=LLM_MODEL):
        self.llm_endpoint = llm_endpoint
        self.model = model
    
    def generate_contextual_recommendations(
        self, 
        speech_analysis: dict, 
        user_context: dict = None,
        domain_context: dict = None, 
        event_context: dict = None,
        audience_context: dict = None
    ) -> dict:
        """
        Generate comprehensive recommendations using LLM with context from knowledge servers
        """
        
        # Build comprehensive context prompt
        context_prompt = self._build_context_prompt(
            speech_analysis, user_context, domain_context, event_context, audience_context
        )
        
        try:
            # Call LLM for recommendation generation
            llm_response = self._call_llm(context_prompt)
            if llm_response:
                return self._format_llm_recommendations(llm_response, speech_analysis)
        except Exception as e:
            print(f"LLM recommendation generation failed: {e}")
        
        # Fallback to rule-based recommendations
        return self._generate_fallback_recommendations(speech_analysis)
    
    def _build_context_prompt(self, speech_analysis, user_context, domain_context, event_context, audience_context):
        """
        Build a comprehensive prompt with all available context
        """
        
        prompt_parts = []
        
        # System prompt
        prompt_parts.append("""You are an expert speech coach providing personalized feedback. 
Analyze the speech data and context to generate specific, actionable recommendations.
Return your response as JSON in this exact format:

{
  "overall_score": 7.5,
  "strengths": ["Clear articulation", "Good pacing"],
  "areas_for_improvement": ["Reduce filler words", "Increase vocal variety"],
  "specific_recommendations": [
    {
      "category": "Delivery",
      "recommendation": "Practice pausing instead of using filler words",
      "rationale": "Based on 5 'um' instances detected",
      "priority": "high"
    }
  ],
  "context_specific_tips": ["Tip 1", "Tip 2"],
  "next_steps": ["Action 1", "Action 2"]
}""")
        
        # Speech analysis data
        prompt_parts.append(f"\n## SPEECH ANALYSIS DATA:")
        prompt_parts.append(f"- Transcript: {speech_analysis.get('transcript', 'N/A')}")
        prompt_parts.append(f"- Word count: {speech_analysis.get('word_count', 0)}")
        
        if 'fillers' in speech_analysis:
            fillers = speech_analysis['fillers']
            prompt_parts.append(f"- Filler words: {fillers.get('total_fillers', 0)} total ({fillers.get('filler_percentage', 0):.1f}%)")
            if fillers.get('fillers'):
                prompt_parts.append(f"- Filler breakdown: {fillers['fillers']}")
        
        if 'delivery_metrics' in speech_analysis:
            metrics = speech_analysis['delivery_metrics']
            prompt_parts.append(f"- Speaking pace: {metrics.get('pace', 'N/A')} WPM")
            prompt_parts.append(f"- Vocal variety: {metrics.get('vocal_variety', 'N/A')}/10")
            prompt_parts.append(f"- Confidence level: {metrics.get('confidence', 'N/A')}/10")
        
        # User context
        if user_context:
            prompt_parts.append(f"\n## USER PROFILE:")
            prompt_parts.append(f"- Experience level: {user_context.get('speaking_experience', 'Unknown')}")
            prompt_parts.append(f"- Goals: {user_context.get('goals', 'Not specified')}")
            prompt_parts.append(f"- Previous feedback: {user_context.get('previous_feedback', 'None')}")
        
        # Domain context
        if domain_context:
            prompt_parts.append(f"\n## DOMAIN CONTEXT ({domain_context.get('domain', 'Unknown')}):")
            prompt_parts.append(f"- Standards: {domain_context.get('standards', 'General')}")
            prompt_parts.append(f"- Best practices: {domain_context.get('best_practices', [])}")
            prompt_parts.append(f"- Common challenges: {domain_context.get('challenges', [])}")
        
        # Event context
        if event_context:
            prompt_parts.append(f"\n## EVENT CONTEXT:")
            prompt_parts.append(f"- Event type: {event_context.get('event_type', 'Unknown')}")
            prompt_parts.append(f"- Duration: {event_context.get('duration', 'Unknown')}")
            prompt_parts.append(f"- Success criteria: {event_context.get('success_criteria', [])}")
        
        # Audience context
        if audience_context:
            prompt_parts.append(f"\n## AUDIENCE CONTEXT:")
            prompt_parts.append(f"- Audience type: {audience_context.get('audience_type', 'Unknown')}")
            prompt_parts.append(f"- Expectations: {audience_context.get('expectations', [])}")
            prompt_parts.append(f"- Communication preferences: {audience_context.get('communication_style', 'Unknown')}")
        
        prompt_parts.append("\n## INSTRUCTIONS:")
        prompt_parts.append("Generate personalized recommendations considering all the above context.")
        prompt_parts.append("Focus on actionable advice that addresses the specific speech analysis results.")
        prompt_parts.append("Consider the user's experience level, domain requirements, event type, and audience expectations.")
        prompt_parts.append("Return ONLY the JSON response with no additional text.")
        
        return "\n".join(prompt_parts)
    
    def _call_llm(self, prompt: str) -> Optional[dict]:
        """
        Call the LLM API with the constructed prompt
        """
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": LLM_TEMPERATURE,  # Slightly creative but consistent
                "top_p": 0.9,
                "num_predict": 1000,  # Allow longer responses
                "stop": ["\n\n\n"]  # Stop at multiple newlines
            }
        }
        
        try:
            response = requests.post(
                self.llm_endpoint,
                json=payload,
                timeout=60,  # Longer timeout for complex analysis
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get("response", "").strip()
                
                # Extract JSON from response
                return self._extract_json_response(response_text)
            else:
                print(f"LLM API error: HTTP {response.status_code}")
                return None
                
        except requests.RequestException as e:
            print(f"LLM service error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected LLM error: {e}")
            return None
    
    def _extract_json_response(self, text: str) -> Optional[dict]:
        """
        Extract JSON from LLM response using multiple strategies
        """
        
        # Strategy 1: Direct JSON parsing
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Find JSON block
        json_patterns = [
            r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Nested braces
            r'\{.*?\}',  # Simple braces
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    result = json.loads(match.strip())
                    if self._validate_recommendation_structure(result):
                        return result
                except json.JSONDecodeError:
                    continue
        
        # Strategy 3: Manual extraction for key fields
        return self._extract_manual_recommendations(text)
    
    def _validate_recommendation_structure(self, data: dict) -> bool:
        """
        Validate that the response has the expected recommendation structure
        """
        required_fields = ["specific_recommendations", "areas_for_improvement"]
        return (isinstance(data, dict) and 
                any(field in data for field in required_fields))
    
    def _extract_manual_recommendations(self, text: str) -> dict:
        """
        Manually extract recommendations when JSON parsing fails
        """
        recommendations = {
            "overall_score": 7.0,
            "strengths": [],
            "areas_for_improvement": [],
            "specific_recommendations": [],
            "context_specific_tips": [],
            "next_steps": []
        }
        
        # Extract sections using regex patterns
        sections = {
            "strengths": r"strengths?[:\-]\s*(.+?)(?=areas|specific|next|$)",
            "areas_for_improvement": r"areas?[:\-]\s*(.+?)(?=specific|next|$)",
            "recommendations": r"recommendations?[:\-]\s*(.+?)(?=next|tips|$)",
            "tips": r"tips?[:\-]\s*(.+?)(?=next|$)",
            "next_steps": r"next\s+steps?[:\-]\s*(.+?)$"
        }
        
        for key, pattern in sections.items():
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                content = match.group(1).strip()
                # Split by bullet points or numbers
                items = re.split(r'[\n•\-\*]\s*', content)
                items = [item.strip() for item in items if item.strip()]
                
                if key == "recommendations":
                    for item in items:
                        recommendations["specific_recommendations"].append({
                            "category": "General",
                            "recommendation": item,
                            "rationale": "Based on speech analysis",
                            "priority": "medium"
                        })
                else:
                    recommendations[key] = items[:3]  # Limit to 3 items
        
        return recommendations
    
    def _format_llm_recommendations(self, llm_response: dict, speech_analysis: dict) -> dict:
        """
        Format and enhance LLM recommendations with additional metadata
        """
        
        result = {
            "status": "success",
            "generation_method": "llm",
            "overall_score": llm_response.get("overall_score", 7.0),
            "strengths": llm_response.get("strengths", []),
            "areas_for_improvement": llm_response.get("areas_for_improvement", []),
            "specific_recommendations": llm_response.get("specific_recommendations", []),
            "context_specific_tips": llm_response.get("context_specific_tips", []),
            "next_steps": llm_response.get("next_steps", []),
            "personalized": True,
            "context_applied": True
        }
        
        # Add metadata
        result["analysis_summary"] = {
            "total_words": speech_analysis.get('word_count', 0),
            "filler_percentage": speech_analysis.get('fillers', {}).get('filler_percentage', 0),
            "primary_focus_areas": [rec.get("category") for rec in result["specific_recommendations"][:3]]
        }
        
        return result
    
    def _generate_fallback_recommendations(self, speech_analysis: dict) -> dict:
        """
        Generate rule-based recommendations when LLM is unavailable
        """
        
        recommendations = []
        tips = []
        areas = []
        
        # Analyze filler words
        fillers = speech_analysis.get('fillers', {})
        if fillers.get('total_fillers', 0) > 0:
            filler_pct = fillers.get('filler_percentage', 0)
            areas.append("Reduce filler word usage")
            
            if filler_pct > 5:
                recommendations.append({
                    "category": "Fluency",
                    "recommendation": "Practice speaking with intentional pauses instead of filler words",
                    "rationale": f"Detected {fillers['total_fillers']} filler words ({filler_pct:.1f}% of speech)",
                    "priority": "high"
                })
            else:
                recommendations.append({
                    "category": "Fluency", 
                    "recommendation": "Continue working on minimizing filler words",
                    "rationale": f"Good progress with only {filler_pct:.1f}% filler words",
                    "priority": "medium"
                })
        
        # Analyze delivery metrics
        delivery = speech_analysis.get('delivery_metrics', {})
        if delivery:
            pace = delivery.get('pace', 140)
            if pace < 120:
                areas.append("Increase speaking pace")
                recommendations.append({
                    "category": "Pacing",
                    "recommendation": "Practice speaking at a slightly faster pace",
                    "rationale": f"Current pace of {pace} WPM is slower than optimal (120-160 WPM)",
                    "priority": "medium"
                })
            elif pace > 180:
                areas.append("Slow down speaking pace")
                recommendations.append({
                    "category": "Pacing",
                    "recommendation": "Practice speaking more slowly for better comprehension",
                    "rationale": f"Current pace of {pace} WPM may be too fast for audience",
                    "priority": "high"
                })
        
        return {
            "status": "success",
            "generation_method": "rule_based",
            "overall_score": 7.0,
            "strengths": ["Clear communication attempt", "Willingness to practice"],
            "areas_for_improvement": areas,
            "specific_recommendations": recommendations,
            "context_specific_tips": [
                "Record yourself practicing to build self-awareness",
                "Practice with different types of content",
                "Focus on one improvement area at a time"
            ],
            "next_steps": [
                "Practice the top recommendation daily",
                "Record progress weekly",
                "Seek feedback from others"
            ],
            "personalized": False,
            "context_applied": False
        }

# Global instance for easy usage
llm_recommender = LLMRecommendationGenerator()
