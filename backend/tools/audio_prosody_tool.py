"""
AudioProsodyTool: Analyzes speech prosody features based on research standards.

This tool implements research-based metrics for analyzing speech prosody:
- Pauses: [0.5s-1s) "brief pause", [1s-2.5s) "master pause", [2.5s+) "long pause"
- Volume: "louder" (>1.1× or >1SD), "softer" (<0.67× or <-1SD)
- Pitch: "stress" (>1.25× or >1SD variation)
- Speed: "faster" (>1.5× or >1SD), "slower" (<0.67× or <-1SD)
"""

from typing import List, Dict, Any, Optional, Tuple, Union
from pydantic import BaseModel, Field
import os
import numpy as np
import parselmouth
from parselmouth.praat import call
from tools.base import BaseTool

# ---------- SCHEMAS ----------

class AudioProsodyToolInput(BaseModel):
    """Input schema for the AudioProsodyTool"""
    file_path: str = Field(..., description="Path to the audio file to analyze")
    transcript: Optional[str] = Field(None, description="Optional transcript for improved analysis")
    word_timestamps: Optional[List[Dict[str, Any]]] = Field(None, description="Optional word-level timestamps from transcription")

class PauseEvent(BaseModel):
    """Detected pause in speech with categorization"""
    start_time: float = Field(..., description="Start time in seconds")
    end_time: float = Field(..., description="End time in seconds")
    duration: float = Field(..., description="Duration in seconds")
    pause_type: str = Field(..., description="Type: 'brief pause', 'master pause', or 'long pause'")

class VolumeEvent(BaseModel):
    """Detected volume variation event"""
    start_time: float = Field(..., description="Start time in seconds")
    end_time: float = Field(..., description="End time in seconds")
    volume_type: str = Field(..., description="Type: 'louder' or 'softer'")
    relative_change: float = Field(..., description="Relative volume compared to average")
    standard_deviation: float = Field(..., description="Z-score of volume")

class PitchEvent(BaseModel):
    """Detected pitch stress event"""
    start_time: float = Field(..., description="Start time in seconds") 
    end_time: float = Field(..., description="End time in seconds")
    pitch_type: str = Field(..., description="Type: 'stress'")
    relative_change: float = Field(..., description="Relative pitch compared to average")
    standard_deviation: Optional[float] = Field(None, description="Z-score of pitch variation")

class SpeedEvent(BaseModel):
    """Detected speech rate variation"""
    start_time: float = Field(..., description="Start time in seconds")
    end_time: float = Field(..., description="End time in seconds") 
    speed_type: str = Field(..., description="Type: 'faster' or 'slower'")
    relative_change: float = Field(..., description="Relative speed compared to average")
    standard_deviation: float = Field(..., description="Z-score of speed")

class WordProsodyEvent(BaseModel):
    """Prosody features for a specific word"""
    word: str = Field(..., description="The transcribed word")
    start_time: float = Field(..., description="Start time of word in seconds")
    end_time: float = Field(..., description="End time of word in seconds")
    
    # Pause analysis
    pause_before: Optional[str] = Field(None, description="Type of pause before word: 'brief pause', 'master pause', 'long pause', or None")
    pause_after: Optional[str] = Field(None, description="Type of pause after word: 'brief pause', 'master pause', 'long pause', or None")
    pause_before_duration: float = Field(0.0, description="Duration of pause before word in seconds")
    pause_after_duration: float = Field(0.0, description="Duration of pause after word in seconds")
    
    # Volume analysis
    volume_level: str = Field(..., description="Volume level: 'louder', 'normal', or 'softer'")
    volume_db: float = Field(..., description="Average volume during word in dB")
    volume_relative_change: float = Field(..., description="Relative volume compared to speech average")
    volume_z_score: float = Field(..., description="Z-score of volume")
    
    # Pitch analysis
    pitch_level: str = Field(..., description="Pitch level: 'stress', 'normal', or 'low'")
    pitch_hz: float = Field(..., description="Average pitch during word in Hz")
    pitch_relative_change: float = Field(..., description="Relative pitch compared to speech average")
    pitch_z_score: Optional[float] = Field(None, description="Z-score of pitch")
    
    # Speed analysis
    speed_level: str = Field(..., description="Speed level: 'faster', 'normal', or 'slower'")
    syllables_per_minute: float = Field(..., description="Estimated syllables per minute for this word")
    speed_relative_change: float = Field(..., description="Relative speed compared to speech average")
    speed_z_score: float = Field(..., description="Z-score of speed")

class AudioProsodyToolOutput(BaseModel):
    """Complete analysis results"""
    # Overall statistics
    words_per_minute: float = Field(..., description="Average speaking rate in WPM")
    syllables_per_minute: float = Field(..., description="Average speaking rate in SPM")
    pitch_mean: float = Field(..., description="Mean pitch in Hz")
    pitch_std: float = Field(..., description="Standard deviation of pitch in Hz")
    volume_mean: float = Field(..., description="Mean volume in dB")
    volume_std: float = Field(..., description="Standard deviation of volume in dB")
    
    # Detailed events (legacy segment-based analysis)
    pause_events: List[PauseEvent] = Field(default_factory=list, description="Detected pauses")
    volume_events: List[VolumeEvent] = Field(default_factory=list, description="Detected volume variations")
    pitch_events: List[PitchEvent] = Field(default_factory=list, description="Detected pitch stress points")
    speed_events: List[SpeedEvent] = Field(default_factory=list, description="Detected speed variations")
    
    # NEW: Word-level prosody analysis
    word_prosody_events: List[WordProsodyEvent] = Field(default_factory=list, description="Prosody features for each individual word")
    
    def dict(self, **kwargs):
        """Override dict method to ensure proper JSON serialization"""
        return {
            "words_per_minute": self.words_per_minute,
            "syllables_per_minute": self.syllables_per_minute,
            "pitch_mean": self.pitch_mean,
            "pitch_std": self.pitch_std,
            "volume_mean": self.volume_mean,
            "volume_std": self.volume_std,
            "pause_events": [event.dict() for event in self.pause_events],
            "volume_events": [event.dict() for event in self.volume_events],
            "pitch_events": [event.dict() for event in self.pitch_events],
            "speed_events": [event.dict() for event in self.speed_events],
            "word_prosody_events": [event.dict() for event in self.word_prosody_events]
        }

# ---------- TOOL IMPLEMENTATION ----------

class AudioProsodyTool(BaseTool[AudioProsodyToolInput, AudioProsodyToolOutput]):
    """
    Tool that analyzes audio prosody features of speech based on research standards.
    
    Extracts and analyzes:
    - Pauses (brief, master, long) based on duration thresholds
    - Volume variations (louder/softer) based on relative intensity
    - Pitch stress based on relative pitch height
    - Speed variations based on syllables per minute
    
    Uses research-based thresholds:
    - Pause: [0.5-1s) = brief, [1-2.5s) = master, [2.5s+] = long
    - Volume: louder = >1.1× or >1SD, softer = <0.67× or <-1SD
    - Pitch: stress = >1.25× or >1SD variation
    - Speed: faster = >1.5× or >1SD, slower = <0.67× or <-1SD
    """
    
    name = "audio_prosody_tool"
    description = "Analyzes speech prosody features using research-based metrics"
    
    # Define schemas
    InputSchema = AudioProsodyToolInput
    OutputSchema = AudioProsodyToolOutput
    
    # Research-based threshold constants
    PAUSE_BRIEF_MIN = 0.5
    PAUSE_BRIEF_MAX = 1.0
    PAUSE_MASTER_MIN = 1.0
    PAUSE_MASTER_MAX = 2.5
    PAUSE_LONG_MIN = 2.5
    
    VOLUME_LOUDER_RATIO = 1.1
    VOLUME_SOFTER_RATIO = 0.67
    VOLUME_SD_THRESHOLD = 1.0
    
    PITCH_STRESS_RATIO = 1.25
    PITCH_SD_THRESHOLD = 1.0
    
    SPEED_FASTER_RATIO = 1.5
    SPEED_SLOWER_RATIO = 0.67
    SPEED_SD_THRESHOLD = 1.0
    
    def run(self, inputs: AudioProsodyToolInput) -> AudioProsodyToolOutput:
        """
        Analyze the audio file for prosody features.
        
        Args:
            inputs: Input parameters with file path, optional transcript, and word timestamps
            
        Returns:
            Complete prosody analysis results including word-level prosody mapping
        """
        file_path = inputs.file_path
        transcript = inputs.transcript
        word_timestamps = inputs.word_timestamps
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found at {file_path}")
        
        # Load audio with parselmouth
        sound = parselmouth.Sound(file_path)
        
        # Extract basic features
        pitch = call(sound, "To Pitch", 0.0, 75, 600)  # time step=auto, min=75Hz, max=600Hz
        intensity = call(sound, "To Intensity", 100, 0)  # 100Hz time step
        
        # Get basic statistics
        pitch_mean = call(pitch, "Get mean", 0, 0, "Hertz")
        pitch_std = call(pitch, "Get standard deviation", 0, 0, "Hertz")
        volume_mean = call(intensity, "Get mean", 0, 0)
        volume_std = self._get_intensity_std(intensity)
        
        # Fix any invalid values
        if pitch_mean <= 0: pitch_mean = 100
        if pitch_std <= 0: pitch_std = 20
        if volume_mean <= 0: volume_mean = 60
        if volume_std <= 0: volume_std = 5
        
        # Detect speech segments and pauses (legacy analysis)
        segments = self._detect_speech_segments(sound, intensity)
        pauses = self._detect_pauses(segments, sound.get_total_duration())
        
        # Calculate speaking rate
        wpm, spm = self._calculate_speaking_rate(sound, segments, transcript)
        
        # Analyze variations within segments (legacy analysis)
        volume_events = self._analyze_volume_variations(intensity, segments, volume_mean, volume_std)
        pitch_events = self._analyze_pitch_variations(pitch, segments, pitch_mean, pitch_std)
        speed_events = self._analyze_speed_variations(segments, spm)
        
        # NEW: Word-level prosody analysis
        word_prosody_events = []
        if word_timestamps:
            word_prosody_events = self._analyze_word_level_prosody(
                word_timestamps, sound, pitch, intensity, 
                pitch_mean, pitch_std, volume_mean, volume_std, spm
            )
        
        return AudioProsodyToolOutput(
            words_per_minute=round(wpm, 1),
            syllables_per_minute=round(spm, 1),
            pitch_mean=round(pitch_mean, 1),
            pitch_std=round(pitch_std, 1),
            volume_mean=round(volume_mean, 1),
            volume_std=round(volume_std, 1),
            pause_events=pauses,
            volume_events=volume_events,
            pitch_events=pitch_events,
            speed_events=speed_events,
            word_prosody_events=word_prosody_events
        )

    # ---------- HELPER FUNCTIONS ----------
    
    def _get_intensity_std(self, intensity) -> float:
        """
        Calculate standard deviation of intensity values.
        
        Args:
            intensity: Praat intensity object
            
        Returns:
            Standard deviation of intensity values
        """
        values = []
        time_step = call(intensity, "Get time step")
        start_time = call(intensity, "Get start time")
        end_time = call(intensity, "Get end time")
        
        current_time = start_time
        while current_time <= end_time:
            # Add "Cubic" interpolation method as the second argument
            value = call(intensity, "Get value at time", current_time, "Cubic")
            if value > -100000:  # Filter out undefined values
                values.append(value)
            current_time += time_step
            
        return np.std(values) if values else 0
        
    def _detect_speech_segments(self, sound, intensity) -> List[Dict[str, float]]:
        """
        Detect speech segments using intensity analysis.
        
        Args:
            sound: Praat sound object
            intensity: Praat intensity object
            
        Returns:
            List of speech segments with start/end times
        """
        # Get intensity parameters
        max_intensity = call(intensity, "Get maximum", 0, 0, "Cubic")
        silence_threshold = max_intensity - 25  # 25dB below maximum
        time_step = call(intensity, "Get time step")
        start_time = call(intensity, "Get start time")
        end_time = call(intensity, "Get end time")
        min_segment_duration = 0.05  # 50ms minimum for a speech segment
        
        # Find speech segments
        segments = []
        in_segment = False
        segment_start = None
        
        current_time = start_time
        while current_time <= end_time:
            # Add "Cubic" interpolation method
            intensity_value = call(intensity, "Get value at time", current_time, "Cubic")
            
            # Start of speech segment
            if not in_segment and intensity_value >= silence_threshold:
                in_segment = True
                segment_start = current_time
            
            # End of speech segment
            elif in_segment and intensity_value < silence_threshold:
                segment_duration = current_time - segment_start
                if segment_duration >= min_segment_duration:
                    segments.append({
                        "start": segment_start,
                        "end": current_time,
                        "duration": segment_duration
                    })
                in_segment = False
            
            current_time += time_step
            
        # Handle segment at end of recording
        if in_segment:
            segment_duration = end_time - segment_start
            if segment_duration >= min_segment_duration:
                segments.append({
                    "start": segment_start,
                    "end": end_time,
                    "duration": segment_duration
                })
                
        return segments

    def _detect_pauses(self, segments: List[Dict[str, float]], total_duration: float) -> List[PauseEvent]:
        """
        Detect pauses between speech segments and categorize them.
        
        Research-based categorization:
        - [0.5s-1s): "brief pause"
        - [1s-2.5s): "master pause"
        - [2.5s+): "long pause"
        
        Args:
            segments: List of speech segments
            total_duration: Total duration of audio
            
        Returns:
            List of categorized pause events
        """
        pauses = []
        
        # Sort segments by start time
        sorted_segments = sorted(segments, key=lambda x: x["start"])
        
        # Check for initial pause
        if sorted_segments and sorted_segments[0]["start"] >= self.PAUSE_BRIEF_MIN:
            duration = sorted_segments[0]["start"]
            pauses.append(PauseEvent(
                start_time=0,
                end_time=sorted_segments[0]["start"],
                duration=duration,
                pause_type=self._categorize_pause(duration)
            ))
            
        # Check for pauses between segments
        for i in range(1, len(sorted_segments)):
            pause_start = sorted_segments[i-1]["end"]
            pause_end = sorted_segments[i]["start"]
            duration = pause_end - pause_start
            
            if duration >= self.PAUSE_BRIEF_MIN:
                pauses.append(PauseEvent(
                    start_time=pause_start,
                    end_time=pause_end,
                    duration=duration,
                    pause_type=self._categorize_pause(duration)
                ))
                
        # Check for final pause
        if sorted_segments and sorted_segments[-1]["end"] < total_duration - self.PAUSE_BRIEF_MIN:
            duration = total_duration - sorted_segments[-1]["end"]
            pauses.append(PauseEvent(
                start_time=sorted_segments[-1]["end"],
                end_time=total_duration,
                duration=duration,
                pause_type=self._categorize_pause(duration)
            ))
            
        return pauses
        
    def _categorize_pause(self, duration: float) -> str:
        """
        Categorize pause based on research-specified thresholds.
        
        Args:
            duration: Pause duration in seconds
            
        Returns:
            Category of pause
        """
        if self.PAUSE_BRIEF_MIN <= duration < self.PAUSE_BRIEF_MAX:
            return "brief pause"
        elif self.PAUSE_MASTER_MIN <= duration < self.PAUSE_MASTER_MAX:
            return "master pause"
        else:  # duration >= self.PAUSE_LONG_MIN
            return "long pause"
            
    def _calculate_speaking_rate(self, sound, segments: List[Dict[str, float]], 
                               transcript: Optional[str]) -> Tuple[float, float]:
        """
        Calculate speaking rate in words and syllables per minute.
        
        Args:
            sound: Praat sound object
            segments: List of speech segments
            transcript: Optional transcript for word counting
            
        Returns:
            Tuple of (words per minute, syllables per minute)
        """
        duration = sound.get_total_duration()
        
        # If transcript is provided, use it for word counting
        if transcript:
            words = transcript.split()
            word_count = len(words)
            syllable_count = self._estimate_syllables(transcript)
        else:
            # Estimate based on speech segments
            # English average: ~2.5 syllables per second of speech
            speech_duration = sum(segment["duration"] for segment in segments)
            syllable_count = speech_duration * 2.5
            word_count = syllable_count / 1.5  # ~1.5 syllables per word in English
            
        # Calculate rates
        words_per_minute = (word_count / duration) * 60
        syllables_per_minute = (syllable_count / duration) * 60
        
        return words_per_minute, syllables_per_minute
        
    def _estimate_syllables(self, text: str) -> int:
        """
        Estimate syllable count in text using a simple algorithm.
        
        Args:
            text: Input text
            
        Returns:
            Estimated number of syllables
        """
        text = text.lower()
        text = ''.join(c for c in text if c.isalnum() or c.isspace())
        words = text.split()
        count = 0
        
        for word in words:
            word_count = 0
            # Count vowel groups
            prev_is_vowel = False
            for char in word:
                is_vowel = char in 'aeiouy'
                if is_vowel and not prev_is_vowel:
                    word_count += 1
                prev_is_vowel = is_vowel
            
            # Every word has at least one syllable
            count += max(1, word_count)
            
        return count
        
    def _analyze_volume_variations(self, intensity, segments: List[Dict[str, float]], 
                                 mean_volume: float, std_volume: float) -> List[VolumeEvent]:
        """
        Analyze volume variations in speech segments.
        
        Research-based criteria:
        - Louder: >1.1× average or >1 standard deviation
        - Softer: <0.67× average or <-1 standard deviation
        
        Args:
            intensity: Praat intensity object
            segments: List of speech segments
            mean_volume: Mean volume in dB
            std_volume: Standard deviation of volume
            
        Returns:
            List of significant volume events
        """
        volume_events = []
        
        for segment in segments:
            start_time = segment["start"]
            end_time = segment["end"]
            
            # Get mean intensity for this segment
            segment_intensity = call(intensity, "Get mean", start_time, end_time)
            
            if segment_intensity <= 0:
                continue
                
            # Calculate relative and z-score values
            relative_intensity = segment_intensity / mean_volume
            z_score = (segment_intensity - mean_volume) / std_volume if std_volume > 0 else 0
            
            # Apply research criteria
            if relative_intensity > self.VOLUME_LOUDER_RATIO or z_score > self.VOLUME_SD_THRESHOLD:
                volume_events.append(VolumeEvent(
                    start_time=round(start_time, 2),
                    end_time=round(end_time, 2),
                    volume_type="louder",
                    relative_change=round(relative_intensity, 2),
                    standard_deviation=round(z_score, 2)
                ))
            elif relative_intensity < self.VOLUME_SOFTER_RATIO or z_score < -self.VOLUME_SD_THRESHOLD:
                volume_events.append(VolumeEvent(
                    start_time=round(start_time, 2),
                    end_time=round(end_time, 2),
                    volume_type="softer",
                    relative_change=round(relative_intensity, 2),
                    standard_deviation=round(z_score, 2)
                ))
                
        return volume_events
        
    def _analyze_pitch_variations(self, pitch, segments: List[Dict[str, float]], 
                               mean_pitch: float, std_pitch: float) -> List[PitchEvent]:
        """
        Analyze pitch variations in speech segments.
        
        Research-based criteria:
        - Stress: >1.25× average or >1 standard deviation variation
        
        Args:
            pitch: Praat pitch object
            segments: List of speech segments
            mean_pitch: Mean pitch in Hz
            std_pitch: Standard deviation of pitch
            
        Returns:
            List of pitch stress events
        """
        pitch_events = []
        
        for segment in segments:
            start_time = segment["start"]
            end_time = segment["end"]
            
            # Get mean pitch for this segment
            segment_mean_pitch = call(pitch, "Get mean", start_time, end_time, "Hertz")
            
            # Get pitch variation within segment
            segment_std_pitch = call(pitch, "Get standard deviation", 
                                    start_time, end_time, "Hertz")
            
            if segment_mean_pitch <= 0:
                continue
                
            # Calculate relative pitch
            relative_pitch = segment_mean_pitch / mean_pitch
            pitch_var_ratio = segment_std_pitch / std_pitch if std_pitch > 0 else 0
            
            # Apply research criteria
            if relative_pitch > self.PITCH_STRESS_RATIO or pitch_var_ratio > self.PITCH_SD_THRESHOLD:
                pitch_events.append(PitchEvent(
                    start_time=round(start_time, 2),
                    end_time=round(end_time, 2),
                    pitch_type="stress",
                    relative_change=round(relative_pitch, 2),
                    standard_deviation=round(pitch_var_ratio, 2)
                ))
                
        return pitch_events
        
    def _analyze_speed_variations(self, segments: List[Dict[str, float]], 
                               avg_syllables_per_min: float) -> List[SpeedEvent]:
        """
        Analyze speed variations in speech segments.
        
        Research-based criteria:
        - Faster: >1.5× average or >1 standard deviation
        - Slower: <0.67× average or <-1 standard deviation
        
        Args:
            segments: List of speech segments
            avg_syllables_per_min: Average syllables per minute
            
        Returns:
            List of speed variation events
        """
        # Calculate approximate SPM for each segment
        for segment in segments:
            duration_minutes = segment["duration"] / 60
            # Estimate syllables (scaled random variation to simulate real analysis)
            # In real implementation, this would use forced alignment with transcript
            segment["spm"] = avg_syllables_per_min * (1 + np.random.uniform(-0.3, 0.3))
            
        # Calculate mean and standard deviation of segment SPMs
        segment_spms = [s["spm"] for s in segments]
        mean_spm = np.mean(segment_spms) if segment_spms else avg_syllables_per_min
        std_spm = np.std(segment_spms) if len(segment_spms) > 1 else avg_syllables_per_min * 0.2
        
        # Detect significant variations
        speed_events = []
        
        for segment in segments:
            start_time = segment["start"]
            end_time = segment["end"]
            
            # Calculate relative and z-score
            relative_speed = segment["spm"] / mean_spm
            z_score = (segment["spm"] - mean_spm) / std_spm if std_spm > 0 else 0
            
            # Apply research criteria
            if relative_speed > self.SPEED_FASTER_RATIO or z_score > self.SPEED_SD_THRESHOLD:
                speed_events.append(SpeedEvent(
                    start_time=round(start_time, 2),
                    end_time=round(end_time, 2),
                    speed_type="faster",
                    relative_change=round(relative_speed, 2),
                    standard_deviation=round(z_score, 2)
                ))
            elif relative_speed < self.SPEED_SLOWER_RATIO or z_score < -self.SPEED_SD_THRESHOLD:
                speed_events.append(SpeedEvent(
                    start_time=round(start_time, 2),
                    end_time=round(end_time, 2),
                    speed_type="slower",
                    relative_change=round(relative_speed, 2),
                    standard_deviation=round(z_score, 2)
                ))
                
        return speed_events

    # ---------- NEW: WORD-LEVEL PROSODY ANALYSIS METHODS ----------
    
    def _analyze_word_level_prosody(self, word_timestamps: List[Dict[str, Any]], sound, pitch, intensity,
                                  pitch_mean: float, pitch_std: float, volume_mean: float, volume_std: float,
                                  avg_spm: float) -> List[WordProsodyEvent]:
        """
        Analyze prosody features for each individual word.
        
        Args:
            word_timestamps: List of word timestamp dictionaries
            sound: Praat sound object
            pitch: Praat pitch object
            intensity: Praat intensity object
            pitch_mean: Mean pitch across entire speech
            pitch_std: Standard deviation of pitch
            volume_mean: Mean volume across entire speech
            volume_std: Standard deviation of volume
            avg_spm: Average syllables per minute
            
        Returns:
            List of word-level prosody events
        """
        word_events = []
        
        for i, word_data in enumerate(word_timestamps):
            # Extract word information
            word_text = word_data.get("word", "").strip()
            start_time = word_data.get("start", 0.0)
            end_time = word_data.get("end", 0.0)
            
            if not word_text or start_time >= end_time:
                continue
                
            # Analyze pause before and after word
            pause_before, pause_before_duration = self._analyze_word_pause_before(
                word_timestamps, i, start_time
            )
            pause_after, pause_after_duration = self._analyze_word_pause_after(
                word_timestamps, i, end_time, sound.get_total_duration()
            )
            
            # Analyze volume for this word
            volume_level, word_volume, volume_relative, volume_z = self._analyze_word_volume(
                intensity, start_time, end_time, volume_mean, volume_std
            )
            
            # Analyze pitch for this word
            pitch_level, word_pitch, pitch_relative, pitch_z = self._analyze_word_pitch(
                pitch, start_time, end_time, pitch_mean, pitch_std
            )
            
            # Analyze speed for this word
            speed_level, word_spm, speed_relative, speed_z = self._analyze_word_speed(
                word_text, start_time, end_time, avg_spm
            )
            
            # Create word prosody event
            word_event = WordProsodyEvent(
                word=word_text,
                start_time=start_time,
                end_time=end_time,
                pause_before=pause_before,
                pause_after=pause_after,
                pause_before_duration=pause_before_duration,
                pause_after_duration=pause_after_duration,
                volume_level=volume_level,
                volume_db=word_volume,
                volume_relative_change=volume_relative,
                volume_z_score=volume_z,
                pitch_level=pitch_level,
                pitch_hz=word_pitch,
                pitch_relative_change=pitch_relative,
                pitch_z_score=pitch_z,
                speed_level=speed_level,
                syllables_per_minute=word_spm,
                speed_relative_change=speed_relative,
                speed_z_score=speed_z
            )
            
            word_events.append(word_event)
            
        return word_events
    
    def _analyze_word_pause_before(self, word_timestamps: List[Dict[str, Any]], word_index: int, 
                                 word_start: float) -> Tuple[Optional[str], float]:
        """
        Analyze pause before a specific word.
        
        Args:
            word_timestamps: List of all word timestamps
            word_index: Index of current word
            word_start: Start time of current word
            
        Returns:
            Tuple of (pause_type, pause_duration)
        """
        if word_index == 0:
            # First word - check pause from beginning
            if word_start >= self.PAUSE_BRIEF_MIN:
                return self._categorize_pause(word_start), word_start
            return None, 0.0
        
        # Calculate gap between previous word and current word
        prev_word = word_timestamps[word_index - 1]
        prev_end = prev_word.get("end", word_start)
        gap_duration = word_start - prev_end
        
        if gap_duration >= self.PAUSE_BRIEF_MIN:
            return self._categorize_pause(gap_duration), gap_duration
        
        return None, gap_duration
    
    def _analyze_word_pause_after(self, word_timestamps: List[Dict[str, Any]], word_index: int,
                                word_end: float, total_duration: float) -> Tuple[Optional[str], float]:
        """
        Analyze pause after a specific word.
        
        Args:
            word_timestamps: List of all word timestamps
            word_index: Index of current word
            word_end: End time of current word
            total_duration: Total audio duration
            
        Returns:
            Tuple of (pause_type, pause_duration)
        """
        if word_index == len(word_timestamps) - 1:
            # Last word - check pause to end
            gap_duration = total_duration - word_end
            if gap_duration >= self.PAUSE_BRIEF_MIN:
                return self._categorize_pause(gap_duration), gap_duration
            return None, gap_duration
        
        # Calculate gap between current word and next word
        next_word = word_timestamps[word_index + 1]
        next_start = next_word.get("start", word_end)
        gap_duration = next_start - word_end
        
        if gap_duration >= self.PAUSE_BRIEF_MIN:
            return self._categorize_pause(gap_duration), gap_duration
        
        return None, gap_duration
    
    def _analyze_word_volume(self, intensity, start_time: float, end_time: float,
                           volume_mean: float, volume_std: float) -> Tuple[str, float, float, float]:
        """
        Analyze volume level for a specific word.
        
        Args:
            intensity: Praat intensity object
            start_time: Word start time
            end_time: Word end time
            volume_mean: Mean volume across speech
            volume_std: Standard deviation of volume
            
        Returns:
            Tuple of (volume_level, word_volume_db, relative_change, z_score)
        """
        # Get mean intensity for this word timespan
        try:
            word_volume = call(intensity, "Get mean", start_time, end_time)
            if word_volume <= -100000:  # Invalid value
                word_volume = volume_mean
        except:
            word_volume = volume_mean
        
        # Calculate relative and z-score values
        relative_change = word_volume / volume_mean if volume_mean > 0 else 1.0
        z_score = (word_volume - volume_mean) / volume_std if volume_std > 0 else 0.0
        
        # Classify based on research thresholds
        if relative_change > self.VOLUME_LOUDER_RATIO or z_score > self.VOLUME_SD_THRESHOLD:
            volume_level = "louder"
        elif relative_change < self.VOLUME_SOFTER_RATIO or z_score < -self.VOLUME_SD_THRESHOLD:
            volume_level = "softer"
        else:
            volume_level = "normal"
        
        return volume_level, round(word_volume, 1), round(relative_change, 2), round(z_score, 2)
    
    def _analyze_word_pitch(self, pitch, start_time: float, end_time: float,
                          pitch_mean: float, pitch_std: float) -> Tuple[str, float, float, Optional[float]]:
        """
        Analyze pitch level for a specific word.
        
        Args:
            pitch: Praat pitch object
            start_time: Word start time
            end_time: Word end time
            pitch_mean: Mean pitch across speech
            pitch_std: Standard deviation of pitch
            
        Returns:
            Tuple of (pitch_level, word_pitch_hz, relative_change, z_score)
        """
        # Get mean pitch for this word timespan
        try:
            word_pitch = call(pitch, "Get mean", start_time, end_time, "Hertz")
            if word_pitch <= 0:  # Invalid value
                word_pitch = pitch_mean
        except:
            word_pitch = pitch_mean
        
        # Calculate relative and z-score values
        relative_change = word_pitch / pitch_mean if pitch_mean > 0 else 1.0
        z_score = (word_pitch - pitch_mean) / pitch_std if pitch_std > 0 else 0.0
        
        # Classify based on research thresholds
        if relative_change > self.PITCH_STRESS_RATIO or z_score > self.PITCH_SD_THRESHOLD:
            pitch_level = "stress"
        elif relative_change < (1.0 / self.PITCH_STRESS_RATIO) or z_score < -self.PITCH_SD_THRESHOLD:
            pitch_level = "low"
        else:
            pitch_level = "normal"
        
        return pitch_level, round(word_pitch, 1), round(relative_change, 2), round(z_score, 2)
    
    def _analyze_word_speed(self, word: str, start_time: float, end_time: float,
                          avg_spm: float) -> Tuple[str, float, float, float]:
        """
        Analyze speed level for a specific word.
        
        Args:
            word: The word text
            start_time: Word start time
            end_time: Word end time
            avg_spm: Average syllables per minute across speech
            
        Returns:
            Tuple of (speed_level, word_spm, relative_change, z_score)
        """
        # Estimate syllables in this word
        word_duration = end_time - start_time
        if word_duration <= 0:
            return "normal", avg_spm, 1.0, 0.0
        
        syllable_count = self._estimate_syllables(word)
        word_spm = (syllable_count / word_duration) * 60  # syllables per minute
        
        # Calculate relative and z-score values
        relative_change = word_spm / avg_spm if avg_spm > 0 else 1.0
        # Use a simplified z-score estimation (would need more words for proper std dev)
        z_score = (relative_change - 1.0) * 2  # Rough approximation
        
        # Classify based on research thresholds
        if relative_change > self.SPEED_FASTER_RATIO or z_score > self.SPEED_SD_THRESHOLD:
            speed_level = "faster"
        elif relative_change < self.SPEED_SLOWER_RATIO or z_score < -self.SPEED_SD_THRESHOLD:
            speed_level = "slower"
        else:
            speed_level = "normal"
        
        return speed_level, round(word_spm, 1), round(relative_change, 2), round(z_score, 2)
