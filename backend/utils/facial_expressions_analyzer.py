import cv2
import pandas as pd
from deepface import DeepFace

def analyze_facial_expressions(video_path: str, output_csv: str = "facial_expressions.csv", frame_skip: int = 1):
    """
    Analyzes facial expressions in a video using DeepFace.

    Args:
        video_path (str): Path to the video file.
        output_csv (str): CSV file to save results.
        frame_skip (int): Process every Nth frame to speed up analysis.

    Returns:
        pd.DataFrame: Frame-wise emotion predictions.
    """
    cap = cv2.VideoCapture(video_path)
    frame_num = 0
    results_list = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_num += 1

        # Skip frames if frame_skip > 1
        if frame_num % frame_skip != 0:
            continue

        try:
            # Analyze emotions using DeepFace
            analysis = DeepFace.analyze(frame, actions=["emotion"], enforce_detection=False)
            # DeepFace may return a list if multiple faces are detected
            if isinstance(analysis, list):
                analysis = analysis[0] if analysis else {"emotion": {e: 0 for e in ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]}}
            emotions = analysis.get("emotion", {})
            if isinstance(emotions, list):
                emotions = emotions[0] if emotions else {e: 0 for e in ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]}
            if not isinstance(emotions, dict):
                emotions = {e: 0 for e in ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]}
        except Exception as e:
            # If no face detected, record zeroes
            print(f"Frame {frame_num}: {e}")
            emotions = {e: 0 for e in ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]}

        # Record results
        emotions["frame"] = frame_num
        results_list.append(emotions)

    cap.release()

    # Convert to DataFrame
    df = pd.DataFrame(results_list)
    df.to_csv(output_csv, index=False)
    print(f"Facial expression analysis saved to {output_csv}")
    return df
