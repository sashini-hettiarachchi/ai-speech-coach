"""
Overall Score Tool: Calculate Overall Performance Score

This tool calculates the overall performance score using CSSEF competency scores
with context-specific weights.

Features:
- Calculates weighted overall score from CSSEF competencies
- Provides breakdown of weighted scores by competency
- Handles missing context scenarios with default weights
"""

import os
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from tools.base import BaseTool
from utils.constants import CONTEXT_DATA


class OverallScoreToolInput(BaseModel):
    """Input schema for Overall Score Tool"""
    
    cssef_scores: Dict[str, Dict[str, Any]] = Field(..., description="CSSEF competency scores and feedback")
    context: Optional[str] = Field(None, description="Speaking context for weighting")


class OverallScoreToolOutput(BaseModel):
    """Output schema for Overall Score Tool"""
    
    overall_score: float = Field(..., description="Weighted overall performance score (1-5)")
    scoring_breakdown: Dict[str, float] = Field(..., description="Breakdown of weighted scores by competency")


class OverallScoreTool(BaseTool[OverallScoreToolInput, OverallScoreToolOutput]):
    """
    Tool for calculating overall performance score from CSSEF competencies
    
    Uses CSSEF competency scores with context-specific weights to calculate
    an overall performance score and provides breakdown by competency.
    """
    
    name = "overall_score_tool"
    description = "Calculates overall score from CSSEF competencies"
    
    InputSchema = OverallScoreToolInput
    OutputSchema = OverallScoreToolOutput
    
    def __init__(self):
        """Initialize the tool with context weights"""
        # Load context weights from constants
        self.context_data = CONTEXT_DATA
        
        # Default weights if context data not available
        self.default_weights = {
            "C1_topic_choice": 0.142,
            "C2_purpose": 0.142,
            "C3_supporting_material": 1/7,
            "C4_organization": 1/7,
            "C5_language_use": 1/7,
            "C6_vocal_variety": 1/7,
            "C7_pronunciation_and_grammar": 1/7
        }
        
        print("Overall Score Tool initialized successfully")
    
    def run(self, inputs: OverallScoreToolInput) -> OverallScoreToolOutput:
        """
        Calculate overall score from CSSEF competencies.
        
        Args:
            inputs: Overall score calculation inputs
            
        Returns:
            Overall score and breakdown output
        """
        # Get context weights
        weights = self._get_context_weights(inputs.context)
        
        # Calculate weighted overall score
        overall_score, breakdown = self._calculate_overall_score(inputs.cssef_scores, weights)
        
        return OverallScoreToolOutput(
            overall_score=overall_score,
            scoring_breakdown=breakdown
        )
    
    def _get_context_weights(self, context: Optional[str]) -> Optional[Dict[str, float]]:
        """Get appropriate weights for the given context"""
        
        if not context or not self.context_data:
            return None  # No weights for no context - use simple average
        
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
        
        return None  # No valid context found - use simple average
    
    def _calculate_overall_score(self, cssef_scores: Dict[str, Dict[str, Any]], weights: Optional[Dict[str, float]]) -> tuple[float, Dict[str, float]]:
        """Calculate weighted overall score from CSSEF competencies"""
        
        total_score = 0.0
        total_weight = 0.0
        breakdown = {}
        valid_score_count = 0
        
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
        
        # If no weights (no context), calculate simple average
        if weights is None:
            print("No context provided - calculating simple average of CSSEF scores")
            for eval_key in key_mapping.keys():
                if eval_key in cssef_scores:
                    competency_data = cssef_scores[eval_key]
                    if isinstance(competency_data, dict) and 'score' in competency_data:
                        score = float(competency_data['score'])
                        total_score += score
                        valid_score_count += 1
                        breakdown[eval_key] = score
                        
                        print(f"CSSEF {eval_key}: score={score} (unweighted)")
            
            # Calculate simple average
            if valid_score_count > 0:
                overall_score = total_score / valid_score_count
            else:
                overall_score = 0
                
            print(f"Simple average calculation: {total_score:.3f} / {valid_score_count} = {overall_score:.3f}")
        
        # If weights provided (context available), calculate weighted average
        else:
            print("Context provided - calculating weighted average of CSSEF scores")
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
            
            # Calculate weighted average
            if total_weight > 0:
                overall_score = total_score / total_weight
            else:
                overall_score = 0
                
            print(f"Weighted average calculation: {total_score:.3f} / {total_weight:.3f} = {overall_score:.3f}")
        
        # Ensure score is within 1-5 range
        overall_score = max(1.0, min(5.0, overall_score))
        
        return overall_score, breakdown