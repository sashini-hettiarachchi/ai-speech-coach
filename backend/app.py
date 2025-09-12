from flask import Flask, jsonify
from utils.facial_expressions_analyzer import analyze_facial_expressions
from utils.delivery_metrics import analyze_delivery
from utils.filler_detector import count_filler_words
from utils.transcriber import transcrib_audio_with_whisper
from utils.recommendations import give_recommendations
import os
from flask_cors import CORS



app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

CORS(app)

@app.route('/')
def home():
    return 

@app.route('/api/v1/analyze', methods=['POST'])
def analyze_speech_v2():
    print("Starting speech analysis...")
    filepath = 'test_data/test2.wav'
    transcript = transcrib_audio_with_whisper(filepath)
    print("Transcript:", transcript)
    fillers = count_filler_words(transcript)
    print("Fillers:", fillers)
    recommendations = give_recommendations(transcript)
    print("recommendations:", recommendations)
    delivery_metrics = analyze_delivery(filepath, transcript)
    print("Delivery Metrics:", delivery_metrics)
    # df = analyze_facial_expressions("test_data/test_video1.mp4", "test_data/video_emotions.csv")
    # print(df.head())
    return jsonify({
        "transcript": transcript,
        "fillers": fillers,
        "recommendations": recommendations,
        "delivery_metrics": delivery_metrics
    })


if __name__ == '__main__':
    app.run(debug=True)
