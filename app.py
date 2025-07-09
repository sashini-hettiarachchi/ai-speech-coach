from flask import Flask, request, jsonify, render_template
from utils.transcriber import transcribe_audio
from utils.filler_detector import count_fillers
# from utils.grammar_checker import correct_grammar
from utils.delivery_metrics import analyze_delivery
from utils.pitch_analyzer import analyze_pitch
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return 

@app.route('/analyze', methods=['POST'])
def analyze_speech():
    # file = request.files['audio']
    # filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    filepath = 'test_data/test2.wav'

   
    print(filepath)
    # file.save(filepath)

    transcript = transcribe_audio(filepath)
    print("Transcript:", transcript)
    fillers = count_fillers(transcript)
    print("Fillers:", fillers)
    # corrected = correct_grammar(transcript)
    # delivery = analyze_delivery(filepath, transcript)
    # print("Delivery Metrics:", delivery)
    pitch = analyze_pitch(filepath)
  
  
   
    print("Pitch Analysis:", pitch)

    result = {
        "transcript": transcript,
        # "corrected": corrected,
        "filler_words": fillers,
        # "delivery_metrics": delivery,
        "pitch": pitch
    }
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
