#!/usr/bin/env python3
"""
MCP-compliant Domain Knowledge Server for Speech Coach
Provides domain-specific speaking guidelines via MCP protocol
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DomainKnowledgeMCPServer:
    """
    MCP-compliant Domain Knowledge Server that provides speaking guidelines
    and best practices for different domains.
    """
    
    def __init__(self):
        """Initialize the Domain Knowledge Server with MCP capabilities"""
        self.knowledge_base = self._load_domain_knowledge()
        self.protocol_version = "1.0"
        self.server_name = "domain-knowledge-server"
        self.server_version = "1.0.0"
        
        # Initialize LLM integration
        try:
            from utils.llm_recommendations import LLMRecommendationGenerator
            self.llm_recommender = LLMRecommendationGenerator()
            self.llm_enabled = True
            logger.info(f"MCP Domain Knowledge Server initialized with LLM support, protocol v{self.protocol_version}")
        except ImportError:
            self.llm_enabled = False
            logger.warning(f"MCP Domain Knowledge Server initialized without LLM support, protocol v{self.protocol_version}")

    def _load_domain_knowledge(self) -> Dict[str, Any]:
        """Load domain knowledge from JSON resource"""
        try:
            resource_path = os.path.join(os.path.dirname(__file__), 'resources', 'domain_knowledge.json')
            with open(resource_path, 'r') as f:
                knowledge = json.load(f)
            logger.info(f"Domain knowledge loaded successfully with {len(knowledge.get('domains', {}))} domains")
            return knowledge
        except Exception as e:
            logger.error(f"Error loading domain knowledge: {e}")
            # Fallback to empty knowledge base
            return {"domains": {}, "available_focus_areas": []}

    # MCP Resource Methods
    def list_resources(self) -> Dict[str, Any]:
        """MCP resources/list endpoint implementation"""
        resources = []
        
        # Add direct resources for each domain
        for domain_id, domain_data in self.knowledge_base.get("domains", {}).items():
            resources.append({
                "uri": f"domain://{domain_id}",
                "name": f"{domain_id}-knowledge",
                "title": f"{domain_data.get('name', domain_id.title())} Knowledge",
                "description": f"Speaking guidelines and best practices for {domain_data.get('name', domain_id.title())}",
                "mimeType": "application/json"
            })
        
        # Add resource for listing all available domains
        resources.append({
            "uri": "domain://available-domains",
            "name": "available-domains",
            "title": "Available Speaking Domains",
            "description": "List of all available speaking domains and their descriptions",
            "mimeType": "application/json"
        })
        
        return {
            "jsonrpc": "2.0",
            "result": {
                "protocol": "mcp",
                "version": self.protocol_version,
                "resources": resources
            }
        }
    
    def list_resource_templates(self) -> Dict[str, Any]:
        """MCP resources/templates/list endpoint implementation"""
        templates = [
            {
                "uriTemplate": "domain://{domain_id}/focus/{focus_area}",
                "name": "domain-focus-area",
                "title": "Domain Specific Focus Area",
                "description": "Guidelines for a specific focus area within a speaking domain",
                "mimeType": "application/json",
                "parameters": [
                    {
                        "name": "domain_id",
                        "description": "Speaking domain identifier",
                        "required": True,
                        "schema": {"type": "string", "enum": list(self.knowledge_base.get("domains", {}).keys())}
                    },
                    {
                        "name": "focus_area",
                        "description": "Specific aspect of speaking to focus on",
                        "required": True,
                        "schema": {"type": "string", "enum": self.knowledge_base.get("available_focus_areas", [])}
                    }
                ]
            },
            {
                "uriTemplate": "domain://analysis/{domain_id}",
                "name": "domain-analysis",
                "title": "Domain Speech Analysis",
                "description": "Analyze speech metrics against domain-specific expectations",
                "mimeType": "application/json",
                "parameters": [
                    {
                        "name": "domain_id",
                        "description": "Speaking domain identifier",
                        "required": True,
                        "schema": {"type": "string", "enum": list(self.knowledge_base.get("domains", {}).keys())}
                    }
                ]
            }
        ]
        
        return {
            "jsonrpc": "2.0",
            "result": {
                "protocol": "mcp",
                "version": self.protocol_version,
                "resourceTemplates": templates
            }
        }
    
    def read_resource(self, uri: str) -> Dict[str, Any]:
        """MCP resources/read endpoint implementation"""
        try:
            # Handle direct domain resources
            if uri.startswith("domain://") and not uri.endswith("available-domains"):
                domain_id = uri.split("//")[1]
                if domain_id in self.knowledge_base.get("domains", {}):
                    domain_data = self.knowledge_base["domains"][domain_id]
                    return {
                        "jsonrpc": "2.0",
                        "result": {
                            "uri": uri,
                            "mimeType": "application/json",
                            "content": domain_data
                        }
                    }
            
            # Handle available domains resource
            elif uri == "domain://available-domains":
                domains_list = {
                    domain_id: {
                        "name": domain_data.get("name", domain_id),
                        "description": f"Guidelines for {domain_data.get('name', domain_id)} presentations"
                    }
                    for domain_id, domain_data in self.knowledge_base.get("domains", {}).items()
                }
                
                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "uri": uri,
                        "mimeType": "application/json",
                        "content": {
                            "available_domains": domains_list,
                            "count": len(domains_list)
                        }
                    }
                }
            
            # Handle domain focus area template
            elif "/focus/" in uri:
                parts = uri.replace("domain://", "").split("/focus/")
                if len(parts) == 2:
                    domain_id, focus_area = parts
                    if domain_id in self.knowledge_base.get("domains", {}):
                        domain_data = self.knowledge_base["domains"][domain_id]
                        
                        # Extract focus area content
                        if focus_area == "structure" and "structure" in domain_data:
                            content = {
                                "domain": domain_data.get("name", domain_id),
                                "focus": "structure",
                                "guidelines": domain_data["structure"]
                            }
                        elif focus_area == "delivery" and "delivery" in domain_data:
                            content = {
                                "domain": domain_data.get("name", domain_id),
                                "focus": "delivery", 
                                "guidelines": domain_data["delivery"]
                            }
                        elif focus_area == "best_practices" and "best_practices" in domain_data:
                            content = {
                                "domain": domain_data.get("name", domain_id),
                                "focus": "best_practices",
                                "practices": domain_data["best_practices"]
                            }
                        elif focus_area == "common_mistakes" and "common_mistakes" in domain_data:
                            content = {
                                "domain": domain_data.get("name", domain_id),
                                "focus": "common_mistakes",
                                "mistakes": domain_data["common_mistakes"]
                            }
                        elif focus_area == "all":
                            content = {
                                "domain": domain_data.get("name", domain_id),
                                "guidelines": domain_data
                            }
                        else:
                            return self._error_response("Invalid focus area")
                        
                        return {
                            "jsonrpc": "2.0",
                            "result": {
                                "uri": uri,
                                "mimeType": "application/json",
                                "content": content
                            }
                        }
            
            # Handle domain analysis template
            elif uri.startswith("domain://analysis/"):
                domain_id = uri.split("/")[-1]
                if domain_id in self.knowledge_base.get("domains", {}):
                    domain_data = self.knowledge_base["domains"][domain_id]
                    
                    # Provide analysis guidelines for this domain
                    analysis_guidelines = {
                        "domain": domain_data.get("name", domain_id),
                        "analysis_guidelines": {
                            "pace": self._get_target_pace_for_domain(domain_id),
                            "filler_tolerance": self._get_filler_tolerance_for_domain(domain_id),
                            "key_metrics": ["pace", "filler_words", "vocal_variety", "confidence"],
                            "domain_specific_expectations": domain_data
                        }
                    }
                    
                    return {
                        "jsonrpc": "2.0",
                        "result": {
                            "uri": uri,
                            "mimeType": "application/json",
                            "content": analysis_guidelines
                        }
                    }
            
            # Resource not found
            return self._error_response("Resource not found", -32001)
            
        except Exception as e:
            logger.error(f"Error reading resource {uri}: {e}")
            return self._error_response(f"Error reading resource: {str(e)}")
    
    # MCP Tool Methods
    def list_tools(self) -> Dict[str, Any]:
        """MCP tools/list endpoint implementation"""
        tools = [
            {
                "name": "analyzeSpeech",
                "description": "Analyze speech metrics against domain-specific criteria",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "domain": {
                            "type": "string", 
                            "description": "Speaking domain for analysis",
                            "enum": list(self.knowledge_base.get("domains", {}).keys())
                        },
                        "speech_metrics": {
                            "type": "object",
                            "description": "Speech analysis metrics",
                            "properties": {
                                "pace_wpm": {"type": "number", "description": "Speaking pace in words per minute"},
                                "filler_words_count": {"type": "number", "description": "Number of filler words used"},
                                "vocal_variety_score": {"type": "number", "description": "Vocal variety score (0-10)"},
                                "confidence_score": {"type": "number", "description": "Confidence score (0-10)"}
                            },
                            "required": ["pace_wpm"]
                        }
                    },
                    "required": ["domain", "speech_metrics"]
                }
            },
            {
                "name": "generateImprovementPlan",
                "description": "Generate domain-specific improvement plan based on skill level",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "domain": {
                            "type": "string", 
                            "description": "Speaking domain for improvement plan",
                            "enum": list(self.knowledge_base.get("domains", {}).keys())
                        },
                        "skill_level": {
                            "type": "string",
                            "description": "Speaker's skill level",
                            "enum": ["beginner", "intermediate", "advanced", "expert"]
                        },
                        "improvement_areas": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Areas to focus improvement on"
                        }
                    },
                    "required": ["domain", "skill_level"]
                }
            },
            {
                "name": "compareDomains",
                "description": "Compare guidelines across different speaking domains",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "domains": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of domains to compare",
                            "minItems": 1
                        },
                        "aspect": {
                            "type": "string",
                            "description": "Aspect to compare across domains",
                            "enum": self.knowledge_base.get("available_focus_areas", [])
                        }
                    },
                    "required": ["domains"]
                }
            }
        ]
        
        return {
            "jsonrpc": "2.0",
            "result": {
                "protocol": "mcp",
                "version": self.protocol_version,
                "tools": tools
            }
        }
    
    def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """MCP tools/call endpoint implementation"""
        try:
            if tool_name == "analyzeSpeech":
                return self._analyze_speech_tool(parameters)
            elif tool_name == "generateImprovementPlan":
                return self._generate_improvement_plan_tool(parameters)
            elif tool_name == "compareDomains":
                return self._compare_domains_tool(parameters)
            else:
                return self._error_response(f"Unknown tool: {tool_name}", -32601)
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return self._error_response(f"Error calling tool: {str(e)}")
    
    def _analyze_speech_tool(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Implementation of analyzeSpeech tool"""
        domain = parameters.get("domain")
        speech_metrics = parameters.get("speech_metrics", {})
        
        if not domain or domain not in self.knowledge_base.get("domains", {}):
            return self._error_response("Invalid domain")
        
        domain_data = self.knowledge_base["domains"][domain]
        
        analysis = {
            "domain": domain_data.get("name", domain),
            "domain_id": domain,
            "analysis_timestamp": datetime.now().isoformat(),
            "overall_score": 0,
            "detailed_analysis": {},
            "domain_specific_recommendations": []
        }
        
        # Analyze pace against domain expectations
        pace_wpm = speech_metrics.get("pace_wpm", 0)
        target_pace = self._get_target_pace_for_domain(domain)
        
        pace_score = max(0, 100 - abs(pace_wpm - target_pace) * 2)
        analysis["detailed_analysis"]["pace"] = {
            "score": pace_score,
            "target_wpm": target_pace,
            "actual_wpm": pace_wpm,
            "domain_expectation": domain_data.get("delivery", {}).get("pace", "Not specified"),
            "evaluation": "Good pace" if pace_score > 80 else "Needs adjustment"
        }
        
        # Analyze filler words 
        filler_count = speech_metrics.get("filler_count", speech_metrics.get("filler_words_count", 0))
        filler_tolerance = self._get_filler_tolerance_for_domain(domain)
        filler_score = max(0, 100 - max(0, filler_count - filler_tolerance) * 10)
        
        analysis["detailed_analysis"]["filler_words"] = {
            "score": filler_score,
            "count": filler_count,
            "domain_tolerance": filler_tolerance,
            "evaluation": self._evaluate_filler_usage(filler_count, filler_tolerance)
        }
        
        # Calculate overall score
        analysis["overall_score"] = (pace_score + filler_score) / 2
        
        # Generate basic domain-specific recommendations first
        if "best_practices" in domain_data:
            if analysis["overall_score"] < 70:
                analysis["domain_specific_recommendations"] = domain_data["best_practices"][:3]
            elif analysis["overall_score"] < 85:
                analysis["domain_specific_recommendations"] = domain_data["best_practices"][:2]
            else:
                analysis["domain_specific_recommendations"] = ["Continue practicing to maintain excellent performance"]
        
        # Enhance with LLM if available
        if self.llm_enabled:
            try:
                # Create a simplified speech analysis object for LLM
                speech_analysis = {
                    "transcript": speech_metrics.get("transcript", ""),
                    "word_count": speech_metrics.get("word_count", 100),
                    "fillers": {
                        "total_fillers": filler_count,
                        "filler_percentage": speech_metrics.get("filler_percentage", 0),
                        "fillers": ["um", "uh"]  # Default fillers if not specified
                    },
                    "delivery_metrics": {
                        "pace": pace_wpm,
                        "vocal_variety": speech_metrics.get("vocal_variety", 7.5),
                        "confidence": speech_metrics.get("confidence_score", 7.0),
                        "overall_score": analysis["overall_score"] / 10  # Scale to 0-10
                    }
                }
                
                # Get domain context from knowledge base
                domain_context = {
                    "domain": domain,
                    "domain_name": domain_data.get("name", domain),
                    "standards": domain_data.get("delivery", {}),
                    "best_practices": domain_data.get("best_practices", []),
                    "challenges": domain_data.get("common_mistakes", [])
                }
                
                # Generate LLM-based recommendations
                llm_response = self.llm_recommender.generate_contextual_recommendations(
                    speech_analysis=speech_analysis,
                    domain_context=domain_context
                )
                
                # Add LLM insights to the analysis
                if "specific_recommendations" in llm_response:
                    enhanced_recommendations = []
                    for rec in llm_response["specific_recommendations"]:
                        enhanced_recommendations.append(rec["recommendation"])
                    
                    # Replace the static recommendations if we have LLM ones
                    if enhanced_recommendations:
                        analysis["domain_specific_recommendations"] = enhanced_recommendations[:3]
                
                # Add additional LLM insights
                analysis["llm_insights"] = {
                    "strengths": llm_response.get("strengths", []),
                    "areas_for_improvement": llm_response.get("areas_for_improvement", []),
                    "context_specific_tips": llm_response.get("context_specific_tips", []),
                    "next_steps": llm_response.get("next_steps", []),
                    "generation_method": "llm"
                }
                
                logger.info(f"Enhanced domain analysis with LLM insights for domain: {domain}")
                
            except Exception as e:
                logger.error(f"Error enhancing analysis with LLM: {str(e)}")
                # Add a note about LLM enhancement failure
                analysis["llm_insights"] = {
                    "error": "LLM enhancement failed, using static recommendations",
                    "generation_method": "static"
                }
        
        return {
            "jsonrpc": "2.0",
            "result": analysis
        }
    
    def _generate_improvement_plan_tool(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Implementation of generateImprovementPlan tool"""
        domain = parameters.get("domain")
        skill_level = parameters.get("skill_level", "intermediate")
        improvement_areas = parameters.get("improvement_areas", ["structure", "delivery"])
        user_id = parameters.get("user_id", "")  # Optional user ID for personalization
        
        if not domain or domain not in self.knowledge_base.get("domains", {}):
            return self._error_response("Invalid domain")
        
        domain_data = self.knowledge_base["domains"][domain]
        
        plan = {
            "domain": domain_data.get("name", domain),
            "skill_level": skill_level,
            "improvement_focus": improvement_areas,
            "action_plan": [],
            "practice_exercises": [],
            "success_metrics": []
        }
        
        # Add domain-specific action items
        for area in improvement_areas:
            if area == "structure" and "structure" in domain_data:
                plan["action_plan"].append({
                    "area": "Structure",
                    "domain_guidance": domain_data["structure"],
                    "actions": [
                        f"Practice {domain_data['structure'].get('opening', 'opening')}",
                        f"Develop {domain_data['structure'].get('body', 'body')}",
                        f"Master {domain_data['structure'].get('closing', 'closing')}"
                    ]
                })
            elif area == "delivery" and "delivery" in domain_data:
                plan["action_plan"].append({
                    "area": "Delivery",
                    "domain_guidance": domain_data["delivery"],
                    "actions": [
                        f"Work on {domain_data['delivery'].get('pace', 'pacing')}",
                        f"Practice {domain_data['delivery'].get('vocal_variety', 'vocal variety')}",
                        f"Develop {domain_data['delivery'].get('gestures', 'gestures')}"
                    ]
                })
        
        # Add skill-level specific exercises
        if skill_level.lower() == "beginner":
            plan["practice_exercises"] = [
                f"Study {domain_data.get('name', domain).lower()} presentation examples",
                "Record yourself practicing domain-specific content",
                "Practice basic structure with domain guidelines"
            ]
        elif skill_level.lower() == "intermediate":
            plan["practice_exercises"] = [
                f"Practice {domain_data.get('name', domain).lower()} presentations with feedback",
                "Work on domain-specific vocal techniques",
                "Join domain-relevant speaking opportunities"
            ]
        else:  # advanced
            plan["practice_exercises"] = [
                f"Mentor others in {domain_data.get('name', domain).lower()}",
                f"Speak at {domain_data.get('name', domain).lower()} events",
                "Develop signature style within domain guidelines"
            ]
        
        # Add domain-specific success metrics
        plan["success_metrics"] = [
            f"Follows {domain_data.get('name', domain).lower()} structure guidelines",
            f"Meets {domain_data.get('name', domain).lower()} delivery expectations", 
            "Demonstrates domain-appropriate best practices",
            "Avoids domain-specific common mistakes"
        ]
        
        # Enhance with LLM if available
        if self.llm_enabled:
            try:
                # Create context for LLM
                domain_context = {
                    "domain": domain,
                    "domain_name": domain_data.get("name", domain),
                    "standards": domain_data.get("delivery", {}),
                    "best_practices": domain_data.get("best_practices", []),
                    "challenges": domain_data.get("common_mistakes", [])
                }
                
                # Create a user context if user_id is provided
                user_context = None
                if user_id:
                    # For demonstration, creating a minimal user context
                    # In a real implementation, you'd fetch this from user knowledge server
                    user_context = {
                        "user_id": user_id,
                        "skill_level": skill_level,
                        "improvement_areas": improvement_areas,
                        "speaking_experience": "Some experience" if skill_level == "intermediate" else "Limited experience" if skill_level == "beginner" else "Extensive experience"
                    }
                
                # Construct a speech analysis object with minimal data
                # This is used to maintain compatibility with the LLM interface
                speech_analysis = {
                    "delivery_metrics": {
                        "overall_score": 7.0  # Default score
                    }
                }
                
                # Generate LLM-based improvement plan
                llm_response = self.llm_recommender.generate_contextual_recommendations(
                    speech_analysis=speech_analysis,
                    domain_context=domain_context,
                    user_context=user_context
                )
                
                # Enhance plan with LLM insights
                if "specific_recommendations" in llm_response:
                    for rec in llm_response["specific_recommendations"]:
                        area = rec.get("category", "General")
                        for action_plan in plan["action_plan"]:
                            if action_plan["area"].lower() == area.lower():
                                # Add to existing area
                                action_plan["actions"].append(rec["recommendation"])
                                break
                        else:
                            # Create new area if not found
                            plan["action_plan"].append({
                                "area": area,
                                "actions": [rec["recommendation"]],
                                "source": "llm"
                            })
                
                # Add personalized practice exercises
                if "next_steps" in llm_response and llm_response["next_steps"]:
                    # Mix LLM-generated exercises with the static ones
                    plan["practice_exercises"] = (
                        plan["practice_exercises"][:1] +
                        llm_response["next_steps"][:2] +
                        plan["practice_exercises"][1:2]
                    )
                
                # Add additional LLM insights
                plan["llm_insights"] = {
                    "strengths": llm_response.get("strengths", []),
                    "areas_for_improvement": llm_response.get("areas_for_improvement", []),
                    "context_specific_tips": llm_response.get("context_specific_tips", []),
                    "generation_method": "llm"
                }
                
                logger.info(f"Enhanced improvement plan with LLM insights for domain: {domain}, skill level: {skill_level}")
                
            except Exception as e:
                logger.error(f"Error enhancing improvement plan with LLM: {str(e)}")
                # Add a note about LLM enhancement failure
                plan["llm_insights"] = {
                    "error": "LLM enhancement failed, using static recommendations",
                    "generation_method": "static"
                }
        
        return {
            "jsonrpc": "2.0",
            "result": plan
        }
    
    def _compare_domains_tool(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Implementation of compareDomains tool"""
        domains = parameters.get("domains", [])
        aspect = parameters.get("aspect", "structure")
        
        comparison = {
            "comparison_aspect": aspect,
            "domains_compared": [],
            "similarities": [],
            "key_differences": [],
            "guidelines_by_domain": {}
        }
        
        domain_guidelines = {}
        for domain in domains:
            if domain in self.knowledge_base.get("domains", {}):
                domain_data = self.knowledge_base["domains"][domain]
                comparison["domains_compared"].append(domain_data.get("name", domain))
                
                if aspect == "structure" and "structure" in domain_data:
                    domain_guidelines[domain] = domain_data["structure"]
                elif aspect == "delivery" and "delivery" in domain_data:
                    domain_guidelines[domain] = domain_data["delivery"]
                elif aspect == "best_practices" and "best_practices" in domain_data:
                    domain_guidelines[domain] = domain_data["best_practices"]
                elif aspect == "common_mistakes" and "common_mistakes" in domain_data:
                    domain_guidelines[domain] = domain_data["common_mistakes"]
        
        comparison["guidelines_by_domain"] = domain_guidelines
        
        # Add generic similarities and differences
        comparison["similarities"] = [
            "All domains emphasize clear communication",
            "Structure and preparation are universally important",
            "Audience awareness is critical across domains"
        ]
        
        comparison["key_differences"] = [
            "Corporate: Focus on business outcomes and ROI",
            "Technical: Emphasis on clarity of complex concepts",
            "Academic: Scholarly rigor and research methodology",
            "Public Speaking: Audience engagement and persuasion"
        ]
        
        return {
            "jsonrpc": "2.0",
            "result": comparison
        }
    
    # MCP Prompts Methods
    def list_prompts(self) -> Dict[str, Any]:
        """MCP prompts/list endpoint implementation"""
        prompts = [
            {
                "name": "analyze-speech-by-domain",
                "title": "Analyze Speech By Domain",
                "description": "Analyze speech metrics against domain-specific expectations",
                "arguments": [
                    {
                        "name": "domain",
                        "type": "string",
                        "description": "Speaking domain to analyze against",
                        "enum": list(self.knowledge_base.get("domains", {}).keys()),
                        "required": True
                    },
                    {
                        "name": "pace_wpm", 
                        "type": "number",
                        "description": "Speaking pace in words per minute",
                        "required": True
                    },
                    {
                        "name": "filler_words_count",
                        "type": "number",
                        "description": "Number of filler words used",
                        "required": True
                    },
                    {
                        "name": "include_recommendations",
                        "type": "boolean",
                        "description": "Include domain-specific recommendations in analysis",
                        "required": False
                    }
                ]
            },
            {
                "name": "get-domain-guidelines",
                "title": "Get Domain Guidelines",
                "description": "Get speaking guidelines for a specific domain",
                "arguments": [
                    {
                        "name": "domain",
                        "type": "string",
                        "description": "Speaking domain",
                        "enum": list(self.knowledge_base.get("domains", {}).keys()),
                        "required": True
                    },
                    {
                        "name": "focus_area",
                        "type": "string",
                        "description": "Specific area to focus on",
                        "enum": self.knowledge_base.get("available_focus_areas", []),
                        "required": False
                    }
                ]
            }
        ]
        
        return {
            "jsonrpc": "2.0",
            "result": {
                "protocol": "mcp",
                "version": self.protocol_version,
                "prompts": prompts
            }
        }
    
    def get_prompt(self, prompt_name: str) -> Dict[str, Any]:
        """MCP prompts/get endpoint implementation"""
        if prompt_name == "analyze-speech-by-domain":
            return {
                "jsonrpc": "2.0",
                "result": {
                    "name": "analyze-speech-by-domain",
                    "title": "Analyze Speech By Domain",
                    "description": "Analyze speech metrics against domain-specific expectations",
                    "template": "Analyze my speech metrics (pace: {{pace_wpm}} WPM, filler words: {{filler_words_count}}) for a {{domain}} presentation.{{#include_recommendations}} Include specific recommendations for improvement.{{/include_recommendations}}",
                    "arguments": [
                        {
                            "name": "domain",
                            "type": "string",
                            "description": "Speaking domain to analyze against",
                            "enum": list(self.knowledge_base.get("domains", {}).keys()),
                            "required": True
                        },
                        {
                            "name": "pace_wpm", 
                            "type": "number",
                            "description": "Speaking pace in words per minute",
                            "required": True
                        },
                        {
                            "name": "filler_words_count",
                            "type": "number",
                            "description": "Number of filler words used",
                            "required": True
                        },
                        {
                            "name": "include_recommendations",
                            "type": "boolean",
                            "description": "Include domain-specific recommendations in analysis",
                            "required": False
                        }
                    ]
                }
            }
        elif prompt_name == "get-domain-guidelines":
            return {
                "jsonrpc": "2.0",
                "result": {
                    "name": "get-domain-guidelines",
                    "title": "Get Domain Guidelines",
                    "description": "Get speaking guidelines for a specific domain",
                    "template": "Provide guidelines for {{domain}} presentations{{#focus_area}} focusing specifically on {{focus_area}}{{/focus_area}}.",
                    "arguments": [
                        {
                            "name": "domain",
                            "type": "string",
                            "description": "Speaking domain",
                            "enum": list(self.knowledge_base.get("domains", {}).keys()),
                            "required": True
                        },
                        {
                            "name": "focus_area",
                            "type": "string",
                            "description": "Specific area to focus on",
                            "enum": self.knowledge_base.get("available_focus_areas", []),
                            "required": False
                        }
                    ]
                }
            }
        else:
            return self._error_response(f"Prompt not found: {prompt_name}", -32001)
    
    # Helper methods for domain knowledge
    def _get_target_pace_for_domain(self, domain: str) -> int:
        """Get target speaking pace for domain"""
        pace_targets = {
            "corporate": 125,  # Measured professional pace
            "technical": 110,  # Slower for complex concepts  
            "academic": 120,   # Moderate pace for note-taking
            "public_speaking": 135  # Engaging pace
        }
        return pace_targets.get(domain, 130)
    
    def _get_filler_tolerance_for_domain(self, domain: str) -> int:
        """Get filler word tolerance for domain"""
        tolerance = {
            "corporate": 2,     # Low tolerance in business settings
            "academic": 3,      # Moderate tolerance in scholarly context
            "technical": 4,     # Higher tolerance for complex explanations
            "public_speaking": 2  # Low tolerance for polished presentations
        }
        return tolerance.get(domain, 3)
    
    def _evaluate_filler_usage(self, count: int, tolerance: int) -> str:
        """Evaluate filler word usage"""
        if count == 0:
            return "Excellent - no filler words detected"
        elif count <= tolerance:
            return "Good - within acceptable range"
        elif count <= tolerance * 2:
            return "Needs improvement - excessive filler words"
        else:
            return "Poor - significant filler word issue"
    
    def _error_response(self, message: str, code: int = -32603) -> Dict[str, Any]:
        """Generate standard MCP error response"""
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": code,
                "message": message
            }
        }

    def handle_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle MCP protocol requests and route to appropriate handlers
        
        Args:
            method: The MCP method name (e.g., "resources/list")
            params: The parameters for the method
            
        Returns:
            MCP-compliant response dictionary
        """
        try:
            if method == "resources/list":
                return self.list_resources()
            elif method == "resources/templates/list":
                return self.list_resource_templates()
            elif method == "resources/read":
                uri = params.get("uri")
                if not uri:
                    return self._error_response("Missing required parameter: uri")
                return self.read_resource(uri)
            elif method == "tools/list":
                return self.list_tools()
            elif method == "tools/call":
                tool_name = params.get("name")
                tool_params = params.get("parameters", {})
                if not tool_name:
                    return self._error_response("Missing required parameter: name")
                return self.call_tool(tool_name, tool_params)
            elif method == "prompts/list":
                return self.list_prompts()
            elif method == "prompts/get":
                prompt_name = params.get("name")
                if not prompt_name:
                    return self._error_response("Missing required parameter: name")
                return self.get_prompt(prompt_name)
            else:
                return self._error_response(f"Unsupported method: {method}", -32601)
        except Exception as e:
            logger.error(f"Error handling request {method}: {e}")
            return self._error_response(f"Internal server error: {str(e)}")
    
    def health_check(self) -> Dict[str, Any]:
        """Check health status of the knowledge server"""
        domains_count = len(self.knowledge_base.get("domains", {}))
        return {
            "status": "healthy" if domains_count > 0 else "degraded",
            "server_name": self.server_name,
            "server_version": self.server_version,
            "protocol_version": self.protocol_version,
            "domains_loaded": domains_count,
            "timestamp": datetime.now().isoformat()
        }

# For testing purposes
if __name__ == "__main__":
    server = DomainKnowledgeMCPServer()
    
    # Test MCP resources listing
    print("=== MCP Resources List ===")
    resources_response = server.handle_request("resources/list", {})
    print(json.dumps(resources_response, indent=2))
    
    # Test MCP resource templates
    print("\n=== MCP Resource Templates List ===")
    templates_response = server.handle_request("resources/templates/list", {})
    print(json.dumps(templates_response, indent=2))
    
    # Test MCP resource read
    print("\n=== MCP Resource Read ===")
    read_response = server.handle_request("resources/read", {"uri": "domain://corporate/focus/structure"})
    print(json.dumps(read_response, indent=2))
    
    # Test MCP tools list
    print("\n=== MCP Tools List ===")
    tools_response = server.handle_request("tools/list", {})
    print(json.dumps(tools_response, indent=2))
    
    # Test MCP tool call
    print("\n=== MCP Tool Call ===")
    tool_response = server.handle_request("tools/call", {
        "name": "analyzeSpeech", 
        "parameters": {
            "domain": "corporate",
            "speech_metrics": {
                "pace_wpm": 140,
                "filler_words_count": 5
            }
        }
    })
    print(json.dumps(tool_response, indent=2))
