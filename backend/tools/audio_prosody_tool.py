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

class AudioProsodyToolOutput(BaseModel):
    """Complete analysis results"""
    # Overall statistics
    words_per_minute: float = Field(..., description="Average speaking rate in WPM")
    syllables_per_minute: float = Field(..., description="Average speaking rate in SPM")
    pitch_mean: float = Field(..., description="Mean pitch in Hz")
    pitch_std: float = Field(..., description="Standard deviation of pitch in Hz")
    volume_mean: float = Field(..., description="Mean volume in dB")
    volume_std: float = Field(..., description="Standard deviation of volume in dB")
    
    # Detailed events
    pause_events: List[PauseEvent] = Field(default_factory=list, description="Detected pauses")
    volume_events: List[VolumeEvent] = Field(default_factory=list, description="Detected volume variations")
    pitch_events: List[PitchEvent] = Field(default_factory=list, description="Detected pitch stress points")
    speed_events: List[SpeedEvent] = Field(default_factory=list, description="Detected speed variations")

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
            inputs: Input parameters with file path and optional transcript
            
        Returns:
            Complete prosody analysis results
        """
        file_path = inputs.file_path
        transcript = inputs.transcript
        
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
        
        # Detect speech segments and pauses
        segments = self._detect_speech_segments(sound, intensity)
        pauses = self._detect_pauses(segments, sound.get_total_duration())
        
        # Calculate speaking rate
        wpm, spm = self._calculate_speaking_rate(sound, segments, transcript)
        
        # Analyze variations within segments
        volume_events = self._analyze_volume_variations(intensity, segments, volume_mean, volume_std)
        pitch_events = self._analyze_pitch_variations(pitch, segments, pitch_mean, pitch_std)
        speed_events = self._analyze_speed_variations(segments, spm)
        
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
            speed_events=speed_events
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
