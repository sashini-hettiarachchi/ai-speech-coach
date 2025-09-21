#!/usr/bin/env python3
"""
Unified Knowledge Interface for Speech Coach LLM Integration
Provides a single interface for LLMs to access domain, user, and event context
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

# Import our knowledge servers
from .domain_knowledge_server import DomainKnowledgeServer
from .user_knowledge_server import UserKnowledgeServer
from .event_knowledge_server import EventKnowledgeServer
from .audience_knowledge_server import AudienceKnowledgeServer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpeechCoachLLMInterface:
    """
    Unified interface for LLMs to access contextual knowledge for speech coaching
    
    This interface aggregates knowledge from four specialized servers:
    - Domain Knowledge: Speaking domain guidelines and best practices
    - User Knowledge: User profiles, history, and personalized coaching data
    - Event Knowledge: Event-specific context and audience adaptation
    - Audience Knowledge: Audience profiles and adaptation strategies
    """
    
    def __init__(self):
        self.domain_server = DomainKnowledgeServer()
        self.user_server = UserKnowledgeServer()
        self.event_server = EventKnowledgeServer()
        self.audience_server = AudienceKnowledgeServer()
        logger.info("Speech Coach LLM Interface initialized with all knowledge servers")
    
    def get_comprehensive_context(self, 
                                user_id: str,
                                domain: str = "public_speaking",
                                event_id: Optional[str] = None,
                                audience_id: Optional[str] = None,
                                speech_metrics: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get comprehensive context from all knowledge sources for LLM coaching
        
        Args:
            user_id: User identifier
            domain: Speaking domain (public_speaking, corporate, technical, academic)
            event_id: Specific event identifier (optional)
            audience_id: Specific audience identifier (optional)
            speech_metrics: Current speech analysis results (optional)
        
        Returns:
            Comprehensive context dictionary with all relevant information
        """
        context = {
            "context_timestamp": datetime.now().isoformat(),
            "request_parameters": {
                "user_id": user_id,
                "domain": domain,
                "event_id": event_id,
                "audience_id": audience_id,
                "has_speech_metrics": speech_metrics is not None
            },
            "knowledge_sources": {},
            "coaching_synthesis": {},
            "context_type": "comprehensive_coaching_context"
        }
        
        try:
            # Get user context
            logger.info(f"Gathering user context for {user_id}")
            user_context = self.user_server.get_context_for_llm("coaching_context", user_id=user_id)
            context["knowledge_sources"]["user"] = user_context
            
            # Get domain context
            logger.info(f"Gathering domain context for {domain}")
            domain_context = self.domain_server.get_context_for_llm("domain_guidelines", domain=domain, focus_area="all")
            context["knowledge_sources"]["domain"] = domain_context
            
            # Get event context if provided
            if event_id:
                logger.info(f"Gathering event context for {event_id}")
                event_context = self.event_server.get_context_for_llm("event_context", event_id=event_id)
                event_coaching = self.event_server.get_context_for_llm("coaching_tips", 
                                                                     event_id=event_id,
                                                                     skill_level=user_context.get("coaching_context", {}).get("current_skill_level", "intermediate"))
                context["knowledge_sources"]["event"] = {
                    "context": event_context,
                    "coaching_tips": event_coaching
                }
            
            # Get audience context if provided
            if audience_id:
                logger.info(f"Gathering audience context for {audience_id}")
                audience_profile = self.audience_server.get_context_for_llm("audience_profile", audience_id=audience_id)
                audience_strategy = self.audience_server.get_context_for_llm("adaptation_strategy", audience_id=audience_id)
                audience_coaching = self.audience_server.get_context_for_llm("coaching_tips", 
                                                                           audience_id=audience_id,
                                                                           skill_level=user_context.get("coaching_context", {}).get("current_skill_level", "intermediate"))
                context["knowledge_sources"]["audience"] = {
                    "profile": audience_profile,
                    "adaptation_strategy": audience_strategy,
                    "coaching_tips": audience_coaching
                }
            
            # Perform speech analysis if metrics provided
            if speech_metrics:
                logger.info("Analyzing speech metrics against context")
                
                # Domain-specific analysis
                domain_analysis = self.domain_server.get_context_for_llm("analyze_speech",
                                                                        domain=domain,
                                                                        speech_metrics=speech_metrics)
                context["knowledge_sources"]["domain_analysis"] = domain_analysis
                
                # Event-specific analysis if event provided
                if event_id:
                    event_analysis = self.event_server.get_context_for_llm("event_fit_analysis",
                                                                         event_id=event_id,
                                                                         speech_metrics=speech_metrics)
                    context["knowledge_sources"]["event_analysis"] = event_analysis
                
                # Audience-specific analysis if audience provided
                if audience_id:
                    audience_analysis = self.audience_server.get_context_for_llm("audience_analysis",
                                                                               audience_id=audience_id,
                                                                               speech_metrics=speech_metrics)
                    context["knowledge_sources"]["audience_analysis"] = audience_analysis
            
            # Synthesize coaching recommendations
            context["coaching_synthesis"] = self._synthesize_coaching_recommendations(context["knowledge_sources"])
            
            return context
            
        except Exception as e:
            logger.error(f"Error gathering comprehensive context: {str(e)}")
            context["error"] = str(e)
            return context
    
    def _synthesize_coaching_recommendations(self, knowledge_sources: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize recommendations from all knowledge sources"""
        synthesis = {
            "priority_areas": [],
            "personalized_approach": {},
            "context_specific_tips": [],
            "success_metrics": [],
            "improvement_focus": {}
        }
        
        # Extract user preferences and challenges
        user_data = knowledge_sources.get("user", {})
        if user_data.get("coaching_context"):
            coaching_context = user_data["coaching_context"]
            synthesis["personalized_approach"] = {
                "skill_level": coaching_context.get("current_skill_level"),
                "primary_goals": coaching_context.get("primary_goals", []),
                "challenge_areas": coaching_context.get("challenge_areas", []),
                "learning_preferences": coaching_context.get("learning_preferences", []),
                "coaching_style": user_data.get("personalization_recommendations", {}).get("coaching_approach", "balanced")
            }
            
            # Priority areas from user challenges
            synthesis["priority_areas"].extend(coaching_context.get("challenge_areas", [])[:3])
        
        # Extract domain-specific guidance
        domain_data = knowledge_sources.get("domain", {})
        if domain_data.get("complete_guidelines"):
            guidelines = domain_data["complete_guidelines"]
            synthesis["context_specific_tips"].extend(guidelines.get("best_practices", [])[:3])
        
        # Extract event-specific recommendations
        event_data = knowledge_sources.get("event", {})
        if event_data and event_data.get("coaching_tips"):
            event_tips = event_data["coaching_tips"]
            if event_tips.get("targeted_coaching"):
                for tip in event_tips["targeted_coaching"]:
                    if tip.get("priority") == "high":
                        synthesis["context_specific_tips"].append(f"[Event-{tip.get('category')}] {tip.get('recommendation')}")
        
        # Extract audience-specific recommendations
        audience_data = knowledge_sources.get("audience", {})
        if audience_data and audience_data.get("coaching_tips"):
            audience_tips = audience_data["coaching_tips"]
            if audience_tips.get("engagement_tactics"):
                for tactic in audience_tips["engagement_tactics"][:2]:  # Top 2 tactics
                    synthesis["context_specific_tips"].append(f"[Audience] {tactic}")
        
        # Performance analysis integration
        domain_analysis = knowledge_sources.get("domain_analysis", {})
        if domain_analysis.get("detailed_analysis"):
            analysis = domain_analysis["detailed_analysis"]
            for metric, data in analysis.items():
                if data.get("score", 100) < 70:
                    synthesis["improvement_focus"][metric] = {
                        "current_score": data.get("score"),
                        "target": data.get("target"),
                        "recommendation": f"Focus on improving {metric}"
                    }
        
        # Success metrics synthesis
        if user_data.get("progress_summary", {}).get("goal_progress"):
            for goal, progress in user_data["progress_summary"]["goal_progress"].items():
                if progress.get("progress_percentage", 0) < 80:
                    synthesis["success_metrics"].append(f"Progress toward {goal}: {progress.get('progress_percentage', 0)}%")
        
        return synthesis
    
    def get_contextual_feedback(self,
                              user_id: str,
                              speech_analysis: Dict[str, Any],
                              domain: str = "public_speaking",
                              event_id: Optional[str] = None,
                              audience_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate contextual feedback based on speech analysis and all available context
        
        Args:
            user_id: User identifier
            speech_analysis: Complete speech analysis results
            domain: Speaking domain
            event_id: Specific event identifier (optional)
            audience_id: Specific audience identifier (optional)
        
        Returns:
            Contextual feedback with personalized recommendations
        """
        logger.info(f"Generating contextual feedback for user {user_id}")
        
        # Get comprehensive context
        context = self.get_comprehensive_context(
            user_id=user_id,
            domain=domain,
            event_id=event_id,
            audience_id=audience_id,
            speech_metrics=speech_analysis.get("metrics", {})
        )
        
        # Generate feedback structure
        feedback = {
            "feedback_timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "session_context": {
                "domain": domain,
                "event_id": event_id,
                "audience_id": audience_id,
                "analysis_summary": speech_analysis
            },
            "contextual_insights": self._generate_contextual_insights(context),
            "personalized_recommendations": self._generate_personalized_recommendations(context),
            "progress_tracking": self._generate_progress_insights(context),
            "next_steps": self._generate_next_steps(context),
            "context_type": "contextual_feedback"
        }
        
        return feedback
    
    def _generate_contextual_insights(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights based on comprehensive context"""
        insights = {
            "performance_highlights": [],
            "improvement_opportunities": [],
            "context_alignment": {}
        }
        
        # Domain alignment insights
        domain_analysis = context["knowledge_sources"].get("domain_analysis", {})
        if domain_analysis.get("overall_score"):
            score = domain_analysis["overall_score"]
            if score >= 80:
                insights["performance_highlights"].append(f"Strong alignment with domain best practices (Score: {score})")
            elif score < 60:
                insights["improvement_opportunities"].append(f"Opportunity to better align with domain guidelines (Score: {score})")
        
        # Audience alignment insights
        audience_analysis = context["knowledge_sources"].get("audience_analysis", {})
        if audience_analysis.get("fit_analysis"):
            fit_data = audience_analysis["fit_analysis"]
            for metric, analysis in fit_data.items():
                if analysis.get("audience_appropriateness") == "needs_adjustment":
                    insights["improvement_opportunities"].append(f"Adjust {metric} for better audience fit")
        
        return insights
    
    def _generate_personalized_recommendations(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate personalized recommendations based on user profile and context"""
        recommendations = []
        
        synthesis = context.get("coaching_synthesis", {})
        user_approach = synthesis.get("personalized_approach", {})
        
        # Skill level specific recommendations
        skill_level = user_approach.get("skill_level", "intermediate")
        if skill_level == "beginner":
            recommendations.append({
                "category": "Foundation Building",
                "recommendation": "Focus on mastering basic structure and reducing nervousness",
                "rationale": "Building confidence through consistent fundamentals",
                "priority": "high"
            })
        elif skill_level == "advanced":
            recommendations.append({
                "category": "Mastery Development",
                "recommendation": "Focus on subtle audience reading and dynamic adaptation",
                "rationale": "Advanced skills for expert-level performance",
                "priority": "medium"
            })
        
        # Goal-specific recommendations
        goals = user_approach.get("primary_goals", [])
        for goal in goals:
            if goal == "build_confidence":
                recommendations.append({
                    "category": "Confidence Building",
                    "recommendation": "Practice with smaller, supportive audiences first",
                    "rationale": "Gradual confidence building through positive experiences",
                    "priority": "high"
                })
            elif goal == "increase_engagement":
                recommendations.append({
                    "category": "Audience Engagement",
                    "recommendation": "Incorporate more interactive elements and storytelling",
                    "rationale": "Direct alignment with engagement goals",
                    "priority": "high"
                })
        
        return recommendations
    
    def _generate_progress_insights(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate progress tracking insights"""
        progress = {
            "current_trajectory": "stable",
            "milestone_progress": {},
            "comparative_performance": {}
        }
        
        user_data = context["knowledge_sources"].get("user", {})
        if user_data.get("progress_summary"):
            progress_data = user_data["progress_summary"]
            progress["current_trajectory"] = progress_data.get("improvement_trend", "stable")
            progress["milestone_progress"] = progress_data.get("goal_progress", {})
        
        return progress
    
    def _generate_next_steps(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate actionable next steps"""
        next_steps = []
        
        synthesis = context.get("coaching_synthesis", {})
        
        # Priority areas
        for area in synthesis.get("priority_areas", [])[:2]:  # Top 2 priorities
            next_steps.append({
                "action": f"Practice exercises targeting {area}",
                "timeframe": "Next 1-2 sessions",
                "category": "skill_development"
            })
        
        # Context-specific steps
        if synthesis.get("improvement_focus"):
            for metric, data in synthesis["improvement_focus"].items():
                next_steps.append({
                    "action": data.get("recommendation", f"Work on {metric}"),
                    "timeframe": "Immediate focus",
                    "category": "performance_improvement"
                })
        
        return next_steps
    
    def get_available_options(self) -> Dict[str, Any]:
        """Get all available options for testing and integration"""
        return {
            "available_users": self.user_server.get_context_for_llm("available_users"),
            "available_domains": self.domain_server.get_context_for_llm("available_domains"),
            "available_events": self.event_server.get_context_for_llm("available_events"),
            "available_audiences": self.audience_server.get_context_for_llm("available_audiences"),
            "context_type": "available_options"
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of all knowledge servers"""
        return {
            "status": "healthy",
            "servers": {
                "domain_server": "initialized",
                "user_server": "initialized", 
                "event_server": "initialized",
                "audience_server": "initialized"
            },
            "timestamp": datetime.now().isoformat(),
            "context_type": "health_check"
        }

# Example usage and testing
def main():
    """Test the unified LLM interface"""
    interface = SpeechCoachLLMInterface()
    
    # Test health check
    print("=== Health Check ===")
    health = interface.health_check()
    print(json.dumps(health, indent=2))
    
    # Test available options
    print("\n=== Available Options ===")
    options = interface.get_available_options()
    print(json.dumps(options, indent=2))
    
    # Test comprehensive context with audience
    print("\n=== Comprehensive Context with Audience ===")
    comprehensive_context = interface.get_comprehensive_context(
        user_id="user123",
        domain="corporate",
        event_id="quarterly_review",
        audience_id="executives",
        speech_metrics={
            "pace_wpm": 140,
            "filler_words_count": 5,
            "vocal_variety_score": 7.2,
            "confidence_score": 7.8
        }
    )
    print(json.dumps(comprehensive_context, indent=2))
    
    # Test contextual feedback with audience
    print("\n=== Contextual Feedback with Audience ===")
    sample_analysis = {
        "metrics": {
            "pace_wpm": 140,
            "filler_words_count": 5,
            "vocal_variety_score": 7.2,
            "confidence_score": 7.8
        },
        "transcript": "Sample presentation transcript...",
        "delivery_score": 7.5
    }
    
    feedback = interface.get_contextual_feedback(
        user_id="user123",
        speech_analysis=sample_analysis,
        domain="corporate",
        event_id="quarterly_review",
        audience_id="executives"
    )
    print(json.dumps(feedback, indent=2))

if __name__ == "__main__":
    main()
