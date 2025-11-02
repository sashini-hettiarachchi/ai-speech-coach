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
    goal = db.Column(db.Text)  # Speech goal/objective (optional when with_context=False)
    audience_description = db.Column(db.Text)  # Target audience description (optional when with_context=False)
    key_points = db.Column(db.Text)  # Key points or outline (optional)
    self_improvement_goal = db.Column(db.Text)  # Self-improvement goals (optional)
    context = db.Column(db.String(100))  # academic, persuasive, storytelling, professional (optional when with_context=False)
    
    # New fields for speech workflow management
    with_context = db.Column(db.Boolean, nullable=False, default=True)  # Whether speech includes detailed context
    completed = db.Column(db.Boolean, nullable=False, default=False)  # Whether speech practice is completed
    prpsa_completed = db.Column(db.Boolean, nullable=False, default=False)  # Whether PRPSA assessment is completed
    
    # Legacy fields (for backward compatibility)
    description = db.Column(db.Text)  # Deprecated - use goal instead
    
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
            'goal': self.goal,
            'audience_description': self.audience_description,
            'key_points': self.key_points,
            'self_improvement_goal': self.self_improvement_goal,
            'context': self.context,
            'with_context': self.with_context,
            'completed': self.completed,
            'prpsa_completed': self.prpsa_completed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'session_count': len(self.sessions),
            # Legacy field for backward compatibility
            'description': self.description
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
    media_url = db.Column(db.String(2000))  # Path to stored audio/video file (increased for GCS signed URLs)
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


class UserSelfRating(db.Model):
    """
    User self-rating model for storing user's self-evaluation of their speech sessions.
    Allows users to rate themselves on each CSSEF criterion before or after AI analysis.
    """
    __tablename__ = 'user_self_ratings'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False, index=True)
    
    # CSSEF Criterion Ratings (1-10 scale)
    c1_topic_choice_score = db.Column(db.Integer)  # Topic choice & focus
    c1_topic_choice_comment = db.Column(db.Text)
    
    c2_purpose_score = db.Column(db.Integer)  # Thesis & purpose
    c2_purpose_comment = db.Column(db.Text)
    
    c3_supporting_score = db.Column(db.Integer)  # Supporting materials
    c3_supporting_comment = db.Column(db.Text)
    
    c4_organization_score = db.Column(db.Integer)  # Organization & structure
    c4_organization_comment = db.Column(db.Text)
    
    c5_language_score = db.Column(db.Integer)  # Language use
    c5_language_comment = db.Column(db.Text)
    
    c6_vocal_variety_score = db.Column(db.Integer)  # Vocal variety & delivery
    c6_vocal_variety_comment = db.Column(db.Text)
    
    c7_pronunciation_score = db.Column(db.Integer)  # Pronunciation & articulation
    c7_pronunciation_comment = db.Column(db.Text)
    
    c8_physical_score = db.Column(db.Integer)  # Physical delivery
    c8_physical_comment = db.Column(db.Text)
    
    # Overall user feedback
    overall_comment = db.Column(db.Text)  # General self-reflection
    confidence_level = db.Column(db.Integer)  # How confident they feel about their rating (1-5)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    session = db.relationship('Session', backref='user_self_rating', uselist=False)
    
    def __repr__(self):
        return f'<UserSelfRating {self.id} for Session {self.session_id}>'
    
    def to_dict(self):
        """Convert user self-rating to dictionary"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'ratings': {
                'C1_topic_choice': {
                    'score': self.c1_topic_choice_score,
                    'comment': self.c1_topic_choice_comment
                },
                'C2_purpose': {
                    'score': self.c2_purpose_score,
                    'comment': self.c2_purpose_comment
                },
                'C3_supporting_material': {
                    'score': self.c3_supporting_score,
                    'comment': self.c3_supporting_comment
                },
                'C4_organization': {
                    'score': self.c4_organization_score,
                    'comment': self.c4_organization_comment
                },
                'C5_language_use': {
                    'score': self.c5_language_score,
                    'comment': self.c5_language_comment
                },
                'C6_vocal_variety': {
                    'score': self.c6_vocal_variety_score,
                    'comment': self.c6_vocal_variety_comment
                },
                'C7_pronunciation_and_grammar': {
                    'score': self.c7_pronunciation_score,
                    'comment': self.c7_pronunciation_comment
                },
                'C8_physical_behaviors': {
                    'score': self.c8_physical_score,
                    'comment': self.c8_physical_comment
                }
            },
            'overall_comment': self.overall_comment,
            'confidence_level': self.confidence_level,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def from_dict(self, data):
        """Update user self-rating from dictionary data"""
        if 'ratings' in data:
            ratings = data['ratings']
            
            # C1 - Topic Choice
            if 'C1_topic_choice' in ratings:
                score = ratings['C1_topic_choice'].get('score')
                self.c1_topic_choice_score = score if score is not None else None
                self.c1_topic_choice_comment = ratings['C1_topic_choice'].get('comment', '')
            
            # C2 - Purpose
            if 'C2_purpose' in ratings:
                score = ratings['C2_purpose'].get('score')
                self.c2_purpose_score = score if score is not None else None
                self.c2_purpose_comment = ratings['C2_purpose'].get('comment', '')
            
            # C3 - Supporting Material
            if 'C3_supporting_material' in ratings:
                score = ratings['C3_supporting_material'].get('score')
                self.c3_supporting_score = score if score is not None else None
                self.c3_supporting_comment = ratings['C3_supporting_material'].get('comment', '')
            
            # C4 - Organization
            if 'C4_organization' in ratings:
                score = ratings['C4_organization'].get('score')
                self.c4_organization_score = score if score is not None else None
                self.c4_organization_comment = ratings['C4_organization'].get('comment', '')
            
            # C5 - Language Use
            if 'C5_language_use' in ratings:
                score = ratings['C5_language_use'].get('score')
                self.c5_language_score = score if score is not None else None
                self.c5_language_comment = ratings['C5_language_use'].get('comment', '')
            
            # C6 - Vocal Variety
            if 'C6_vocal_variety' in ratings:
                score = ratings['C6_vocal_variety'].get('score')
                self.c6_vocal_variety_score = score if score is not None else None
                self.c6_vocal_variety_comment = ratings['C6_vocal_variety'].get('comment', '')
            
            # C7 - Pronunciation
            if 'C7_pronunciation_and_grammar' in ratings:
                score = ratings['C7_pronunciation_and_grammar'].get('score')
                self.c7_pronunciation_score = score if score is not None else None
                self.c7_pronunciation_comment = ratings['C7_pronunciation_and_grammar'].get('comment', '')
            
            # C8 - Physical Behaviors
            if 'C8_physical_behaviors' in ratings:
                score = ratings['C8_physical_behaviors'].get('score')
                self.c8_physical_score = score if score is not None else None
                self.c8_physical_comment = ratings['C8_physical_behaviors'].get('comment', '')
        
        # Overall feedback
        if 'overall_comment' in data:
            self.overall_comment = data['overall_comment']
        if 'confidence_level' in data:
            self.confidence_level = data['confidence_level']


class PRPSAAssessment(db.Model):
    """
    Personal Report of Public Speaking Anxiety (PRPSA) Assessment model.
    Stores responses to the 34-question PRPSA survey and calculated anxiety score.
    
    Reference: McCroskey, J. C. (1970). Measures of communication-bound anxiety. 
    Speech Monographs, 37, 269-277.
    """
    __tablename__ = 'prpsa_assessments'
    
    id = db.Column(db.Integer, primary_key=True)
    speech_id = db.Column(db.Integer, db.ForeignKey('speeches.id'), nullable=False, unique=True, index=True)
    
    # Individual question responses (1-5 Likert scale)
    # Strongly Disagree = 1, Disagree = 2, Neutral = 3, Agree = 4, Strongly Agree = 5
    q1 = db.Column(db.Integer, nullable=False)   # While preparing for giving a speech, I feel tense and nervous
    q2 = db.Column(db.Integer, nullable=False)   # I feel tense when I see the words "speech" and "public speech" on a course outline
    q3 = db.Column(db.Integer, nullable=False)   # My thoughts become confused and jumbled when I am giving a speech
    q4 = db.Column(db.Integer, nullable=False)   # Right after giving a speech I feel that I have had a pleasant experience (REVERSE)
    q5 = db.Column(db.Integer, nullable=False)   # I get anxious when I think about a speech coming up
    q6 = db.Column(db.Integer, nullable=False)   # I have no fear of giving a speech (REVERSE)
    q7 = db.Column(db.Integer, nullable=False)   # Although I am nervous just before starting a speech, I soon settle down (REVERSE)
    q8 = db.Column(db.Integer, nullable=False)   # I look forward to giving a speech (REVERSE)
    q9 = db.Column(db.Integer, nullable=False)   # When the instructor announces a speaking assignment in class, I can feel myself getting tense
    q10 = db.Column(db.Integer, nullable=False)  # My hands tremble when I am giving a speech
    q11 = db.Column(db.Integer, nullable=False)  # I feel relaxed while giving a speech (REVERSE)
    q12 = db.Column(db.Integer, nullable=False)  # I enjoy preparing for a speech (REVERSE)
    q13 = db.Column(db.Integer, nullable=False)  # I am in constant fear of forgetting what I prepared to say
    q14 = db.Column(db.Integer, nullable=False)  # I get anxious if someone asks me something about my topic that I don't know
    q15 = db.Column(db.Integer, nullable=False)  # I face the prospect of giving a speech with confidence (REVERSE)
    q16 = db.Column(db.Integer, nullable=False)  # I feel that I am in complete possession of myself while giving a speech (REVERSE)
    q17 = db.Column(db.Integer, nullable=False)  # My mind is clear when giving a speech (REVERSE)
    q18 = db.Column(db.Integer, nullable=False)  # I do not dread giving a speech (REVERSE)
    q19 = db.Column(db.Integer, nullable=False)  # I perspire just before starting a speech
    q20 = db.Column(db.Integer, nullable=False)  # My heart beats very fast just as I start a speech
    q21 = db.Column(db.Integer, nullable=False)  # I experience considerable anxiety while sitting in the room just before my speech starts
    q22 = db.Column(db.Integer, nullable=False)  # Certain parts of my body feel very tense and rigid while giving a speech
    q23 = db.Column(db.Integer, nullable=False)  # Realizing that only a little time remains in a speech makes me very tense and anxious
    q24 = db.Column(db.Integer, nullable=False)  # While giving a speech, I know I can control my feelings of tension and stress (REVERSE)
    q25 = db.Column(db.Integer, nullable=False)  # I breathe faster just before starting a speech
    q26 = db.Column(db.Integer, nullable=False)  # I feel comfortable and relaxed in the hour or so just before giving a speech (REVERSE)
    q27 = db.Column(db.Integer, nullable=False)  # I do poorer on speeches because I am anxious
    q28 = db.Column(db.Integer, nullable=False)  # I feel anxious when the teacher announces the date of a speaking assignment
    q29 = db.Column(db.Integer, nullable=False)  # When I make a mistake while giving a speech, I find it hard to concentrate on the parts that follow
    q30 = db.Column(db.Integer, nullable=False)  # During an important speech I experience a feeling of helplessness building up inside me
    q31 = db.Column(db.Integer, nullable=False)  # I have trouble falling asleep the night before a speech
    q32 = db.Column(db.Integer, nullable=False)  # My heart beats very fast while I present a speech
    q33 = db.Column(db.Integer, nullable=False)  # I feel anxious while waiting to give my speech
    q34 = db.Column(db.Integer, nullable=False)  # While giving a speech, I get so nervous I forget facts I really know
    
    # Calculated fields
    total_score = db.Column(db.Integer, nullable=False)  # PRPSA score (34-170)
    anxiety_level = db.Column(db.String(20), nullable=False)  # 'Low', 'Moderate', 'High'
    
    # Metadata
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    speech = db.relationship('Speech', backref=db.backref('prpsa_assessment', uselist=False))
    
    def __repr__(self):
        return f'<PRPSAAssessment {self.id} for Speech {self.speech_id}>'
    
    @classmethod
    def calculate_score(cls, responses):
        """
        Calculate PRPSA score from responses.
        Formula: PRPSA = 72 - (sum of reverse items) + (sum of regular items)
        
        Args:
            responses: dict with keys q1-q34 and values 1-5
            
        Returns:
            tuple: (total_score, anxiety_level)
        """
        # Reverse scored items (these measure lack of anxiety, so higher scores = less anxiety)
        reverse_items = [4, 6, 7, 8, 11, 12, 15, 16, 17, 18, 24, 26]
        
        # Regular scored items (these measure anxiety, so higher scores = more anxiety)
        regular_items = [1, 2, 3, 5, 9, 10, 13, 14, 19, 20, 21, 22, 23, 25, 27, 28, 29, 30, 31, 32, 33, 34]
        
        # Calculate sums
        reverse_sum = sum(responses[f'q{i}'] for i in reverse_items)
        regular_sum = sum(responses[f'q{i}'] for i in regular_items)
        
        # Apply PRPSA formula
        total_score = 72 - reverse_sum + regular_sum
        
        # Determine anxiety level
        if total_score < 98:
            anxiety_level = 'Low'
        elif total_score <= 131:
            anxiety_level = 'Moderate'
        else:
            anxiety_level = 'High'
            
        return total_score, anxiety_level
    
    def to_dict(self, include_responses=True):
        """Convert PRPSA assessment to dictionary"""
        result = {
            'id': self.id,
            'speech_id': self.speech_id,
            'total_score': self.total_score,
            'anxiety_level': self.anxiety_level,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
        
        if include_responses:
            result['responses'] = {
                f'q{i}': getattr(self, f'q{i}') for i in range(1, 35)
            }
            
        return result
    
    @classmethod
    def from_responses(cls, speech_id, responses):
        """
        Create PRPSAAssessment from response dictionary
        
        Args:
            speech_id: ID of the associated speech
            responses: dict with keys q1-q34 and values 1-5
            
        Returns:
            PRPSAAssessment instance
        """
        # Validate responses
        for i in range(1, 35):
            key = f'q{i}'
            if key not in responses or not (1 <= responses[key] <= 5):
                raise ValueError(f"Invalid response for {key}: must be between 1 and 5")
        
        # Calculate score and anxiety level
        total_score, anxiety_level = cls.calculate_score(responses)
        
        # Create assessment
        assessment = cls(
            speech_id=speech_id,
            total_score=total_score,
            anxiety_level=anxiety_level,
            **{f'q{i}': responses[f'q{i}'] for i in range(1, 35)}
        )
        
        return assessment
