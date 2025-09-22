from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import traceback

# Import analysis utilities (with fallbacks for missing dependencies)
try:
    from utils.delivery_metrics import analyze_delivery
except ImportError:
    def analyze_delivery(filepath, transcript):
        return {"pace": 140, "vocal_variety": 7.5, "confidence": 8.0, "overall_score": 7.8}

try:
    from utils.filler_detector import count_filler_words
except ImportError:
    def count_filler_words(transcript):
        return {"total_fillers": 3, "filler_percentage": 2.1, "fillers": ["um", "uh"]}

try:
    from utils.transcriber import transcrib_audio_with_whisper
except ImportError:
    def transcrib_audio_with_whisper(filepath):
        return "Hello everyone, thank you for joining my presentation today. Um, so, I want to talk about the importance of clear communication."

# Import the unified LLM interface
from mcp_servers.llm_interface import SpeechCoachLLMInterface
from utils.llm_recommendations import llm_recommender

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configure CORS properly
CORS(app, 
     origins=["http://localhost:3000"], 
     methods=["GET", "POST", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"],
     supports_credentials=True)

# Initialize the unified LLM interface
llm_interface = SpeechCoachLLMInterface()

@app.after_request
def after_request(response):
    """Add CORS headers to all responses"""
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

@app.route('/')
def home():
    return jsonify({"message": "Speech Coach API", "status": "running"})

@app.route('/api/v1/analyze', methods=['POST', 'OPTIONS'])
def analyze_speech():
    """Main endpoint for speech analysis with knowledge server integration"""
    
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        return '', 200
    
    print("Starting speech analysis...")
    
    try:
        # Check if file is uploaded
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Save uploaded file
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        print(f"File saved: {filepath}")
        
        # Get context parameters (with defaults)
        user_id = request.form.get('user_id', 'user123')
        event_id = request.form.get('event_id', 'quarterly_review')
        audience_id = request.form.get('audience_id', 'clients')
        domain = request.form.get('domain', 'public_speaking')
        
        print(f"Context: user={user_id}, domain={domain}, event={event_id}, audience={audience_id}")
        
        # Step 1: Basic speech analysis
        transcript = transcrib_audio_with_whisper(filepath)
        print("Transcript:", transcript[:100] + "..." if len(transcript) > 100 else transcript)
        
        fillers = count_filler_words(transcript)
        print("Fillers:", fillers)
        
        delivery_metrics = analyze_delivery(filepath, transcript)
        print("Delivery Metrics:", delivery_metrics)
        
        # Step 2: Generate contextual feedback using knowledge servers
        try:
            speech_analysis = {
                "transcript": transcript,
                "fillers": fillers,
                "delivery_metrics": delivery_metrics,
                "word_count": len(transcript.split()) if transcript else 0,
                "metrics": {
                    "pace_wpm": delivery_metrics.get("pace", 140),
                    "filler_words_count": fillers.get("total_fillers", 0),
                    "vocal_variety_score": delivery_metrics.get("vocal_variety", 7.0),
                    "confidence_score": delivery_metrics.get("confidence", 7.5),
                    "overall_score": delivery_metrics.get("overall_score", 7.5)
                }
            }
            
            # Get context from knowledge servers
            try:
                # Get all context information
                user_context = llm_interface.user_knowledge_server.get_context(user_id)
                domain_context = llm_interface.domain_knowledge_server.get_context(domain)
                event_context = llm_interface.event_knowledge_server.get_context(event_id)
                audience_context = llm_interface.audience_knowledge_server.get_context(audience_id)
                
                print(f"Retrieved context - User: {user_context is not None}, Domain: {domain_context is not None}")
                
                # Generate LLM-based recommendations with context
                llm_recommendations = llm_recommender.generate_contextual_recommendations(
                    speech_analysis=speech_analysis,
                    user_context=user_context,
                    domain_context=domain_context,
                    event_context=event_context,
                    audience_context=audience_context
                )
                
                # Format recommendations for frontend
                recommendations = []
                if llm_recommendations.get('specific_recommendations'):
                    for rec in llm_recommendations['specific_recommendations']:
                        category = rec.get('category', 'General')
                        recommendation = rec.get('recommendation', '')
                        rationale = rec.get('rationale', '')
                        priority = rec.get('priority', 'medium')
                        
                        priority_emoji = {
                            'high': '🚨',
                            'medium': '⚡',
                            'low': '💡'
                        }.get(priority, '📝')
                        
                        recommendations.append(f"{priority_emoji} **{category}**: {recommendation}\n   *{rationale}*")
                
                if llm_recommendations.get('context_specific_tips'):
                    recommendations.append("\n**💡 Context-Specific Tips:**")
                    for tip in llm_recommendations['context_specific_tips']:
                        recommendations.append(f"   • {tip}")
                
                if llm_recommendations.get('next_steps'):
                    recommendations.append("\n**🎯 Next Steps:**")
                    for step in llm_recommendations['next_steps']:
                        recommendations.append(f"   • {step}")
                
                formatted_recommendations = "\n\n".join(recommendations) if recommendations else "Keep practicing your speaking skills!"
                
                # Enhanced contextual feedback
                contextual_feedback = {
                    "llm_recommendations": llm_recommendations,
                    "overall_score": llm_recommendations.get('overall_score', 7.0),
                    "strengths": llm_recommendations.get('strengths', []),
                    "areas_for_improvement": llm_recommendations.get('areas_for_improvement', []),
                    "personalized": llm_recommendations.get('personalized', False),
                    "context_applied": llm_recommendations.get('context_applied', False),
                    "generation_method": llm_recommendations.get('generation_method', 'unknown'),
                    "context_sources": {
                        "user_context": user_context is not None,
                        "domain_context": domain_context is not None,
                        "event_context": event_context is not None,
                        "audience_context": audience_context is not None
                    }
                }
                
                context_applied = True
                print(f"✅ LLM recommendations generated successfully ({contextual_feedback['generation_method']})")
                
            except Exception as llm_error:
                print(f"LLM recommendation error: {str(llm_error)}")
                
                # Fallback to original knowledge server approach
                contextual_feedback = llm_interface.get_contextual_feedback(
                    user_id=user_id,
                    speech_analysis=speech_analysis,
                    domain=domain,
                    event_id=event_id,
                    audience_id=audience_id
                )
                
                # Extract recommendations from knowledge server feedback
                recommendations = []
                if 'personalized_recommendations' in contextual_feedback:
                    for rec in contextual_feedback['personalized_recommendations']:
                        recommendations.append(f"**{rec['category']}**: {rec['recommendation']} - {rec['rationale']}")
                
                if 'next_steps' in contextual_feedback:
                    recommendations.extend([f"**Next Step**: {step}" for step in contextual_feedback['next_steps']])
                
                formatted_recommendations = "\n\n".join(recommendations) if recommendations else "Keep practicing your speaking skills!"
                context_applied = True
                print("Knowledge server integration successful (fallback)")
            
        except Exception as e:
            print(f"Error with knowledge servers: {str(e)}")
            traceback.print_exc()
            
            # Final fallback recommendations
            formatted_recommendations = f"""
**📊 Delivery Analysis**
- Filler words detected: {fillers.get('total_fillers', 0)} ({fillers.get('filler_percentage', 0):.1f}% of speech)
- Speaking pace: {delivery_metrics.get('pace', 140)} words per minute
- Confidence level: {delivery_metrics.get('confidence', 7.5)}/10

**🎯 Recommendations**
- Practice reducing filler words like 'um', 'uh', and 'like'
- Maintain your current speaking pace
- Continue working on vocal variety and emphasis
- Record yourself practicing to build awareness
            """.strip()
            
            contextual_feedback = {"error": str(e), "fallback": True}
            context_applied = False
        
        # Clean up uploaded file
        try:
            os.remove(filepath)
            print(f"Cleaned up file: {filepath}")
        except Exception as e:
            print(f"Could not remove file: {e}")

        print({
            "transcript": transcript,
            "fillers": fillers,
            "delivery_metrics": delivery_metrics,
            "recommendations": formatted_recommendations,
            "contextual_feedback": contextual_feedback,
            "context_applied": context_applied,
            "status": "success"
        })
        # Return response
        response = {
            "transcript": transcript,
            "fillers": fillers,
            "delivery_metrics": delivery_metrics,
            "recommendations": formatted_recommendations,
            "contextual_feedback": contextual_feedback,
            "context_applied": context_applied,
            "status": "success"
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error in analyze_speech: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@app.route('/api/v1/test-llm', methods=['POST', 'OPTIONS'])
def test_llm_recommendations():
    """Test endpoint for LLM recommendations with sample data"""
    
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        # Sample speech analysis data
        sample_speech_analysis = {
            "transcript": "Um, hello everyone. So, like, today I want to talk about, uh, the importance of communication. You know, it's really important and, um, we should all work on it.",
            "word_count": 28,
            "fillers": {
                "total_fillers": 5,
                "filler_percentage": 17.9,
                "fillers": ["um", "uh", "like", "you know", "so"]
            },
            "delivery_metrics": {
                "pace": 135,
                "vocal_variety": 6.5,
                "confidence": 7.0,
                "overall_score": 6.8
            }
        }
        
        # Get context parameters from request
        data = request.get_json() or {}
        user_id = data.get('user_id', 'user123')
        domain = data.get('domain', 'public_speaking')
        event_id = data.get('event_id', 'quarterly_review')
        audience_id = data.get('audience_id', 'clients')
        
        # Get context from knowledge servers
        user_context = llm_interface.user_knowledge_server.get_context(user_id)
        domain_context = llm_interface.domain_knowledge_server.get_context(domain)
        event_context = llm_interface.event_knowledge_server.get_context(event_id)
        audience_context = llm_interface.audience_knowledge_server.get_context(audience_id)
        
        # Generate LLM recommendations
        llm_recommendations = llm_recommender.generate_contextual_recommendations(
            speech_analysis=sample_speech_analysis,
            user_context=user_context,
            domain_context=domain_context,
            event_context=event_context,
            audience_context=audience_context
        )
        
        return jsonify({
            "status": "success",
            "sample_data": sample_speech_analysis,
            "context_retrieved": {
                "user_context": user_context is not None,
                "domain_context": domain_context is not None,
                "event_context": event_context is not None,
                "audience_context": audience_context is not None
            },
            "llm_recommendations": llm_recommendations,
            "llm_endpoint": llm_recommender.llm_endpoint,
            "model": llm_recommender.model
        })
        
    except Exception as e:
        print(f"Test LLM error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Check health of all knowledge servers"""
    try:
        health = llm_interface.health_check()
        return jsonify(health)
    except Exception as e:
        return jsonify({"error": f"Health check failed: {str(e)}"}), 500

@app.route('/api/v1/options', methods=['GET'])
def get_available_options():
    """Get all available users, domains, events, and audiences"""
    try:
        options = llm_interface.get_available_options()
        return jsonify(options)
    except Exception as e:
        return jsonify({"error": f"Failed to get options: {str(e)}"}), 500

if __name__ == '__main__':
    print("🚀 Starting Speech Coach API with LLM-Enhanced Knowledge Servers...")
    print("📡 Available endpoints:")
    print("   • GET  /api/v1/health - Check server status")
    print("   • GET  /api/v1/options - Get available options")
    print("   • POST /api/v1/analyze - Analyze speech with file upload")
    print("   • POST /api/v1/test-llm - Test LLM recommendations")
    print("🤖 LLM Integration:")
    print(f"   • Ollama endpoint: {llm_recommender.llm_endpoint}")
    print(f"   • Model: {llm_recommender.model}")
    print("🌐 CORS enabled for http://localhost:3000")
    app.run(host='0.0.0.0', port=5005, debug=True)
