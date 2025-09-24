#!/usr/bin/env python3
"""
MCP Client for Speech Coach
Provides a unified client to communicate with MCP-compliant knowledge servers
"""

import json
import logging
import requests
from typing import Dict, Any, List, Optional, Union, Callable
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPClient:
    """
    MCP Client for communicating with MCP-compliant knowledge servers
    Implements the Model Context Protocol to standardize interactions
    """
    
    def __init__(self, server_instance=None, server_url=None):
        """
        Initialize the MCP Client with either a direct server instance or a remote URL
        
        Args:
            server_instance: A local MCP server instance (for in-process communication)
            server_url: URL of a remote MCP server (for HTTP communication)
        """
        if server_instance and server_url:
            raise ValueError("Cannot specify both server_instance and server_url")
        
        self.server_instance = server_instance
        self.server_url = server_url
        self.protocol_version = "1.0"
        self._resources_cache = None
        self._resource_templates_cache = None
        self._tools_cache = None
        self._prompts_cache = None
        
        logger.info(f"MCP Client initialized, protocol v{self.protocol_version}")
    
    def _send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Send a request to the MCP server
        
        Args:
            method: The MCP method name (e.g., "resources/list")
            params: The parameters for the method
            
        Returns:
            MCP response dictionary
        """
        if params is None:
            params = {}
        
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1  # Simple ID for now
        }
        
        try:
            if self.server_instance:
                # Direct in-process communication
                response = self.server_instance.handle_request(method, params)
                return response
            elif self.server_url:
                # HTTP communication
                headers = {"Content-Type": "application/json"}
                response = requests.post(self.server_url, json=request, headers=headers)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    error_msg = f"HTTP Error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    return {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32000,
                            "message": error_msg
                        },
                        "id": 1
                    }
            else:
                error_msg = "No server instance or URL provided"
                logger.error(error_msg)
                return {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32000,
                        "message": error_msg
                    },
                    "id": 1
                }
        except Exception as e:
            error_msg = f"Error sending request: {str(e)}"
            logger.error(error_msg)
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32000,
                    "message": error_msg
                },
                "id": 1
            }
    
    def list_resources(self) -> List[Dict[str, Any]]:
        """
        List all available resources from the MCP server
        
        Returns:
            List of resource dictionaries
        """
        if self._resources_cache is None:
            response = self._send_request("resources/list")
            
            if "result" in response:
                self._resources_cache = response["result"].get("resources", [])
            else:
                error_msg = response.get("error", {}).get("message", "Unknown error")
                logger.error(f"Error listing resources: {error_msg}")
                self._resources_cache = []
        
        return self._resources_cache
    
    def list_resource_templates(self) -> List[Dict[str, Any]]:
        """
        List all available resource templates from the MCP server
        
        Returns:
            List of resource template dictionaries
        """
        if self._resource_templates_cache is None:
            response = self._send_request("resources/templates/list")
            
            if "result" in response:
                self._resource_templates_cache = response["result"].get("resourceTemplates", [])
            else:
                error_msg = response.get("error", {}).get("message", "Unknown error")
                logger.error(f"Error listing resource templates: {error_msg}")
                self._resource_templates_cache = []
        
        return self._resource_templates_cache
    
    def read_resource(self, uri: str) -> Dict[str, Any]:
        """
        Read a specific resource from the MCP server
        
        Args:
            uri: The resource URI to read
            
        Returns:
            Resource content dictionary
        """
        response = self._send_request("resources/read", {"uri": uri})
        
        if "result" in response:
            return response["result"].get("content", {})
        else:
            error_msg = response.get("error", {}).get("message", "Unknown error")
            logger.error(f"Error reading resource {uri}: {error_msg}")
            return {}
    
    def resolve_template_uri(self, template_name: str, **kwargs) -> str:
        """
        Resolve a resource template URI with parameters
        
        Args:
            template_name: The name of the template to resolve
            **kwargs: Parameters to substitute in the template
            
        Returns:
            The resolved URI string
        """
        templates = self.list_resource_templates()
        matching_template = None
        
        for template in templates:
            if template.get("name") == template_name:
                matching_template = template
                break
        
        if matching_template is None:
            logger.error(f"Template not found: {template_name}")
            return ""
        
        uri_template = matching_template.get("uriTemplate", "")
        
        # Simple template substitution
        for key, value in kwargs.items():
            placeholder = f"{{{key}}}"
            if placeholder in uri_template:
                uri_template = uri_template.replace(placeholder, str(value))
        
        return uri_template
    
    def read_template_resource(self, template_name: str, **kwargs) -> Dict[str, Any]:
        """
        Read a resource using a template
        
        Args:
            template_name: The name of the template to use
            **kwargs: Parameters for the template
            
        Returns:
            Resource content dictionary
        """
        uri = self.resolve_template_uri(template_name, **kwargs)
        if uri:
            return self.read_resource(uri)
        else:
            return {}
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all available tools from the MCP server
        
        Returns:
            List of tool dictionaries
        """
        if self._tools_cache is None:
            response = self._send_request("tools/list")
            
            if "result" in response:
                self._tools_cache = response["result"].get("tools", [])
            else:
                error_msg = response.get("error", {}).get("message", "Unknown error")
                logger.error(f"Error listing tools: {error_msg}")
                self._tools_cache = []
        
        return self._tools_cache
    
    def call_tool(self, tool_name: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Call a tool on the MCP server
        
        Args:
            tool_name: Name of the tool to call
            parameters: Parameters for the tool
            
        Returns:
            Tool result dictionary
        """
        if parameters is None:
            parameters = {}
            
        response = self._send_request("tools/call", {
            "name": tool_name,
            "parameters": parameters
        })
        
        if "result" in response:
            return response["result"]
        else:
            error_msg = response.get("error", {}).get("message", "Unknown error")
            logger.error(f"Error calling tool {tool_name}: {error_msg}")
            return {}
    
    def list_prompts(self) -> List[Dict[str, Any]]:
        """
        List all available prompts from the MCP server
        
        Returns:
            List of prompt dictionaries
        """
        if self._prompts_cache is None:
            response = self._send_request("prompts/list")
            
            if "result" in response:
                self._prompts_cache = response["result"].get("prompts", [])
            else:
                error_msg = response.get("error", {}).get("message", "Unknown error")
                logger.error(f"Error listing prompts: {error_msg}")
                self._prompts_cache = []
        
        return self._prompts_cache
    
    def get_prompt(self, prompt_name: str) -> Dict[str, Any]:
        """
        Get a specific prompt from the MCP server
        
        Args:
            prompt_name: Name of the prompt to get
            
        Returns:
            Prompt dictionary
        """
        response = self._send_request("prompts/get", {"name": prompt_name})
        
        if "result" in response:
            return response["result"]
        else:
            error_msg = response.get("error", {}).get("message", "Unknown error")
            logger.error(f"Error getting prompt {prompt_name}: {error_msg}")
            return {}
    
    def render_prompt(self, prompt_name: str, **kwargs) -> str:
        """
        Render a prompt with parameters
        
        Args:
            prompt_name: Name of the prompt to render
            **kwargs: Parameters for the prompt
            
        Returns:
            Rendered prompt string
        """
        prompt = self.get_prompt(prompt_name)
        if not prompt:
            return ""
        
        template = prompt.get("template", "")
        
        # Handle simple substitution ({{param}})
        for key, value in kwargs.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in template:
                template = template.replace(placeholder, str(value))
        
        # Handle conditional sections ({{#param}}content{{/param}})
        for key, value in kwargs.items():
            start_tag = f"{{{{#{key}}}}}"
            end_tag = f"{{{{/{key}}}}}"
            
            if start_tag in template and end_tag in template:
                start_idx = template.find(start_tag)
                end_idx = template.find(end_tag) + len(end_tag)
                
                if start_idx >= 0 and end_idx > start_idx:
                    section = template[start_idx:end_idx]
                    content = section[len(start_tag):template.find(end_tag, start_idx)]
                    
                    if value:
                        # Include the content without the tags
                        template = template.replace(section, content)
                    else:
                        # Remove the entire section
                        template = template.replace(section, "")
        
        return template
    
    def clear_cache(self):
        """Clear all cached data"""
        self._resources_cache = None
        self._resource_templates_cache = None
        self._tools_cache = None
        self._prompts_cache = None
        logger.info("MCP Client cache cleared")
    
    def health_check(self) -> Dict[str, str]:
        """
        Check the health status of the MCP server
        
        Returns:
            Health status dictionary
        """
        try:
            if self.server_instance:
                return self.server_instance.health_check()
            elif self.server_url:
                health_url = f"{self.server_url.rstrip('/')}/health"
                response = requests.get(health_url)
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"status": "unhealthy", "reason": f"HTTP Error: {response.status_code}"}
            else:
                return {"status": "unhealthy", "reason": "No server instance or URL provided"}
        except Exception as e:
            return {"status": "unhealthy", "reason": str(e)}


class MCPKnowledgeInterface:
    """
    Unified interface for accessing multiple MCP knowledge servers
    Combines different knowledge sources through MCP protocol
    """
    
    def __init__(self):
        """Initialize the MCP Knowledge Interface"""
        self.domain_client = None
        self.user_client = None
        self.event_client = None
        self.audience_client = None
        logger.info("MCP Knowledge Interface initialized")
    
    def initialize_servers(self, servers_config: Dict[str, Any]):
        """
        Initialize connections to MCP servers
        
        Args:
            servers_config: Configuration for MCP servers
        """
        # Initialize with direct server instances if provided
        if "domain_server" in servers_config:
            self.domain_client = MCPClient(server_instance=servers_config["domain_server"])
            logger.info("Domain knowledge server connected (direct)")
        elif "domain_server_url" in servers_config:
            self.domain_client = MCPClient(server_url=servers_config["domain_server_url"])
            logger.info(f"Domain knowledge server connected at {servers_config['domain_server_url']}")
        
        if "user_server" in servers_config:
            self.user_client = MCPClient(server_instance=servers_config["user_server"])
            logger.info("User knowledge server connected (direct)")
        elif "user_server_url" in servers_config:
            self.user_client = MCPClient(server_url=servers_config["user_server_url"])
            logger.info(f"User knowledge server connected at {servers_config['user_server_url']}")
        
        if "event_server" in servers_config:
            self.event_client = MCPClient(server_instance=servers_config["event_server"])
            logger.info("Event knowledge server connected (direct)")
        elif "event_server_url" in servers_config:
            self.event_client = MCPClient(server_url=servers_config["event_server_url"])
            logger.info(f"Event knowledge server connected at {servers_config['event_server_url']}")
        
        if "audience_server" in servers_config:
            self.audience_client = MCPClient(server_instance=servers_config["audience_server"])
            logger.info("Audience knowledge server connected (direct)")
        elif "audience_server_url" in servers_config:
            self.audience_client = MCPClient(server_url=servers_config["audience_server_url"])
            logger.info(f"Audience knowledge server connected at {servers_config['audience_server_url']}")
    
    def get_domain_knowledge(self, domain_id: str) -> Dict[str, Any]:
        """
        Get domain-specific speaking knowledge
        
        Args:
            domain_id: Domain identifier (e.g., "technical", "corporate")
            
        Returns:
            Domain knowledge dictionary
        """
        if not self.domain_client:
            logger.warning("Domain knowledge server not connected")
            return {}
        
        return self.domain_client.read_resource(f"domain://{domain_id}")
    
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Get user profile and speaking history
        
        Args:
            user_id: User identifier
            
        Returns:
            User profile dictionary
        """
        if not self.user_client:
            logger.warning("User knowledge server not connected")
            return {}
        
        return self.user_client.read_resource(f"user://{user_id}")
    
    def get_event_guidelines(self, event_id: str) -> Dict[str, Any]:
        """
        Get event-specific speaking guidelines
        
        Args:
            event_id: Event type identifier
            
        Returns:
            Event guidelines dictionary
        """
        if not self.event_client:
            logger.warning("Event knowledge server not connected")
            return {}
        
        return self.event_client.read_resource(f"event://{event_id}")
    
    def get_audience_insights(self, audience_id: str) -> Dict[str, Any]:
        """
        Get audience-specific insights and recommendations
        
        Args:
            audience_id: Audience type identifier
            
        Returns:
            Audience insights dictionary
        """
        if not self.audience_client:
            logger.warning("Audience knowledge server not connected")
            return {}
        
        return self.audience_client.read_resource(f"audience://{audience_id}")
    
    def analyze_speech_for_domain(self, domain_id: str, speech_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze speech metrics against domain-specific expectations
        
        Args:
            domain_id: Domain identifier
            speech_metrics: Dictionary of speech metrics
            
        Returns:
            Analysis results dictionary
        """
        if not self.domain_client:
            logger.warning("Domain knowledge server not connected")
            return {}
        
        return self.domain_client.call_tool("analyzeSpeech", {
            "domain": domain_id,
            "speech_metrics": speech_metrics
        })
    
    def analyze_audience_match(self, audience_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze audience based on provided characteristics
        
        Args:
            audience_params: Dictionary of audience parameters
            
        Returns:
            Audience analysis dictionary
        """
        if not self.audience_client:
            logger.warning("Audience knowledge server not connected")
            return {}
        
        return self.audience_client.call_tool("analyzeAudience", audience_params)
    
    def track_user_improvement(self, user_id: str, metric: str) -> Dict[str, Any]:
        """
        Track user improvement in a specific speaking metric
        
        Args:
            user_id: User identifier
            metric: Metric to track (e.g., "pace", "filler_words")
            
        Returns:
            Improvement tracking dictionary
        """
        if not self.user_client:
            logger.warning("User knowledge server not connected")
            return {}
        
        return self.user_client.call_tool("trackImprovement", {
            "user_id": user_id,
            "metric": metric
        })
    
    def get_comprehensive_feedback_context(self, speech_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get comprehensive context for generating feedback
        
        Args:
            speech_data: Dictionary with speech analysis data
            
        Returns:
            Comprehensive context dictionary
        """
        context = {}
        
        # Extract identifiers from speech data
        domain_id = speech_data.get("domain_id", "")
        user_id = speech_data.get("user_id", "")
        event_id = speech_data.get("event_id", "")
        audience_id = speech_data.get("audience_id", "")
        
        # Gather domain knowledge
        if domain_id and self.domain_client:
            domain_knowledge = self.get_domain_knowledge(domain_id)
            domain_analysis = self.analyze_speech_for_domain(
                domain_id, 
                speech_data.get("metrics", {})
            )
            context["domain"] = {
                "knowledge": domain_knowledge,
                "analysis": domain_analysis
            }
        
        # Gather user knowledge
        if user_id and self.user_client:
            user_profile = self.get_user_profile(user_id)
            context["user"] = {
                "profile": user_profile
            }
        
        # Gather event knowledge
        if event_id and self.event_client:
            event_guidelines = self.get_event_guidelines(event_id)
            context["event"] = {
                "guidelines": event_guidelines
            }
        
        # Gather audience knowledge
        if audience_id and self.audience_client:
            audience_insights = self.get_audience_insights(audience_id)
            context["audience"] = {
                "insights": audience_insights
            }
        
        return context
    
    def generate_personalized_tips(self, user_id: str, focus_area: str = None, domain: str = None) -> Dict[str, Any]:
        """
        Generate personalized speaking tips for a user
        
        Args:
            user_id: User identifier
            focus_area: Area to focus tips on (optional)
            domain: Speaking domain to consider (optional)
            
        Returns:
            Personalized tips dictionary
        """
        if not self.user_client:
            logger.warning("User knowledge server not connected")
            return {}
        
        params = {"user_id": user_id}
        if focus_area:
            params["focus_area"] = focus_area
        if domain:
            params["domain"] = domain
        
        return self.user_client.call_tool("getPersonalizedTips", params)
    
    def suggest_improvement_plan(self, user_id: str, domain_id: str) -> Dict[str, Any]:
        """
        Generate a domain-specific improvement plan for a user
        
        Args:
            user_id: User identifier
            domain_id: Domain identifier
            
        Returns:
            Improvement plan dictionary
        """
        if not self.domain_client or not self.user_client:
            logger.warning("Required knowledge servers not connected")
            return {}
        
        # Get user profile to determine skill level
        user_profile = self.get_user_profile(user_id)
        skill_level = user_profile.get("skill_level", "intermediate")
        
        # Get areas needing improvement from user profile
        improvement_areas = user_profile.get("improvement_areas", ["delivery", "structure"])
        
        # Generate improvement plan from domain knowledge server
        return self.domain_client.call_tool("generateImprovementPlan", {
            "domain": domain_id,
            "skill_level": skill_level,
            "improvement_areas": improvement_areas
        })
    
    def build_feedback_prompt(self, speech_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a comprehensive prompt for generating feedback and optionally generate LLM response
        
        Args:
            speech_data: Dictionary with speech analysis data
            
        Returns:
            Dictionary with prompt and optionally LLM-generated feedback
        """
        context = self.get_comprehensive_feedback_context(speech_data)
        prompt_parts = []
        
        # Add domain-specific part
        if "domain" in context:
            domain_name = context["domain"]["knowledge"].get("name", "this domain")
            prompt_parts.append(f"For a {domain_name} presentation:")
            
            # Add analysis insights
            if "analysis" in context["domain"]:
                analysis = context["domain"]["analysis"]
                if "overall_score" in analysis:
                    prompt_parts.append(f"- Overall score: {analysis['overall_score']}/100")
                if "detailed_analysis" in analysis:
                    for key, details in analysis["detailed_analysis"].items():
                        if "evaluation" in details:
                            prompt_parts.append(f"- {key.replace('_', ' ').title()}: {details['evaluation']}")
        
        # Add user-specific part
        if "user" in context and "profile" in context["user"]:
            profile = context["user"]["profile"]
            name = profile.get("name", "the speaker")
            skill_level = profile.get("skill_level", "intermediate")
            prompt_parts.append(f"\nFor {name}, a {skill_level} speaker:")
            
            # Add strengths and weaknesses if available
            if "strengths" in profile:
                strengths = profile["strengths"][:3] if len(profile["strengths"]) > 3 else profile["strengths"]
                prompt_parts.append(f"- Strengths: {', '.join(strengths)}")
            if "improvement_areas" in profile:
                improvements = profile["improvement_areas"][:3] if len(profile["improvement_areas"]) > 3 else profile["improvement_areas"]
                prompt_parts.append(f"- Areas to improve: {', '.join(improvements)}")
        
        # Add event-specific part if available
        if "event" in context and "guidelines" in context["event"]:
            guidelines = context["event"]["guidelines"]
            event_name = guidelines.get("name", "this event type")
            prompt_parts.append(f"\nFor a {event_name}:")
            
            # Add key requirements if available
            if "requirements" in guidelines:
                req = guidelines["requirements"]
                if isinstance(req, dict) and len(req) > 0:
                    prompt_parts.append("- Key requirements:")
                    for key, value in list(req.items())[:3]:
                        prompt_parts.append(f"  - {key}: {value}")
                elif isinstance(req, list) and len(req) > 0:
                    prompt_parts.append(f"- Key requirements: {', '.join(req[:3])}")
        
        # Add audience-specific part if available
        if "audience" in context and "insights" in context["audience"]:
            insights = context["audience"]["insights"]
            audience_name = insights.get("name", "this audience type")
            prompt_parts.append(f"\nFor a {audience_name} audience:")
            
            # Add preferences if available
            if "preferences" in insights:
                pref = insights["preferences"]
                if isinstance(pref, dict) and len(pref) > 0:
                    prompt_parts.append("- Audience preferences:")
                    for key, value in list(pref.items())[:3]:
                        prompt_parts.append(f"  - {key}: {value}")
        
        # Add analysis data
        metrics = speech_data.get("metrics", {})
        prompt_parts.append("\nSpeech metrics:")
        for key, value in metrics.items():
            prompt_parts.append(f"- {key}: {value}")
        
        # Add specific instructions
        prompt_parts.append("\nBased on this context, provide:")
        prompt_parts.append("1. A concise assessment of the speech performance")
        prompt_parts.append("2. Three specific strengths with examples")
        prompt_parts.append("3. Three specific areas for improvement with actionable advice")
        prompt_parts.append("4. A personalized practice suggestion")
        
        prompt_text = "\n".join(prompt_parts)
        
        # Create response with at minimum the prompt
        response = {
            "prompt": prompt_text,
            "generated_feedback": None,
            "generation_method": "template"
        }
        
        # Try to generate LLM feedback if possible
        try:
            # Try to import LLM tools on-demand
            from utils.llm_recommendations import LLMRecommendationGenerator
            llm_recommender = LLMRecommendationGenerator()
            
            # Create a simplified speech analysis object for LLM
            speech_analysis = {
                "transcript": speech_data.get("transcript", ""),
                "word_count": speech_data.get("word_count", 100),
                "fillers": {
                    "total_fillers": metrics.get("filler_count", 0),
                    "filler_percentage": metrics.get("filler_percentage", 0)
                },
                "delivery_metrics": {
                    "pace": metrics.get("pace_wpm", 140),
                    "vocal_variety": metrics.get("vocal_variety", 7.5),
                    "confidence": metrics.get("confidence_score", 7.0),
                    "overall_score": metrics.get("overall_score", 7.0)
                }
            }
            
            # Get domain, user, event, and audience contexts
            domain_context = context.get("domain", {}).get("knowledge", {}) if "domain" in context else None
            user_context = context.get("user", {}).get("profile", {}) if "user" in context else None
            event_context = context.get("event", {}).get("guidelines", {}) if "event" in context else None
            audience_context = context.get("audience", {}).get("insights", {}) if "audience" in context else None
            
            # Generate LLM feedback
            llm_feedback = llm_recommender.generate_contextual_recommendations(
                speech_analysis=speech_analysis,
                domain_context=domain_context,
                user_context=user_context,
                event_context=event_context,
                audience_context=audience_context
            )
            
            # Add LLM-generated feedback to response
            response["generated_feedback"] = llm_feedback
            response["generation_method"] = "llm"
            
            logger.info("Successfully generated LLM feedback")
            
        except ImportError:
            logger.warning("LLM tools not available for feedback generation")
        except Exception as e:
            logger.error(f"Error generating LLM feedback: {str(e)}")
        
        return response
    
    def check_servers_health(self) -> Dict[str, Dict[str, str]]:
        """
        Check the health status of all connected MCP servers
        
        Returns:
            Dictionary with health status for each server
        """
        health = {}
        
        if self.domain_client:
            health["domain"] = self.domain_client.health_check()
        
        if self.user_client:
            health["user"] = self.user_client.health_check()
        
        if self.event_client:
            health["event"] = self.event_client.health_check()
        
        if self.audience_client:
            health["audience"] = self.audience_client.health_check()
        
        return health

# For testing purposes
if __name__ == "__main__":
    # Example usage of MCPClient
    from domain_server_mcp import DomainKnowledgeMCPServer
    
    # Create an MCP server instance
    domain_server = DomainKnowledgeMCPServer()
    
    # Create an MCP client connected to the server
    client = MCPClient(server_instance=domain_server)
    
    # List resources
    print("=== MCP Resources ===")
    resources = client.list_resources()
    for resource in resources:
        print(f"- {resource.get('title')}: {resource.get('uri')}")
    
    # Call a tool
    print("\n=== Tool Call Result ===")
    result = client.call_tool("analyzeSpeech", {
        "domain": "corporate",
        "speech_metrics": {
            "pace_wpm": 140,
            "filler_words_count": 5
        }
    })
    print(json.dumps(result, indent=2))
