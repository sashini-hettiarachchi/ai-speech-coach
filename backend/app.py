from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import traceback
import json
from datetime import datetime
from typing import Dict, Any, Optional
from utils.transcriber import transcrib_audio_with_whisper

# Import application configuration
from config import (
    SERVER_HOST, SERVER_PORT, DEBUG_MODE, 
    CORS_ORIGINS, CORS_METHODS, CORS_HEADERS, 
    CORS_SUPPORTS_CREDENTIALS, UPLOAD_FOLDER,
    MCP_PROTOCOL_VERSION
)

# Import analysis utilities
from utils.delivery_metrics import analyze_delivery
from utils.filler_detector import count_filler_words

# Import MCP Knowledge Interface


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
        event_id = request.form.get('event_id')
        audience_id = request.form.get('audience_id')
        
        print(f"🎯 Analysis request - User: {user_id}, Domain: {domain_id}")
        
        # Save uploaded file
        filename = file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        print(f"💾 File saved: {filepath}")
        
        # Step 1: Transcribe audio
        print("🗣️ Starting transcription...")
        transcript = transcrib_audio_with_whisper(filepath)
        print("✅ Transcription completed")

        # Step 2: Analyze filler words
        print("🔍 Analyzing filler words...")
        filler_analysis = count_filler_words(transcript)
        
        # Step 3: Analyze delivery metrics
        print("📊 Analyzing delivery metrics...")
        delivery_analysis = analyze_delivery(filepath, transcript)
        
        # Prepare speech metrics for MCP knowledge servers
        speech_metrics = {
            "filler_count": filler_analysis.get("total_fillers", 0),
            "filler_percentage": filler_analysis.get("filler_percentage", 0),
            "pace_wpm": delivery_analysis.get("pace", 140),
            "vocal_variety": delivery_analysis.get("vocal_variety", 7.5),
            "confidence_score": delivery_analysis.get("confidence", 8.0),
            "overall_score": delivery_analysis.get("overall_score", 7.8)
        }
        
     
 
        
        # Step 6: Generate MCP-enhanced feedback with LLM
        print("🧠 Generating context-aware feedback...")
     
    
        
        # Clean up uploaded file
        try:
            os.remove(filepath)
        except Exception as e:
            print(f"⚠️ Could not remove file {filepath}: {e}")
        
        print("✅ Analysis completed successfully")
   
        
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
    """Check health of all knowledge servers"""
    try:
        health = mcp_interface.check_servers_health()
        return jsonify({
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "services": health,
            "mcp_version": MCP_PROTOCOL_VERSION
        })
    except Exception as e:
        return jsonify({"error": f"Health check failed: {str(e)}"}), 500


if __name__ == '__main__':
    print("🚀 Starting Speech Coach API with MCP-Enhanced Knowledge Servers...")
    print("📡 Available endpoints:")
    print("   • GET  /api/v1/health - Check server status")
    print("   • GET  /api/v1/options - Get available options")
    print("   • POST /api/v1/analyze - Analyze speech with file upload + LLM integration")
    
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=DEBUG_MODE)
