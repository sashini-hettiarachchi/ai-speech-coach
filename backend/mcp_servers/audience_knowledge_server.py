#!/usr/bin/env python3
"""
Audience Knowledge Server for Speech Coach
Provides audience-specific context, adaptation strategies, and communication guidelines
"""

import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudienceType(Enum):
    EXECUTIVES = "executives"
    TECHNICAL_TEAM = "technical_team"
    GENERAL_PUBLIC = "general_public"
    STUDENTS = "students"
    PEERS = "peers"
    CLIENTS = "clients"
    INVESTORS = "investors"
    MIXED = "mixed"

class ExpertiseLevel(Enum):
    NOVICE = "novice"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"
    MIXED = "mixed"

class AudienceSize(Enum):
    SMALL = "small"      # 1-10 people
    MEDIUM = "medium"    # 11-50 people
    LARGE = "large"      # 51-200 people
    MASSIVE = "massive"  # 200+ people

@dataclass
class AudienceProfile:
    audience_id: str
    name: str
    type: AudienceType
    size: AudienceSize
    expertise_level: ExpertiseLevel
    demographics: Dict[str, Any]
    communication_preferences: List[str]
    attention_span_minutes: int
    interaction_style: str
    cultural_considerations: List[str]
    success_metrics: List[str]

class AudienceKnowledgeServer:
    """
    Provides audience-specific knowledge for speech coaching
    
    This server manages audience profiles, adaptation strategies,
    and communication guidelines for different audience types.
    """
    
    def __init__(self):
        self.audiences = self._load_audience_data()
        self.adaptation_strategies = self._load_adaptation_strategies()
        logger.info("Audience Knowledge Server initialized")
    
    def _load_audience_data(self) -> Dict[str, AudienceProfile]:
        """Load predefined audience profiles"""
        audiences = {}
        
        # Executive Audience
        audiences["executives"] = AudienceProfile(
            audience_id="executives",
            name="Executive Leadership Team",
            type=AudienceType.EXECUTIVES,
            size=AudienceSize.SMALL,
            expertise_level=ExpertiseLevel.EXPERT,
            demographics={
                "roles": ["CEO", "CTO", "CFO", "VP", "Director"],
                "seniority": "senior",
                "education_level": "advanced",
                "industry_experience": "high",
                "decision_making_authority": "high"
            },
            communication_preferences=[
                "data_driven",
                "results_focused",
                "concise",
                "strategic_focus",
                "roi_oriented"
            ],
            attention_span_minutes=30,
            interaction_style="formal_qa",
            cultural_considerations=[
                "time_sensitive",
                "results_oriented",
                "hierarchical_respect",
                "professional_formality"
            ],
            success_metrics=[
                "clear_roi_communication",
                "strategic_alignment",
                "decision_facilitation",
                "confidence_in_leadership"
            ]
        )
        
        # Technical Team
        audiences["technical_team"] = AudienceProfile(
            audience_id="technical_team",
            name="Technical Engineering Team",
            type=AudienceType.TECHNICAL_TEAM,
            size=AudienceSize.MEDIUM,
            expertise_level=ExpertiseLevel.EXPERT,
            demographics={
                "roles": ["Software Engineer", "DevOps", "Architect", "Technical Lead"],
                "seniority": "mixed",
                "education_level": "technical",
                "industry_experience": "high",
                "technical_depth": "deep"
            },
            communication_preferences=[
                "technical_accuracy",
                "detailed_explanations",
                "practical_examples",
                "code_samples",
                "architecture_diagrams"
            ],
            attention_span_minutes=45,
            interaction_style="interactive_discussion",
            cultural_considerations=[
                "detail_oriented",
                "accuracy_focused",
                "collaborative",
                "problem_solving_mindset"
            ],
            success_metrics=[
                "technical_understanding",
                "implementation_clarity",
                "problem_resolution",
                "team_alignment"
            ]
        )
        
        # General Public
        audiences["general_public"] = AudienceProfile(
            audience_id="general_public",
            name="General Public Audience",
            type=AudienceType.GENERAL_PUBLIC,
            size=AudienceSize.LARGE,
            expertise_level=ExpertiseLevel.NOVICE,
            demographics={
                "roles": ["General Public", "Various Backgrounds"],
                "seniority": "mixed",
                "education_level": "varied",
                "industry_experience": "low_to_mixed",
                "familiarity_with_topic": "low"
            },
            communication_preferences=[
                "simple_language",
                "storytelling",
                "visual_aids",
                "relatable_examples",
                "emotional_connection"
            ],
            attention_span_minutes=20,
            interaction_style="engaging_presentation",
            cultural_considerations=[
                "diverse_backgrounds",
                "varying_attention_levels",
                "need_for_engagement",
                "accessibility_concerns"
            ],
            success_metrics=[
                "audience_engagement",
                "message_comprehension",
                "emotional_impact",
                "memorable_takeaways"
            ]
        )
        
        # Students
        audiences["students"] = AudienceProfile(
            audience_id="students",
            name="Academic Students",
            type=AudienceType.STUDENTS,
            size=AudienceSize.MEDIUM,
            expertise_level=ExpertiseLevel.INTERMEDIATE,
            demographics={
                "roles": ["Students", "Trainees", "Interns"],
                "seniority": "junior",
                "education_level": "learning",
                "industry_experience": "low",
                "learning_motivation": "high"
            },
            communication_preferences=[
                "educational_content",
                "interactive_elements",
                "practical_applications",
                "step_by_step_guidance",
                "encouragement"
            ],
            attention_span_minutes=25,
            interaction_style="educational_interactive",
            cultural_considerations=[
                "learning_focused",
                "question_friendly",
                "mistake_tolerant",
                "growth_oriented"
            ],
            success_metrics=[
                "learning_outcomes",
                "knowledge_retention",
                "skill_development",
                "engagement_levels"
            ]
        )
        
        # Clients
        audiences["clients"] = AudienceProfile(
            audience_id="clients",
            name="Client Stakeholders",
            type=AudienceType.CLIENTS,
            size=AudienceSize.SMALL,
            expertise_level=ExpertiseLevel.MIXED,
            demographics={
                "roles": ["Client Representatives", "Stakeholders", "End Users"],
                "seniority": "mixed",
                "education_level": "varied",
                "industry_experience": "mixed",
                "investment_level": "high"
            },
            communication_preferences=[
                "value_proposition",
                "benefit_focused",
                "customization_options",
                "success_stories",
                "support_assurance"
            ],
            attention_span_minutes=35,
            interaction_style="consultative_dialogue",
            cultural_considerations=[
                "trust_building",
                "relationship_focused",
                "outcome_oriented",
                "service_expectations"
            ],
            success_metrics=[
                "client_satisfaction",
                "trust_establishment",
                "solution_fit",
                "partnership_development"
            ]
        )
        
        # Investors
        audiences["investors"] = AudienceProfile(
            audience_id="investors",
            name="Investment Committee",
            type=AudienceType.INVESTORS,
            size=AudienceSize.SMALL,
            expertise_level=ExpertiseLevel.EXPERT,
            demographics={
                "roles": ["Venture Capitalists", "Angel Investors", "Fund Managers"],
                "seniority": "senior",
                "education_level": "advanced",
                "industry_experience": "high",
                "financial_expertise": "expert"
            },
            communication_preferences=[
                "market_opportunity",
                "financial_projections",
                "competitive_advantage",
                "scalability_focus",
                "risk_assessment"
            ],
            attention_span_minutes=40,
            interaction_style="pitch_presentation",
            cultural_considerations=[
                "high_stakes",
                "financially_driven",
                "competitive_analysis",
                "growth_potential"
            ],
            success_metrics=[
                "investment_interest",
                "market_validation",
                "financial_confidence",
                "partnership_potential"
            ]
        )
        
        return audiences
    
    def _load_adaptation_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Load audience adaptation strategies"""
        return {
            "executives": {
                "content_adaptation": {
                    "focus": "Business outcomes and strategic impact",
                    "structure": "Executive summary → Key metrics → Recommendations → Next steps",
                    "language": "Professional, authoritative, data-driven",
                    "depth": "High-level with drill-down capability"
                },
                "delivery_adaptation": {
                    "pace": "Measured and confident",
                    "tone": "Authoritative but respectful",
                    "interaction": "Formal Q&A, decision-focused",
                    "visual_style": "Clean charts, financial data, strategic frameworks"
                },
                "engagement_tactics": [
                    "Lead with ROI and business value",
                    "Use executive-level metrics and KPIs",
                    "Address strategic implications",
                    "Provide clear decision points",
                    "Anticipate resource and budget questions"
                ]
            },
            "technical_team": {
                "content_adaptation": {
                    "focus": "Technical accuracy and implementation details",
                    "structure": "Problem → Solution → Architecture → Implementation → Testing",
                    "language": "Technical terminology, precise specifications",
                    "depth": "Deep technical detail with practical examples"
                },
                "delivery_adaptation": {
                    "pace": "Detailed but engaging",
                    "tone": "Collaborative and knowledgeable",
                    "interaction": "Interactive discussion, peer-to-peer",
                    "visual_style": "Architecture diagrams, code samples, technical specs"
                },
                "engagement_tactics": [
                    "Show technical depth and expertise",
                    "Provide concrete code examples",
                    "Discuss implementation challenges",
                    "Enable interactive problem-solving",
                    "Address scalability and performance"
                ]
            },
            "general_public": {
                "content_adaptation": {
                    "focus": "Accessibility and relatability",
                    "structure": "Hook → Story → Key message → Practical application → Call to action",
                    "language": "Simple, jargon-free, conversational",
                    "depth": "Surface level with engaging examples"
                },
                "delivery_adaptation": {
                    "pace": "Varied for engagement",
                    "tone": "Warm, approachable, enthusiastic",
                    "interaction": "Engaging, interactive, inclusive",
                    "visual_style": "Simple visuals, infographics, storytelling elements"
                },
                "engagement_tactics": [
                    "Use storytelling and analogies",
                    "Create emotional connections",
                    "Provide relatable examples",
                    "Encourage audience participation",
                    "Make complex topics accessible"
                ]
            },
            "students": {
                "content_adaptation": {
                    "focus": "Learning and skill development",
                    "structure": "Learning objectives → Concept introduction → Examples → Practice → Summary",
                    "language": "Educational, encouraging, clear",
                    "depth": "Progressive complexity with scaffolding"
                },
                "delivery_adaptation": {
                    "pace": "Moderate with pauses for comprehension",
                    "tone": "Supportive, encouraging, patient",
                    "interaction": "Educational dialogue, Q&A friendly",
                    "visual_style": "Educational slides, step-by-step guides, interactive elements"
                },
                "engagement_tactics": [
                    "Set clear learning objectives",
                    "Use interactive learning techniques",
                    "Provide hands-on examples",
                    "Encourage questions and exploration",
                    "Celebrate learning progress"
                ]
            },
            "clients": {
                "content_adaptation": {
                    "focus": "Value proposition and benefits",
                    "structure": "Understanding needs → Solution presentation → Benefits → Implementation → Support",
                    "language": "Customer-focused, benefit-oriented",
                    "depth": "Customized to client needs and industry"
                },
                "delivery_adaptation": {
                    "pace": "Client-paced, responsive to feedback",
                    "tone": "Professional, consultative, trustworthy",
                    "interaction": "Consultative dialogue, needs-focused",
                    "visual_style": "Client-specific examples, ROI calculations, success stories"
                },
                "engagement_tactics": [
                    "Focus on client value and ROI",
                    "Demonstrate understanding of their challenges",
                    "Provide industry-specific examples",
                    "Show customization capabilities",
                    "Address concerns proactively"
                ]
            },
            "investors": {
                "content_adaptation": {
                    "focus": "Market opportunity and financial returns",
                    "structure": "Market opportunity → Solution → Business model → Financial projections → Ask",
                    "language": "Business-focused, growth-oriented, confident",
                    "depth": "Strategic overview with financial depth"
                },
                "delivery_adaptation": {
                    "pace": "Confident and compelling",
                    "tone": "Confident, visionary, data-driven",
                    "interaction": "Pitch presentation, investor Q&A",
                    "visual_style": "Market data, financial projections, growth charts"
                },
                "engagement_tactics": [
                    "Lead with market opportunity size",
                    "Show strong financial projections",
                    "Demonstrate competitive advantage",
                    "Highlight scalability potential",
                    "Address risks and mitigation"
                ]
            }
        }
    
    def get_context_for_llm(self, query_type: str, **kwargs) -> Dict[str, Any]:
        """
        Get audience-specific context for LLM integration
        
        Args:
            query_type: Type of query (audience_profile, adaptation_strategy, coaching_tips)
            **kwargs: Additional parameters
        
        Returns:
            Context dictionary for LLM consumption
        """
        try:
            if query_type == "audience_profile":
                return self._get_audience_profile_context(**kwargs)
            elif query_type == "adaptation_strategy":
                return self._get_adaptation_strategy_context(**kwargs)
            elif query_type == "coaching_tips":
                return self._get_audience_coaching_tips(**kwargs)
            elif query_type == "audience_analysis":
                return self._analyze_speech_for_audience(**kwargs)
            elif query_type == "available_audiences":
                return self._get_available_audiences()
            else:
                return {
                    "error": f"Unknown query type: {query_type}",
                    "available_queries": ["audience_profile", "adaptation_strategy", "coaching_tips", "audience_analysis", "available_audiences"],
                    "context_type": "error"
                }
                
        except Exception as e:
            logger.error(f"Error in get_context_for_llm: {str(e)}")
            return {
                "error": str(e),
                "context_type": "error"
            }
    
    def _get_audience_profile_context(self, audience_id: str = None, audience_type: str = None) -> Dict[str, Any]:
        """Get detailed audience profile"""
        if audience_id and audience_id in self.audiences:
            audience = self.audiences[audience_id]
            return {
                "audience_profile": {
                    "audience_id": audience.audience_id,
                    "name": audience.name,
                    "type": audience.type.value,
                    "size": audience.size.value,
                    "expertise_level": audience.expertise_level.value,
                    "demographics": audience.demographics,
                    "communication_preferences": audience.communication_preferences,
                    "attention_span_minutes": audience.attention_span_minutes,
                    "interaction_style": audience.interaction_style,
                    "cultural_considerations": audience.cultural_considerations,
                    "success_metrics": audience.success_metrics
                },
                "context_type": "audience_profile"
            }
        else:
            return {
                "error": f"Audience not found: {audience_id}",
                "available_audiences": list(self.audiences.keys()),
                "context_type": "error"
            }
    
    def _get_adaptation_strategy_context(self, audience_id: str) -> Dict[str, Any]:
        """Get audience adaptation strategies"""
        if audience_id in self.adaptation_strategies:
            return {
                "audience_id": audience_id,
                "adaptation_strategy": self.adaptation_strategies[audience_id],
                "context_type": "adaptation_strategy"
            }
        else:
            return {
                "error": f"Adaptation strategy not found for audience: {audience_id}",
                "available_audiences": list(self.adaptation_strategies.keys()),
                "context_type": "error"
            }
    
    def _get_audience_coaching_tips(self, audience_id: str, skill_level: str = "intermediate") -> Dict[str, Any]:
        """Get audience-specific coaching tips"""
        if audience_id not in self.audiences:
            return {
                "error": f"Audience not found: {audience_id}",
                "context_type": "error"
            }
        
        audience = self.audiences[audience_id]
        adaptation = self.adaptation_strategies.get(audience_id, {})
        
        # Generate skill-level specific tips
        tips = []
        
        if skill_level == "beginner":
            tips.extend([
                f"Start with understanding {audience.name} expectations",
                f"Focus on {audience.communication_preferences[0]} approach",
                f"Keep presentation under {audience.attention_span_minutes} minutes"
            ])
        elif skill_level == "advanced":
            tips.extend([
                f"Leverage advanced {audience.communication_preferences[0]} techniques",
                f"Anticipate complex questions about {audience.success_metrics[0]}",
                f"Adapt dynamically to {audience.interaction_style} preferences"
            ])
        else:  # intermediate
            tips.extend([
                f"Balance {audience.communication_preferences[0]} with accessibility",
                f"Prepare for {audience.interaction_style} format",
                f"Focus on achieving {audience.success_metrics[0]}"
            ])
        
        return {
            "audience_id": audience_id,
            "audience_name": audience.name,
            "skill_level": skill_level,
            "targeted_tips": tips,
            "engagement_tactics": adaptation.get("engagement_tactics", []),
            "success_focus": audience.success_metrics,
            "context_type": "audience_coaching_tips"
        }
    
    def _analyze_speech_for_audience(self, audience_id: str, speech_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze speech metrics against audience expectations"""
        if audience_id not in self.audiences:
            return {
                "error": f"Audience not found: {audience_id}",
                "context_type": "error"
            }
        
        audience = self.audiences[audience_id]
        analysis = {
            "audience_id": audience_id,
            "audience_name": audience.name,
            "analysis_timestamp": datetime.now().strftime("%Y-%m-%d"),
            "fit_analysis": {},
            "recommendations": [],
            "context_type": "audience_fit_analysis"
        }
        
        # Analyze pace appropriateness
        if "pace_wpm" in speech_metrics:
            pace = speech_metrics["pace_wpm"]
            if audience.type == AudienceType.EXECUTIVES:
                ideal_pace = 125  # Measured, professional pace
            elif audience.type == AudienceType.TECHNICAL_TEAM:
                ideal_pace = 140  # Detailed but engaging
            elif audience.type == AudienceType.GENERAL_PUBLIC:
                ideal_pace = 150  # Varied for engagement
            elif audience.type == AudienceType.STUDENTS:
                ideal_pace = 130  # Moderate with pauses
            else:
                ideal_pace = 135  # Default moderate pace
            
            pace_score = max(0, 100 - abs(pace - ideal_pace) * 2)
            analysis["fit_analysis"]["pace"] = {
                "score": pace_score,
                "ideal_wpm": ideal_pace,
                "actual_wpm": pace,
                "audience_appropriateness": "good" if pace_score >= 80 else "needs_adjustment"
            }
            
            if pace_score < 80:
                analysis["recommendations"].append(f"Adjust pace to ~{ideal_pace} WPM for {audience.name}")
        
        # Analyze technical complexity (if applicable)
        if audience.expertise_level == ExpertiseLevel.NOVICE and "technical_terms_count" in speech_metrics:
            tech_terms = speech_metrics["technical_terms_count"]
            if tech_terms > 5:
                analysis["recommendations"].append("Reduce technical terminology for general audience")
        
        # Analyze engagement appropriateness
        if "interaction_attempts" in speech_metrics:
            interactions = speech_metrics["interaction_attempts"]
            if audience.interaction_style == "formal_qa" and interactions > 3:
                analysis["recommendations"].append("Reduce informal interactions; prepare for formal Q&A")
            elif audience.interaction_style == "interactive_discussion" and interactions < 2:
                analysis["recommendations"].append("Increase interactive elements for technical audience")
        
        return analysis
    
    def _get_available_audiences(self) -> Dict[str, Any]:
        """Get list of available audiences"""
        return {
            "available_audiences": list(self.audiences.keys()),
            "audience_details": {
                audience_id: {
                    "name": audience.name,
                    "type": audience.type.value,
                    "size": audience.size.value,
                    "expertise_level": audience.expertise_level.value,
                    "communication_preferences": audience.communication_preferences[:3]  # Top 3
                }
                for audience_id, audience in self.audiences.items()
            },
            "context_type": "available_options"
        }
    
    def get_audience_profile(self, audience_id: str) -> Optional[AudienceProfile]:
        """Get audience profile by ID"""
        return self.audiences.get(audience_id)
    
    def get_adaptation_strategy(self, audience_id: str) -> Dict[str, Any]:
        """Get adaptation strategy for audience"""
        return self.adaptation_strategies.get(audience_id, {})

# Testing function
def main():
    """Test the Audience Knowledge Server"""
    server = AudienceKnowledgeServer()
    
    print("=== Audience Knowledge Server Test ===\n")
    
    # Test available audiences
    print("1. Available Audiences:")
    available = server.get_context_for_llm("available_audiences")
    print(json.dumps(available, indent=2))
    
    # Test audience profile
    print("\n2. Executive Audience Profile:")
    profile = server.get_context_for_llm("audience_profile", audience_id="executives")
    print(json.dumps(profile, indent=2))
    
    # Test adaptation strategy
    print("\n3. Technical Team Adaptation Strategy:")
    strategy = server.get_context_for_llm("adaptation_strategy", audience_id="technical_team")
    print(json.dumps(strategy, indent=2))
    
    # Test coaching tips
    print("\n4. Client Coaching Tips:")
    tips = server.get_context_for_llm("coaching_tips", audience_id="clients", skill_level="intermediate")
    print(json.dumps(tips, indent=2))
    
    # Test audience analysis
    print("\n5. Speech Analysis for Investors:")
    sample_metrics = {
        "pace_wpm": 160,
        "technical_terms_count": 8,
        "interaction_attempts": 1,
        "confidence_score": 8.5
    }
    analysis = server.get_context_for_llm("audience_analysis", audience_id="investors", speech_metrics=sample_metrics)
    print(json.dumps(analysis, indent=2))

if __name__ == "__main__":
    main()
