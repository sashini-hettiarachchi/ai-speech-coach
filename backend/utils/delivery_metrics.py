import soundfile as sf

def analyze_delivery(filepath, transcript):
    y, sr = sf.read(filepath)
    duration_sec = sf.get_duration(y=y, sr=sr)
    word_count = len(transcript.split())
    wpm = (word_count / duration_sec) * 60

    return {
        "duration_sec": round(duration_sec, 2),
        "word_count": word_count,
        "wpm": round(wpm, 2),
    }
