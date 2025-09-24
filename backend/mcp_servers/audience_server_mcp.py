#!/usr/bin/env python3
"""
MCP-compliant Audience Knowledge Server for Speech Coach
Provides audience-specific insights and recommendations for tailoring speeches
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudienceKnowledgeMCPServer:
    """
    MCP-compliant Audience Knowledge Server that provides audience-specific
    insights and recommendations for tailoring speeches to different audiences.
    """
    
    def __init__(self):
        """Initialize the Audience Knowledge Server with MCP capabilities"""
        self.audience_data = self._load_audience_knowledge()
        self.protocol_version = "1.0"
        self.server_name = "audience-knowledge-server"
        self.server_version = "1.0.0"
        logger.info(f"MCP Audience Knowledge Server initialized, protocol v{self.protocol_version}")

    def _load_audience_knowledge(self) -> Dict[str, Any]:
        """Load audience knowledge from JSON resource"""
        try:
            resource_path = os.path.join(os.path.dirname(__file__), 'resources', 'audience_knowledge.json')
            with open(resource_path, 'r') as f:
                audience_data = json.load(f)
            logger.info(f"Audience knowledge loaded successfully with {len(audience_data.get('audience_types', {}))} audience types")
            return audience_data
        except Exception as e:
            logger.error(f"Error loading audience knowledge: {e}")
            # Fallback to empty knowledge base
            return {"audience_types": {}, "demographics": {}, "characteristics": []}

    # MCP Resource Methods
    def list_resources(self) -> Dict[str, Any]:
        """MCP resources/list endpoint implementation"""
        resources = []
        
        # Add direct resources for each audience type
        for audience_id, audience_data in self.audience_data.get("audience_types", {}).items():
            resources.append({
                "uri": f"audience://{audience_id}",
                "name": f"audience-{audience_id}",
                "title": f"Audience Type: {audience_data.get('name', audience_id)}",
                "description": f"Speaking guidelines for {audience_data.get('name', audience_id)} audiences",
                "mimeType": "application/json"
            })
        
        # Add resource for demographic segments
        for demo_id, demo_data in self.audience_data.get("demographics", {}).items():
            resources.append({
                "uri": f"audience://demographic/{demo_id}",
                "name": f"audience-demographic-{demo_id}",
                "title": f"Audience Demographic: {demo_data.get('name', demo_id)}",
                "description": f"Speaking considerations for {demo_data.get('name', demo_id)} demographic",
                "mimeType": "application/json"
            })
        
        # Add resource for audience characteristics
        resources.append({
            "uri": "audience://characteristics",
            "name": "audience-characteristics",
            "title": "Audience Characteristics",
            "description": "Common audience characteristics and their speaking implications",
            "mimeType": "application/json"
        })
        
        # Add resource for all audience types
        resources.append({
            "uri": "audience://types",
            "name": "audience-types",
            "title": "Audience Types",
            "description": "List of all audience types with basic information",
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
                "uriTemplate": "audience://{audience_id}/preferences",
                "name": "audience-preferences",
                "title": "Audience Preferences",
                "description": "Communication preferences for an audience type",
                "mimeType": "application/json",
                "parameters": [
                    {
                        "name": "audience_id",
                        "description": "Audience type identifier",
                        "required": True,
                        "schema": {"type": "string", "enum": list(self.audience_data.get("audience_types", {}).keys())}
                    }
                ]
            },
            {
                "uriTemplate": "audience://{audience_id}/challenges",
                "name": "audience-challenges",
                "title": "Audience Challenges",
                "description": "Common challenges when addressing this audience type",
                "mimeType": "application/json",
                "parameters": [
                    {
                        "name": "audience_id",
                        "description": "Audience type identifier",
                        "required": True,
                        "schema": {"type": "string", "enum": list(self.audience_data.get("audience_types", {}).keys())}
                    }
                ]
            },
            {
                "uriTemplate": "audience://comparison/{audience_id1}/{audience_id2}",
                "name": "audience-comparison",
                "title": "Audience Type Comparison",
                "description": "Compare preferences and characteristics between two audience types",
                "mimeType": "application/json",
                "parameters": [
                    {
                        "name": "audience_id1",
                        "description": "First audience type identifier",
                        "required": True,
                        "schema": {"type": "string", "enum": list(self.audience_data.get("audience_types", {}).keys())}
                    },
                    {
                        "name": "audience_id2",
                        "description": "Second audience type identifier",
                        "required": True,
                        "schema": {"type": "string", "enum": list(self.audience_data.get("audience_types", {}).keys())}
                    }
                ]
            },
            {
                "uriTemplate": "audience://mixed/{audience_ids}",
                "name": "mixed-audience",
                "title": "Mixed Audience Approach",
                "description": "Guidelines for addressing a mixed audience with multiple types",
                "mimeType": "application/json",
                "parameters": [
                    {
                        "name": "audience_ids",
                        "description": "Comma-separated audience type identifiers",
                        "required": True,
                        "schema": {"type": "string"}
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
            # Handle direct audience type resources
            if uri.startswith("audience://") and not uri.startswith("audience://demographic/") and not uri.endswith("characteristics") and not uri.endswith("types") and not uri.startswith("audience://comparison/") and not uri.startswith("audience://mixed/"):
                parts = uri.replace("audience://", "").split("/")
                audience_id = parts[0]
                
                if audience_id in self.audience_data.get("audience_types", {}):
                    audience_data = self.audience_data["audience_types"][audience_id]
                    
                    # Return complete audience data
                    if len(parts) == 1:
                        return {
                            "jsonrpc": "2.0",
                            "result": {
                                "uri": uri,
                                "mimeType": "application/json",
                                "content": audience_data
                            }
                        }
                    
                    # Return audience preferences
                    elif len(parts) == 2 and parts[1] == "preferences":
                        if "preferences" in audience_data:
                            return {
                                "jsonrpc": "2.0",
                                "result": {
                                    "uri": uri,
                                    "mimeType": "application/json",
                                    "content": {
                                        "audience_id": audience_id,
                                        "audience_name": audience_data.get("name", audience_id),
                                        "preferences": audience_data["preferences"]
                                    }
                                }
                            }
                    
                    # Return audience challenges
                    elif len(parts) == 2 and parts[1] == "challenges":
                        if "challenges" in audience_data:
                            return {
                                "jsonrpc": "2.0",
                                "result": {
                                    "uri": uri,
                                    "mimeType": "application/json",
                                    "content": {
                                        "audience_id": audience_id,
                                        "audience_name": audience_data.get("name", audience_id),
                                        "challenges": audience_data["challenges"]
                                    }
                                }
                            }
            
            # Handle demographic resources
            elif uri.startswith("audience://demographic/"):
                demographic_id = uri.replace("audience://demographic/", "")
                
                if demographic_id in self.audience_data.get("demographics", {}):
                    demographic_data = self.audience_data["demographics"][demographic_id]
                    
                    return {
                        "jsonrpc": "2.0",
                        "result": {
                            "uri": uri,
                            "mimeType": "application/json",
                            "content": demographic_data
                        }
                    }
            
            # Handle audience characteristics resource
            elif uri == "audience://characteristics":
                characteristics = self.audience_data.get("characteristics", [])
                
                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "uri": uri,
                        "mimeType": "application/json",
                        "content": {
                            "characteristics_count": len(characteristics),
                            "characteristics": characteristics
                        }
                    }
                }
            
            # Handle audience types list
            elif uri == "audience://types":
                types = {}
                for audience_id, audience_data in self.audience_data.get("audience_types", {}).items():
                    types[audience_id] = {
                        "name": audience_data.get("name", audience_id),
                        "description": audience_data.get("description", ""),
                        "expertise_level": audience_data.get("expertise_level", ""),
                        "key_interests": audience_data.get("key_interests", [])
                    }
                
                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "uri": uri,
                        "mimeType": "application/json",
                        "content": {
                            "audience_types_count": len(types),
                            "audience_types": types
                        }
                    }
                }
            
            # Handle audience comparison
            elif uri.startswith("audience://comparison/"):
                parts = uri.replace("audience://comparison/", "").split("/")
                if len(parts) == 2:
                    audience_id1 = parts[0]
                    audience_id2 = parts[1]
                    
                    if (audience_id1 in self.audience_data.get("audience_types", {}) and 
                        audience_id2 in self.audience_data.get("audience_types", {})):
                        
                        audience_data1 = self.audience_data["audience_types"][audience_id1]
                        audience_data2 = self.audience_data["audience_types"][audience_id2]
                        
                        comparison = self._compare_audiences(audience_id1, audience_id2, audience_data1, audience_data2)
                        
                        return {
                            "jsonrpc": "2.0",
                            "result": {
                                "uri": uri,
                                "mimeType": "application/json",
                                "content": comparison
                            }
                        }
            
            # Handle mixed audience
            elif uri.startswith("audience://mixed/"):
                audience_ids_str = uri.replace("audience://mixed/", "")
                audience_ids = [id.strip() for id in audience_ids_str.split(",")]
                
                valid_ids = [id for id in audience_ids if id in self.audience_data.get("audience_types", {})]
                
                if valid_ids:
                    mixed_guidance = self._generate_mixed_audience_guidance(valid_ids)
                    
                    return {
                        "jsonrpc": "2.0",
                        "result": {
                            "uri": uri,
                            "mimeType": "application/json",
                            "content": mixed_guidance
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
                "name": "analyzeAudience",
                "description": "Analyze an audience based on provided characteristics",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "expertise_level": {
                            "type": "string",
                            "description": "Audience's expertise level in the topic",
                            "enum": ["novice", "intermediate", "expert", "mixed"]
                        },
                        "age_group": {
                            "type": "string",
                            "description": "Predominant age group of the audience",
                            "enum": ["youth", "young_adult", "middle_aged", "senior", "mixed"]
                        },
                        "industry": {
                            "type": "string",
                            "description": "Industry or field of the audience"
                        },
                        "interests": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Key interests of the audience"
                        },
                        "size": {
                            "type": "string",
                            "description": "Size of the audience",
                            "enum": ["small", "medium", "large"]
                        }
                    },
                    "required": ["expertise_level"]
                }
            },
            {
                "name": "recommendAudienceApproach",
                "description": "Recommend an approach for a specific audience type",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "audience_id": {
                            "type": "string",
                            "description": "Audience type identifier",
                            "enum": list(self.audience_data.get("audience_types", {}).keys())
                        },
                        "topic": {
                            "type": "string",
                            "description": "Topic of the presentation"
                        },
                        "purpose": {
                            "type": "string",
                            "description": "Purpose of the communication",
                            "enum": ["inform", "persuade", "entertain", "inspire", "instruct"]
                        }
                    },
                    "required": ["audience_id"]
                }
            },
            {
                "name": "audienceFeedbackAnalysis",
                "description": "Analyze audience feedback and suggest improvements",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "audience_id": {
                            "type": "string",
                            "description": "Audience type identifier",
                            "enum": list(self.audience_data.get("audience_types", {}).keys())
                        },
                        "engagement_level": {
                            "type": "number",
                            "description": "Engagement level (1-10)",
                            "minimum": 1,
                            "maximum": 10
                        },
                        "feedback_points": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Key feedback points from the audience"
                        },
                        "questions_asked": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Questions asked by the audience"
                        }
                    },
                    "required": ["audience_id", "engagement_level"]
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
            if tool_name == "analyzeAudience":
                return self._analyze_audience_tool(parameters)
            elif tool_name == "recommendAudienceApproach":
                return self._recommend_audience_approach_tool(parameters)
            elif tool_name == "audienceFeedbackAnalysis":
                return self._audience_feedback_analysis_tool(parameters)
            else:
                return self._error_response(f"Unknown tool: {tool_name}", -32601)
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return self._error_response(f"Error calling tool: {str(e)}")
    
    def _analyze_audience_tool(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Implementation of analyzeAudience tool"""
        expertise_level = parameters.get("expertise_level", "mixed")
        age_group = parameters.get("age_group", "mixed")
        industry = parameters.get("industry", "general")
        interests = parameters.get("interests", [])
        size = parameters.get("size", "medium")
        
        # Find the best matching audience type
        match_scores = {}
        for audience_id, audience_data in self.audience_data.get("audience_types", {}).items():
            score = 0
            
            # Match on expertise level
            if audience_data.get("expertise_level") == expertise_level:
                score += 3
            
            # Match on age group if applicable
            if "demographics" in audience_data and audience_data["demographics"].get("age_group") == age_group:
                score += 2
            
            # Match on industry if applicable
            if audience_data.get("industry") == industry:
                score += 3
            
            # Match on interests
            audience_interests = audience_data.get("key_interests", [])
            for interest in interests:
                if interest in audience_interests:
                    score += 1
            
            # Match on size
            if audience_data.get("size") == size:
                score += 1
            
            match_scores[audience_id] = score
        
        # Get best matching audience type
        best_match = None
        best_score = -1
        for audience_id, score in match_scores.items():
            if score > best_score:
                best_score = score
                best_match = audience_id
        
        # Get audience data
        audience_data = {}
        if best_match:
            audience_data = self.audience_data["audience_types"][best_match]
        
        # Format the response
        analysis = {
            "audience_parameters": {
                "expertise_level": expertise_level,
                "age_group": age_group,
                "industry": industry,
                "interests": interests,
                "size": size
            },
            "best_match": {
                "audience_id": best_match,
                "audience_name": audience_data.get("name", best_match) if best_match else "Custom Audience",
                "match_score": best_score,
                "audience_data": audience_data
            },
            "analysis": {
                "communication_recommendations": self._generate_communication_recommendations(expertise_level, size),
                "content_complexity": self._recommend_content_complexity(expertise_level),
                "engagement_strategies": self._recommend_engagement_strategies(age_group, size)
            },
            "customized_approach": self._generate_custom_approach(parameters)
        }
        
        return {
            "jsonrpc": "2.0",
            "result": analysis
        }
    
    def _recommend_audience_approach_tool(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Implementation of recommendAudienceApproach tool"""
        audience_id = parameters.get("audience_id")
        topic = parameters.get("topic", "general")
        purpose = parameters.get("purpose", "inform")
        
        if not audience_id or audience_id not in self.audience_data.get("audience_types", {}):
            return self._error_response("Invalid audience_id")
        
        audience_data = self.audience_data["audience_types"][audience_id]
        
        # Format the response with audience-specific recommendations
        approach = {
            "audience_id": audience_id,
            "audience_name": audience_data.get("name", audience_id),
            "topic": topic,
            "purpose": purpose,
            "approach_recommendations": {
                "content_focus": self._recommend_content_focus(audience_data, topic, purpose),
                "communication_style": self._recommend_communication_style(audience_data, purpose),
                "structure": self._recommend_structure(audience_data, purpose),
                "examples_and_analogies": self._recommend_examples(audience_data, topic)
            },
            "speaking_techniques": self._recommend_speaking_techniques(audience_data),
            "potential_challenges": audience_data.get("challenges", []),
            "visual_aid_recommendations": self._recommend_visual_aids(audience_data)
        }
        
        return {
            "jsonrpc": "2.0",
            "result": approach
        }
    
    def _audience_feedback_analysis_tool(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Implementation of audienceFeedbackAnalysis tool"""
        audience_id = parameters.get("audience_id")
        engagement_level = parameters.get("engagement_level", 5)
        feedback_points = parameters.get("feedback_points", [])
        questions_asked = parameters.get("questions_asked", [])
        
        if not audience_id or audience_id not in self.audience_data.get("audience_types", {}):
            return self._error_response("Invalid audience_id")
        
        audience_data = self.audience_data["audience_types"][audience_id]
        
        # Analyze engagement level
        engagement_analysis = "low"
        if engagement_level >= 8:
            engagement_analysis = "high"
        elif engagement_level >= 5:
            engagement_analysis = "moderate"
        
        # Analyze feedback and questions
        feedback_themes = self._extract_feedback_themes(feedback_points)
        question_themes = self._extract_question_themes(questions_asked)
        
        # Generate recommendations
        recommendations = self._generate_improvement_recommendations(
            audience_data, 
            engagement_analysis, 
            feedback_themes, 
            question_themes
        )
        
        # Format the response
        feedback_analysis = {
            "audience_id": audience_id,
            "audience_name": audience_data.get("name", audience_id),
            "feedback_summary": {
                "engagement_level": engagement_level,
                "engagement_rating": engagement_analysis,
                "feedback_themes": feedback_themes,
                "question_themes": question_themes
            },
            "audience_specific_insights": {
                "expectations_met": engagement_level >= 7,
                "areas_of_interest": question_themes,
                "areas_for_improvement": [theme for theme, count in feedback_themes.items() if count > 0]
            },
            "recommendations": recommendations
        }
        
        return {
            "jsonrpc": "2.0",
            "result": feedback_analysis
        }
    
    # MCP Prompts Methods
    def list_prompts(self) -> Dict[str, Any]:
        """MCP prompts/list endpoint implementation"""
        prompts = [
            {
                "name": "audience-tailored-communication",
                "title": "Audience-Tailored Communication",
                "description": "Generate communication recommendations tailored to a specific audience",
                "arguments": [
                    {
                        "name": "audience_id",
                        "type": "string",
                        "description": "Audience type identifier",
                        "enum": list(self.audience_data.get("audience_types", {}).keys()),
                        "required": True
                    },
                    {
                        "name": "topic",
                        "type": "string",
                        "description": "Topic of the communication",
                        "required": True
                    },
                    {
                        "name": "duration_minutes",
                        "type": "number",
                        "description": "Duration of the communication in minutes",
                        "required": False
                    }
                ]
            },
            {
                "name": "audience-engagement-strategies",
                "title": "Audience Engagement Strategies",
                "description": "Generate strategies to better engage a specific audience",
                "arguments": [
                    {
                        "name": "audience_id",
                        "type": "string",
                        "description": "Audience type identifier",
                        "enum": list(self.audience_data.get("audience_types", {}).keys()),
                        "required": True
                    },
                    {
                        "name": "current_engagement_level",
                        "type": "string",
                        "description": "Current level of audience engagement",
                        "enum": ["low", "moderate", "high"],
                        "required": True
                    },
                    {
                        "name": "format",
                        "type": "string",
                        "description": "Format of the communication",
                        "enum": ["presentation", "workshop", "panel_discussion", "lecture", "interactive_session"],
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
        if prompt_name == "audience-tailored-communication":
            return {
                "jsonrpc": "2.0",
                "result": {
                    "name": "audience-tailored-communication",
                    "title": "Audience-Tailored Communication",
                    "description": "Generate communication recommendations tailored to a specific audience",
                    "template": "Provide recommendations for communicating about {{topic}} to a {{audience_name}} audience.{{#duration_minutes}} The presentation should be about {{duration_minutes}} minutes long.{{/duration_minutes}}",
                    "arguments": [
                        {
                            "name": "audience_id",
                            "type": "string",
                            "description": "Audience type identifier",
                            "enum": list(self.audience_data.get("audience_types", {}).keys()),
                            "required": True
                        },
                        {
                            "name": "audience_name",
                            "type": "string",
                            "description": "Name of the audience type",
                            "required": True
                        },
                        {
                            "name": "topic",
                            "type": "string",
                            "description": "Topic of the communication",
                            "required": True
                        },
                        {
                            "name": "duration_minutes",
                            "type": "number",
                            "description": "Duration of the communication in minutes",
                            "required": False
                        }
                    ]
                }
            }
        elif prompt_name == "audience-engagement-strategies":
            return {
                "jsonrpc": "2.0",
                "result": {
                    "name": "audience-engagement-strategies",
                    "title": "Audience Engagement Strategies",
                    "description": "Generate strategies to better engage a specific audience",
                    "template": "Suggest strategies to increase engagement for a {{audience_name}} audience that currently has {{current_engagement_level}} engagement.{{#format}} This is for a {{format}} format.{{/format}}",
                    "arguments": [
                        {
                            "name": "audience_id",
                            "type": "string",
                            "description": "Audience type identifier",
                            "enum": list(self.audience_data.get("audience_types", {}).keys()),
                            "required": True
                        },
                        {
                            "name": "audience_name",
                            "type": "string",
                            "description": "Name of the audience type",
                            "required": True
                        },
                        {
                            "name": "current_engagement_level",
                            "type": "string",
                            "description": "Current level of audience engagement",
                            "enum": ["low", "moderate", "high"],
                            "required": True
                        },
                        {
                            "name": "format",
                            "type": "string",
                            "description": "Format of the communication",
                            "enum": ["presentation", "workshop", "panel discussion", "lecture", "interactive session"],
                            "required": False
                        }
                    ]
                }
            }
        else:
            return self._error_response(f"Prompt not found: {prompt_name}", -32001)
    
    # Helper methods for audience knowledge
    def _compare_audiences(self, audience_id1: str, audience_id2: str, audience_data1: Dict[str, Any], audience_data2: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two audience types"""
        comparison = {
            "audiences": [
                {
                    "id": audience_id1,
                    "name": audience_data1.get("name", audience_id1),
                    "description": audience_data1.get("description", "")
                },
                {
                    "id": audience_id2,
                    "name": audience_data2.get("name", audience_id2),
                    "description": audience_data2.get("description", "")
                }
            ],
            "similarities": [],
            "differences": [],
            "approach_comparison": {}
        }
        
        # Compare expertise levels
        expertise1 = audience_data1.get("expertise_level", "")
        expertise2 = audience_data2.get("expertise_level", "")
        if expertise1 == expertise2:
            comparison["similarities"].append(f"Both have similar expertise levels: {expertise1}")
        else:
            comparison["differences"].append(f"Expertise level: {audience_data1.get('name', audience_id1)} is {expertise1}, while {audience_data2.get('name', audience_id2)} is {expertise2}")
        
        # Compare key interests
        interests1 = set(audience_data1.get("key_interests", []))
        interests2 = set(audience_data2.get("key_interests", []))
        
        common_interests = interests1 & interests2
        if common_interests:
            comparison["similarities"].append(f"Common interests: {', '.join(common_interests)}")
        
        unique_interests1 = interests1 - interests2
        unique_interests2 = interests2 - interests1
        
        if unique_interests1:
            comparison["differences"].append(f"{audience_data1.get('name', audience_id1)} unique interests: {', '.join(unique_interests1)}")
        
        if unique_interests2:
            comparison["differences"].append(f"{audience_data2.get('name', audience_id2)} unique interests: {', '.join(unique_interests2)}")
        
        # Compare preferences
        pref1 = audience_data1.get("preferences", {})
        pref2 = audience_data2.get("preferences", {})
        
        comparison["approach_comparison"] = {
            audience_id1: {
                "communication_style": pref1.get("communication_style", "Not specified"),
                "content_complexity": pref1.get("content_complexity", "Not specified"),
                "examples_preferred": pref1.get("examples_preferred", "Not specified")
            },
            audience_id2: {
                "communication_style": pref2.get("communication_style", "Not specified"),
                "content_complexity": pref2.get("content_complexity", "Not specified"),
                "examples_preferred": pref2.get("examples_preferred", "Not specified")
            }
        }
        
        return comparison
    
    def _generate_mixed_audience_guidance(self, audience_ids: List[str]) -> Dict[str, Any]:
        """Generate guidance for a mixed audience"""
        audience_types = []
        expertise_levels = set()
        all_preferences = []
        common_challenges = []
        
        # Gather data from each audience type
        for audience_id in audience_ids:
            audience_data = self.audience_data["audience_types"][audience_id]
            audience_types.append({
                "id": audience_id,
                "name": audience_data.get("name", audience_id),
                "expertise_level": audience_data.get("expertise_level", "")
            })
            
            expertise_levels.add(audience_data.get("expertise_level", ""))
            
            if "preferences" in audience_data:
                all_preferences.append(audience_data["preferences"])
            
            if "challenges" in audience_data:
                common_challenges.extend(audience_data["challenges"])
        
        # Generate mixed audience recommendations
        mixed_approach = {
            "communication_style": "balanced",
            "content_structure": "layered",
            "examples": "diverse",
            "technical_level": "mixed"
        }
        
        if len(expertise_levels) == 1:
            # If all audiences have same expertise level
            expertise = list(expertise_levels)[0]
            mixed_approach["technical_level"] = expertise
        elif "expert" in expertise_levels and "novice" in expertise_levels:
            # If mixed expertise with experts and novices
            mixed_approach["content_structure"] = "progressive complexity"
            mixed_approach["technical_level"] = "multi-tiered"
        
        # Format the response
        guidance = {
            "audience_composition": {
                "types": audience_types,
                "expertise_distribution": list(expertise_levels)
            },
            "mixed_audience_approach": mixed_approach,
            "recommendations": {
                "structure": "Layered content with clear entry points for different expertise levels",
                "communication": "Balance technical and accessible language, defining terms when needed",
                "engagement": "Use diverse examples relevant to multiple audience segments",
                "visual_aids": "Include both overview visuals and detailed information"
            },
            "common_challenges": list(set(common_challenges))[:5]  # Top 5 unique challenges
        }
        
        return guidance
    
    def _generate_communication_recommendations(self, expertise_level: str, size: str) -> List[str]:
        """Generate communication recommendations based on expertise level and audience size"""
        recommendations = []
        
        # Expertise-based recommendations
        if expertise_level == "novice":
            recommendations.extend([
                "Use simple, accessible language avoiding jargon",
                "Provide clear definitions for any technical terms",
                "Use relatable analogies to explain complex concepts"
            ])
        elif expertise_level == "intermediate":
            recommendations.extend([
                "Balance technical language with accessibility",
                "Reference familiar concepts when introducing new ones",
                "Acknowledge audience's existing knowledge"
            ])
        elif expertise_level == "expert":
            recommendations.extend([
                "Use field-specific terminology appropriately",
                "Focus on advanced concepts and recent developments",
                "Reference specialized knowledge and current research"
            ])
        else:  # mixed
            recommendations.extend([
                "Layer content with both basic concepts and advanced applications",
                "Define terms selectively when moving to advanced content",
                "Provide both high-level summaries and detailed explanations"
            ])
        
        # Size-based recommendations
        if size == "small":
            recommendations.extend([
                "Create an interactive, conversational atmosphere",
                "Use direct engagement and questions",
                "Be prepared for more personalized discussions"
            ])
        elif size == "medium":
            recommendations.extend([
                "Balance structured content with interactive elements",
                "Include Q&A segments throughout the presentation",
                "Use small group discussions when appropriate"
            ])
        elif size == "large":
            recommendations.extend([
                "Use strong, clear vocal projection",
                "Incorporate audience response systems for engagement",
                "Focus on broadly relatable examples and analogies"
            ])
        
        return recommendations
    
    def _recommend_content_complexity(self, expertise_level: str) -> Dict[str, Any]:
        """Recommend content complexity based on expertise level"""
        if expertise_level == "novice":
            return {
                "level": "basic",
                "vocabulary": "simplified",
                "concept_depth": "foundational",
                "technical_detail": "minimal",
                "background_explanation": "extensive"
            }
        elif expertise_level == "intermediate":
            return {
                "level": "moderate",
                "vocabulary": "field-specific",
                "concept_depth": "applied",
                "technical_detail": "moderate",
                "background_explanation": "contextual"
            }
        elif expertise_level == "expert":
            return {
                "level": "advanced",
                "vocabulary": "specialized",
                "concept_depth": "nuanced",
                "technical_detail": "in-depth",
                "background_explanation": "minimal"
            }
        else:  # mixed
            return {
                "level": "tiered",
                "vocabulary": "progressive",
                "concept_depth": "layered",
                "technical_detail": "varied",
                "background_explanation": "selective"
            }
    
    def _recommend_engagement_strategies(self, age_group: str, size: str) -> List[str]:
        """Recommend engagement strategies based on age group and size"""
        strategies = []
        
        # Age-based strategies
        if age_group == "youth":
            strategies.extend([
                "Use interactive activities and games",
                "Incorporate multimedia and visual elements",
                "Keep segments brief with frequent transitions"
            ])
        elif age_group == "young_adult":
            strategies.extend([
                "Reference current trends and technologies",
                "Use collaborative problem-solving activities",
                "Incorporate social media and digital interaction"
            ])
        elif age_group == "middle_aged":
            strategies.extend([
                "Connect content to professional applications",
                "Acknowledge experience while introducing new concepts",
                "Use structured discussions and case studies"
            ])
        elif age_group == "senior":
            strategies.extend([
                "Ensure clear visual and audio presentation",
                "Relate new concepts to historical context",
                "Allow time for reflection and questions"
            ])
        else:  # mixed
            strategies.extend([
                "Use diverse examples relevant across generations",
                "Vary engagement methods throughout the presentation",
                "Create opportunities for intergenerational interaction"
            ])
        
        # Size-based strategies
        if size == "small":
            strategies.extend([
                "Facilitate group discussion and dialogue",
                "Use roundtable format for sharing perspectives",
                "Adapt content based on direct audience feedback"
            ])
        elif size == "medium":
            strategies.extend([
                "Incorporate small group breakouts",
                "Use polling and audience response systems",
                "Balance presentation with interactive elements"
            ])
        elif size == "large":
            strategies.extend([
                "Use storytelling to create emotional connection",
                "Incorporate physical movement or standing when appropriate",
                "Use visual aids visible from all areas of the venue"
            ])
        
        return strategies
    
    def _generate_custom_approach(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a custom approach based on audience parameters"""
        expertise_level = parameters.get("expertise_level", "mixed")
        age_group = parameters.get("age_group", "mixed")
        industry = parameters.get("industry", "general")
        
        approach = {
            "opening_strategy": self._recommend_opening_strategy(expertise_level, age_group),
            "content_organization": self._recommend_content_organization(expertise_level),
            "key_messaging_approach": self._recommend_messaging_approach(expertise_level, industry),
            "visual_aid_recommendations": self._recommend_visual_approach(expertise_level, age_group),
            "closing_strategy": "Summarize key points and provide clear next steps"
        }
        
        return approach
    
    def _recommend_opening_strategy(self, expertise_level: str, age_group: str) -> str:
        """Recommend an opening strategy based on expertise and age"""
        if expertise_level == "novice" and age_group in ["youth", "young_adult"]:
            return "Start with an engaging story or surprising fact to build interest"
        elif expertise_level == "expert":
            return "Begin with a thought-provoking question or recent development in the field"
        elif age_group == "senior":
            return "Open with context and clear statement of purpose before delving into content"
        else:
            return "Start with a relatable scenario that demonstrates the relevance of the topic"
    
    def _recommend_content_organization(self, expertise_level: str) -> str:
        """Recommend content organization based on expertise level"""
        if expertise_level == "novice":
            return "Sequential building of concepts with clear transitions between topics"
        elif expertise_level == "expert":
            return "Thematic organization with emphasis on connections between advanced concepts"
        elif expertise_level == "mixed":
            return "Core concepts first with progressive layers of complexity and optional deep dives"
        else:
            return "Balanced approach with clear structure and moderate conceptual jumps"
    
    def _recommend_messaging_approach(self, expertise_level: str, industry: str) -> str:
        """Recommend messaging approach based on expertise and industry"""
        if industry == "technical" or industry == "scientific":
            if expertise_level == "expert":
                return "Focus on methodologies, innovations, and technical implications"
            else:
                return "Emphasize practical applications while providing necessary technical background"
        elif industry == "business" or industry == "corporate":
            return "Highlight business value, ROI, and strategic implications"
        elif industry == "education":
            return "Focus on learning outcomes and practical application of concepts"
        else:
            return "Balance informational content with practical relevance and engaging delivery"
    
    def _recommend_visual_approach(self, expertise_level: str, age_group: str) -> str:
        """Recommend visual approach based on expertise and age"""
        if expertise_level == "novice":
            return "Use simplified visuals with clear labels and minimal text"
        elif expertise_level == "expert":
            return "Include detailed data visualizations and complex models when relevant"
        
        if age_group in ["youth", "young_adult"]:
            return "Use modern design with dynamic elements and multimedia"
        elif age_group == "senior":
            return "Ensure high contrast, readable text, and clear visual hierarchy"
        
        return "Balance visual appeal with informational clarity, using consistent design elements"
    
    def _recommend_content_focus(self, audience_data: Dict[str, Any], topic: str, purpose: str) -> List[str]:
        """Recommend content focus based on audience, topic and purpose"""
        focus_points = []
        
        # Consider audience expertise
        expertise = audience_data.get("expertise_level", "intermediate")
        if expertise == "novice":
            focus_points.append("Focus on fundamental concepts and practical applications")
        elif expertise == "expert":
            focus_points.append("Emphasize advanced concepts, latest developments, and nuanced analysis")
        else:
            focus_points.append("Balance foundational concepts with more advanced applications")
        
        # Consider audience interests
        interests = audience_data.get("key_interests", [])
        if interests:
            focus_points.append(f"Connect {topic} to audience interests: {', '.join(interests[:3])}")
        
        # Consider purpose
        if purpose == "inform":
            focus_points.append("Prioritize clarity, organization, and comprehensive coverage of key points")
        elif purpose == "persuade":
            focus_points.append("Focus on compelling evidence, addressing counterarguments, and clear benefits")
        elif purpose == "entertain":
            focus_points.append("Emphasize engaging stories, humor, and relatable examples")
        elif purpose == "inspire":
            focus_points.append("Highlight vision, possibilities, and emotional connection")
        elif purpose == "instruct":
            focus_points.append("Focus on clear steps, demonstrations, and practical application")
        
        return focus_points
    
    def _recommend_communication_style(self, audience_data: Dict[str, Any], purpose: str) -> Dict[str, str]:
        """Recommend communication style based on audience and purpose"""
        style = {}
        
        # Get audience preferences
        preferences = audience_data.get("preferences", {})
        
        # Determine formality
        formality = preferences.get("formality", "moderate")
        style["formality"] = formality
        
        # Determine tone
        if purpose == "inform":
            style["tone"] = "clear and objective"
        elif purpose == "persuade":
            style["tone"] = "confident and compelling"
        elif purpose == "entertain":
            style["tone"] = "energetic and engaging"
        elif purpose == "inspire":
            style["tone"] = "passionate and visionary"
        elif purpose == "instruct":
            style["tone"] = "clear and authoritative"
        else:
            style["tone"] = preferences.get("tone", "balanced")
        
        # Determine pace
        expertise = audience_data.get("expertise_level", "intermediate")
        if expertise == "novice":
            style["pace"] = "measured with ample explanation"
        elif expertise == "expert":
            style["pace"] = "efficient with focused elaboration"
        else:
            style["pace"] = "moderate with targeted elaboration"
        
        # Determine language
        style["language"] = preferences.get("language_style", "clear and accessible")
        
        return style
    
    def _recommend_structure(self, audience_data: Dict[str, Any], purpose: str) -> Dict[str, str]:
        """Recommend presentation structure based on audience and purpose"""
        structure = {}
        
        # Determine introduction
        if purpose == "inform" or purpose == "instruct":
            structure["introduction"] = "Clear agenda and objectives"
        elif purpose == "persuade":
            structure["introduction"] = "Compelling problem statement or opportunity"
        elif purpose == "entertain":
            structure["introduction"] = "Engaging hook or story"
        elif purpose == "inspire":
            structure["introduction"] = "Powerful vision or challenge"
        
        # Determine body structure
        expertise = audience_data.get("expertise_level", "intermediate")
        if expertise == "novice":
            structure["body"] = "Sequential with clear transitions between concepts"
        elif expertise == "expert":
            structure["body"] = "Conceptual with emphasis on connections and implications"
        else:
            structure["body"] = "Balanced with logical flow and appropriate depth"
        
        # Determine conclusion
        if purpose == "inform":
            structure["conclusion"] = "Summary of key points and significance"
        elif purpose == "persuade":
            structure["conclusion"] = "Clear call to action with reinforced benefits"
        elif purpose == "entertain":
            structure["conclusion"] = "Memorable closing that ties back to opening"
        elif purpose == "inspire":
            structure["conclusion"] = "Motivational call to action and future vision"
        elif purpose == "instruct":
            structure["conclusion"] = "Summary of process and next steps for application"
        
        return structure
    
    def _recommend_examples(self, audience_data: Dict[str, Any], topic: str) -> List[str]:
        """Recommend examples and analogies based on audience and topic"""
        examples = []
        
        # Consider audience interests
        interests = audience_data.get("key_interests", [])
        if interests:
            examples.append(f"Draw analogies between {topic} and {interests[0] if interests else 'relevant field'}")
        
        # Consider audience demographics
        demographics = audience_data.get("demographics", {})
        if "industry" in demographics:
            examples.append(f"Use examples from {demographics['industry']} industry")
        
        # Consider audience expertise
        expertise = audience_data.get("expertise_level", "intermediate")
        if expertise == "novice":
            examples.append("Use familiar everyday analogies to explain complex concepts")
        elif expertise == "expert":
            examples.append("Reference advanced case studies and specific implementations")
        else:
            examples.append("Balance familiar examples with field-specific applications")
        
        # Add general recommendation
        examples.append(f"Ensure examples are current and directly relevant to {topic}")
        
        return examples
    
    def _recommend_speaking_techniques(self, audience_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Recommend speaking techniques based on audience"""
        techniques = []
        
        # Consider audience preferences
        preferences = audience_data.get("preferences", {})
        
        # Add specific techniques
        techniques.append({
            "technique": "Vocal variety",
            "application": preferences.get("vocal_variety", "Moderate variation in pace, pitch, and volume")
        })
        
        techniques.append({
            "technique": "Movement and gestures",
            "application": preferences.get("movement", "Purposeful movement with natural gestures")
        })
        
        techniques.append({
            "technique": "Eye contact",
            "application": preferences.get("eye_contact", "Regular eye contact across the audience")
        })
        
        techniques.append({
            "technique": "Engagement methods",
            "application": preferences.get("engagement", "Balance presentation with interactive elements")
        })
        
        return techniques
    
    def _recommend_visual_aids(self, audience_data: Dict[str, Any]) -> Dict[str, str]:
        """Recommend visual aids based on audience"""
        visual_aids = {}
        
        # Consider audience preferences
        preferences = audience_data.get("preferences", {})
        
        # Determine visual style
        visual_aids["style"] = preferences.get("visual_style", "Clean and professional with clear hierarchy")
        
        # Determine text usage
        expertise = audience_data.get("expertise_level", "intermediate")
        if expertise == "novice":
            visual_aids["text"] = "Minimal text with clear explanations"
        elif expertise == "expert":
            visual_aids["text"] = "Concise text with relevant technical details"
        else:
            visual_aids["text"] = "Balanced text with key points highlighted"
        
        # Determine visuals
        visual_aids["visuals"] = preferences.get("visual_content", "Mix of data visualizations, diagrams, and relevant imagery")
        
        # Determine density
        visual_aids["density"] = preferences.get("content_density", "Moderate with clear focus on key points")
        
        return visual_aids
    
    def _extract_feedback_themes(self, feedback_points: List[str]) -> Dict[str, int]:
        """Extract themes from feedback points"""
        themes = {
            "content": 0,
            "delivery": 0,
            "engagement": 0,
            "structure": 0,
            "visuals": 0,
            "clarity": 0,
            "relevance": 0,
            "technical_depth": 0
        }
        
        # Simple keyword matching for theme extraction
        for point in feedback_points:
            point_lower = point.lower()
            
            if any(word in point_lower for word in ["content", "information", "material", "topic"]):
                themes["content"] += 1
            
            if any(word in point_lower for word in ["delivery", "speaking", "voice", "tone", "pace"]):
                themes["delivery"] += 1
            
            if any(word in point_lower for word in ["engage", "interact", "interest", "boring", "exciting"]):
                themes["engagement"] += 1
            
            if any(word in point_lower for word in ["structure", "organization", "flow", "transition"]):
                themes["structure"] += 1
            
            if any(word in point_lower for word in ["visual", "slide", "graph", "chart", "image"]):
                themes["visuals"] += 1
            
            if any(word in point_lower for word in ["clear", "unclear", "confusing", "understand"]):
                themes["clarity"] += 1
            
            if any(word in point_lower for word in ["relevant", "irrelevant", "applicable", "useful"]):
                themes["relevance"] += 1
            
            if any(word in point_lower for word in ["technical", "depth", "detailed", "complex", "simple"]):
                themes["technical_depth"] += 1
        
        # Remove themes with no matches
        return {k: v for k, v in themes.items() if v > 0}
    
    def _extract_question_themes(self, questions: List[str]) -> Dict[str, int]:
        """Extract themes from audience questions"""
        themes = {
            "clarification": 0,
            "application": 0,
            "extension": 0,
            "challenge": 0,
            "comparison": 0,
            "technical": 0,
            "future_implications": 0,
            "personal_experience": 0
        }
        
        # Simple keyword matching for theme extraction
        for question in questions:
            question_lower = question.lower()
            
            if any(word in question_lower for word in ["mean", "define", "explain", "what is", "how does"]):
                themes["clarification"] += 1
            
            if any(word in question_lower for word in ["apply", "use", "implement", "practice", "example"]):
                themes["application"] += 1
            
            if any(word in question_lower for word in ["more", "beyond", "further", "addition", "also"]):
                themes["extension"] += 1
            
            if any(word in question_lower for word in ["disagree", "challenge", "problem", "issue", "concern"]):
                themes["challenge"] += 1
            
            if any(word in question_lower for word in ["compare", "difference", "similar", "versus", "better"]):
                themes["comparison"] += 1
            
            if any(word in question_lower for word in ["technical", "specific", "detail", "process", "method"]):
                themes["technical"] += 1
            
            if any(word in question_lower for word in ["future", "next", "trend", "develop", "evolve"]):
                themes["future_implications"] += 1
            
            if any(word in question_lower for word in ["experience", "personal", "yourself", "opinion"]):
                themes["personal_experience"] += 1
        
        # Remove themes with no matches
        return {k: v for k, v in themes.items() if v > 0}
    
    def _generate_improvement_recommendations(self, audience_data: Dict[str, Any], engagement_analysis: str, feedback_themes: Dict[str, int], question_themes: Dict[str, int]) -> List[Dict[str, str]]:
        """Generate improvement recommendations based on audience feedback"""
        recommendations = []
        
        # Address engagement level
        if engagement_analysis == "low":
            recommendations.append({
                "area": "Engagement",
                "recommendation": "Increase interactive elements and audience participation",
                "priority": "high"
            })
        
        # Address top feedback themes
        if feedback_themes:
            top_theme = max(feedback_themes.items(), key=lambda x: x[1])[0]
            
            if top_theme == "content":
                recommendations.append({
                    "area": "Content",
                    "recommendation": "Refine content to better match audience expertise level and interests",
                    "priority": "high"
                })
            elif top_theme == "delivery":
                recommendations.append({
                    "area": "Delivery",
                    "recommendation": "Work on pace, vocal variety, and confidence in presentation",
                    "priority": "high"
                })
            elif top_theme == "engagement":
                recommendations.append({
                    "area": "Engagement",
                    "recommendation": "Incorporate more interactive elements and audience involvement",
                    "priority": "high"
                })
            elif top_theme == "structure":
                recommendations.append({
                    "area": "Structure",
                    "recommendation": "Improve organization with clearer transitions and signposting",
                    "priority": "high"
                })
            elif top_theme == "visuals":
                recommendations.append({
                    "area": "Visuals",
                    "recommendation": "Enhance visual aids with clearer graphics and less text",
                    "priority": "high"
                })
            elif top_theme == "clarity":
                recommendations.append({
                    "area": "Clarity",
                    "recommendation": "Simplify explanations and define technical terms more clearly",
                    "priority": "high"
                })
            elif top_theme == "relevance":
                recommendations.append({
                    "area": "Relevance",
                    "recommendation": "Connect content more explicitly to audience needs and interests",
                    "priority": "high"
                })
            elif top_theme == "technical_depth":
                recommendations.append({
                    "area": "Technical Depth",
                    "recommendation": f"Adjust technical depth to better match audience expertise level",
                    "priority": "high"
                })
        
        # Address question themes
        if "clarification" in question_themes and question_themes["clarification"] > 1:
            recommendations.append({
                "area": "Clarity",
                "recommendation": "Define terms more clearly and provide additional context for concepts",
                "priority": "medium"
            })
        
        if "application" in question_themes and question_themes["application"] > 1:
            recommendations.append({
                "area": "Application",
                "recommendation": "Include more practical examples and real-world applications",
                "priority": "medium"
            })
        
        if "technical" in question_themes and question_themes["technical"] > 1:
            expertise = audience_data.get("expertise_level", "intermediate")
            if expertise == "expert":
                recommendations.append({
                    "area": "Technical Depth",
                    "recommendation": "Increase technical detail to better satisfy expert audience",
                    "priority": "medium"
                })
            else:
                recommendations.append({
                    "area": "Technical Depth",
                    "recommendation": "Provide technical details in supplementary materials",
                    "priority": "medium"
                })
        
        # Add audience-specific recommendation
        audience_type = audience_data.get("name", "this audience")
        expertise = audience_data.get("expertise_level", "intermediate")
        
        recommendations.append({
            "area": "Audience Alignment",
            "recommendation": f"Better tailor your approach to {audience_type} by focusing on their {expertise} level and specific interests",
            "priority": "medium"
        })
        
        return recommendations
    
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
        audience_types_count = len(self.audience_data.get("audience_types", {}))
        return {
            "status": "healthy" if audience_types_count > 0 else "degraded",
            "server_name": self.server_name,
            "server_version": self.server_version,
            "protocol_version": self.protocol_version,
            "audience_types_loaded": audience_types_count,
            "timestamp": datetime.now().isoformat()
        }

# For testing purposes
if __name__ == "__main__":
    server = AudienceKnowledgeMCPServer()
    
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
    read_response = server.handle_request("resources/read", {"uri": "audience://technical"})
    print(json.dumps(read_response, indent=2))
    
    # Test MCP tools list
    print("\n=== MCP Tools List ===")
    tools_response = server.handle_request("tools/list", {})
    print(json.dumps(tools_response, indent=2))
    
    # Test MCP tool call
    print("\n=== MCP Tool Call ===")
    tool_response = server.handle_request("tools/call", {
        "name": "analyzeAudience", 
        "parameters": {
            "expertise_level": "expert",
            "age_group": "middle_aged",
            "industry": "technology"
        }
    })
    print(json.dumps(tool_response, indent=2))
