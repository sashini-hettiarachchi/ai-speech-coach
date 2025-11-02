"""
ScorerTool: Calculates competency scores based on speech analysis metrics.

This tool aggregates data from all analysis tools and calculates standardized
scores for various communication competencies based on the CSSEF framework
and context-specific weight profiles.
"""

import os
import json
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field
from tools.base import BaseTool

class ScorerToolInput(BaseModel):
    """Input schema for ScorerTool"""
    # Transcription metrics
    transcript: str = Field(..., description="Full transcript text")
    word_count: int = Field(..., description="Total word count")
    
    # Audio prosody metrics
    words_per_minute: float = Field(..., description="Speaking pace in words per minute")
    pitch_variation: float = Field(..., description="Standard deviation of pitch")
    filler_percentage: float = Field(..., description="Percentage of words that are fillers")
    pause_count: int = Field(..., description="Number of significant pauses")
    
    # NLP structure metrics
    structure_quality: float = Field(..., description="Structure quality score (0-10)")
    readability_score: float = Field(..., description="Readability score (0-100)")
    
    # Pronunciation metrics
    pronunciation_score: float = Field(..., description="Pronunciation accuracy (0-100)")
    grammar_error_count: int = Field(..., description="Number of grammar errors")
    
    # Video pose metrics (optional)
    eye_contact_pct: float = Field(None, description="Eye contact percentage")
    gesture_rate: float = Field(None, description="Gestures per minute")
    facial_expressiveness: float = Field(None, description="Facial expressiveness (0-10)")
    
    # Context parameters
    context_label: str = Field("Academic", description="Speaking context (Academic, Persuasive, Storytelling)")

class CompetencyScores(BaseModel):
    """Schema for CSSEF (Communication Skills and Speaker Effectiveness Framework) competency scores"""
    clarity: float = Field(..., description="Clarity of communication (0-1)")
    confidence: float = Field(..., description="Speaker confidence (0-1)")
    engagement: float = Field(..., description="Audience engagement (0-1)")
    structure: float = Field(..., description="Content structure and organization (0-1)")
    delivery: float = Field(..., description="Delivery style effectiveness (0-1)")
    language_use: float = Field(..., description="Language use and vocabulary (0-1)")
    nonverbal: float = Field(..., description="Nonverbal communication (0-1)")
    persuasiveness: float = Field(..., description="Persuasive impact (0-1)")

class CSEFCompetencyScores(BaseModel):
    """Schema for the 8 CSSEF competencies"""
    C1_topic_choice: float = Field(..., description="Topic choice & focus (0-1)")
    C2_thesis: float = Field(..., description="Thesis & purpose (0-1)")
    C3_supporting: float = Field(..., description="Supporting materials (0-1)")
    C4_organization: float = Field(..., description="Organization & structure (0-1)")
    C5_language: float = Field(..., description="Language use (0-1)")
    C6_vocal_variety: float = Field(..., description="Vocal variety & delivery (0-1)")
    C7_pronunciation: float = Field(..., description="Pronunciation & articulation (0-1)")
    C8_physical: float = Field(..., description="Physical delivery (0-1)")

class CompetencyPriority(BaseModel):
    """Schema for a prioritized competency"""
    competency: str = Field(..., description="Competency name")
    score: float = Field(..., description="Score (0-1)")
    weight: float = Field(..., description="Context-specific weight")
    priority: float = Field(..., description="Priority score (higher needs more attention)")

class ScorerToolOutput(BaseModel):
    """Output schema for ScorerTool"""
    competency_scores: CompetencyScores = Field(
        ..., 
        description="Calculated scores for each competency area"
    )
    cssef_scores: CSEFCompetencyScores = Field(
        ...,
        description="CSSEF framework competency scores"
    )
    overall_score: float = Field(
        ..., 
        description="Overall context-weighted effectiveness score (0-1)"
    )
    strengths: List[str] = Field(
        default_factory=list,
        description="List of identified strengths"
    )
    areas_for_improvement: List[str] = Field(
        default_factory=list,
        description="List of areas for improvement"
    )
    priorities: List[CompetencyPriority] = Field(
        default_factory=list,
        description="Prioritized list of competencies for improvement based on context weights"
    )
    context_weights: List[float] = Field(
        default_factory=list,
        description="Context weights used for scoring"
    )
    context_label: str = Field(
        "Academic",
        description="Speaking context used for weighting"
    )

class ScorerTool(BaseTool[ScorerToolInput, ScorerToolOutput]):
    """
    Tool for calculating competency scores based on speech analysis metrics.
    
    Aggregates data from all analysis tools and calculates standardized
    scores for various communication competencies based on the CSSEF
    (Communication Skills and Speaker Effectiveness Framework).
    
    Features context-aware scoring that weighs competencies differently
    based on the speaking context (Academic, Persuasive, Storytelling).
    """
    
    name = "scorer_tool"
    description = "Calculates context-aware competency scores based on speech analysis metrics"
    
    # Define schemas for type checking
    InputSchema = ScorerToolInput
    OutputSchema = ScorerToolOutput
    
    def __init__(self):
        """Initialize the ScorerTool with context weights from JSON file"""
        self.weights_path = os.path.join(os.path.dirname(__file__), "../data/context_weights.json")
        self.context_weights = self._load_context_weights()
        self.valid_contexts = list(self.context_weights.keys())
        
        # Define the mapping from raw competencies to CSSEF competencies
        self.competency_mapping = {
            "C1_topic_choice": ["clarity"],
            "C2_thesis": ["clarity", "structure"],
            "C3_supporting": ["structure"],
            "C4_organization": ["structure"],
            "C5_language": ["language_use"],
            "C6_vocal_variety": ["delivery"],
            "C7_pronunciation": ["clarity", "delivery"],
            "C8_physical": ["nonverbal"]
        }
        
    def _load_context_weights(self) -> Dict[str, List[float]]:
        """Load context weights from JSON file"""
        try:
            with open(self.weights_path, 'r') as f:
                weights = json.load(f)
            return weights
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # Default weights if file not found or invalid
            default_weights = {
                "Academic": [0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125],
                "Persuasive": [0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125],
                "Storytelling": [0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125]
            }
            print(f"Warning: Could not load context weights ({str(e)}). Using default weights.")
            return default_weights
    
    def run(self, inputs: ScorerToolInput) -> ScorerToolOutput:
        """
        Calculate competency scores from speech analysis metrics.
        
        Args:
            inputs (ScorerToolInput): Input parameters with speech metrics
        
        Returns:
            ScorerToolOutput: Calculated competency scores and insights
        """
        # Normalize context label and validate
        context_label = inputs.context_label.strip().title()
        if context_label not in self.valid_contexts:
            print(f"Warning: Unknown context '{context_label}'. Using 'Academic' instead.")
            context_label = "Academic"
            
        # Get context weights
        context_weights = self.context_weights[context_label]
        
        # Calculate base competency scores
        # Simple scoring implementation
        # In a real implementation, this would use a more sophisticated model
        
        # Calculate clarity score
        clarity = self._calculate_clarity(
            inputs.pronunciation_score,
            inputs.words_per_minute,
            inputs.filler_percentage
        )
        
        # Calculate confidence score
        confidence = self._calculate_confidence(
            inputs.pitch_variation,
            inputs.pause_count,
            inputs.words_per_minute
        )
        
        # Calculate structure score
        structure = inputs.structure_quality / 10.0
        
        # Calculate language use score
        language_use = self._calculate_language_use(
            inputs.readability_score,
            inputs.grammar_error_count,
            inputs.word_count
        )
        
        # Calculate delivery score
        delivery = self._calculate_delivery(
            inputs.words_per_minute,
            inputs.pitch_variation,
            inputs.filler_percentage
        )
        
        # Calculate nonverbal score (if video data is available)
        if all(v is not None for v in [inputs.eye_contact_pct, inputs.gesture_rate, inputs.facial_expressiveness]):
            nonverbal = self._calculate_nonverbal(
                inputs.eye_contact_pct,
                inputs.gesture_rate,
                inputs.facial_expressiveness
            )
        else:
            # Default score if no video data
            nonverbal = 0.75
        
        # Calculate engagement score (composite of other scores)
        engagement = self._calculate_engagement(clarity, delivery, nonverbal)
        
        # Calculate persuasiveness score (composite of other scores)
        persuasiveness = self._calculate_persuasiveness(clarity, confidence, structure, engagement)
        
        # Create competency scores object
        competency_scores = CompetencyScores(
            clarity=clarity,
            confidence=confidence,
            structure=structure,
            language_use=language_use,
            delivery=delivery,
            nonverbal=nonverbal,
            engagement=engagement,
            persuasiveness=persuasiveness
        )
        
        # Map to CSSEF competencies
        cssef_scores = self._map_to_cssef_competencies(competency_scores)
        
        # Calculate context-weighted overall score
        overall_score = self._calculate_context_weighted_score(cssef_scores, context_weights)
        
        # Calculate priorities
        priorities = self._calculate_priorities(cssef_scores, context_weights)
        
        # Identify strengths and areas for improvement based on CSSEF scores
        cssef_dict = cssef_scores.dict()
        strengths = [k for k, v in cssef_dict.items() if v >= 0.75]
        areas_for_improvement = [k for k, v in cssef_dict.items() if v < 0.6]
        
        return ScorerToolOutput(
            competency_scores=competency_scores,
            cssef_scores=cssef_scores,
            overall_score=overall_score,
            strengths=[self._format_competency_name(s) for s in strengths[:3]],
            areas_for_improvement=[self._format_competency_name(a) for a in areas_for_improvement[:3]],
            priorities=priorities,
            context_weights=context_weights,
            context_label=context_label
        )

    def _format_competency_name(self, name: str) -> str:
        """Format competency name for display"""
        # Handle CSSEF competencies with special formatting
        if name.startswith('C') and '_' in name:
            # Extract the competency number and description
            parts = name.split('_', 1)
            if len(parts) == 2:
                competency_num = parts[0]  # e.g., "C1"
                description = parts[1].replace('_', ' ')  # e.g., "topic choice"
                return f"{competency_num}: {description.capitalize()}"
        
        # Handle regular competency names
        return name.replace('_', ' ').capitalize()
    
    def _calculate_clarity(self, pronunciation_score, words_per_minute, filler_percentage):
        """Calculate clarity score"""
        # Higher pronunciation, optimal WPM, low fillers = better clarity
        pronunciation_factor = pronunciation_score / 100.0
        
        # Penalize too fast or too slow speech
        pace_optimality = 1.0 - min(abs(words_per_minute - 150) / 100.0, 0.5)
        
        # Penalize filler words
        filler_factor = 1.0 - min(filler_percentage / 10.0, 0.8)
        
        return min(max(pronunciation_factor * 0.5 + pace_optimality * 0.2 + filler_factor * 0.3, 0.0), 1.0)
    
    def _calculate_confidence(self, pitch_variation, pause_count, words_per_minute):
        """Calculate confidence score"""
        # Moderate pitch variation, appropriate pauses, good pace = better confidence
        pitch_factor = min(pitch_variation / 50.0, 1.0)
        
        # Some pauses are good, but not too many
        pause_factor = 1.0 - min(abs(pause_count - 5) / 10.0, 0.5)
        
        # Higher WPM (within reason) suggests confidence
        pace_factor = min(words_per_minute / 160.0, 1.0)
        
        return min(max(pitch_factor * 0.4 + pause_factor * 0.3 + pace_factor * 0.3, 0.0), 1.0)
    
    def _calculate_language_use(self, readability_score, grammar_error_count, word_count):
        """Calculate language use score"""
        # Higher readability, fewer grammar errors = better language use
        readability_factor = readability_score / 100.0
        
        # Normalize grammar errors by word count
        error_rate = grammar_error_count / max(word_count / 100.0, 1.0)
        grammar_factor = 1.0 - min(error_rate, 1.0)
        
        return min(max(readability_factor * 0.6 + grammar_factor * 0.4, 0.0), 1.0)
    
    def _calculate_delivery(self, words_per_minute, pitch_variation, filler_percentage):
        """Calculate delivery score"""
        # Optimal pace, good pitch variation, low fillers = better delivery
        
        # Ideal WPM around 140-160
        pace_optimality = 1.0 - min(abs(words_per_minute - 150) / 100.0, 0.5)
        
        # Good pitch variation, but not too much
        pitch_optimality = 1.0 - min(abs(pitch_variation - 30) / 30.0, 0.5)
        
        # Fewer fillers = better delivery
        filler_factor = 1.0 - min(filler_percentage / 8.0, 0.8)
        
        return min(max(pace_optimality * 0.4 + pitch_optimality * 0.3 + filler_factor * 0.3, 0.0), 1.0)
    
    def _calculate_nonverbal(self, eye_contact_pct, gesture_rate, facial_expressiveness):
        """Calculate nonverbal communication score"""
        # Good eye contact, appropriate gestures, and expressiveness = better nonverbal
        eye_contact_factor = eye_contact_pct / 100.0
        
        # Optimal gesture rate around 8-12 per minute
        gesture_optimality = 1.0 - min(abs(gesture_rate - 10) / 15.0, 0.5)
        
        # Facial expressiveness (already 0-10 scale)
        expression_factor = facial_expressiveness / 10.0
        
        return min(max(eye_contact_factor * 0.4 + gesture_optimality * 0.3 + expression_factor * 0.3, 0.0), 1.0)
    
    def _calculate_engagement(self, clarity, delivery, nonverbal):
        """Calculate audience engagement score"""
        # Engagement is a composite of clarity, delivery, and nonverbal
        return min(max(clarity * 0.3 + delivery * 0.4 + nonverbal * 0.3, 0.0), 1.0)
    
    def _calculate_persuasiveness(self, clarity, confidence, structure, engagement):
        """Calculate persuasiveness score"""
        # Persuasiveness is a composite of clarity, confidence, structure, and engagement
        return min(max(clarity * 0.25 + confidence * 0.25 + structure * 0.25 + engagement * 0.25, 0.0), 1.0)
    
    def _map_to_cssef_competencies(self, competency_scores: CompetencyScores) -> CSEFCompetencyScores:
        """
        Map raw competency scores to CSSEF competencies.
        
        Args:
            competency_scores: Raw competency scores
            
        Returns:
            CSEFCompetencyScores: Mapped CSSEF competency scores
        """
        # Get raw scores as a dictionary
        scores = competency_scores.dict()
        
        # TODO: Refine these mappings with more sophisticated weightings
        # This is a simple mapping implementation that can be enhanced later
        
        # Map C1: Topic choice & focus (primarily from clarity)
        c1_score = scores["clarity"]
        
        # Map C2: Thesis & purpose (from clarity and structure)
        c2_score = 0.7 * scores["clarity"] + 0.3 * scores["structure"]
        
        # Map C3: Supporting materials (primarily from structure)
        c3_score = scores["structure"]
        
        # Map C4: Organization & structure (directly from structure)
        c4_score = scores["structure"]
        
        # Map C5: Language use (directly from language_use)
        c5_score = scores["language_use"]
        
        # Map C6: Vocal variety & delivery (primarily from delivery)
        c6_score = scores["delivery"]
        
        # Map C7: Pronunciation & articulation (from clarity and delivery)
        c7_score = 0.6 * scores["clarity"] + 0.4 * scores["delivery"]
        
        # Map C8: Physical delivery (directly from nonverbal)
        c8_score = scores["nonverbal"]
        
        return CSEFCompetencyScores(
            C1_topic_choice=c1_score,
            C2_thesis=c2_score,
            C3_supporting=c3_score,
            C4_organization=c4_score,
            C5_language=c5_score,
            C6_vocal_variety=c6_score,
            C7_pronunciation=c7_score,
            C8_physical=c8_score
        )
    
    def _calculate_context_weighted_score(self, cssef_scores: CSEFCompetencyScores, weights: List[float]) -> float:
        """
        Calculate the context-weighted overall score.
        
        Args:
            cssef_scores: CSSEF competency scores
            weights: Context-specific weights for each CSSEF competency
            
        Returns:
            float: Context-weighted overall score (0-1)
        """
        scores = list(cssef_scores.dict().values())
        
        # Calculate weighted sum
        weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
        
        # Ensure result is in range [0, 1]
        return min(max(weighted_sum, 0.0), 1.0)
    
    def _calculate_priorities(self, cssef_scores: CSEFCompetencyScores, weights: List[float]) -> List[CompetencyPriority]:
        """
        Calculate priority scores for each CSSEF competency.
        Priority = (1 - score) * weight
        Higher priority means this competency needs more attention in this context.
        
        Args:
            cssef_scores: CSSEF competency scores
            weights: Context-specific weights for each CSSEF competency
            
        Returns:
            List[CompetencyPriority]: Prioritized list of competencies
        """
        scores_dict = cssef_scores.dict()
        priorities = []
        
        for i, (competency, score) in enumerate(scores_dict.items()):
            weight = weights[i]
            priority_score = (1.0 - score) * weight
            
            priorities.append(CompetencyPriority(
                competency=competency,
                score=score,
                weight=weight,
                priority=priority_score
            ))
        
        # Sort by priority (highest first)
        priorities.sort(key=lambda x: x.priority, reverse=True)
        
        return priorities
