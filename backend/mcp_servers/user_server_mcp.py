#!/usr/bin/env python3
"""
MCP-compliant User Knowledge Server for Speech Coach
Provides user-specific speaking profiles and improvement tracking
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserKnowledgeMCPServer:
    """
    MCP-compliant User Knowledge Server that provides user-specific speaking profiles,
    history, preferences, and improvement tracking.
    """
    
    def __init__(self):
        """Initialize the User Knowledge Server with MCP capabilities"""
        self.users_data = self._load_user_knowledge()
        self.protocol_version = "1.0"
        self.server_name = "user-knowledge-server"
        self.server_version = "1.0.0"
        logger.info(f"MCP User Knowledge Server initialized, protocol v{self.protocol_version}")

    def _load_user_knowledge(self) -> Dict[str, Any]:
        """Load user knowledge from JSON resource"""
        try:
            resource_path = os.path.join(os.path.dirname(__file__), 'resources', 'user_knowledge.json')
            with open(resource_path, 'r') as f:
                users_data = json.load(f)
            logger.info(f"User knowledge loaded successfully with {len(users_data.get('users', {}))} users")
            return users_data
        except Exception as e:
            logger.error(f"Error loading user knowledge: {e}")
            # Fallback to empty knowledge base
            return {"users": {}, "skill_levels": ["beginner", "intermediate", "advanced", "expert"]}

    # MCP Resource Methods
    def list_resources(self) -> Dict[str, Any]:
        """MCP resources/list endpoint implementation"""
        resources = []
        
        # Add direct resources for each user
        for user_id, user_data in self.users_data.get("users", {}).items():
            resources.append({
                "uri": f"user://{user_id}",
                "name": f"user-{user_id}",
                "title": f"User Profile: {user_data.get('name', user_id)}",
                "description": f"Speaking profile and history for user {user_data.get('name', user_id)}",
                "mimeType": "application/json"
            })
        
        # Add resource for user profiles directory
        resources.append({
            "uri": "user://profiles",
            "name": "user-profiles",
            "title": "User Profiles Directory",
            "description": "List of all user profiles with basic information",
            "mimeType": "application/json"
        })
        
        # Add resource for user skill levels
        resources.append({
            "uri": "user://skill-levels",
            "name": "user-skill-levels",
            "title": "User Skill Levels",
            "description": "Available user skill level classifications",
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
                "uriTemplate": "user://{user_id}/history",
                "name": "user-history",
                "title": "User Speaking History",
                "description": "Historical speaking data for a specific user",
                "mimeType": "application/json",
                "parameters": [
                    {
                        "name": "user_id",
                        "description": "User identifier",
                        "required": True,
                        "schema": {"type": "string", "enum": list(self.users_data.get("users", {}).keys())}
                    }
                ]
            },
            {
                "uriTemplate": "user://{user_id}/preferences",
                "name": "user-preferences",
                "title": "User Speaking Preferences",
                "description": "Speaking preferences for a specific user",
                "mimeType": "application/json",
                "parameters": [
                    {
                        "name": "user_id",
                        "description": "User identifier",
                        "required": True,
                        "schema": {"type": "string", "enum": list(self.users_data.get("users", {}).keys())}
                    }
                ]
            },
            {
                "uriTemplate": "user://{user_id}/improvement/{metric}",
                "name": "user-improvement-metric",
                "title": "User Improvement in Specific Metric",
                "description": "Improvement tracking for a specific speaking metric",
                "mimeType": "application/json",
                "parameters": [
                    {
                        "name": "user_id",
                        "description": "User identifier",
                        "required": True,
                        "schema": {"type": "string", "enum": list(self.users_data.get("users", {}).keys())}
                    },
                    {
                        "name": "metric",
                        "description": "Speaking metric to track improvement",
                        "required": True,
                        "schema": {"type": "string", "enum": ["pace", "filler_words", "vocal_variety", "confidence", "all"]}
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
            # Handle direct user resources
            if uri.startswith("user://") and not uri.endswith("profiles") and not uri.endswith("skill-levels"):
                parts = uri.replace("user://", "").split("/")
                user_id = parts[0]
                
                if user_id in self.users_data.get("users", {}):
                    user_data = self.users_data["users"][user_id]
                    
                    # Return complete user profile
                    if len(parts) == 1:
                        return {
                            "jsonrpc": "2.0",
                            "result": {
                                "uri": uri,
                                "mimeType": "application/json",
                                "content": user_data
                            }
                        }
                    
                    # Return user history
                    elif len(parts) == 2 and parts[1] == "history":
                        if "speaking_history" in user_data:
                            return {
                                "jsonrpc": "2.0",
                                "result": {
                                    "uri": uri,
                                    "mimeType": "application/json",
                                    "content": {
                                        "user_id": user_id,
                                        "user_name": user_data.get("name", user_id),
                                        "history": user_data["speaking_history"]
                                    }
                                }
                            }
                    
                    # Return user preferences
                    elif len(parts) == 2 and parts[1] == "preferences":
                        if "preferences" in user_data:
                            return {
                                "jsonrpc": "2.0",
                                "result": {
                                    "uri": uri,
                                    "mimeType": "application/json",
                                    "content": {
                                        "user_id": user_id,
                                        "user_name": user_data.get("name", user_id),
                                        "preferences": user_data["preferences"]
                                    }
                                }
                            }
                    
                    # Return user improvement metrics
                    elif len(parts) == 3 and parts[1] == "improvement":
                        metric = parts[2]
                        if "improvement" in user_data:
                            if metric == "all":
                                content = {
                                    "user_id": user_id,
                                    "user_name": user_data.get("name", user_id),
                                    "improvement_metrics": user_data["improvement"]
                                }
                            elif metric in user_data["improvement"]:
                                content = {
                                    "user_id": user_id,
                                    "user_name": user_data.get("name", user_id),
                                    "metric": metric,
                                    "improvement_data": user_data["improvement"][metric]
                                }
                            else:
                                return self._error_response(f"Metric {metric} not found for user {user_id}")
                                
                            return {
                                "jsonrpc": "2.0",
                                "result": {
                                    "uri": uri,
                                    "mimeType": "application/json",
                                    "content": content
                                }
                            }
            
            # Handle user profiles directory
            elif uri == "user://profiles":
                profiles = {}
                for user_id, user_data in self.users_data.get("users", {}).items():
                    profiles[user_id] = {
                        "name": user_data.get("name", user_id),
                        "skill_level": user_data.get("skill_level", "beginner"),
                        "presentation_count": len(user_data.get("speaking_history", [])),
                        "preferred_domains": user_data.get("preferences", {}).get("preferred_domains", []),
                    }
                
                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "uri": uri,
                        "mimeType": "application/json",
                        "content": {
                            "profiles_count": len(profiles),
                            "profiles": profiles
                        }
                    }
                }
            
            # Handle skill levels resource
            elif uri == "user://skill-levels":
                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "uri": uri,
                        "mimeType": "application/json",
                        "content": {
                            "available_skill_levels": self.users_data.get("skill_levels", ["beginner", "intermediate", "advanced", "expert"]),
                            "level_descriptions": {
                                "beginner": "New to public speaking, focusing on core skills",
                                "intermediate": "Has basic skills, working on confidence and style",
                                "advanced": "Comfortable speaker working on advanced techniques",
                                "expert": "Experienced speaker refining mastery and teaching others"
                            }
                        }
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
                "name": "getUserProfile",
                "description": "Get complete user profile with history and preferences",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User identifier",
                            "enum": list(self.users_data.get("users", {}).keys())
                        }
                    },
                    "required": ["user_id"]
                }
            },
            {
                "name": "trackImprovement",
                "description": "Track user improvement over time for a specific metric",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User identifier",
                            "enum": list(self.users_data.get("users", {}).keys())
                        },
                        "metric": {
                            "type": "string",
                            "description": "Speaking metric to track",
                            "enum": ["pace", "filler_words", "vocal_variety", "confidence"]
                        },
                        "time_period": {
                            "type": "string",
                            "description": "Time period to analyze",
                            "enum": ["week", "month", "quarter", "year", "all"]
                        }
                    },
                    "required": ["user_id", "metric"]
                }
            },
            {
                "name": "getPersonalizedTips",
                "description": "Get personalized speaking tips based on user profile and history",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User identifier",
                            "enum": list(self.users_data.get("users", {}).keys())
                        },
                        "focus_area": {
                            "type": "string",
                            "description": "Area to focus tips on",
                            "enum": ["pace", "filler_words", "vocal_variety", "confidence", "structure", "all"]
                        },
                        "domain": {
                            "type": "string",
                            "description": "Optional speaking domain to consider"
                        }
                    },
                    "required": ["user_id"]
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
            if tool_name == "getUserProfile":
                return self._get_user_profile_tool(parameters)
            elif tool_name == "trackImprovement":
                return self._track_improvement_tool(parameters)
            elif tool_name == "getPersonalizedTips":
                return self._get_personalized_tips_tool(parameters)
            else:
                return self._error_response(f"Unknown tool: {tool_name}", -32601)
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return self._error_response(f"Error calling tool: {str(e)}")
    
    def _get_user_profile_tool(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Implementation of getUserProfile tool"""
        user_id = parameters.get("user_id")
        
        if not user_id or user_id not in self.users_data.get("users", {}):
            return self._error_response("Invalid user_id")
        
        user_data = self.users_data["users"][user_id]
        
        # Format the response
        profile = {
            "user_id": user_id,
            "name": user_data.get("name", user_id),
            "skill_level": user_data.get("skill_level", "beginner"),
            "preferences": user_data.get("preferences", {}),
            "speaking_stats": {
                "total_presentations": len(user_data.get("speaking_history", [])),
                "average_scores": self._calculate_average_scores(user_data),
                "top_strengths": user_data.get("strengths", []),
                "improvement_areas": user_data.get("improvement_areas", [])
            },
            "recent_history": user_data.get("speaking_history", [])[:3] if user_data.get("speaking_history") else []
        }
        
        return {
            "jsonrpc": "2.0",
            "result": profile
        }
    
    def _track_improvement_tool(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Implementation of trackImprovement tool"""
        user_id = parameters.get("user_id")
        metric = parameters.get("metric")
        time_period = parameters.get("time_period", "all")
        
        if not user_id or user_id not in self.users_data.get("users", {}):
            return self._error_response("Invalid user_id")
        
        user_data = self.users_data["users"][user_id]
        
        if "improvement" not in user_data or metric not in user_data["improvement"]:
            return self._error_response(f"No improvement data found for metric: {metric}")
        
        metric_data = user_data["improvement"][metric]
        
        # Calculate trend and improvement percentage
        if len(metric_data) >= 2:
            start_value = metric_data[0].get("value", 0)
            current_value = metric_data[-1].get("value", 0)
            
            if start_value > 0:
                improvement_percentage = ((current_value - start_value) / start_value) * 100
            else:
                improvement_percentage = 0
                
            trend_direction = "improving" if improvement_percentage > 0 else "declining"
        else:
            improvement_percentage = 0
            trend_direction = "stable"
        
        # Format the response
        improvement_data = {
            "user_id": user_id,
            "user_name": user_data.get("name", user_id),
            "metric": metric,
            "time_period": time_period,
            "trend_summary": {
                "direction": trend_direction,
                "improvement_percentage": round(improvement_percentage, 2),
                "start_value": metric_data[0].get("value", 0) if metric_data else 0,
                "current_value": metric_data[-1].get("value", 0) if metric_data else 0
            },
            "data_points": metric_data
        }
        
        return {
            "jsonrpc": "2.0",
            "result": improvement_data
        }
    
    def _get_personalized_tips_tool(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Implementation of getPersonalizedTips tool"""
        user_id = parameters.get("user_id")
        focus_area = parameters.get("focus_area", "all")
        domain = parameters.get("domain", "general")
        
        if not user_id or user_id not in self.users_data.get("users", {}):
            return self._error_response("Invalid user_id")
        
        user_data = self.users_data["users"][user_id]
        
        # Get user skill level
        skill_level = user_data.get("skill_level", "beginner")
        
        # Determine user's weak areas
        weak_areas = user_data.get("improvement_areas", [])
        
        # Generate personalized tips based on user data
        tips = self._generate_tips(skill_level, focus_area, domain, weak_areas)
        
        # Format the response
        personalized_tips = {
            "user_id": user_id,
            "user_name": user_data.get("name", user_id),
            "skill_level": skill_level,
            "focus_area": focus_area,
            "domain": domain,
            "personalized_tips": tips
        }
        
        return {
            "jsonrpc": "2.0",
            "result": personalized_tips
        }
    
    # MCP Prompts Methods
    def list_prompts(self) -> Dict[str, Any]:
        """MCP prompts/list endpoint implementation"""
        prompts = [
            {
                "name": "user-improvement-report",
                "title": "User Improvement Report",
                "description": "Generate a report on user's improvement in speaking skills",
                "arguments": [
                    {
                        "name": "user_id",
                        "type": "string",
                        "description": "User identifier",
                        "enum": list(self.users_data.get("users", {}).keys()),
                        "required": True
                    },
                    {
                        "name": "time_frame",
                        "type": "string",
                        "description": "Time frame for the report",
                        "enum": ["last_presentation", "last_month", "last_quarter", "all_time"],
                        "required": False
                    }
                ]
            },
            {
                "name": "personalized-practice-plan",
                "title": "Personalized Practice Plan",
                "description": "Create a personalized speaking practice plan for the user",
                "arguments": [
                    {
                        "name": "user_id",
                        "type": "string",
                        "description": "User identifier",
                        "enum": list(self.users_data.get("users", {}).keys()),
                        "required": True
                    },
                    {
                        "name": "duration_weeks",
                        "type": "number",
                        "description": "Duration of practice plan in weeks",
                        "required": False
                    },
                    {
                        "name": "intensity",
                        "type": "string",
                        "description": "Intensity of practice plan",
                        "enum": ["light", "moderate", "intensive"],
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
        if prompt_name == "user-improvement-report":
            return {
                "jsonrpc": "2.0",
                "result": {
                    "name": "user-improvement-report",
                    "title": "User Improvement Report",
                    "description": "Generate a report on user's improvement in speaking skills",
                    "template": "Generate a speaking improvement report for {{user_name}}{{#time_frame}} over {{time_frame}}{{/time_frame}}. Focus on progress in key metrics and provide recommendations for continued growth.",
                    "arguments": [
                        {
                            "name": "user_id",
                            "type": "string",
                            "description": "User identifier",
                            "enum": list(self.users_data.get("users", {}).keys()),
                            "required": True
                        },
                        {
                            "name": "user_name",
                            "type": "string",
                            "description": "User's name",
                            "required": True
                        },
                        {
                            "name": "time_frame",
                            "type": "string",
                            "description": "Time frame for the report",
                            "enum": ["the last presentation", "the past month", "the past quarter", "all time"],
                            "required": False
                        }
                    ]
                }
            }
        elif prompt_name == "personalized-practice-plan":
            return {
                "jsonrpc": "2.0",
                "result": {
                    "name": "personalized-practice-plan",
                    "title": "Personalized Practice Plan",
                    "description": "Create a personalized speaking practice plan for the user",
                    "template": "Create a {{#duration_weeks}}{{duration_weeks}}-week {{/duration_weeks}}{{#intensity}}{{intensity}} {{/intensity}}speaking practice plan for {{user_name}}, a {{skill_level}} speaker. Focus on improving {{#focus_areas}}{{focus_areas}}{{/focus_areas}}{{^focus_areas}}overall speaking skills{{/focus_areas}}.",
                    "arguments": [
                        {
                            "name": "user_id",
                            "type": "string",
                            "description": "User identifier",
                            "enum": list(self.users_data.get("users", {}).keys()),
                            "required": True
                        },
                        {
                            "name": "user_name",
                            "type": "string",
                            "description": "User's name",
                            "required": True
                        },
                        {
                            "name": "skill_level",
                            "type": "string",
                            "description": "User's speaking skill level",
                            "enum": ["beginner", "intermediate", "advanced", "expert"],
                            "required": True
                        },
                        {
                            "name": "duration_weeks",
                            "type": "number",
                            "description": "Duration of practice plan in weeks",
                            "required": False
                        },
                        {
                            "name": "intensity",
                            "type": "string",
                            "description": "Intensity of practice plan",
                            "enum": ["light", "moderate", "intensive"],
                            "required": False
                        },
                        {
                            "name": "focus_areas",
                            "type": "string",
                            "description": "Specific areas to focus on",
                            "required": False
                        }
                    ]
                }
            }
        else:
            return self._error_response(f"Prompt not found: {prompt_name}", -32001)
    
    # Helper methods for user knowledge
    def _calculate_average_scores(self, user_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate average scores across speaking metrics"""
        history = user_data.get("speaking_history", [])
        if not history:
            return {
                "pace": 0,
                "filler_words": 0,
                "vocal_variety": 0,
                "confidence": 0,
                "overall": 0
            }
        
        # Initialize counters
        metrics = {
            "pace": {"total": 0, "count": 0},
            "filler_words": {"total": 0, "count": 0},
            "vocal_variety": {"total": 0, "count": 0},
            "confidence": {"total": 0, "count": 0},
            "overall": {"total": 0, "count": 0}
        }
        
        # Aggregate scores
        for entry in history:
            scores = entry.get("scores", {})
            for metric, counter in metrics.items():
                if metric in scores:
                    counter["total"] += scores[metric]
                    counter["count"] += 1
        
        # Calculate averages
        averages = {}
        for metric, counter in metrics.items():
            if counter["count"] > 0:
                averages[metric] = round(counter["total"] / counter["count"], 1)
            else:
                averages[metric] = 0
        
        return averages
    
    def _generate_tips(self, skill_level: str, focus_area: str, domain: str, weak_areas: List[str]) -> List[Dict[str, Any]]:
        """Generate personalized tips based on user data"""
        all_tips = {
            "pace": [
                {
                    "title": "Controlled Pacing",
                    "description": "Practice speaking at a steady rate, aiming for 120-140 words per minute for most contexts.",
                    "skill_level": "beginner"
                },
                {
                    "title": "Strategic Pauses",
                    "description": "Use deliberate pauses to emphasize key points and give listeners time to process information.",
                    "skill_level": "intermediate"
                },
                {
                    "title": "Dynamic Pace Shifting",
                    "description": "Master changing your pace intentionally - slower for complex points, faster for engaging stories.",
                    "skill_level": "advanced"
                }
            ],
            "filler_words": [
                {
                    "title": "Filler Word Awareness",
                    "description": "Record yourself speaking and count how many times you use words like 'um', 'uh', 'like', and 'you know'.",
                    "skill_level": "beginner"
                },
                {
                    "title": "Replace Fillers with Pauses",
                    "description": "When tempted to use a filler word, practice replacing it with a deliberate pause instead.",
                    "skill_level": "intermediate"
                },
                {
                    "title": "Mindful Speaking Practice",
                    "description": "Develop a heightened awareness of your speech patterns through regular mindful speaking exercises.",
                    "skill_level": "advanced"
                }
            ],
            "vocal_variety": [
                {
                    "title": "Basic Voice Modulation",
                    "description": "Practice changing your volume and tone when speaking to add interest to your delivery.",
                    "skill_level": "beginner"
                },
                {
                    "title": "Pitch and Inflection",
                    "description": "Experiment with raising and lowering your pitch to emphasize different points and avoid monotone delivery.",
                    "skill_level": "intermediate"
                },
                {
                    "title": "Advanced Vocal Techniques",
                    "description": "Master vocal techniques like resonance, projection, and tonal quality to create a compelling speaking voice.",
                    "skill_level": "advanced"
                }
            ],
            "confidence": [
                {
                    "title": "Preparation Builds Confidence",
                    "description": "Thoroughly prepare and practice your content to build natural confidence in your delivery.",
                    "skill_level": "beginner"
                },
                {
                    "title": "Confident Body Language",
                    "description": "Stand tall with shoulders back, make eye contact, and use purposeful gestures to project confidence.",
                    "skill_level": "intermediate"
                },
                {
                    "title": "Authentic Presence",
                    "description": "Develop your unique speaking style that feels natural and allows your authentic personality to shine through.",
                    "skill_level": "advanced"
                }
            ],
            "structure": [
                {
                    "title": "Basic Three-Part Structure",
                    "description": "Organize your speeches with a clear introduction, body, and conclusion for easy understanding.",
                    "skill_level": "beginner"
                },
                {
                    "title": "Signposting and Transitions",
                    "description": "Use verbal signposts and smooth transitions to guide your audience through your content.",
                    "skill_level": "intermediate"
                },
                {
                    "title": "Advanced Structural Patterns",
                    "description": "Experiment with different structural patterns like problem-solution, chronological, or comparative frameworks.",
                    "skill_level": "advanced"
                }
            ]
        }
        
        # Select tips based on parameters
        selected_tips = []
        
        if focus_area == "all":
            # Include tips from all areas
            focus_areas = all_tips.keys()
        else:
            # Focus on specific area
            focus_areas = [focus_area]
        
        # Add tips based on skill level and focus areas
        for area in focus_areas:
            area_tips = all_tips.get(area, [])
            
            # Select tips appropriate for the skill level
            if skill_level == "beginner":
                relevant_tips = [tip for tip in area_tips if tip["skill_level"] == "beginner"]
            elif skill_level == "intermediate":
                relevant_tips = [tip for tip in area_tips if tip["skill_level"] in ["beginner", "intermediate"]]
            else:  # advanced or expert
                relevant_tips = area_tips
            
            # Prioritize tips for weak areas
            if area in weak_areas:
                for tip in relevant_tips:
                    tip["priority"] = "high"
                    selected_tips.append(tip)
            else:
                # Only add one tip for non-weak areas to avoid overwhelming
                if relevant_tips:
                    tip = relevant_tips[0]
                    tip["priority"] = "normal"
                    selected_tips.append(tip)
        
        # Add domain-specific tips if available
        if domain != "general":
            domain_tip = {
                "title": f"{domain.capitalize()} Domain Focus",
                "description": f"For {domain} speaking, focus on domain-specific terminology and presentation styles.",
                "skill_level": "all",
                "priority": "domain-specific"
            }
            selected_tips.append(domain_tip)
        
        return selected_tips
    
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
        users_count = len(self.users_data.get("users", {}))
        return {
            "status": "healthy" if users_count > 0 else "degraded",
            "server_name": self.server_name,
            "server_version": self.server_version,
            "protocol_version": self.protocol_version,
            "users_loaded": users_count,
            "timestamp": datetime.now().isoformat()
        }

# For testing purposes
if __name__ == "__main__":
    server = UserKnowledgeMCPServer()
    
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
    read_response = server.handle_request("resources/read", {"uri": "user://user1"})
    print(json.dumps(read_response, indent=2))
    
    # Test MCP tools list
    print("\n=== MCP Tools List ===")
    tools_response = server.handle_request("tools/list", {})
    print(json.dumps(tools_response, indent=2))
    
    # Test MCP tool call
    print("\n=== MCP Tool Call ===")
    tool_response = server.handle_request("tools/call", {
        "name": "getUserProfile", 
        "parameters": {
            "user_id": "user1"
        }
    })
    print(json.dumps(tool_response, indent=2))
