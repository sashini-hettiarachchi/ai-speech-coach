#!/usr/bin/env python3
"""
Event Knowledge Server for Speech Coach
Provides event-specific context and audience-tailored coaching recommendations for LLMs
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventType(Enum):
    BUSINESS_PRESENTATION = "business_presentation"
    CONFERENCE_TALK = "conference_talk"
    WORKSHOP = "workshop"
    TEAM_MEETING = "team_meeting"
    SALES_PITCH = "sales_pitch"
    ACADEMIC_PRESENTATION = "academic_presentation"
    WEBINAR = "webinar"
    KEYNOTE = "keynote"
    TRAINING_SESSION = "training_session"
    DEMO = "product_demo"

class AudienceSize(Enum):
    SMALL = "small"  # 2-10 people
    MEDIUM = "medium"  # 11-50 people
    LARGE = "large"  # 51-200 people
    VERY_LARGE = "very_large"  # 200+ people

class AudienceExpertise(Enum):
    NOVICE = "novice"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"
    MIXED = "mixed"

class PresentationFormat(Enum):
    IN_PERSON = "in_person"
    VIRTUAL = "virtual"
    HYBRID = "hybrid"

@dataclass
class AudienceProfile:
    size: AudienceSize
    expertise_level: AudienceExpertise
    demographics: Dict[str, Any]
    engagement_preferences: List[str]
    attention_span_minutes: int
    interaction_style: str
    cultural_considerations: List[str]

@dataclass
class EventContext:
    event_id: str
    event_type: EventType
    name: str
    duration_minutes: int
    format: PresentationFormat
    audience: AudienceProfile
    objectives: List[str]
    key_success_metrics: List[str]
    constraints: List[str]
    special_considerations: List[str]

@dataclass
class CoachingRecommendation:
    category: str
    recommendation: str
    rationale: str
    priority: str  # high, medium, low
    audience_specific: bool

class EventKnowledgeBase:
    """Knowledge base for event types, audience profiles, and context-specific coaching"""
    
    def __init__(self):
        self.events = self._initialize_sample_events()
        self.event_type_guidelines = self._initialize_event_type_guidelines()
    
    def _initialize_sample_events(self) -> Dict[str, EventContext]:
        """Initialize sample event contexts"""
        return {
            "quarterly_review": EventContext(
                event_id="quarterly_review",
                event_type=EventType.BUSINESS_PRESENTATION,
                name="Q3 Quarterly Business Review",
                duration_minutes=30,
                format=PresentationFormat.IN_PERSON,
                audience=AudienceProfile(
                    size=AudienceSize.MEDIUM,
                    expertise_level=AudienceExpertise.EXPERT,
                    demographics={
                        "roles": ["executives", "senior_managers", "department_heads"],
                        "seniority": "senior",
                        "familiarity_with_topic": "high"
                    },
                    engagement_preferences=["data_driven", "results_focused", "concise"],
                    attention_span_minutes=45,
                    interaction_style="formal_qa",
                    cultural_considerations=["time_sensitive", "results_oriented"]
                ),
                objectives=[
                    "Present quarterly performance metrics",
                    "Highlight key achievements and challenges",
                    "Outline strategy for Q4",
                    "Secure buy-in for upcoming initiatives"
                ],
                key_success_metrics=[
                    "Clear communication of results",
                    "Stakeholder confidence in leadership",
                    "Approved Q4 budget allocation",
                    "Alignment on strategic priorities"
                ],
                constraints=["30-minute time limit", "formal setting", "board members present"],
                special_considerations=["High-stakes environment", "Financial implications", "Strategic decisions"]
            ),
            "tech_conference": EventContext(
                event_id="tech_conference",
                event_type=EventType.CONFERENCE_TALK,
                name="AI in Healthcare Conference Talk",
                duration_minutes=45,
                format=PresentationFormat.HYBRID,
                audience=AudienceProfile(
                    size=AudienceSize.LARGE,
                    expertise_level=AudienceExpertise.MIXED,
                    demographics={
                        "roles": ["developers", "researchers", "product_managers", "students"],
                        "seniority": "mixed",
                        "familiarity_with_topic": "varied"
                    },
                    engagement_preferences=["interactive", "demo_focused", "practical_examples"],
                    attention_span_minutes=25,
                    interaction_style="casual_qa",
                    cultural_considerations=["diverse_backgrounds", "international_audience"]
                ),
                objectives=[
                    "Share technical innovation",
                    "Demonstrate practical applications", 
                    "Build thought leadership",
                    "Network with industry peers"
                ],
                key_success_metrics=[
                    "Audience engagement levels",
                    "Questions and discussion quality",
                    "Social media mentions",
                    "Follow-up connections"
                ],
                constraints=["Mixed virtual/in-person audience", "45-minute slot", "Technical demos required"],
                special_considerations=["Diverse expertise levels", "International audience", "Technology failures possible"]
            ),
            "team_standup": EventContext(
                event_id="team_standup",
                event_type=EventType.TEAM_MEETING,
                name="Weekly Team Standup",
                duration_minutes=15,
                format=PresentationFormat.VIRTUAL,
                audience=AudienceProfile(
                    size=AudienceSize.SMALL,
                    expertise_level=AudienceExpertise.INTERMEDIATE,
                    demographics={
                        "roles": ["team_members", "project_manager"],
                        "seniority": "mixed",
                        "familiarity_with_topic": "high"
                    },
                    engagement_preferences=["concise", "action_oriented", "collaborative"],
                    attention_span_minutes=20,
                    interaction_style="informal",
                    cultural_considerations=["team_dynamics", "psychological_safety"]
                ),
                objectives=[
                    "Share progress updates",
                    "Identify blockers",
                    "Coordinate team efforts",
                    "Maintain team alignment"
                ],
                key_success_metrics=[
                    "Clear status communication",
                    "Identified action items",
                    "Team coordination",
                    "Meeting efficiency"
                ],
                constraints=["15-minute time limit", "Virtual format", "Weekly cadence"],
                special_considerations=["Team morale", "Remote work challenges", "Time zone differences"]
            ),
            "sales_demo": EventContext(
                event_id="sales_demo",
                event_type=EventType.SALES_PITCH,
                name="Enterprise Software Demo",
                duration_minutes=60,
                format=PresentationFormat.VIRTUAL,
                audience=AudienceProfile(
                    size=AudienceSize.SMALL,
                    expertise_level=AudienceExpertise.INTERMEDIATE,
                    demographics={
                        "roles": ["decision_makers", "end_users", "technical_evaluators"],
                        "seniority": "senior_and_mid",
                        "familiarity_with_topic": "moderate"
                    },
                    engagement_preferences=["benefit_focused", "interactive", "use_case_driven"],
                    attention_span_minutes=30,
                    interaction_style="consultative",
                    cultural_considerations=["buying_process", "budget_constraints"]
                ),
                objectives=[
                    "Demonstrate product value",
                    "Address specific use cases",
                    "Handle objections",
                    "Advance sales process"
                ],
                key_success_metrics=[
                    "Engagement during demo",
                    "Relevant questions asked",
                    "Next meeting scheduled",
                    "Technical requirements discussed"
                ],
                constraints=["Virtual demo environment", "Product limitations", "Competitive landscape"],
                special_considerations=["Sales cycle stage", "Budget approval process", "Technical integration complexity"]
            )
        }
    
    def _initialize_event_type_guidelines(self) -> Dict[EventType, Dict[str, Any]]:
        """Initialize guidelines for different event types"""
        return {
            EventType.BUSINESS_PRESENTATION: {
                "recommended_structure": {
                    "opening": "Executive summary and agenda",
                    "body": "Key metrics, insights, and strategic recommendations",
                    "closing": "Clear next steps and decision points"
                },
                "tone": "Professional and authoritative",
                "pace": "Measured and confident",
                "interaction_style": "Formal Q&A at designated times",
                "visual_aids": "Data-heavy slides with clear charts",
                "time_management": "Strict adherence to schedule",
                "success_factors": ["Data accuracy", "Strategic insight", "Clear recommendations"]
            },
            EventType.CONFERENCE_TALK: {
                "recommended_structure": {
                    "opening": "Hook and compelling problem statement",
                    "body": "Solution exploration with examples",
                    "closing": "Key takeaways and call to action"
                },
                "tone": "Engaging and thought-provoking",
                "pace": "Dynamic with strategic pauses",
                "interaction_style": "Interactive throughout",
                "visual_aids": "Visually appealing with minimal text",
                "time_management": "Buffer time for audience interaction",
                "success_factors": ["Audience engagement", "Novel insights", "Memorable delivery"]
            },
            EventType.TEAM_MEETING: {
                "recommended_structure": {
                    "opening": "Quick agenda review",
                    "body": "Status updates and problem-solving",
                    "closing": "Action items and next steps"
                },
                "tone": "Collaborative and supportive",
                "pace": "Efficient but inclusive",
                "interaction_style": "Open discussion encouraged",
                "visual_aids": "Simple status dashboards",
                "time_management": "Respect time boundaries",
                "success_factors": ["Team alignment", "Clear action items", "Inclusive participation"]
            },
            EventType.SALES_PITCH: {
                "recommended_structure": {
                    "opening": "Value proposition and agenda",
                    "body": "Solution demonstration with benefits",
                    "closing": "Next steps and commitment"
                },
                "tone": "Consultative and customer-focused",
                "pace": "Adaptive to customer engagement",
                "interaction_style": "Highly interactive and responsive",
                "visual_aids": "Customer-specific examples and ROI",
                "time_management": "Flexible based on customer interest",
                "success_factors": ["Customer engagement", "Objection handling", "Value demonstration"]
            }
        }
    
    def get_event_context(self, event_id: str) -> Dict[str, Any]:
        """Get complete context for a specific event"""
        if event_id not in self.events:
            raise ValueError(f"Event {event_id} not found")
        
        event = self.events[event_id]
        guidelines = self.event_type_guidelines.get(event.event_type, {})
        
        # Convert event data to dict and handle enums
        event_dict = asdict(event)
        
        # Convert enum values to strings
        event_dict["event_type"] = event.event_type.value
        event_dict["format"] = event.format.value
        event_dict["audience"]["size"] = event.audience.size.value
        event_dict["audience"]["expertise_level"] = event.audience.expertise_level.value
        
        return {
            "event_context": event_dict,
            "event_type_guidelines": guidelines,
            "context_type": "event_context"
        }
    
    def get_coaching_tips(self, event_id: str, user_skill_level: str = "intermediate") -> Dict[str, Any]:
        """Generate event-specific coaching tips"""
        if event_id not in self.events:
            raise ValueError(f"Event {event_id} not found")
        
        event = self.events[event_id]
        guidelines = self.event_type_guidelines.get(event.event_type, {})
        
        coaching_tips = {
            "event_id": event_id,
            "event_type": event.event_type.value,
            "targeted_coaching": self._generate_targeted_coaching(event, user_skill_level),
            "audience_adaptation": self._generate_audience_adaptation_tips(event.audience),
            "format_specific_tips": self._generate_format_tips(event.format),
            "success_optimization": self._generate_success_tips(event),
            "context_type": "coaching_tips"
        }
        
        return coaching_tips
    
    def _generate_targeted_coaching(self, event: EventContext, skill_level: str) -> List[Dict[str, Any]]:
        """Generate coaching recommendations based on event and skill level"""
        recommendations = []
        
        # Event type specific recommendations
        if event.event_type == EventType.BUSINESS_PRESENTATION:
            recommendations.append({
                "category": "Content",
                "recommendation": "Lead with key business outcomes and metrics",
                "rationale": "Business audiences prioritize results and strategic impact",
                "priority": "high",
                "audience_specific": True
            })
            recommendations.append({
                "category": "Delivery",
                "recommendation": "Maintain professional, measured pace",
                "rationale": "Executive audiences expect confident, authoritative delivery",
                "priority": "high",
                "audience_specific": True
            })
        
        elif event.event_type == EventType.CONFERENCE_TALK:
            recommendations.append({
                "category": "Engagement",
                "recommendation": "Use interactive elements and audience polling",
                "rationale": "Conference audiences expect engaging, participatory experiences",
                "priority": "high",
                "audience_specific": True
            })
            recommendations.append({
                "category": "Content",
                "recommendation": "Include practical examples and actionable takeaways",
                "rationale": "Mixed expertise levels need concrete, applicable insights",
                "priority": "medium",
                "audience_specific": True
            })
        
        elif event.event_type == EventType.SALES_PITCH:
            recommendations.append({
                "category": "Strategy",
                "recommendation": "Focus on customer-specific value and ROI",
                "rationale": "Sales contexts require clear value demonstration",
                "priority": "high",
                "audience_specific": True
            })
            recommendations.append({
                "category": "Interaction",
                "recommendation": "Encourage questions and handle objections gracefully",
                "rationale": "Sales environments require responsive, consultative approach",
                "priority": "high",
                "audience_specific": True
            })
        
        # Skill level adjustments
        if skill_level == "beginner":
            recommendations.append({
                "category": "Preparation",
                "recommendation": "Practice key transitions and have backup plans ready",
                "rationale": "Beginners benefit from extra preparation and contingency planning",
                "priority": "high",
                "audience_specific": False
            })
        elif skill_level == "advanced":
            recommendations.append({
                "category": "Mastery",
                "recommendation": "Focus on subtle audience reading and dynamic adaptation",
                "rationale": "Advanced speakers can handle real-time adjustments",
                "priority": "medium",
                "audience_specific": False
            })
        
        return recommendations
    
    def _generate_audience_adaptation_tips(self, audience: AudienceProfile) -> List[str]:
        """Generate audience-specific adaptation tips"""
        tips = []
        
        # Size-based tips
        if audience.size == AudienceSize.SMALL:
            tips.append("Use conversational tone and encourage frequent interaction")
            tips.append("Make eye contact with each individual")
        elif audience.size == AudienceSize.LARGE:
            tips.append("Project voice clearly and use larger gestures")
            tips.append("Use rhetorical questions to maintain engagement")
        
        # Expertise-based tips
        if audience.expertise_level == AudienceExpertise.EXPERT:
            tips.append("Use technical terminology appropriately")
            tips.append("Focus on advanced insights and strategic implications")
        elif audience.expertise_level == AudienceExpertise.NOVICE:
            tips.append("Define technical terms and provide context")
            tips.append("Use analogies and simple examples")
        elif audience.expertise_level == AudienceExpertise.MIXED:
            tips.append("Layer information from basic to advanced")
            tips.append("Provide multiple entry points for different expertise levels")
        
        # Engagement preference tips
        if "interactive" in audience.engagement_preferences:
            tips.append("Plan regular interaction points throughout presentation")
        if "data_driven" in audience.engagement_preferences:
            tips.append("Support points with relevant metrics and evidence")
        if "concise" in audience.engagement_preferences:
            tips.append("Be direct and avoid unnecessary elaboration")
        
        return tips
    
    def _generate_format_tips(self, format: PresentationFormat) -> List[str]:
        """Generate format-specific tips"""
        tips = []
        
        if format == PresentationFormat.VIRTUAL:
            tips.extend([
                "Look directly at camera for eye contact",
                "Use clear, larger gestures visible on screen",
                "Check audio/video quality before starting",
                "Have technical backup plans ready",
                "Use virtual engagement tools (polls, chat, etc.)"
            ])
        elif format == PresentationFormat.IN_PERSON:
            tips.extend([
                "Use full stage presence and natural movement",
                "Adapt voice projection to room size",
                "Make eye contact across entire audience",
                "Use physical props if appropriate"
            ])
        elif format == PresentationFormat.HYBRID:
            tips.extend([
                "Balance attention between in-person and virtual audiences",
                "Ensure virtual participants can see and hear clearly",
                "Use both in-person and virtual interaction methods",
                "Have technical support readily available"
            ])
        
        return tips
    
    def _generate_success_tips(self, event: EventContext) -> List[str]:
        """Generate tips for achieving event-specific success metrics"""
        tips = []
        
        for objective in event.objectives:
            if "metrics" in objective.lower() or "performance" in objective.lower():
                tips.append("Use clear data visualization and highlight key trends")
            elif "strategy" in objective.lower() or "initiatives" in objective.lower():
                tips.append("Connect strategic recommendations to business outcomes")
            elif "demonstrate" in objective.lower() or "demo" in objective.lower():
                tips.append("Practice technical demonstrations and have fallback options")
            elif "alignment" in objective.lower() or "coordinate" in objective.lower():
                tips.append("Summarize key agreements and action items clearly")
        
        # Time management tips based on duration
        if event.duration_minutes <= 15:
            tips.append("Focus on essential points only - avoid tangents")
        elif event.duration_minutes >= 45:
            tips.append("Plan energy breaks and engagement resets")
        
        return tips
    
    def analyze_event_speech_fit(self, event_id: str, speech_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze how well speech metrics fit the event context"""
        if event_id not in self.events:
            raise ValueError(f"Event {event_id} not found")
        
        event = self.events[event_id]
        analysis = {
            "event_id": event_id,
            "event_type": event.event_type.value,
            "fit_analysis": {},
            "recommendations": [],
            "context_type": "event_fit_analysis"
        }
        
        # Analyze pace appropriateness
        pace_wpm = speech_metrics.get("pace_wpm", 0)
        ideal_pace = self._get_ideal_pace_for_event_type(event.event_type)
        pace_score = max(0, 100 - abs(pace_wpm - ideal_pace) * 1.5)
        
        analysis["fit_analysis"]["pace"] = {
            "score": pace_score,
            "ideal_wpm": ideal_pace,
            "actual_wpm": pace_wpm,
            "event_appropriateness": "good" if pace_score > 80 else "needs_adjustment"
        }
        
        # Analyze interaction appropriateness
        if event.audience.interaction_style == "formal_qa" and speech_metrics.get("questions_during_presentation", 0) > 0:
            analysis["recommendations"].append("Save questions for designated Q&A time in formal settings")
        
        # Analyze duration fit
        estimated_duration = speech_metrics.get("estimated_duration_minutes", event.duration_minutes)
        if estimated_duration > event.duration_minutes * 1.1:
            analysis["recommendations"].append(f"Content may exceed {event.duration_minutes}-minute time limit")
        
        return analysis
    
    def _get_ideal_pace_for_event_type(self, event_type: EventType) -> int:
        """Get ideal speaking pace for event type"""
        pace_map = {
            EventType.BUSINESS_PRESENTATION: 125,  # Measured, professional
            EventType.CONFERENCE_TALK: 140,       # Engaging, energetic
            EventType.TEAM_MEETING: 130,          # Natural, conversational
            EventType.SALES_PITCH: 135,           # Persuasive, adaptive
            EventType.WORKSHOP: 120,              # Educational, clear
            EventType.ACADEMIC_PRESENTATION: 115  # Scholarly, careful
        }
        return pace_map.get(event_type, 130)

class EventKnowledgeServer:
    """Server interface for LLM integration with event knowledge"""
    
    def __init__(self):
        self.knowledge_base = EventKnowledgeBase()
        logger.info("Event Knowledge Server initialized")
    
    def get_context_for_llm(self, query_type: str, **kwargs) -> Dict[str, Any]:
        """
        Main interface for LLM to get event context
        
        Query types:
        - event_context: Get complete event context
        - coaching_tips: Get event-specific coaching recommendations
        - event_fit_analysis: Analyze speech fit for event
        - available_events: List available events for testing
        """
        try:
            if query_type == "event_context":
                event_id = kwargs.get("event_id")
                if not event_id:
                    return {"error": "event_id required", "context_type": "error"}
                return self.knowledge_base.get_event_context(event_id)
            
            elif query_type == "coaching_tips":
                event_id = kwargs.get("event_id")
                skill_level = kwargs.get("skill_level", "intermediate")
                if not event_id:
                    return {"error": "event_id required", "context_type": "error"}
                return self.knowledge_base.get_coaching_tips(event_id, skill_level)
            
            elif query_type == "event_fit_analysis":
                event_id = kwargs.get("event_id")
                speech_metrics = kwargs.get("speech_metrics", {})
                if not event_id:
                    return {"error": "event_id required", "context_type": "error"}
                return self.knowledge_base.analyze_event_speech_fit(event_id, speech_metrics)
            
            elif query_type == "available_events":
                return {
                    "available_events": list(self.knowledge_base.events.keys()),
                    "event_details": {
                        event_id: {
                            "name": event.name,
                            "type": event.event_type.value,
                            "duration": event.duration_minutes,
                            "audience_size": event.audience.size.value,
                            "format": event.format.value
                        }
                        for event_id, event in self.knowledge_base.events.items()
                    },
                    "context_type": "available_options"
                }
            
            else:
                return {
                    "error": f"Unknown query type: {query_type}",
                    "available_query_types": ["event_context", "coaching_tips", "event_fit_analysis", "available_events"],
                    "context_type": "error"
                }
                
        except Exception as e:
            logger.error(f"Error processing query {query_type}: {str(e)}")
            return {
                "error": str(e),
                "query_type": query_type,
                "context_type": "error"
            }

# Example usage and testing
def main():
    """Test the event knowledge server"""
    server = EventKnowledgeServer()
    
    # Test available events
    print("=== Available Events ===")
    events = server.get_context_for_llm("available_events")
    print(json.dumps(events, indent=2))
    
    # Test coaching tips
    print("\n=== Coaching Tips for Business Presentation ===")
    tips = server.get_context_for_llm("coaching_tips", event_id="quarterly_review", skill_level="intermediate")
    print(json.dumps(tips, indent=2))
    
    # Test event fit analysis
    print("\n=== Event Fit Analysis ===")
    test_metrics = {
        "pace_wpm": 150,
        "estimated_duration_minutes": 35,
        "questions_during_presentation": 0
    }
    fit_analysis = server.get_context_for_llm("event_fit_analysis", event_id="quarterly_review", speech_metrics=test_metrics)
    print(json.dumps(fit_analysis, indent=2))

if __name__ == "__main__":
    main()
