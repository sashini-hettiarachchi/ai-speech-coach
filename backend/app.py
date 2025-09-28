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
from mcp_servers.mcp_interface import MCPKnowledgeInterface

app = Flask(__name__)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configure CORS
CORS(app, 
     origins=CORS_ORIGINS, 
     methods=CORS_METHODS,
     allow_headers=CORS_HEADERS,
     supports_credentials=CORS_SUPPORTS_CREDENTIALS)

# Initialize the MCP Knowledge Interface
mcp_interface = MCPKnowledgeInterface()

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
        
        # Step 4: Get contextual information from MCP servers
        user_profile = mcp_interface.get_user_profile(user_id)
        domain_guidelines = mcp_interface.get_domain_guidelines(domain_id)
        
        event_guidelines = {}
        if event_id:
            event_guidelines = mcp_interface.get_event_guidelines(event_id)
        
        audience_insights = {}
        if audience_id:
            audience_insights = mcp_interface.get_audience_insights(audience_id)
            
        # Step 5: Build context-aware speech data
        speech_data = {
            "domain_id": domain_id,
            "user_id": user_id,
            "event_id": event_id,
            "audience_id": audience_id,
            "metrics": speech_metrics,
            "transcript": transcript,
            "user_profile": user_profile,
            "domain_guidelines": domain_guidelines,
            "event_guidelines": event_guidelines,
            "audience_insights": audience_insights
        }
        
        # Step 6: Generate MCP-enhanced feedback with LLM
        print("🧠 Generating context-aware feedback...")
        mcp_feedback = mcp_interface.generate_enhanced_feedback(speech_data)
        
        # Step 7: Generate traditional feedback
        print("🤖 Generating traditional feedback...")
        traditional_feedback = mcp_interface.generate_traditional_feedback({
            "transcript": transcript,
            "filler_analysis": filler_analysis,
            "delivery_metrics": delivery_analysis
        })
        
        # Step 8: Compile response
        response_data = {
            "status": "success",
            "transcript": transcript,
            "filler_words": {
                "total_fillers": filler_analysis.get("total_fillers", 0),
                "filler_percentage": filler_analysis.get("filler_percentage", 0),
                "fillers": filler_analysis.get("fillers", [])
            },
            "delivery_metrics": {
                "pace_wpm": delivery_analysis.get("pace", 140),
                "vocal_variety": delivery_analysis.get("vocal_variety", 7.5),
                "confidence_score": delivery_analysis.get("confidence", 8.0)
            },
            "mcp_enhanced_feedback": {
                "strengths": mcp_feedback.get("strengths", []),
                "improvements": mcp_feedback.get("improvements", []),
                "revised_speech": mcp_feedback.get("revised_speech", "")
            },
            "traditional_feedback": {
                "strengths": traditional_feedback.get("strengths", []),
                "improvements": traditional_feedback.get("improvements", []),
                "revised_speech": traditional_feedback.get("revised_speech", "")
            }
        }
        
        # Clean up uploaded file
        try:
            os.remove(filepath)
        except Exception as e:
            print(f"⚠️ Could not remove file {filepath}: {e}")
        
        print("✅ Analysis completed successfully")
        return jsonify(response_data)
        
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

@app.route('/api/v1/options', methods=['GET'])
def get_available_options():
    """Get all available users, domains, events, and audiences"""
    try:
        # Get resources from MCP servers - since we're reusing the same server instance for all clients
        # we only need to get resources from the domain client
        response = mcp_interface.domain_client._send_request("resources/list")
        resources = response.get("result", {}).get("resources", [])
        
        # Extract options from resources
        domains = []
        users = []
        events = []
        audiences = []
        
        for resource in resources:
            uri = resource.get("uri", "")
            
            if uri.startswith("domain://") and not uri.endswith("available-domains"):
                domain_id = uri.replace("domain://", "")
                domains.append({
                    "id": domain_id,
                    "name": resource.get("title", domain_id)
                })
            elif uri.startswith("user://"):
                user_id = uri.replace("user://", "")
                users.append({
                    "id": user_id,
                    "name": resource.get("title", user_id)
                })
            elif uri.startswith("event://"):
                event_id = uri.replace("event://", "")
                events.append({
                    "id": event_id,
                    "name": resource.get("title", event_id)
                })
            elif uri.startswith("audience://"):
                audience_id = uri.replace("audience://", "")
                audiences.append({
                    "id": audience_id,
                    "name": resource.get("title", audience_id)
                })
        
        return jsonify({
            "domains": domains,
            "users": users,
            "events": events,
            "audiences": audiences
        })
    except Exception as e:
        return jsonify({"error": f"Failed to get options: {str(e)}"}), 500

if __name__ == '__main__':
    print("🚀 Starting Speech Coach API with MCP-Enhanced Knowledge Servers...")
    print("📡 Available endpoints:")
    print("   • GET  /api/v1/health - Check server status")
    print("   • GET  /api/v1/options - Get available options")
    print("   • POST /api/v1/analyze - Analyze speech with file upload + LLM integration")
    
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=DEBUG_MODE)
