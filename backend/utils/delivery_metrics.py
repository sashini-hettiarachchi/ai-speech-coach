import parselmouth
from parselmouth.praat import call
import math

def _handle_nan_inf(value, default=0.0):
    """
    Handle NaN and infinity values by replacing them with sensible defaults.
    
    Args:
        value: The value to check and potentially replace
        default: Default value to use if value is NaN or infinite
        
    Returns:
        Valid numeric value
    """
    if value is None:
        return default
    
    try:
        # Convert to float if not already
        value = float(value)
        
        # Check for NaN or infinity
        if math.isnan(value) or math.isinf(value):
            return default
        
        return value
    except (ValueError, TypeError):
        return default

def analyze_delivery(filepath, transcript):
    snd = parselmouth.Sound(filepath)

    # Get pitch
    pitch = call(snd, "To Pitch", 0.0, 75, 600)  # time step=0 auto, minF0=75Hz, maxF0=600Hz
    mean_pitch = call(pitch, "Get mean", 0, 0, "Hertz")
    stdev_pitch = call(pitch, "Get standard deviation", 0, 0, "Hertz")

    # Get intensity
    intensity = call(snd, "To Intensity", 100.0, 0.0)
    mean_intensity = call(intensity, "Get mean", 0, 0, "energy")
    duration = snd.get_total_duration()
    word_count = len(transcript.split())
    wpm = word_count / (duration / 60) if duration > 0 else 0

    # Handle NaN/Inf values
    mean_pitch = _handle_nan_inf(mean_pitch, 150.0)
    stdev_pitch = _handle_nan_inf(stdev_pitch, 20.0)
    mean_intensity = _handle_nan_inf(mean_intensity, 60.0)
    duration = _handle_nan_inf(duration, 1.0)
    wpm = _handle_nan_inf(wpm, 120.0)

    return {
        "mean_pitch": round(mean_pitch, 2),
        "pitch_variation": round(stdev_pitch, 2),
        "mean_intensity": round(mean_intensity, 2),
        "duration": round(duration, 2),
        "word_count": word_count,
        "wpm": round(wpm, 2)
    }