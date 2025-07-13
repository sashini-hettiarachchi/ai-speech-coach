# import librosa
# import numpy as np

# def analyze_pitch(filepath):
#     y, sr = librosa.load(filepath)
#     pitches, magnitudes = librosa.piptrack(y=y, sr=sr)

#     pitch_values = []
#     for t in range(pitches.shape[1]):
#         index = magnitudes[:, t].argmax()
#         pitch = pitches[index, t]
#         if pitch > 0:
#             pitch_values.append(pitch)

#     if not pitch_values:
#         return {"average_pitch": 0, "pitch_range": 0, "pitch_variability": 0}

#     return {
#         "average_pitch": round(np.mean(pitch_values), 2),
#         "pitch_range": round(max(pitch_values) - min(pitch_values), 2),
#         "pitch_variability": round(np.std(pitch_values), 2)
#     }

import parselmouth

def analyze_pitch(file_path):
    snd = parselmouth.Sound(file_path)
    pitch = snd.to_pitch()
    start_time = pitch.get_start_time()

    return {
        "start_time": start_time,
    }

