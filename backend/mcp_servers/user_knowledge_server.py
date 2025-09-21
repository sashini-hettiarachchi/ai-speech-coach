#!/usr/bin/env python3
"""
User Knowledge Server for Speech Coach
Provides user-specific context and personalized coaching recommendations for LLMs
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict, field
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SkillLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class SpeakingGoal(Enum):
    CONFIDENCE = "build_confidence"
    CLARITY = "improve_clarity"
    ENGAGEMENT = "increase_engagement"
    PROFESSIONALISM = "enhance_professionalism"
    TECHNICAL_COMMUNICATION = "technical_communication"
    LEADERSHIP = "leadership_communication"

@dataclass
class UserProfile:
    user_id: str
    name: str
    skill_level: SkillLevel
    primary_goals: List[SpeakingGoal]
    speaking_experience_years: int
    preferred_domains: List[str]
    challenge_areas: List[str]
    strengths: List[str]
    learning_preferences: List[str]
    created_date: str
    last_updated: str

@dataclass 
class SpeechSession:
    session_id: str
    user_id: str
    date: str
    domain: str
    duration_minutes: int
    metrics: Dict[str, Any]
    feedback_received: List[str]
    improvement_areas_identified: List[str]
    goals_addressed: List[str]
    satisfaction_score: Optional[int] = None

@dataclass
class UserProgress:
    user_id: str
    skill_progression: Dict[str, float]  # skill -> score progression
    goals_progress: Dict[str, Dict[str, Any]]  # goal -> progress data
    improvement_trend: str  # "improving", "stable", "declining"
    last_assessment_date: str
    next_milestone: str
    sessions_completed: int
    total_practice_time_minutes: int

class UserKnowledgeBase:
    """Knowledge base for user profiles, history, and personalized coaching"""
    
    def __init__(self):
        self.users = self._initialize_sample_users()
        self.sessions = self._initialize_sample_sessions()
        self.progress_data = self._initialize_progress_data()
    
    def _initialize_sample_users(self) -> Dict[str, UserProfile]:
        """Initialize sample user profiles for testing"""
        return {
            "user123": UserProfile(
                user_id="user123",
                name="Alex Johnson",
                skill_level=SkillLevel.INTERMEDIATE,
                primary_goals=[SpeakingGoal.CONFIDENCE, SpeakingGoal.ENGAGEMENT],
                speaking_experience_years=3,
                preferred_domains=["public_speaking", "corporate"],
                challenge_areas=["filler_words", "eye_contact", "vocal_variety"],
                strengths=["content_organization", "clear_articulation"],
                learning_preferences=["visual_feedback", "practice_sessions", "peer_feedback"],
                created_date="2024-01-15",
                last_updated="2025-09-20"
            ),
            "user456": UserProfile(
                user_id="user456", 
                name="Dr. Sarah Chen",
                skill_level=SkillLevel.ADVANCED,
                primary_goals=[SpeakingGoal.TECHNICAL_COMMUNICATION, SpeakingGoal.LEADERSHIP],
                speaking_experience_years=8,
                preferred_domains=["technical", "academic"],
                challenge_areas=["pace_control", "audience_adaptation"],
                strengths=["technical_accuracy", "logical_structure", "expertise"],
                learning_preferences=["data_driven_feedback", "comparative_analysis"],
                created_date="2023-06-10",
                last_updated="2025-09-18"
            ),
            "user789": UserProfile(
                user_id="user789",
                name="Marcus Williams",
                skill_level=SkillLevel.BEGINNER,
                primary_goals=[SpeakingGoal.CONFIDENCE, SpeakingGoal.CLARITY],
                speaking_experience_years=1,
                preferred_domains=["public_speaking"],
                challenge_areas=["nervousness", "filler_words", "structure", "voice_projection"],
                strengths=["enthusiasm", "authenticity"],
                learning_preferences=["step_by_step_guidance", "frequent_practice", "positive_reinforcement"],
                created_date="2025-03-01",
                last_updated="2025-09-21"
            )
        }
    
    def _initialize_sample_sessions(self) -> Dict[str, List[SpeechSession]]:
        """Initialize sample speech sessions"""
        return {
            "user123": [
                SpeechSession(
                    session_id="session_001",
                    user_id="user123",
                    date="2025-09-15",
                    domain="corporate",
                    duration_minutes=8,
                    metrics={
                        "pace_wpm": 145,
                        "filler_words_count": 7,
                        "pause_frequency": 0.15,
                        "vocal_variety_score": 6.5,
                        "confidence_score": 7.2
                    },
                    feedback_received=[
                        "Good content organization",
                        "Reduce filler words", 
                        "Improve eye contact"
                    ],
                    improvement_areas_identified=["filler_words", "eye_contact"],
                    goals_addressed=["confidence"],
                    satisfaction_score=8
                ),
                SpeechSession(
                    session_id="session_002",
                    user_id="user123",
                    date="2025-09-18",
                    domain="public_speaking",
                    duration_minutes=6,
                    metrics={
                        "pace_wpm": 138,
                        "filler_words_count": 4,
                        "pause_frequency": 0.18,
                        "vocal_variety_score": 7.1,
                        "confidence_score": 7.8
                    },
                    feedback_received=[
                        "Improved filler word usage",
                        "Better pacing",
                        "Continue working on engagement"
                    ],
                    improvement_areas_identified=["audience_engagement"],
                    goals_addressed=["confidence", "engagement"],
                    satisfaction_score=9
                )
            ],
            "user456": [
                SpeechSession(
                    session_id="session_003",
                    user_id="user456",
                    date="2025-09-14",
                    domain="technical",
                    duration_minutes=12,
                    metrics={
                        "pace_wpm": 108,
                        "filler_words_count": 2,
                        "pause_frequency": 0.22,
                        "vocal_variety_score": 8.2,
                        "technical_clarity_score": 9.1
                    },
                    feedback_received=[
                        "Excellent technical accuracy",
                        "Consider audience adaptation",
                        "Maintain engaging pace"
                    ],
                    improvement_areas_identified=["audience_adaptation", "pace_variation"],
                    goals_addressed=["technical_communication"],
                    satisfaction_score=8
                )
            ],
            "user789": [
                SpeechSession(
                    session_id="session_004",
                    user_id="user789",
                    date="2025-09-20",
                    domain="public_speaking",
                    duration_minutes=4,
                    metrics={
                        "pace_wpm": 180,
                        "filler_words_count": 12,
                        "pause_frequency": 0.08,
                        "vocal_variety_score": 4.2,
                        "confidence_score": 5.1
                    },
                    feedback_received=[
                        "Slow down your pace",
                        "Practice reducing filler words",
                        "Use more strategic pauses",
                        "Great enthusiasm!"
                    ],
                    improvement_areas_identified=["pace_control", "filler_words", "strategic_pauses"],
                    goals_addressed=["confidence", "clarity"],
                    satisfaction_score=7
                )
            ]
        }
    
    def _initialize_progress_data(self) -> Dict[str, UserProgress]:
        """Initialize user progress tracking"""
        return {
            "user123": UserProgress(
                user_id="user123",
                skill_progression={
                    "overall_confidence": 7.5,  # improved from 6.0
                    "filler_word_control": 7.0,  # improved from 5.5
                    "content_organization": 8.5,  # strength maintained
                    "vocal_variety": 6.8,  # slight improvement
                    "audience_engagement": 6.2   # area of focus
                },
                goals_progress={
                    "build_confidence": {
                        "target_score": 8.0,
                        "current_score": 7.5,
                        "progress_percentage": 75,
                        "trend": "improving"
                    },
                    "increase_engagement": {
                        "target_score": 7.5,
                        "current_score": 6.2,
                        "progress_percentage": 45,
                        "trend": "stable"
                    }
                },
                improvement_trend="improving",
                last_assessment_date="2025-09-18",
                next_milestone="Achieve consistent 8+ confidence score",
                sessions_completed=15,
                total_practice_time_minutes=120
            ),
            "user456": UserProgress(
                user_id="user456",
                skill_progression={
                    "technical_communication": 9.2,
                    "leadership_presence": 8.1,
                    "audience_adaptation": 6.8,
                    "pace_control": 7.5,
                    "content_expertise": 9.5
                },
                goals_progress={
                    "technical_communication": {
                        "target_score": 9.0,
                        "current_score": 9.2,
                        "progress_percentage": 100,
                        "trend": "achieving"
                    },
                    "leadership_communication": {
                        "target_score": 8.5,
                        "current_score": 8.1,
                        "progress_percentage": 85,
                        "trend": "improving"
                    }
                },
                improvement_trend="improving",
                last_assessment_date="2025-09-14",
                next_milestone="Master audience adaptation techniques",
                sessions_completed=28,
                total_practice_time_minutes=350
            ),
            "user789": UserProgress(
                user_id="user789",
                skill_progression={
                    "overall_confidence": 5.1,  # starting low but improving
                    "pace_control": 3.8,  # major area for improvement
                    "filler_word_control": 4.2,  # needs work
                    "content_clarity": 6.5,  # relative strength
                    "enthusiasm": 8.0   # natural strength
                },
                goals_progress={
                    "build_confidence": {
                        "target_score": 7.0,
                        "current_score": 5.1,
                        "progress_percentage": 25,
                        "trend": "improving_slowly"
                    },
                    "improve_clarity": {
                        "target_score": 7.5,
                        "current_score": 6.5,
                        "progress_percentage": 65,
                        "trend": "stable"
                    }
                },
                improvement_trend="improving_slowly",
                last_assessment_date="2025-09-20",
                next_milestone="Achieve comfortable pace control",
                sessions_completed=3,
                total_practice_time_minutes=18
            )
        }
    
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get complete user profile"""
        if user_id not in self.users:
            raise ValueError(f"User {user_id} not found")
        
        user = self.users[user_id]
        return {
            "user_profile": asdict(user),
            "context_type": "user_profile"
        }
    
    def get_user_coaching_context(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive coaching context for a user"""
        if user_id not in self.users:
            raise ValueError(f"User {user_id} not found")
        
        user = self.users[user_id]
        progress = self.progress_data.get(user_id)
        recent_sessions = self.sessions.get(user_id, [])[-3:]  # Last 3 sessions
        
        context = {
            "user_id": user_id,
            "coaching_context": {
                "current_skill_level": user.skill_level.value,
                "primary_goals": [goal.value for goal in user.primary_goals],
                "challenge_areas": user.challenge_areas,
                "strengths": user.strengths,
                "learning_preferences": user.learning_preferences,
                "preferred_domains": user.preferred_domains
            },
            "progress_summary": {
                "improvement_trend": progress.improvement_trend if progress else "no_data",
                "sessions_completed": progress.sessions_completed if progress else 0,
                "skill_scores": progress.skill_progression if progress else {},
                "goal_progress": progress.goals_progress if progress else {}
            },
            "recent_performance": {
                "last_session_metrics": recent_sessions[-1].metrics if recent_sessions else {},
                "recent_improvement_areas": list(set(
                    area for session in recent_sessions 
                    for area in session.improvement_areas_identified
                )),
                "recent_feedback_themes": list(set(
                    feedback for session in recent_sessions 
                    for feedback in session.feedback_received
                ))
            },
            "personalization_recommendations": self._generate_personalization_recommendations(user, progress, recent_sessions),
            "context_type": "user_coaching_context"
        }
        
        return context
    
    def _generate_personalization_recommendations(self, user: UserProfile, progress: Optional[UserProgress], recent_sessions: List[SpeechSession]) -> Dict[str, Any]:
        """Generate personalized coaching recommendations"""
        recommendations = {
            "coaching_approach": "",
            "focus_areas": [],
            "motivation_style": "",
            "feedback_style": "",
            "practice_suggestions": []
        }
        
        # Coaching approach based on skill level
        if user.skill_level == SkillLevel.BEGINNER:
            recommendations["coaching_approach"] = "supportive_and_structured"
            recommendations["motivation_style"] = "positive_reinforcement_with_encouragement"
            recommendations["feedback_style"] = "gentle_and_specific"
        elif user.skill_level == SkillLevel.INTERMEDIATE:
            recommendations["coaching_approach"] = "balanced_challenge_and_support"
            recommendations["motivation_style"] = "goal_oriented_with_progress_tracking"
            recommendations["feedback_style"] = "direct_and_actionable"
        else:  # Advanced/Expert
            recommendations["coaching_approach"] = "strategic_and_analytical"
            recommendations["motivation_style"] = "achievement_and_mastery_focused"
            recommendations["feedback_style"] = "detailed_and_comparative"
        
        # Focus areas based on challenge areas and recent performance
        recommendations["focus_areas"] = user.challenge_areas[:3]  # Top 3 challenge areas
        
        # Practice suggestions based on learning preferences
        if "visual_feedback" in user.learning_preferences:
            recommendations["practice_suggestions"].append("Use charts and visual progress tracking")
        if "peer_feedback" in user.learning_preferences:
            recommendations["practice_suggestions"].append("Incorporate peer evaluation exercises")
        if "step_by_step_guidance" in user.learning_preferences:
            recommendations["practice_suggestions"].append("Break down improvements into small, achievable steps")
        
        return recommendations
    
    def get_user_history(self, user_id: str, limit: int = 10) -> Dict[str, Any]:
        """Get user's speech session history"""
        if user_id not in self.users:
            raise ValueError(f"User {user_id} not found")
        
        sessions = self.sessions.get(user_id, [])
        limited_sessions = sessions[-limit:] if limit else sessions
        
        return {
            "user_id": user_id,
            "session_history": [asdict(session) for session in limited_sessions],
            "total_sessions": len(sessions),
            "context_type": "user_history"
        }
    
    def analyze_user_progress(self, user_id: str) -> Dict[str, Any]:
        """Analyze user's progress and trends"""
        if user_id not in self.users:
            raise ValueError(f"User {user_id} not found")
        
        user = self.users[user_id]
        progress = self.progress_data.get(user_id)
        sessions = self.sessions.get(user_id, [])
        
        if not progress or not sessions:
            return {
                "user_id": user_id,
                "analysis": "insufficient_data",
                "context_type": "progress_analysis"
            }
        
        # Calculate trends
        session_scores = []
        for session in sessions:
            if 'confidence_score' in session.metrics:
                session_scores.append(session.metrics['confidence_score'])
        
        trend_analysis = "improving" if len(session_scores) >= 2 and session_scores[-1] > session_scores[0] else "stable"
        
        analysis = {
            "user_id": user_id,
            "progress_analysis": {
                "overall_trend": progress.improvement_trend,
                "confidence_trend": trend_analysis,
                "sessions_completed": progress.sessions_completed,
                "total_practice_time": progress.total_practice_time_minutes,
                "current_skill_scores": progress.skill_progression,
                "goal_achievement": progress.goals_progress,
                "next_milestone": progress.next_milestone
            },
            "insights": self._generate_progress_insights(user, progress, sessions),
            "context_type": "progress_analysis"
        }
        
        return analysis
    
    def _generate_progress_insights(self, user: UserProfile, progress: UserProgress, sessions: List[SpeechSession]) -> List[str]:
        """Generate insights about user progress"""
        insights = []
        
        # Skill level insights
        if user.skill_level == SkillLevel.BEGINNER and progress.sessions_completed >= 5:
            insights.append("User is gaining experience and building foundational skills")
        
        # Goal progress insights
        for goal, goal_data in progress.goals_progress.items():
            if goal_data["progress_percentage"] >= 80:
                insights.append(f"Approaching mastery in {goal.replace('_', ' ')}")
            elif goal_data["progress_percentage"] < 30:
                insights.append(f"Early stage in {goal.replace('_', ' ')} development")
        
        # Improvement trend insights
        if progress.improvement_trend == "improving":
            insights.append("Showing consistent improvement across sessions")
        elif progress.improvement_trend == "stable":
            insights.append("Performance has stabilized - consider new challenges")
        
        return insights

class UserKnowledgeServer:
    """Server interface for LLM integration with user knowledge"""
    
    def __init__(self):
        self.knowledge_base = UserKnowledgeBase()
        logger.info("User Knowledge Server initialized")
    
    def get_context_for_llm(self, query_type: str, **kwargs) -> Dict[str, Any]:
        """
        Main interface for LLM to get user context
        
        Query types:
        - user_profile: Get basic user profile
        - coaching_context: Get comprehensive coaching context
        - user_history: Get session history
        - progress_analysis: Get progress trends and insights
        - available_users: List available users for testing
        """
        try:
            if query_type == "user_profile":
                user_id = kwargs.get("user_id")
                if not user_id:
                    return {"error": "user_id required", "context_type": "error"}
                return self.knowledge_base.get_user_profile(user_id)
            
            elif query_type == "coaching_context":
                user_id = kwargs.get("user_id")
                if not user_id:
                    return {"error": "user_id required", "context_type": "error"}
                return self.knowledge_base.get_user_coaching_context(user_id)
            
            elif query_type == "user_history":
                user_id = kwargs.get("user_id")
                limit = kwargs.get("limit", 10)
                if not user_id:
                    return {"error": "user_id required", "context_type": "error"}
                return self.knowledge_base.get_user_history(user_id, limit)
            
            elif query_type == "progress_analysis":
                user_id = kwargs.get("user_id")
                if not user_id:
                    return {"error": "user_id required", "context_type": "error"}
                return self.knowledge_base.analyze_user_progress(user_id)
            
            elif query_type == "available_users":
                return {
                    "available_users": list(self.knowledge_base.users.keys()),
                    "user_details": {
                        user_id: {
                            "name": user.name,
                            "skill_level": user.skill_level.value,
                            "primary_goals": [goal.value for goal in user.primary_goals]
                        }
                        for user_id, user in self.knowledge_base.users.items()
                    },
                    "context_type": "available_options"
                }
            
            else:
                return {
                    "error": f"Unknown query type: {query_type}",
                    "available_query_types": ["user_profile", "coaching_context", "user_history", "progress_analysis", "available_users"],
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
    """Test the user knowledge server"""
    server = UserKnowledgeServer()
    
    # Test available users
    print("=== Available Users ===")
    users = server.get_context_for_llm("available_users")
    print(json.dumps(users, indent=2))
    
    # Test coaching context
    print("\n=== Coaching Context for Intermediate User ===")
    coaching_context = server.get_context_for_llm("coaching_context", user_id="user123")
    print(json.dumps(coaching_context, indent=2))
    
    # Test progress analysis
    print("\n=== Progress Analysis for Beginner User ===")
    progress = server.get_context_for_llm("progress_analysis", user_id="user789")
    print(json.dumps(progress, indent=2))

if __name__ == "__main__":
    main()
