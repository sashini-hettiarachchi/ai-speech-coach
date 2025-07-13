from flask import Flask, jsonify
from utils.transcriber import transcribe_audio_with_speech_to_text
from utils.filler_detector import count_fillers_with_gemini
from utils.recommendations import give_recommendations_with_gemini
import os
from flask_cors import CORS



app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

CORS(app)

@app.route('/')
def home():
    return 

# @app.route('/v1/analyze', methods=['POST'])
# def analyze_speech():
#     # file = request.files['audio']
#     # filepath = os.path.join(UPLOAD_FOLDER, file.filename)
#     filepath = 'test_data/test2.wav'

   
#     print(filepath)
#     # file.save(filepath)

#     transcript = transcribe_audio(filepath)
#     print("Transcript:", transcript)
#     fillers = count_fillers(transcript)
#     print("Fillers:", fillers)
#     # corrected = correct_grammar(transcript)
#     # delivery = analyze_delivery(filepath, transcript)
#     # print("Delivery Metrics:", delivery)
#     pitch = analyze_pitch(filepath)
  
  
   
#     print("Pitch Analysis:", pitch)

#     result = {
#         "transcript": transcript,
#         # "corrected": corrected,
#         "filler_words": fillers,
#         # "delivery_metrics": delivery,
#         "pitch": pitch
#     }
#     return jsonify(result)

@app.route('/api/v1/analyze', methods=['POST'])
def analyze_speech_v2():
    print("Starting speech analysis...")
    filepath = 'test_data/test2.wav'
    transcript = transcribe_audio_with_speech_to_text(filepath)
    print("Transcript:", transcript)
    fillers = count_fillers_with_gemini(transcript)
    print("Fillers:", fillers)
    recommendations = give_recommendations_with_gemini(transcript)
    print("recommendations:", recommendations)
    return jsonify({
        "transcript": transcript,
        "fillers": fillers,
        "recommendations": recommendations
    })


if __name__ == '__main__':
    app.run(debug=True)
