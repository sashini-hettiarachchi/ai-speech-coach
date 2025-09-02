import parselmouth
from parselmouth.praat import call

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
    wpm = word_count / (duration / 60)

    return {
        "mean_pitch": round(mean_pitch, 2),
        "pitch_variation": round(stdev_pitch, 2),
        "mean_intensity": round(mean_intensity, 2),
        "duration": round(duration, 2),
        "word_count": word_count,
        "wpm": round(wpm, 2)
    }