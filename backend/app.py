from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import traceback
import json
from datetime import datetime
from typing import Dict, Any, Optional
from utils.recommendations import give_recommendations

# Import application configuration
from config import (
    SERVER_HOST, SERVER_PORT, DEBUG_MODE, 
    CORS_ORIGINS, CORS_METHODS, CORS_HEADERS, 
    CORS_SUPPORTS_CREDENTIALS, UPLOAD_FOLDER,
    MCP_PROTOCOL_VERSION
)

# Import MCP Tools
from tools.transcribe_tool import TranscribeTool
from tools.audio_prosody_tool import AudioProsodyTool
from tools.nlp_structure_tool import NLPStructureTool
from tools.pronunciation_tool import PronunciationTool
from tools.video_pose_tool import VideoPoseTool
from tools.filler_detector_tool import FillerDetectorTool
from tools.scorer_tool import ScorerTool, ScorerToolInput
from tools.feedback_generator_tool import FeedbackGeneratorTool, FeedbackGeneratorToolInput

# Import utilities for backward compatibility
from utils.filler_detector import count_filler_words


app = Flask(__name__)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configure CORS
CORS(app, 
     origins=CORS_ORIGINS, 
     methods=CORS_METHODS,
     allow_headers=CORS_HEADERS,
     supports_credentials=CORS_SUPPORTS_CREDENTIALS)


@app.after_request
def after_request(response):
    """Add CORS headers to all responses"""
    response.headers.add('Access-Control-Allow-Origin', CORS_ORIGINS[0])
    response.headers.add('Access-Control-Allow-Headers', ','.join(CORS_HEADERS))
    response.headers.add('Access-Control-Allow-Methods', ','.join(CORS_METHODS + ['PUT', 'DELETE']))
    response.headers.add('Access-Control-Allow-Credentials', 'true' if CORS_SUPPORTS_CREDENTIALS else 'false')
    return response

@app.route('/')
def home():
    return jsonify({"message": "Speech Coach API", "status": "running"})

@app.route('/api/v1/analyze', methods=['POST', 'OPTIONS'])
def analyze_speech():
    """Main endpoint for speech analysis with MCP-integrated knowledge server recommendations"""
    
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        print("📝 Received speech analysis request")
        
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Get optional parameters for MCP context
        user_id = request.form.get('user_id', 'user123')
        domain_id = request.form.get('domain', 'public_speaking')
        context_label = request.form.get('context_label', 'academic')
        
        print(f"🎯 Analysis request - User: {user_id}, Domain: {domain_id}")
        
        # Save uploaded file
        filename = file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        print(f"💾 File saved: {filepath}")
        
        # Initialize MCP tools
        tools = {
            "transcribe": TranscribeTool(model_size="tiny"),
            "audio_prosody": AudioProsodyTool(),
            "nlp_structure": NLPStructureTool(),
            "pronunciation": PronunciationTool(),
            "filler_detector": FillerDetectorTool(),
            "scorer": ScorerTool(),
            "feedback_generator": FeedbackGeneratorTool()
        }
        
        # Check if the file is a video
        _, ext = os.path.splitext(filepath)
        is_video = ext.lower() in ['.mp4', '.avi', '.mov', '.mkv', '.webm']
        if is_video:
            tools["video_pose"] = VideoPoseTool()
            
        # Step 1: Transcribe audio
        print("🗣️ Starting transcription...")
        transcription_result = tools["transcribe"]({"file_path": filepath})
        transcript = transcription_result.transcript
        segments = transcription_result.segments
        print("✅ Transcription completed", transcript, segments)

        # Step 2: Analyze audio prosody
        print("🎵 Analyzing audio prosody...")
        prosody_result = tools["audio_prosody"]({"file_path": filepath, "transcript": transcript})
        print("✅ Audio prosody analysis completed", prosody_result)
        
        # # Step 3: Analyze speech structure using NLP
        # print("🔍 Analyzing speech structure...")
        # structure_result = tools["nlp_structure"]({"transcript": transcript})
        # print("✅ Structure analysis completed")
        
        # Step 4: Analyze pronunciation
        # print("🔊 Analyzing pronunciation...")
        # pronunciation_result = tools["pronunciation"]({
        #     "file_path": filepath,
        #     "transcript": transcript
        # })
        # print("✅ Pronunciation analysis completed")
        
        # # Step 5: Analyze video (if applicable)
        # video_result = None
        # if is_video and "video_pose" in tools:
        #     print("🎥 Analyzing video pose and expressions...")
        #     video_result = tools["video_pose"]({"file_path": filepath})
        #     print("✅ Video analysis completed")
        
        # Step 6: Calculate competency scores
        # print("🏆 Calculating competency scores...")
        # scorer_input = ScorerToolInput(
        #     transcript=transcript,
        #     word_count=len(transcript.split()),
        #     words_per_minute=prosody_result.words_per_minute,
        #     syllables_per_minute=prosody_result.syllables_per_minute,
        #     pitch_mean=prosody_result.pitch_mean,
        #     pitch_std=prosody_result.pitch_std,
        #     volume_mean=prosody_result.volume_mean,
        #     volume_std=prosody_result.volume_std,
        #     pause_events=prosody_result.pause_events,
        #     volume_events=prosody_result.volume_events,
        #     pitch_events=prosody_result.pitch_events,
        #     speed_events=prosody_result.speed_events,
        #     # structure_quality=structure_result.structure_quality,
        #     # readability_score=structure_result.readability_score,
        #     # pronunciation_score=pronunciation_result.pronunciation_score,
        #     # grammar_error_count=len(pronunciation_result.grammar_errors),
        #     # Optional video metrics
        #     # eye_contact_pct=video_result.eye_contact_pct if video_result else None,
        #     # gesture_rate=video_result.gesture_rate if video_result else None,
        #     # facial_expressiveness=video_result.facial_expressiveness if video_result else None
        # )
        
        # score_result = tools["scorer"](scorer_input)
        # print("✅ Competency scoring completed")
        
        # # Step 6.5: Perform detailed filler word analysis with MCP tool
        # print("🔍 Performing detailed filler word analysis...")
        filler_result = tools["filler_detector"]({"transcript": transcript, "use_llm": True})
        filler_analysis = filler_result.dict()
        print(f"✅ Detected {filler_result.total_fillers} filler words ({filler_result.filler_percentage:.1f}%), filler_result: {filler_result}")

        # Step 7: Generate feedback
        print("💭 Generating personalized feedback...")
        feedback_input = {
            "context_label": context_label,
            "speech_duration": prosody_result.pause_events[-1].end_time if prosody_result.pause_events else 60.0,
            "words_per_minute": prosody_result.words_per_minute,
            "transcript": transcript,  # Include transcript for LLM-based feedback
            "filler_analysis": filler_analysis,  # Include detailed filler analysis
            "prosody_results": prosody_result.dict(),
        }
        
        feedback_result = tools["feedback_generator"](feedback_input)
        print("✅ Feedback generation completed")
        feedback_without_context = give_recommendations(transcript)
        
        # Prepare response
        response = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "request": {
                "user_id": user_id,
                "domain": domain_id,
                "context_label": context_label,
                "file_name": filename
            },
            "analysis": {
                "transcript": transcript,
                "segments": [segment.dict() for segment in segments],
                "audio_prosody": prosody_result.dict(),
                # "structure": structure_result.dict(),
                # "pronunciation": pronunciation_result.dict(),
                "filler_analysis": filler_analysis,
                # "scores": score_result.dict(),
                "feedback": feedback_result.dict(),
                "feedback_without_context": feedback_without_context
            }
        }
        
        # Add video analysis if available
        # if video_result:
        #     response["analysis"]["video"] = video_result.dict()
            
        # Clean up uploaded file
        try:
            os.remove(filepath)
        except Exception as e:
            print(f"⚠️ Could not remove file {filepath}: {e}")
        
        print("✅ Analysis completed successfully")
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ Error in speech analysis: {str(e)}")
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Check health of all MCP tools"""
    try:
        # Initialize each tool to check if they load successfully
        tools = {
            "transcribe": TranscribeTool(model_size="tiny"),
            "audio_prosody": AudioProsodyTool(),
            "nlp_structure": NLPStructureTool(),
            "pronunciation": PronunciationTool(),
            "video_pose": VideoPoseTool(),
            "filler_detector": FillerDetectorTool(),
            "scorer": ScorerTool(),
            "feedback_generator": FeedbackGeneratorTool()
        }
        
        # Check each tool and collect statuses
        health = {}
        for name, tool in tools.items():
            try:
                # Just access the tool attributes to check if it's working
                health[name] = {
                    "status": "ok",
                    "name": tool.name,
                    "description": tool.description
                }
            except Exception as tool_error:
                health[name] = {
                    "status": "error",
                    "error": str(tool_error)
                }
        
        return jsonify({
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "tools": health,
            "mcp_version": MCP_PROTOCOL_VERSION
        })
    except Exception as e:
        return jsonify({"error": f"Health check failed: {str(e)}"}), 500


@app.route('/api/v1/options', methods=['GET'])
def get_options():
    """Get available options for analysis parameters"""
    options = {
        "context_labels": [
            "academic", 
            "persuasive", 
            "storytelling",
        ],
        "supported_file_types": [
            "audio/wav", 
            "audio/mp3", 
            "audio/m4a", 
            "video/mp4", 
            "video/webm"
        ],
        "mcp_tools": [
            "transcribe_tool",
            "audio_prosody_tool",
            "nlp_structure_tool", 
            "pronunciation_tool",
            "video_pose_tool",
            "filler_detector_tool",
            "scorer_tool", 
            "feedback_generator_tool"
        ]
    }
    
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "options": options,
        "mcp_version": MCP_PROTOCOL_VERSION
    })

if __name__ == '__main__':
    print("🚀 Starting Speech Coach API with MCP Tools...")
    print("📡 Available endpoints:")
    print("   • GET  /api/v1/health - Check tools and server status")
    print("   • GET  /api/v1/options - Get available options")
    print("   • POST /api/v1/analyze - Analyze speech with MCP tools pipeline")
    print(f"📂 Upload folder: {UPLOAD_FOLDER}")
    print(f"🔗 Accepting CORS from: {CORS_ORIGINS}")
    
    # Ensure upload folder exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=DEBUG_MODE)
