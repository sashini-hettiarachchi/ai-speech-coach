from flask import Flask, jsonify, request, g
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
import traceback
import json
from datetime import datetime
from typing import Dict, Any, Optional
from utils.recommendations import give_recommendations

# Import database models
from models import db, User, Speech, Session

# Import authentication utilities
from auth0_utils import auth0_required, get_current_user, get_auth0_user_id, AuthError, handle_auth_error

# Import application configuration
from config import (
    SERVER_HOST, SERVER_PORT, DEBUG_MODE, 
    CORS_ORIGINS, CORS_METHODS, CORS_HEADERS, 
    CORS_SUPPORTS_CREDENTIALS, UPLOAD_FOLDER,
    MCP_PROTOCOL_VERSION, SQLALCHEMY_DATABASE_URI,
    SQLALCHEMY_TRACK_MODIFICATIONS, SQLALCHEMY_ENGINE_OPTIONS
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
from utils.gcs_storage import upload_speech_file, delete_speech_file, refresh_media_url


app = Flask(__name__)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = SQLALCHEMY_ENGINE_OPTIONS

# Initialize database
db.init_app(app)
migrate = Migrate(app, db)

# Configure CORS with proper preflight handling
CORS(app, 
     origins=CORS_ORIGINS, 
     methods=CORS_METHODS,
     allow_headers=CORS_HEADERS,
     supports_credentials=CORS_SUPPORTS_CREDENTIALS,
     expose_headers=["Content-Type", "Authorization"],
     max_age=86400)  # Cache preflight for 24 hours

# Register error handlers
app.register_error_handler(AuthError, handle_auth_error)

@app.route('/')
def home():
    return jsonify({"message": "Speech Coach API", "status": "running"})

@app.route('/api/v1/analyze', methods=['POST'])
@auth0_required
def analyze_speech():
    """Main endpoint for speech analysis with MCP-integrated knowledge server recommendations"""
    
    try:
        print("📝 Received speech analysis request")
        
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Get user and parameters
        user = get_current_user()
        auth0_user_id = get_auth0_user_id()
        
        # Get speech ID and context parameters
        speech_id = request.form.get('speech_id')
        session_title = request.form.get('session_title')  # Optional session title
        if not speech_id:
            return jsonify({"error": "speech_id is required"}), 400
        # Verify speech belongs to user
        speech = Speech.query.filter_by(id=int(speech_id), user_id=int(user.id)).first()
        if not speech:
            return jsonify({"error": "Speech not found or access denied"}), 404
        
        context_label = speech.context  # Use speech's context
        # domain_id = 'public_speaking'
        speech_title = speech.title
        speech_goal = speech.goal
        speech_audience_description = speech.audience_description
        speech_key_points = speech.key_points
        speech_self_improvement_goal = speech.self_improvement_goal

        print(f"🎯 Analysis request - User: {auth0_user_id}, Speech: {speech.title}, Context: {context_label}")
        
        # Save uploaded file temporarily
        filename = file.filename
        temp_filepath = os.path.join(UPLOAD_FOLDER, f"temp_{filename}")
        file.save(temp_filepath)
        
        print(f"💾 File saved temporarily: {temp_filepath}")
        
        # Upload to Google Cloud Storage
        try:
            blob_name, gcs_signed_url = upload_speech_file(temp_filepath, filename)
            print(f"☁️ File uploaded to GCS: {gcs_signed_url}")
            print(f"📏 GCS URL length: {len(gcs_signed_url)} characters")
        except Exception as gcs_error:
            print(f"❌ GCS upload failed: {str(gcs_error)}")
            # Clean up temp file
            try:
                os.remove(temp_filepath)
            except:
                pass
            return jsonify({"error": f"File upload failed: {str(gcs_error)}"}), 500
        
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
        _, ext = os.path.splitext(temp_filepath)
        is_video = ext.lower() in ['.mp4', '.avi', '.mov', '.mkv', '.webm']
        if is_video:
            tools["video_pose"] = VideoPoseTool()
            
        # Step 1: Transcribe audio
        print("🗣️ Starting transcription...")
        transcription_result = tools["transcribe"]({"file_path": temp_filepath})
        transcript = transcription_result.transcript
        segments = transcription_result.segments
        print("✅ Transcription completed", transcript, segments)

        # Step 2: Analyze audio prosody
        print("🎵 Analyzing audio prosody...")
        prosody_result = tools["audio_prosody"]({"file_path": temp_filepath, "transcript": transcript})
        print("✅ Audio prosody analysis completed")
        
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
            "speech_title": speech_title,
            "speech_goal": speech_goal,
            "speech_audience_description": speech_audience_description,
            "speech_key_points": speech_key_points,
            "speech_self_improvement_goal": speech_self_improvement_goal,
        }
        
        feedback_result = tools["feedback_generator"](feedback_input)
        print("✅ Feedback generation completed")
        
        # Generate general feedback without context awareness
        feedback_without_context_raw = give_recommendations(transcript, prosody_result.dict() if prosody_result else None, filler_analysis)
        
        # Parse the structured feedback response
        feedback_without_context = feedback_without_context_raw
        try:
            import json
            feedback_without_context = json.loads(feedback_without_context_raw)
        except (json.JSONDecodeError, TypeError):
            # Keep as string if parsing fails
            print("Warning: Could not parse feedback_without_context as JSON, storing as string")
            feedback_without_context = feedback_without_context_raw
        
        # Save session to database
        try:
            # Validate URL length before saving
            if len(gcs_signed_url) > 2000:
                print(f"⚠️ Warning: GCS URL length ({len(gcs_signed_url)}) exceeds database limit")
                return jsonify({"error": "Generated URL is too long for database storage"}), 500
            
            # Create new session record
            session = Session(
                speech_id=speech.id,
                title=session_title,  # Add the optional session title
                media_url=gcs_signed_url,  # Store GCS signed URL instead of local path
                media_type='video' if is_video else 'audio',
                original_filename=filename,
                transcript=transcript,
                feedback=feedback_result.feedback if hasattr(feedback_result, 'feedback') else str(feedback_result),
                filler_word_count=filler_result.total_fillers,
                filler_word_percentage=filler_result.filler_percentage,
                filler_word_details=filler_analysis,
                words_per_minute=prosody_result.words_per_minute,
                syllables_per_minute=prosody_result.syllables_per_minute,
                pitch_mean=prosody_result.pitch_mean,
                pitch_std=prosody_result.pitch_std,
                volume_mean=prosody_result.volume_mean,
                volume_std=prosody_result.volume_std,
                pause_events=[event.dict() for event in prosody_result.pause_events],
                pitch_events=[event.dict() for event in prosody_result.pitch_events],
                volume_events=[event.dict() for event in prosody_result.volume_events],
                speed_events=[event.dict() for event in prosody_result.speed_events],
                duration_seconds=prosody_result.pause_events[-1].end_time if prosody_result.pause_events else 60.0,
                full_analysis_results={
                    "segments": [segment.dict() for segment in segments],
                    "audio_prosody": prosody_result.dict(),
                    "filler_analysis": filler_analysis,
                    "feedback": feedback_result.dict(),
                    "feedback_without_context": feedback_without_context,
                    "gcs_blob_name": blob_name  # Store blob name for future operations
                },
                analysis_version="1.0"
            )
            
            db.session.add(session)
            db.session.commit()
            
            print(f"✅ Saved session {session.id} to database")
            
        except Exception as db_error:
            print(f"⚠️ Database save error: {str(db_error)}")
            db.session.rollback()
            # Continue without failing the request
        
        # Prepare response
        response = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "request": {
                "user_id": auth0_user_id,
                "speech_id": speech.id,
                "speech_title": speech.title,
                # "domain": domain_id,
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
        
        # Add session ID if successfully saved
        if 'session' in locals():
            response["session_id"] = session.id
        
        # Add video analysis if available
        # if video_result:
        #     response["analysis"]["video"] = video_result.dict()
            
        # Clean up temporary uploaded file
        try:
            os.remove(temp_filepath)
            print(f"🗑️ Cleaned up temporary file: {temp_filepath}")
        except Exception as e:
            print(f"⚠️ Could not remove temporary file {temp_filepath}: {e}")
        
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

# =============================================
# NEW AUTH0 + DATABASE ENDPOINTS
# =============================================

@app.route('/api/v1/auth/user', methods=['GET'])
@auth0_required
def get_current_user_info():
    """Get current authenticated user information"""
    try:
        user = get_current_user()
        auth0_user_id = get_auth0_user_id()
        
        return jsonify({
            "status": "success",
            "user": {
                "id": user.id,
                "auth0_user_id": auth0_user_id,
                "synced_at": user.synced_at.isoformat() if user.synced_at else None,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/speeches', methods=['GET'])
@auth0_required
def get_user_speeches():
    """Get all speeches for the authenticated user"""
    try:
        user = get_current_user()
        speeches = Speech.query.filter_by(user_id=user.id).order_by(Speech.updated_at.desc()).all()
        
        return jsonify({
            "status": "success",
            "speeches": [speech.to_dict() for speech in speeches]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/speeches', methods=['POST'])
@auth0_required
def create_speech():
    """Create a new speech for the authenticated user"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'goal', 'audience_description', 'context']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Create new speech
        speech = Speech(
            user_id=user.id,
            title=data['title'],
            goal=data['goal'],
            audience_description=data['audience_description'],
            key_points=data.get('key_points', ''),
            self_improvement_goal=data.get('self_improvement_goal', ''),
            context=data['context'],
            # Legacy field for backward compatibility
            description=data.get('description', data.get('goal', ''))
        )
        
        db.session.add(speech)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "speech": speech.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/speeches/<int:speech_id>', methods=['GET'])
@auth0_required
def get_speech(speech_id):
    """Get a specific speech with its sessions"""
    try:
        user = get_current_user()
        speech = Speech.query.filter_by(id=speech_id, user_id=user.id).first()
        
        if not speech:
            return jsonify({"error": "Speech not found"}), 404
        
        return jsonify({
            "status": "success",
            "speech": speech.to_dict(include_sessions=True)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/speeches/<int:speech_id>', methods=['PUT'])
@auth0_required
def update_speech(speech_id):
    """Update a specific speech"""
    try:
        user = get_current_user()
        speech = Speech.query.filter_by(id=speech_id, user_id=user.id).first()
        
        if not speech:
            return jsonify({"error": "Speech not found"}), 404
        
        data = request.get_json()
        
        # Update fields if provided
        if 'title' in data:
            speech.title = data['title']
        if 'goal' in data:
            speech.goal = data['goal']
        if 'audience_description' in data:
            speech.audience_description = data['audience_description']
        if 'key_points' in data:
            speech.key_points = data['key_points']
        if 'self_improvement_goal' in data:
            speech.self_improvement_goal = data['self_improvement_goal']
        if 'context' in data:
            speech.context = data['context']
        # Legacy field for backward compatibility
        if 'description' in data:
            speech.description = data['description']
        
        speech.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "speech": speech.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/speeches/<int:speech_id>', methods=['DELETE'])
@auth0_required
def delete_speech(speech_id):
    """Delete a specific speech and all its sessions"""
    try:
        user = get_current_user()
        speech = Speech.query.filter_by(id=speech_id, user_id=user.id).first()
        
        if not speech:
            return jsonify({"error": "Speech not found"}), 404
        
        db.session.delete(speech)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Speech deleted successfully"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/speeches/<int:speech_id>/sessions', methods=['GET'])
@auth0_required
def get_speech_sessions(speech_id):
    """Get all sessions for a specific speech"""
    try:
        user = get_current_user()
        speech = Speech.query.filter_by(id=speech_id, user_id=user.id).first()
        
        if not speech:
            return jsonify({"error": "Speech not found"}), 404
        
        sessions = Session.query.filter_by(speech_id=speech_id).order_by(Session.created_at.desc()).all()
        
        return jsonify({
            "status": "success",
            "speech": speech.to_dict(),
            "sessions": [session.to_dict() for session in sessions]
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/sessions/<int:session_id>', methods=['GET'])
@auth0_required
def get_session(session_id):
    """Get detailed information about a specific session"""
    try:
        user = get_current_user()
        session = Session.query.join(Speech).filter(
            Session.id == session_id,
            Speech.user_id == user.id
        ).first()
        
        if not session:
            return jsonify({"error": "Session not found"}), 404
        
        return jsonify({
            "status": "success",
            "session": session.to_dict(include_full_analysis=True)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/sessions/<int:session_id>/fix-blob-name', methods=['POST'])
@auth0_required
def fix_session_blob_name(session_id):
    """Fix missing blob name in session's full_analysis_results"""
    try:
        user = get_current_user()
        session = Session.query.join(Speech).filter(
            Session.id == session_id,
            Speech.user_id == user.id
        ).first()
        
        if not session:
            return jsonify({"error": "Session not found"}), 404
        
        if not session.media_url:
            return jsonify({"error": "No media URL found for this session"}), 400
        
        # Extract blob name from media URL
        blob_name = None
        try:
            from urllib.parse import urlparse, unquote
            parsed = urlparse(session.media_url)
            
            if '/storage/v1/b/' in parsed.path and '/o/' in parsed.path:
                path_parts = parsed.path.split('/o/')
                if len(path_parts) > 1:
                    blob_name = unquote(path_parts[1].split('?')[0])
            elif parsed.netloc == 'storage.googleapis.com':
                path_parts = parsed.path.strip('/').split('/', 1)
                if len(path_parts) > 1:
                    blob_name = path_parts[1]
        except Exception as e:
            return jsonify({"error": f"Could not extract blob name: {str(e)}"}), 400
        
        if not blob_name:
            return jsonify({"error": "Could not extract blob name from media URL"}), 400
        
        # Update session's full_analysis_results with blob name
        if not session.full_analysis_results:
            session.full_analysis_results = {}
        
        session.full_analysis_results['gcs_blob_name'] = blob_name
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Blob name updated successfully",
            "blob_name": blob_name
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/sessions/<int:session_id>/refresh-media-url', methods=['POST'])
@auth0_required
def refresh_session_media_url(session_id):
    """Refresh the signed URL for a session's media file"""
    try:
        user = get_current_user()
        session = Session.query.join(Speech).filter(
            Session.id == session_id,
            Speech.user_id == user.id
        ).first()
        
        if not session:
            return jsonify({"error": "Session not found"}), 404
        
        # Get blob name from full analysis results or extract from media URL
        blob_name = None
        if session.full_analysis_results and isinstance(session.full_analysis_results, dict):
            blob_name = session.full_analysis_results.get('gcs_blob_name')
        
        # If no blob name in results, try to extract from media_url
        if not blob_name and session.media_url:
            # Extract blob name from GCS signed URL
            # Signed URLs contain the blob path, we need to extract it
            try:
                from urllib.parse import urlparse, unquote
                parsed = urlparse(session.media_url)
                
                # For GCS signed URLs, the path contains /storage/v1/b/bucket-name/o/blob-name
                if '/storage/v1/b/' in parsed.path and '/o/' in parsed.path:
                    # Extract blob name from signed URL path
                    path_parts = parsed.path.split('/o/')
                    if len(path_parts) > 1:
                        blob_name = unquote(path_parts[1].split('?')[0])  # Remove query params
                elif parsed.netloc == 'storage.googleapis.com':
                    # For public URLs: https://storage.googleapis.com/bucket/blob-name
                    path_parts = parsed.path.strip('/').split('/', 1)
                    if len(path_parts) > 1:
                        blob_name = path_parts[1]
                
                print(f"🔍 Extracted blob name from URL: {blob_name}")
            except Exception as extract_error:
                print(f"⚠️ Could not extract blob name from URL: {str(extract_error)}")
        
        if not blob_name:
            return jsonify({"error": "No GCS blob name found for this session and could not extract from URL"}), 400
        
        # Generate new signed URL (6 days expiration)
        new_signed_url = refresh_media_url(blob_name, hours=144)
        
        if not new_signed_url:
            return jsonify({"error": "Failed to generate new signed URL"}), 500
        
        # Update session with new URL
        session.media_url = new_signed_url
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "media_url": new_signed_url,
            "expires_in_hours": 144
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/sessions/<int:session_id>', methods=['DELETE'])
@auth0_required
def delete_session(session_id):
    """Delete a specific session"""
    try:
        user = get_current_user()
        session = Session.query.join(Speech).filter(
            Session.id == session_id,
            Speech.user_id == user.id
        ).first()
        
        if not session:
            return jsonify({"error": "Session not found"}), 404
        
        # Delete associated media file from GCS if it exists
        if session.media_url:
            try:
                # Extract blob name from full analysis results or media URL
                blob_name = None
                if session.full_analysis_results and isinstance(session.full_analysis_results, dict):
                    blob_name = session.full_analysis_results.get('gcs_blob_name')
                
                # If no blob name in results, try to extract from media_url
                if not blob_name:
                    try:
                        from urllib.parse import urlparse, unquote
                        parsed = urlparse(session.media_url)
                        
                        # Extract blob name from GCS URL
                        if '/storage/v1/b/' in parsed.path and '/o/' in parsed.path:
                            path_parts = parsed.path.split('/o/')
                            if len(path_parts) > 1:
                                blob_name = unquote(path_parts[1].split('?')[0])
                        elif parsed.netloc == 'storage.googleapis.com':
                            path_parts = parsed.path.strip('/').split('/', 1)
                            if len(path_parts) > 1:
                                blob_name = path_parts[1]
                    except Exception as extract_error:
                        print(f"⚠️ Could not extract blob name for deletion: {str(extract_error)}")
                
                if blob_name:
                    success = delete_speech_file(blob_name)
                    if success:
                        print(f"✅ Deleted GCS file: {blob_name}")
                    else:
                        print(f"⚠️ Could not delete GCS file: {blob_name}")
                else:
                    print(f"⚠️ No blob name found for session {session_id}")
                    
            except Exception as e:
                print(f"⚠️ Error deleting GCS file for session {session_id}: {str(e)}")
        
        db.session.delete(session)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Session deleted successfully"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Speech Coach API with Auth0 + Database Integration...")
    print("📡 Available endpoints:")
    print("   • GET  /api/v1/health - Check tools and server status")
    print("   • GET  /api/v1/options - Get available options")
    print("   • POST /api/v1/analyze - Analyze speech with MCP tools pipeline")
    print("   • GET  /api/v1/auth/user - Get current user info")
    print("   • GET  /api/v1/speeches - List user speeches")
    print("   • POST /api/v1/speeches - Create new speech")
    print("   • GET  /api/v1/speeches/{id} - Get speech details")
    print("   • PUT  /api/v1/speeches/{id} - Update speech")
    print("   • DELETE /api/v1/speeches/{id} - Delete speech")
    print("   • GET  /api/v1/speeches/{id}/sessions - List speech sessions")
    print("   • GET  /api/v1/sessions/{id} - Get session details")
    print("   • DELETE /api/v1/sessions/{id} - Delete session")
    print("   • POST /api/v1/sessions/{id}/refresh-media-url - Refresh expired media URL")
    print("   • POST /api/v1/sessions/{id}/fix-blob-name - Fix missing GCS blob name")
    print(f"📂 Upload folder: {UPLOAD_FOLDER}")
    print(f"🔗 Accepting CORS from: {CORS_ORIGINS}")
    print(f"🗄️ Database: {SQLALCHEMY_DATABASE_URI.split('@')[1] if '@' in SQLALCHEMY_DATABASE_URI else 'Not configured'}")
    
    # Ensure upload folder exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    # Create database tables if they don't exist
    with app.app_context():
        try:
            db.create_all()
            print("✅ Database tables ready")
        except Exception as e:
            print(f"⚠️ Database initialization error: {str(e)}")
    
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=DEBUG_MODE)
