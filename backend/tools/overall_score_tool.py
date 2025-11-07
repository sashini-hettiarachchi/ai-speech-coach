"""
Overall Score and Summary Tool: Calculate Overall Performance Score and Generate Feedback Summary

This tool calculates the overall performance score using CSSEF competency scores
and generates a structured feedback summary compatible with the Session model.

Features:
- Calculates weighted overall score from CSSEF competencies
- Generates structured feedback summary
- Compatible with existing Session model feedback_summary field
- Handles missing context scenarios
"""

import os
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from tools.base import BaseTool
from utils.constants import CONTEXT_DATA


class OverallScoreToolInput(BaseModel):
    """Input schema for Overall Score and Summary Tool"""
    
    cssef_scores: Dict[str, Dict[str, Any]] = Field(..., description="CSSEF competency scores and feedback")
    context: Optional[str] = Field(None, description="Speaking context for weighting")
    speech_duration: float = Field(..., description="Duration of speech in seconds")
    words_per_minute: float = Field(..., description="Speaking pace")
    filler_percentage: float = Field(..., description="Percentage of filler words")


class OverallScoreToolOutput(BaseModel):
    """Output schema for Overall Score and Summary Tool"""
    
    overall_score: float = Field(..., description="Weighted overall performance score (1-5)")
    feedback_summary: Dict[str, Any] = Field(..., description="Structured feedback summary for Session model")
    scoring_breakdown: Dict[str, float] = Field(..., description="Breakdown of weighted scores by competency")


class OverallScoreTool(BaseTool[OverallScoreToolInput, OverallScoreToolOutput]):
    """
    Tool for calculating overall performance score and generating feedback summary
    
    Uses CSSEF competency scores with context-specific weights to calculate
    an overall performance score and generates a structured feedback summary.
    """
    
    name = "overall_score_tool"
    description = "Calculates overall score and generates feedback summary"
    
    InputSchema = OverallScoreToolInput
    OutputSchema = OverallScoreToolOutput
    
    def __init__(self):
        """Initialize the tool with context weights"""
        # Load context weights from constants
        self.context_data = CONTEXT_DATA
        
        # Default weights if context data not available
        self.default_weights = {
            "C1_topic_choice": 0.14,
            "C2_purpose": 0.14,
            "C3_supporting_material": 0.14,
            "C4_organization": 0.14,
            "C5_language_use": 0.14,
            "C6_vocal_variety": 0.15,
            "C7_pronunciation_and_grammar": 0.15
        }
        
        print("Overall Score Tool initialized successfully")
    
    def run(self, inputs: OverallScoreToolInput) -> OverallScoreToolOutput:
        """
        Calculate overall score and generate feedback summary.
        
        Args:
            inputs: Overall score calculation inputs
            
        Returns:
            Overall score and feedback summary output
        """
        # Get context weights
        weights = self._get_context_weights(inputs.context)
        
        # Calculate weighted overall score
        overall_score, breakdown = self._calculate_overall_score(inputs.cssef_scores, weights)
        
        # Generate feedback summary
        feedback_summary = self._generate_feedback_summary(
            inputs.cssef_scores,
            overall_score,
            inputs.speech_duration,
            inputs.words_per_minute,
            inputs.filler_percentage,
            inputs.context
        )
        
        return OverallScoreToolOutput(
            overall_score=overall_score,
            feedback_summary=feedback_summary,
            scoring_breakdown=breakdown
        )
    
    def _get_context_weights(self, context: Optional[str]) -> Dict[str, float]:
        """Get appropriate weights for the given context"""
        
        if not context or not self.context_data:
            return self.default_weights
        
        context_lower = context.lower()
        context_scores = self.context_data.get("CONTEXT_SCORES", {})
        
        if context_lower in context_scores:
            # Return weights for C1-C7 only (exclude C8_physical_behaviors)
            weights = {}
            for key, value in context_scores[context_lower].items():
                if key.startswith(('C1_', 'C2_', 'C3_', 'C4_', 'C5_', 'C6_', 'C7_')):
                    weights[key] = value
            
            # Normalize weights to sum to 1.0 (excluding C8)
            total_weight = sum(weights.values())
            if total_weight > 0:
                return {k: v / total_weight for k, v in weights.items()}
        
        return self.default_weights
    
    def _calculate_overall_score(self, cssef_scores: Dict[str, Dict[str, Any]], weights: Dict[str, float]) -> tuple[float, Dict[str, float]]:
        """Calculate weighted overall score from CSSEF competencies"""
        
        total_score = 0.0
        total_weight = 0.0
        breakdown = {}
        
        # Map CSSEF evaluation keys to weight keys
        key_mapping = {
            'c1_topic_choice': 'C1_topic_choice',
            'c2_purpose': 'C2_purpose',
            'c3_supporting': 'C3_supporting_material',
            'c4_organization': 'C4_organization',
            'c5_language': 'C5_language_use',
            'c6_vocal_variety': 'C6_vocal_variety',
            'c7_pronunciation': 'C7_pronunciation_and_grammar'
        }
        
        for eval_key, weight_key in key_mapping.items():
            if eval_key in cssef_scores and weight_key in weights:
                competency_data = cssef_scores[eval_key]
                if isinstance(competency_data, dict) and 'score' in competency_data:
                    score = float(competency_data['score'])
                    weight = weights[weight_key]
                    
                    weighted_score = score * weight
                    total_score += weighted_score
                    total_weight += weight
                    breakdown[eval_key] = weighted_score
                    
                    print(f"CSSEF {eval_key}: score={score}, weight={weight:.3f}, weighted={weighted_score:.3f}")
        
        # Calculate final overall score
        if total_weight > 0:
            overall_score = total_score / total_weight
        else:
            overall_score = 3.0  # Default score if no valid scores
        
        # Ensure score is within 1-5 range
        overall_score = max(1.0, min(5.0, overall_score))
        
        print(f"Overall score calculation: {total_score:.3f} / {total_weight:.3f} = {overall_score:.3f}")
        
        return overall_score, breakdown
    
    def _generate_feedback_summary(self, 
                                 cssef_scores: Dict[str, Dict[str, Any]], 
                                 overall_score: float,
                                 duration: float,
                                 wpm: float,
                                 filler_percentage: float,
                                 context: Optional[str]) -> Dict[str, Any]:
        """Generate structured feedback summary compatible with Session model"""
        
        # Extract strengths and improvements from CSSEF scores
        strengths = []
        improvements = []
        
        for competency, data in cssef_scores.items():
            if isinstance(data, dict):
                score = data.get('score', 3.0)
                improvement = data.get('improvement', '')
                
                # If score is good (4+), it's a strength
                if score >= 4.0:
                    competency_name = self._get_competency_name(competency)
                    strengths.append(f"Strong {competency_name.lower()}")
                
                # If improvement suggestion exists and score is not excellent
                if improvement and score < 4.5:
                    improvements.append(improvement)
        
        # Ensure we have at least 2 strengths and improvements
        if len(strengths) < 2:
            strengths.extend([
                "Good effort in speech delivery",
                "Completed the presentation successfully"
            ][:2-len(strengths)])
        
        if len(improvements) < 2:
            improvements.extend([
                "Practice regularly to build confidence",
                "Focus on engaging the audience more effectively"
            ][:2-len(improvements)])
        
        # Create performance summary
        duration_minutes = duration / 60
        performance_level = self._get_performance_level(overall_score)
        
        summary_text = f"This was a {performance_level} {duration_minutes:.1f}-minute {context or 'general'} presentation. "
        
        # Add specific performance notes
        if wpm < 140:
            summary_text += "Speaking pace was slower than typical. "
        elif wpm > 200:
            summary_text += "Speaking pace was faster than typical. "
        
        if filler_percentage > 5:
            summary_text += "Reducing filler words would improve fluency. "
        elif filler_percentage < 2:
            summary_text += "Excellent fluency with minimal filler words. "
        
        # Structure compatible with Session model feedback_summary field
        feedback_summary = {
            "summary": summary_text.strip(),
            "strengths": strengths[:2],  # Limit to 2 for consistency
            "improvements": improvements[:2],  # Limit to 2 for consistency
            "overall_score": overall_score,
            "performance_level": performance_level,
            "metrics": {
                "duration_minutes": duration_minutes,
                "words_per_minute": wpm,
                "filler_percentage": filler_percentage
            }
        }
        
        return feedback_summary
    
    def _get_competency_name(self, competency_key: str) -> str:
        """Get human-readable competency name"""
        names = {
            'c1_topic_choice': 'Topic Choice',
            'c2_purpose': 'Purpose Communication',
            'c3_supporting': 'Supporting Material',
            'c4_organization': 'Organization',
            'c5_language': 'Language Use',
            'c6_vocal_variety': 'Vocal Variety',
            'c7_pronunciation': 'Pronunciation & Grammar'
        }
        return names.get(competency_key, competency_key.replace('_', ' ').title())
    
    def _get_performance_level(self, score: float) -> str:
        """Get performance level description from score"""
        if score >= 4.5:
            return "excellent"
        elif score >= 3.5:
            return "good"
        elif score >= 2.5:
            return "satisfactory"
        else:
            return "developing"