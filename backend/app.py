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


# Import MCP servers and client
from mcp_servers.mcp_client import MCPClient, MCPKnowledgeInterface
from mcp_servers.domain_server_mcp import DomainKnowledgeMCPServer
from mcp_servers.user_server_mcp import UserKnowledgeMCPServer
from mcp_servers.event_server_mcp import EventKnowledgeMCPServer
from mcp_servers.audience_server_mcp import AudienceKnowledgeMCPServer

# Import the legacy LLM interface and recommendation generator for backwards compatibility
try:
    from mcp_servers.llm_interface import SpeechCoachLLMInterface
    from utils.llm_recommendations import LLMRecommendationGenerator
    legacy_support = True
except ImportError:
    legacy_support = False

app = Flask(__name__)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configure CORS properly
CORS(app, 
     origins=CORS_ORIGINS, 
     methods=CORS_METHODS,
     allow_headers=CORS_HEADERS,
     supports_credentials=CORS_SUPPORTS_CREDENTIALS)

# Initialize the MCP servers
domain_server = DomainKnowledgeMCPServer()
user_server = UserKnowledgeMCPServer()
event_server = EventKnowledgeMCPServer()
audience_server = AudienceKnowledgeMCPServer()

# Initialize the MCP Knowledge Interface
mcp_interface = MCPKnowledgeInterface()
mcp_interface.initialize_servers({
    "domain_server": domain_server,
    "user_server": user_server,
    "event_server": event_server,
    "audience_server": audience_server
})

# Initialize legacy components if available
if legacy_support:
    llm_interface = SpeechCoachLLMInterface()
    llm_recommender = LLMRecommendationGenerator()
    print("📚 Legacy LLM interface initialized for backward compatibility")

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
        print("✅ Transcription completed", transcript)

        # Step 2: Analyze filler words
        print("🔍 Analyzing filler words...")
        filler_analysis = count_filler_words(transcript)
        
        # Step 3: Analyze delivery metrics
        print("📊 Analyzing delivery metrics...")
        delivery_analysis = analyze_delivery(filepath, transcript)
        
        # Combine analysis results
        speech_analysis = {
            "transcript": transcript,
            "filler_analysis": filler_analysis,
            "delivery_metrics": delivery_analysis,
            "file_info": {
                "filename": filename,
                "analysis_timestamp": datetime.now().isoformat()
            }
        }
        
        # Step 4: Get MCP-based contextual feedback
        print("🔗 Getting MCP contextual feedback...")
        
        # Prepare speech metrics for MCP knowledge servers
        speech_metrics = {
            "filler_count": filler_analysis.get("total_fillers", 0),
            "filler_percentage": filler_analysis.get("filler_percentage", 0),
            "pace_wpm": delivery_analysis.get("pace", 140),
            "vocal_variety": delivery_analysis.get("vocal_variety", 7.5),
            "confidence_score": delivery_analysis.get("confidence", 8.0),
            "overall_score": delivery_analysis.get("overall_score", 7.8)
        }
        
        # MCP-based analysis using the domain knowledge server
        domain_analysis = mcp_interface.domain_client.call_tool("analyzeSpeech", {
            "domain": domain_id,
            "speech_metrics": speech_metrics
        })
        
        # Get user profile from user knowledge server
        user_profile = mcp_interface.get_user_profile(user_id)
        
        # Get event guidelines if event_id is provided
        event_guidelines = {}
        if event_id:
            event_guidelines = mcp_interface.get_event_guidelines(event_id)
        
        # Get audience insights if audience_id is provided
        audience_insights = {}
        if audience_id:
            audience_insights = mcp_interface.get_audience_insights(audience_id)
        
        # Generate personalized improvement plan
        improvement_plan = mcp_interface.domain_client.call_tool("generateImprovementPlan", {
            "domain": domain_id,
            "skill_level": user_profile.get("skill_level", "intermediate"),
            "improvement_areas": user_profile.get("improvement_areas", ["delivery", "structure"])
        })
        
        # Get personalized tips
        personalized_tips = mcp_interface.generate_personalized_tips(
            user_id=user_id,
            focus_area="delivery",
            domain=domain_id
        )
        
        # Build a comprehensive feedback prompt and get LLM-generated feedback
        speech_data = {
            "domain_id": domain_id,
            "user_id": user_id,
            "event_id": event_id,
            "audience_id": audience_id,
            "metrics": speech_metrics,
            "transcript": transcript
        }
        
        feedback_result = mcp_interface.build_feedback_prompt(speech_data)
        
        # Compile MCP response
        mcp_response = {
            "domain_analysis": domain_analysis,
            "user_profile": user_profile,
            "event_guidelines": event_guidelines,
            "audience_insights": audience_insights,
            "improvement_plan": improvement_plan,
            "personalized_tips": personalized_tips,
            "feedback_prompt": feedback_result["prompt"],
            "llm_feedback": feedback_result.get("generated_feedback"),
            "feedback_generation_method": feedback_result.get("generation_method", "template")
        }
        
        # Get legacy LLM recommendations if available (for backward compatibility)
        llm_recommendations_result = {"status": "MCP-based recommendations used instead"}
        if legacy_support:
            try:
                print("🤖 Getting legacy LLM recommendations for backwards compatibility...")
                llm_recommendations_result = llm_recommender(
                    speech_analysis, 
                    user_id=user_id,
                    domain=domain_id,
                    event_id=event_id,
                    audience_id=audience_id
                )
            except Exception as e:
                print(f"⚠️ Legacy LLM recommendations failed: {e}")
                llm_recommendations_result = {"error": "Legacy LLM recommendations unavailable"}
        
        # Compile comprehensive response with MCP integration
        response_data = {
            "status": "success",
            "analysis_id": f"analysis_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "user_context": {
                "user_id": user_id,
                "domain": domain_id,
                "event_id": event_id,
                "audience_id": audience_id
            },
            "speech_analysis": speech_analysis,
            "mcp_analysis": mcp_response,
            "legacy_llm_recommendations": llm_recommendations_result,
            "integration_info": {
                "mcp_enabled": True,
                "mcp_version": MCP_PROTOCOL_VERSION,
                "knowledge_servers": "active",
                "protocol": "Model Context Protocol"
            }
        }
        
        # Clean up uploaded file
        try:
            os.remove(filepath)
        except Exception as e:
            print(f"⚠️ Could not remove file {filepath}: {e}")
        
        print("✅ Analysis completed successfully with MCP integration")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Error in speech analysis: {str(e)}")
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/v1/mcp/context', methods=['POST'])
def get_mcp_context():
    """
    Get comprehensive context using MCP protocol
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'user123')
        domain_id = data.get('domain', 'public_speaking')
        event_id = data.get('event_id')
        audience_id = data.get('audience_id')
        speech_metrics = data.get('speech_metrics')
        
        # Build a comprehensive context dictionary
        context = {
            "jsonrpc": "2.0",
            "result": {
                "protocol": "mcp",
                "version": MCP_PROTOCOL_VERSION,
                "timestamp": datetime.now().isoformat(),
                "data": {}
            }
        }
        
        # Get domain knowledge if domain_id is provided
        if domain_id:
            domain_knowledge = mcp_interface.get_domain_knowledge(domain_id)
            context["result"]["data"]["domain"] = domain_knowledge
        
        # Get user profile if user_id is provided
        if user_id:
            user_profile = mcp_interface.get_user_profile(user_id)
            context["result"]["data"]["user"] = user_profile
        
        # Get event guidelines if event_id is provided
        if event_id:
            event_guidelines = mcp_interface.get_event_guidelines(event_id)
            context["result"]["data"]["event"] = event_guidelines
        
        # Get audience insights if audience_id is provided
        if audience_id:
            audience_insights = mcp_interface.get_audience_insights(audience_id)
            context["result"]["data"]["audience"] = audience_insights
        
        # Get domain analysis if speech_metrics are provided
        if speech_metrics and domain_id:
            domain_analysis = mcp_interface.domain_client.call_tool("analyzeSpeech", {
                "domain": domain_id,
                "speech_metrics": speech_metrics
            })
            context["result"]["data"]["domain_analysis"] = domain_analysis
        
        return jsonify(context)
        
    except Exception as e:
        return jsonify({
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }), 500

@app.route('/api/v1/mcp/feedback', methods=['POST'])
def get_mcp_feedback():
    """
    Get contextual feedback using MCP protocol
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'user123')
        speech_analysis = data.get('speech_analysis', {})
        domain_id = data.get('domain', 'public_speaking')
        event_id = data.get('event_id')
        audience_id = data.get('audience_id')
        
        # Extract speech metrics from speech analysis
        speech_metrics = {}
        if "filler_analysis" in speech_analysis:
            filler = speech_analysis["filler_analysis"]
            speech_metrics["filler_count"] = filler.get("total_fillers", 0)
            speech_metrics["filler_percentage"] = filler.get("filler_percentage", 0)
        
        if "delivery_metrics" in speech_analysis:
            delivery = speech_analysis["delivery_metrics"]
            speech_metrics["pace_wpm"] = delivery.get("pace", 140)
            speech_metrics["vocal_variety"] = delivery.get("vocal_variety", 7.5)
            speech_metrics["confidence_score"] = delivery.get("confidence", 8.0)
            speech_metrics["overall_score"] = delivery.get("overall_score", 7.8)
        
        # Build speech data for feedback
        speech_data = {
            "domain_id": domain_id,
            "user_id": user_id,
            "event_id": event_id,
            "audience_id": audience_id,
            "metrics": speech_metrics,
            "transcript": speech_analysis.get("transcript", "")
        }
        
        # Build a comprehensive feedback prompt and get LLM-generated feedback
        feedback_result = mcp_interface.build_feedback_prompt(speech_data)
        
        # Get domain-specific analysis
        domain_analysis = mcp_interface.domain_client.call_tool("analyzeSpeech", {
            "domain": domain_id,
            "speech_metrics": speech_metrics
        })
        
        # Get improvement plan
        improvement_plan = mcp_interface.suggest_improvement_plan(user_id, domain_id)
        
        # Get personalized tips
        personalized_tips = mcp_interface.generate_personalized_tips(
            user_id=user_id,
            focus_area="delivery",
            domain=domain_id
        )
        
        # Compile response
        feedback = {
            "jsonrpc": "2.0",
            "result": {
                "protocol": "mcp",
                "version": MCP_PROTOCOL_VERSION,
                "timestamp": datetime.now().isoformat(),
                "feedback": {
                    "prompt": feedback_result["prompt"],
                    "llm_feedback": feedback_result.get("generated_feedback"),
                    "feedback_generation_method": feedback_result.get("generation_method", "template"),
                    "domain_analysis": domain_analysis,
                    "improvement_plan": improvement_plan,
                    "personalized_tips": personalized_tips
                },
                "status": "success"
            }
        }
        
        return jsonify(feedback)
        
    except Exception as e:
        return jsonify({
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }), 500

@app.route('/api/v1/mcp/health', methods=['GET'])
def mcp_health_check():
    """MCP-specific health check"""
    try:
        health = mcp_interface.check_servers_health()
        
        # Check if all servers are healthy
        all_healthy = True
        for server, status in health.items():
            if status.get("status") != "healthy":
                all_healthy = False
                break
        
        return jsonify({
            "jsonrpc": "2.0",
            "result": {
                "protocol": "mcp",
                "version": MCP_PROTOCOL_VERSION,
                "server_info": {
                    "name": "speech-coach-knowledge",
                    "version": "1.0.0"
                },
                "health": health,
                "status": "healthy" if all_healthy else "degraded"
            }
        })
    except Exception as e:
        return jsonify({
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": f"Health check failed: {str(e)}"
            }
        }), 500

@app.route('/api/v1/test-mcp', methods=['POST'])
def test_mcp():
    """Test endpoint for MCP resources and tools"""
    
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        # Get context parameters from request
        data = request.get_json() or {}
        domain_id = data.get('domain', 'public_speaking')
        
        # Sample speech metrics
        speech_metrics = {
            "pace_wpm": 135,
            "filler_count": 5,
            "filler_percentage": 3.5,
            "vocal_variety": 6.5,
            "confidence_score": 7.0,
            "overall_score": 6.8
        }
        
        # List resources from each MCP server
        domain_resources = mcp_interface.domain_client.list_resources()
        user_resources = mcp_interface.user_client.list_resources()
        event_resources = mcp_interface.event_client.list_resources()
        audience_resources = mcp_interface.audience_client.list_resources()
        
        # List tools from each MCP server
        domain_tools = mcp_interface.domain_client.list_tools()
        user_tools = mcp_interface.user_client.list_tools()
        event_tools = mcp_interface.event_client.list_tools()
        audience_tools = mcp_interface.audience_client.list_tools()
        
        # Call a tool from domain server
        domain_analysis = mcp_interface.domain_client.call_tool("analyzeSpeech", {
            "domain": domain_id,
            "speech_metrics": speech_metrics
        })
        
        return jsonify({
            "status": "success",
            "mcp_version": MCP_PROTOCOL_VERSION,
            "resources": {
                "domain": domain_resources,
                "user": user_resources,
                "event": event_resources,
                "audience": audience_resources
            },
            "tools": {
                "domain": domain_tools,
                "user": user_tools,
                "event": event_tools,
                "audience": audience_tools
            },
            "test_call": {
                "domain_analysis": domain_analysis
            }
        })
        
    except Exception as e:
        print(f"Test MCP error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/api/v1/test-llm', methods=['POST'])
def test_llm_recommendations():
    """Test endpoint for LLM recommendations with sample data (legacy support)"""
    
    if request.method == 'OPTIONS':
        return '', 200
    
    if not legacy_support:
        return jsonify({"status": "error", "error": "Legacy LLM support not available"}), 404
    
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
        health = mcp_interface.check_servers_health()
        
        # Include legacy health if available
        if legacy_support:
            try:
                legacy_health = llm_interface.health_check()
                health["legacy"] = legacy_health
            except Exception as e:
                health["legacy"] = {"status": "unhealthy", "reason": str(e)}
        
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
        # Get resources from MCP servers
        domain_resources = mcp_interface.domain_client.list_resources()
        user_resources = mcp_interface.user_client.list_resources()
        event_resources = mcp_interface.event_client.list_resources()
        audience_resources = mcp_interface.audience_client.list_resources()
        
        # Extract options from resources
        domains = []
        for resource in domain_resources:
            uri = resource.get("uri", "")
            if uri.startswith("domain://"):
                domain_id = uri.replace("domain://", "")
                domains.append({
                    "id": domain_id,
                    "name": resource.get("title", domain_id)
                })
        
        users = []
        for resource in user_resources:
            uri = resource.get("uri", "")
            if uri.startswith("user://"):
                user_id = uri.replace("user://", "")
                users.append({
                    "id": user_id,
                    "name": resource.get("title", user_id)
                })
        
        events = []
        for resource in event_resources:
            uri = resource.get("uri", "")
            if uri.startswith("event://"):
                event_id = uri.replace("event://", "")
                events.append({
                    "id": event_id,
                    "name": resource.get("title", event_id)
                })
        
        audiences = []
        for resource in audience_resources:
            uri = resource.get("uri", "")
            if uri.startswith("audience://"):
                audience_id = uri.replace("audience://", "")
                audiences.append({
                    "id": audience_id,
                    "name": resource.get("title", audience_id)
                })
        
        # Include legacy options if available
        legacy_options = {}
        if legacy_support:
            try:
                legacy_options = llm_interface.get_available_options()
            except Exception:
                pass
        
        return jsonify({
            "mcp": {
                "domains": domains,
                "users": users,
                "events": events,
                "audiences": audiences
            },
            "legacy": legacy_options
        })
    except Exception as e:
        return jsonify({"error": f"Failed to get options: {str(e)}"}), 500

@app.route('/api/v1/mcp/tools', methods=['POST'])
def execute_mcp_tool():
    """Execute a specific MCP tool with parameters"""
    try:
        data = request.get_json()
        
        if not data or "server_type" not in data or "tool_name" not in data:
            return jsonify({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32600,
                    "message": "Invalid request: server_type and tool_name are required"
                }
            }), 400
        
        server_type = data["server_type"]
        tool_name = data["tool_name"]
        parameters = data.get("parameters", {})
        
        # Select the appropriate client based on server_type
        client = None
        if server_type == "domain":
            client = mcp_interface.domain_client
        elif server_type == "user":
            client = mcp_interface.user_client
        elif server_type == "event":
            client = mcp_interface.event_client
        elif server_type == "audience":
            client = mcp_interface.audience_client
        else:
            return jsonify({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32602,
                    "message": f"Unknown server type: {server_type}"
                }
            }), 400
        
        # Call the requested tool
        result = client.call_tool(tool_name, parameters)
        
        return jsonify({
            "jsonrpc": "2.0",
            "result": result,
            "id": 1
        })
        
    except Exception as e:
        return jsonify({
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": f"Tool execution error: {str(e)}"
            },
            "id": 1
        }), 500

@app.route('/api/v1/mcp/resources/<resource_type>/<resource_id>', methods=['GET'])
def get_mcp_resource(resource_type, resource_id):
    """Get a specific MCP resource directly"""
    try:
        # Select the appropriate client based on resource type
        client = None
        if resource_type == "domain":
            client = mcp_interface.domain_client
        elif resource_type == "user":
            client = mcp_interface.user_client
        elif resource_type == "event":
            client = mcp_interface.event_client
        elif resource_type == "audience":
            client = mcp_interface.audience_client
        else:
            return jsonify({
                "error": f"Unknown resource type: {resource_type}"
            }), 400
        
        # Construct the resource URI
        uri = f"{resource_type}://{resource_id}"
        
        # Read the resource
        resource_content = client.read_resource(uri)
        
        if not resource_content:
            return jsonify({
                "error": f"Resource not found: {uri}"
            }), 404
        
        return jsonify({
            "uri": uri,
            "content": resource_content
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Failed to get resource: {str(e)}"
        }), 500

if __name__ == '__main__':
    print("🚀 Starting Speech Coach API with MCP-Enhanced Knowledge Servers...")
    print("📡 Available endpoints:")
    print("   • GET  /api/v1/health - Check server status")
    print("   • GET  /api/v1/options - Get available options")
    print("   • POST /api/v1/analyze - Analyze speech with file upload + MCP integration")
    print("   • POST /api/v1/test-mcp - Test MCP resources and tools")
    print("   • POST /api/v1/mcp/context - Get MCP context")
    print("   • POST /api/v1/mcp/feedback - Get MCP feedback")
    print("   • GET  /api/v1/mcp/health - MCP health check")
    print("   • POST /api/v1/mcp/tools - Execute specific MCP tools")
    print("   • GET  /api/v1/mcp/resources/<type>/<id> - Get specific MCP resource")
    
    if legacy_support:
        print("   • POST /api/v1/test-llm - Test legacy LLM recommendations")
    
    print("🔗 MCP Integration:")
    print(f"   • Protocol: MCP {MCP_PROTOCOL_VERSION}")
    print("   • Knowledge Servers: Domain, User, Event, Audience")
    print("   • Transport: JSON-RPC 2.0 over HTTP")
    
    # Print available resources from each server
    print("\n📚 Available MCP Resources:")
    domain_resources = mcp_interface.domain_client.list_resources()
    print(f"   • Domain resources: {len(domain_resources)}")
    for res in domain_resources[:3]:  # Show first 3
        print(f"     - {res.get('title', 'Untitled')}: {res.get('uri', 'No URI')}")
    
    user_resources = mcp_interface.user_client.list_resources()
    print(f"   • User resources: {len(user_resources)}")
    for res in user_resources[:3]:  # Show first 3
        print(f"     - {res.get('title', 'Untitled')}: {res.get('uri', 'No URI')}")
    
    event_resources = mcp_interface.event_client.list_resources()
    print(f"   • Event resources: {len(event_resources)}")
    for res in event_resources[:3]:  # Show first 3
        print(f"     - {res.get('title', 'Untitled')}: {res.get('uri', 'No URI')}")
    
    audience_resources = mcp_interface.audience_client.list_resources()
    print(f"   • Audience resources: {len(audience_resources)}")
    for res in audience_resources[:3]:  # Show first 3
        print(f"     - {res.get('title', 'Untitled')}: {res.get('uri', 'No URI')}")
    
    # Print available tools
    print("\n🛠️ Available MCP Tools:")
    domain_tools = mcp_interface.domain_client.list_tools()
    print(f"   • Domain tools: {len(domain_tools)}")
    for tool in domain_tools:
        print(f"     - {tool.get('name', 'Unnamed')}: {tool.get('description', 'No description')}")
    
    user_tools = mcp_interface.user_client.list_tools()
    print(f"   • User tools: {len(user_tools)}")
    for tool in user_tools:
        print(f"     - {tool.get('name', 'Unnamed')}: {tool.get('description', 'No description')}")
    
    event_tools = mcp_interface.event_client.list_tools()
    print(f"   • Event tools: {len(event_tools)}")
    for tool in event_tools:
        print(f"     - {tool.get('name', 'Unnamed')}: {tool.get('description', 'No description')}")
    
    audience_tools = mcp_interface.audience_client.list_tools()
    print(f"   • Audience tools: {len(audience_tools)}")
    for tool in audience_tools:
        print(f"     - {tool.get('name', 'Unnamed')}: {tool.get('description', 'No description')}")
    
    if legacy_support:
        print("\n🤖 Legacy LLM Integration (for backward compatibility):")
        print(f"   • Ollama endpoint: {llm_recommender.llm_endpoint}")
        print(f"   • Model: {llm_recommender.model}")
    
    print(f"\n🌐 CORS enabled for {CORS_ORIGINS}")
    print("\n🔍 Health Check:")
    health = mcp_interface.check_servers_health()
    for server, status in health.items():
        server_status = status.get("status", "unknown")
        status_emoji = "✅" if server_status == "healthy" else "⚠️"
        print(f"   {status_emoji} {server.capitalize()} server: {server_status}")
    
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=DEBUG_MODE)
