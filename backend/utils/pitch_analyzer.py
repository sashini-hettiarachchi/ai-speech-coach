import parselmouth

def analyze_pitch(file_path):
    snd = parselmouth.Sound(file_path)
    pitch = snd.to_pitch()
    start_time = pitch.get_start_time()

    return {
        "start_time": start_time,
    }

