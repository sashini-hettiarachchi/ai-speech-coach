"""
Database models for Speech Coach application.
Integrates with Auth0 for user management while storing speech/session data locally.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    """
    Minimal user model for Auth0 integration.
    Only stores essential data for relationships - all profile data comes from Auth0.
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    auth0_user_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    synced_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    speeches = db.relationship('Speech', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.auth0_user_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'auth0_user_id': self.auth0_user_id,
            'synced_at': self.synced_at.isoformat() if self.synced_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Speech(db.Model):
    """
    Speech model for organizing user's speaking practice sessions.
    Each speech represents a topic/presentation the user wants to improve on.
    """
    __tablename__ = 'speeches'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Speech Information
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    context = db.Column(db.String(100), nullable=False)  # academic, persuasive, storytelling, professional
    goal = db.Column(db.Text)  # User's improvement goals for this speech
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sessions = db.relationship('Session', backref='speech', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Speech {self.title}>'
    
    def to_dict(self, include_sessions=False):
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'context': self.context,
            'goal': self.goal,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'session_count': len(self.sessions)
        }
        
        if include_sessions:
            result['sessions'] = [session.to_dict() for session in self.sessions]
            
        return result


class Session(db.Model):
    """
    Session model for individual practice sessions within a speech.
    Stores all analysis results, media files, and scoring data.
    """
    __tablename__ = 'sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    speech_id = db.Column(db.Integer, db.ForeignKey('speeches.id'), nullable=False, index=True)
    
    # Session Information
    title = db.Column(db.String(255))  # Optional session title
    
    # Media Information
    media_url = db.Column(db.String(500))  # Path to stored audio/video file
    media_type = db.Column(db.String(50))  # 'audio' or 'video'
    original_filename = db.Column(db.String(255))
    duration_seconds = db.Column(db.Float)
    
    # Core Analysis Results
    transcript = db.Column(db.Text)
    feedback = db.Column(db.Text)
    
    # Filler Word Analysis
    filler_word_count = db.Column(db.Integer, default=0)
    filler_word_percentage = db.Column(db.Float)
    filler_word_details = db.Column(db.JSON)  # Detailed filler analysis with timestamps
    
    # Audio Prosody Analysis
    words_per_minute = db.Column(db.Float)
    syllables_per_minute = db.Column(db.Float)
    pitch_mean = db.Column(db.Float)
    pitch_std = db.Column(db.Float)
    volume_mean = db.Column(db.Float)
    volume_std = db.Column(db.Float)
    
    # Event Data (stored as JSON)
    pause_events = db.Column(db.JSON)  # Pause analysis data
    pitch_events = db.Column(db.JSON)  # Pitch variation events
    volume_events = db.Column(db.JSON)  # Volume variation events
    speed_events = db.Column(db.JSON)  # Speaking speed events
    
    # Video Analysis (if applicable)
    eye_contact_percentage = db.Column(db.Float)
    gesture_rate = db.Column(db.Float)
    facial_expressiveness = db.Column(db.Float)
    video_analysis = db.Column(db.JSON)  # Complete video analysis data
    
    # Scoring and Quality Metrics
    overall_score = db.Column(db.Float)
    pronunciation_score = db.Column(db.Float)
    fluency_score = db.Column(db.Float)
    clarity_score = db.Column(db.Float)
    confidence_score = db.Column(db.Float)
    structure_score = db.Column(db.Float)
    engagement_score = db.Column(db.Float)
    
    # Additional Analysis Data
    grammar_error_count = db.Column(db.Integer, default=0)
    readability_score = db.Column(db.Float)
    structure_quality = db.Column(db.Float)
    
    # Complete Analysis Results (for flexibility)
    full_analysis_results = db.Column(db.JSON)  # Store complete analysis output
    
    # Metadata
    analysis_version = db.Column(db.String(50))  # Track analysis algorithm version
    processing_time_seconds = db.Column(db.Float)  # How long analysis took
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Session {self.id} for Speech {self.speech_id}>'
    
    def to_dict(self, include_full_analysis=False):
        result = {
            'id': self.id,
            'speech_id': self.speech_id,
            'title': self.title,
            
            # Media info
            'media_url': self.media_url,
            'media_type': self.media_type,
            'original_filename': self.original_filename,
            'duration_seconds': self.duration_seconds,
            
            # Core results
            'transcript': self.transcript,
            'feedback': self.feedback,
            
            # Filler words
            'filler_word_count': self.filler_word_count,
            'filler_word_percentage': self.filler_word_percentage,
            'filler_word_details': self.filler_word_details,
            
            # Prosody
            'words_per_minute': self.words_per_minute,
            'syllables_per_minute': self.syllables_per_minute,
            'pitch_mean': self.pitch_mean,
            'pitch_std': self.pitch_std,
            'volume_mean': self.volume_mean,
            'volume_std': self.volume_std,
            
            # Video analysis
            'eye_contact_percentage': self.eye_contact_percentage,
            'gesture_rate': self.gesture_rate,
            'facial_expressiveness': self.facial_expressiveness,
            
            # Scores
            'overall_score': self.overall_score,
            'pronunciation_score': self.pronunciation_score,
            'fluency_score': self.fluency_score,
            'clarity_score': self.clarity_score,
            'confidence_score': self.confidence_score,
            'structure_score': self.structure_score,
            'engagement_score': self.engagement_score,
            
            # Additional metrics
            'grammar_error_count': self.grammar_error_count,
            'readability_score': self.readability_score,
            'structure_quality': self.structure_quality,
            
            # Metadata
            'analysis_version': self.analysis_version,
            'processing_time_seconds': self.processing_time_seconds,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_full_analysis:
            result.update({
                'pause_events': self.pause_events,
                'pitch_events': self.pitch_events,
                'volume_events': self.volume_events,
                'speed_events': self.speed_events,
                'video_analysis': self.video_analysis,
                'full_analysis_results': self.full_analysis_results
            })
            
        return result
    
    def get_scores_summary(self):
        """Get a summary of all scores for progress tracking"""
        return {
            'overall_score': self.overall_score,
            'pronunciation_score': self.pronunciation_score,
            'fluency_score': self.fluency_score,
            'clarity_score': self.clarity_score,
            'confidence_score': self.confidence_score,
            'structure_score': self.structure_score,
            'engagement_score': self.engagement_score,
            'session_date': self.created_at.isoformat() if self.created_at else None
        }
