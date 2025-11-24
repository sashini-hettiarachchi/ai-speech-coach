from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    """
    Minimal user model for Auth0 integration.
    Only stores essential data for relationships - all profile data comes from Auth0.
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    auth0_user_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    participant_id = db.Column(db.String(10), nullable=True, index=True)  # P1, P2, P3, etc.
    synced_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    speeches = db.relationship('Speech', backref='user', lazy=True, cascade='all, delete-orphan')
    prpsa_assessments = db.relationship('UserPRPSAAssessment', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.participant_id or self.auth0_user_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'auth0_user_id': self.auth0_user_id,
            'participant_id': self.participant_id,
            'synced_at': self.synced_at.isoformat() if self.synced_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Speech(db.Model):
    """
    Speech model for tracking individual speech topics and goals.
    Each speech can have multiple practice sessions.
    """
    __tablename__ = 'speeches'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Basic speech information
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    
    # Speech Context and Goals (optional - for context-aware speeches)
    goal = db.Column(db.Text, nullable=True)  # What the user wants to achieve
    audience_description = db.Column(db.Text, nullable=True)  # Who they'll be speaking to
    key_points = db.Column(db.Text, nullable=True)  # Main points to cover
    self_improvement_goal = db.Column(db.Text, nullable=True)  # What they want to improve
    context = db.Column(db.String(100), nullable=True)  # Academic, Storytelling, Persuasive, etc.
    
    # Speech type and completion status
    with_context = db.Column(db.Boolean, default=False, nullable=False)  # Whether this is a context-aware speech
    completed = db.Column(db.Boolean, default=False, nullable=False)  # Whether speech is marked complete
    prpsa_completed = db.Column(db.Boolean, default=False, nullable=False)  # Whether PRPSA assessment is completed
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sessions = db.relationship('Session', backref='speech', lazy=True, cascade='all, delete-orphan')
    prpsa_assessment = db.relationship('PRPSAAssessment', backref='speech', uselist=False, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Speech {self.id}: {self.title}>'
    
    def to_dict(self, include_sessions=False):
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'goal': self.goal,
            'audience_description': self.audience_description,
            'key_points': self.key_points,
            'self_improvement_goal': self.self_improvement_goal,
            'context': self.context,
            'with_context': self.with_context,
            'completed': self.completed,
            'prpsa_completed': self.prpsa_completed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        # Always include session count for UI display
        session_count = Session.query.filter_by(speech_id=self.id).count()
        result['session_count'] = session_count
        
        if include_sessions:
            # Include sessions if requested
            # Note: Need to import Session here to avoid circular imports
            sessions = Session.query.filter_by(speech_id=self.id).order_by(Session.session_number).all()
            result['sessions'] = [session.to_dict() for session in sessions]
            
        return result


class Session(db.Model):
    """
    Session model for individual practice sessions within a speech.
    Stores all analysis results, media files, and scoring data.
    """
    __tablename__ = 'sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    speech_id = db.Column(db.Integer, db.ForeignKey('speeches.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Session Information
    session_number = db.Column(db.Integer, nullable=False)  # Session number within the speech (1, 2, 3, etc.)
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
    
    # Feedback Summary
    feedback_summary = db.Column(db.JSON)  # Summary feedback for the session
    # Structure: {
    #   "summary": "Overall session summary",
    #   "good_points": ["Good thing 1", "Good thing 2"],
    #   "improvement_points": ["Improvement 1", "Improvement 2"]
    # }
    
    # Overall Performance Score
    overall_score = db.Column(db.Float)  # Overall performance score
    
    # CSSEF Competency Scores (C1-C7, excluding C8_physical_behaviors)
    c1_topic_choice_score = db.Column(db.Float)  # Topic choice & focus
    c1_topic_choice_comment = db.Column(db.Text)  # Comment justification
    c1_topic_choice_improvement = db.Column(db.Text)  # Improvement suggestion
    
    c2_purpose_score = db.Column(db.Float)  # Thesis & purpose
    c2_purpose_comment = db.Column(db.Text)
    c2_purpose_improvement = db.Column(db.Text)
    
    c3_supporting_score = db.Column(db.Float)  # Supporting materials
    c3_supporting_comment = db.Column(db.Text)
    c3_supporting_improvement = db.Column(db.Text)
    
    c4_organization_score = db.Column(db.Float)  # Organization & structure
    c4_organization_comment = db.Column(db.Text)
    c4_organization_improvement = db.Column(db.Text)
    
    c5_language_score = db.Column(db.Float)  # Language use
    c5_language_comment = db.Column(db.Text)
    c5_language_improvement = db.Column(db.Text)
    
    c6_vocal_variety_score = db.Column(db.Float)  # Vocal variety & delivery
    c6_vocal_variety_comment = db.Column(db.Text)
    c6_vocal_variety_improvement = db.Column(db.Text)
    
    c7_pronunciation_score = db.Column(db.Float)  # Pronunciation & articulation
    c7_pronunciation_comment = db.Column(db.Text)
    c7_pronunciation_improvement = db.Column(db.Text)
    
    # Revised Speech (Optional)
    revised_speech_text = db.Column(db.Text)  # Revised version of the speech
    revised_speech_audio_url = db.Column(db.String(2000))  # Audio URL for revised speech
    
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
            'session_number': self.session_number,
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
            
            # Feedback Summary
            'feedback_summary': self.feedback_summary,
            
            # Overall Score
            'overall_score': self.overall_score,
            
            # CSSEF Competency Scores (C1-C7)
            'cssef_scores': {
                'c1_topic_choice': {
                    'score': self.c1_topic_choice_score,
                    'comment': self.c1_topic_choice_comment,
                    'improvement': self.c1_topic_choice_improvement
                },
                'c2_purpose': {
                    'score': self.c2_purpose_score,
                    'comment': self.c2_purpose_comment,
                    'improvement': self.c2_purpose_improvement
                },
                'c3_supporting': {
                    'score': self.c3_supporting_score,
                    'comment': self.c3_supporting_comment,
                    'improvement': self.c3_supporting_improvement
                },
                'c4_organization': {
                    'score': self.c4_organization_score,
                    'comment': self.c4_organization_comment,
                    'improvement': self.c4_organization_improvement
                },
                'c5_language': {
                    'score': self.c5_language_score,
                    'comment': self.c5_language_comment,
                    'improvement': self.c5_language_improvement
                },
                'c6_vocal_variety': {
                    'score': self.c6_vocal_variety_score,
                    'comment': self.c6_vocal_variety_comment,
                    'improvement': self.c6_vocal_variety_improvement
                },
                'c7_pronunciation': {
                    'score': self.c7_pronunciation_score,
                    'comment': self.c7_pronunciation_comment,
                    'improvement': self.c7_pronunciation_improvement
                }
            },
            
            # Revised Speech
            'revised_speech_text': self.revised_speech_text,
            'revised_speech_audio_url': self.revised_speech_audio_url,
            
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
                'full_analysis_results': self.full_analysis_results
            })
            
        return result
    
    def get_scores_summary(self):
        """Get a summary of all CSSEF scores for progress tracking"""
        return {
            'overall_score': self.overall_score,
            'cssef_scores': {
                'c1_topic_choice_score': self.c1_topic_choice_score,
                'c2_purpose_score': self.c2_purpose_score,
                'c3_supporting_score': self.c3_supporting_score,
                'c4_organization_score': self.c4_organization_score,
                'c5_language_score': self.c5_language_score,
                'c6_vocal_variety_score': self.c6_vocal_variety_score,
                'c7_pronunciation_score': self.c7_pronunciation_score
            },
            'session_date': self.created_at.isoformat() if self.created_at else None
        }
        
    def get_cssef_competency_names(self):
        """Get the human-readable names for CSSEF competencies"""
        return {
            'c1_topic_choice': 'Topic Choice & Focus',
            'c2_purpose': 'Thesis & Purpose',
            'c3_supporting': 'Supporting Material',
            'c4_organization': 'Organization & Structure',
            'c5_language': 'Language Use',
            'c6_vocal_variety': 'Vocal Variety & Delivery',
            'c7_pronunciation': 'Pronunciation & Articulation'
        }


class UserPRPSAAssessment(db.Model):
    """
    User-level Personal Report of Public Speaking Anxiety (PRPSA) Assessment model.
    Stores initial and post-experimental PRPSA assessments that are tied to the user rather than specific speeches.
    
    Reference: McCroskey, J. C. (1970). Measures of communication-bound anxiety. 
    Speech Monographs, 37, 269-277.
    """
    __tablename__ = 'user_prpsa_assessments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    assessment_type = db.Column(db.String(20), nullable=False)  # 'initial' or 'post_experimental'
    
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
    
    # Unique constraint to ensure only one assessment per type per user
    __table_args__ = (
        db.UniqueConstraint('user_id', 'assessment_type', name='_user_assessment_type_uc'),
    )
    
    def __repr__(self):
        return f'<UserPRPSAAssessment {self.id} for User {self.user_id} ({self.assessment_type})>'
    
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
        """Convert user PRPSA assessment to dictionary"""
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'assessment_type': self.assessment_type,
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
    def from_responses(cls, user_id, assessment_type, responses):
        """
        Create UserPRPSAAssessment from response dictionary
        
        Args:
            user_id: ID of the user
            assessment_type: 'initial' or 'post_experimental'
            responses: dict with keys q1-q34 and values 1-5
            
        Returns:
            UserPRPSAAssessment instance
        """
        # Validate assessment type
        if assessment_type not in ['initial', 'post_experimental']:
            raise ValueError("assessment_type must be 'initial' or 'post_experimental'")
        
        # Validate responses
        for i in range(1, 35):
            key = f'q{i}'
            if key not in responses or not (1 <= responses[key] <= 5):
                raise ValueError(f"Invalid response for {key}: must be between 1 and 5")
        
        # Calculate score and anxiety level
        total_score, anxiety_level = cls.calculate_score(responses)
        
        # Create assessment
        assessment = cls(
            user_id=user_id,
            assessment_type=assessment_type,
            total_score=total_score,
            anxiety_level=anxiety_level,
            **{f'q{i}': responses[f'q{i}'] for i in range(1, 35)}
        )
        
        return assessment


class PRPSAAssessment(db.Model):
    """
    Personal Report of Public Speaking Anxiety (PRPSA) Assessment model.
    Stores responses to the 34-question PRPSA survey and calculated anxiety score.
    
    Reference: McCroskey, J. C. (1970). Measures of communication-bound anxiety. 
    Speech Monographs, 37, 269-277.
    """
    __tablename__ = 'prpsa_assessments'
    
    id = db.Column(db.Integer, primary_key=True)
    speech_id = db.Column(db.Integer, db.ForeignKey('speeches.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    
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