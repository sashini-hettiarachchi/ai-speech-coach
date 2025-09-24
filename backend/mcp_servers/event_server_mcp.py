#!/usr/bin/env python3
"""
MCP-compliant Event Knowledge Server for Speech Coach
Provides event-specific contexts and requirements for speaking situations
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventKnowledgeMCPServer:
    """
    MCP-compliant Event Knowledge Server that provides event-specific contexts,
    requirements, and best practices for different speaking situations.
    """
    
    def __init__(self):
        """Initialize the Event Knowledge Server with MCP capabilities"""
        self.events_data = self._load_event_knowledge()
        self.protocol_version = "1.0"
        self.server_name = "event-knowledge-server"
        self.server_version = "1.0.0"
        logger.info(f"MCP Event Knowledge Server initialized, protocol v{self.protocol_version}")

    def _load_event_knowledge(self) -> Dict[str, Any]:
        """Load event knowledge from JSON resource"""
        try:
            resource_path = os.path.join(os.path.dirname(__file__), 'resources', 'event_knowledge.json')
            with open(resource_path, 'r') as f:
                events_data = json.load(f)
            logger.info(f"Event knowledge loaded successfully with {len(events_data.get('event_types', {}))} event types")
            return events_data
        except Exception as e:
            logger.error(f"Error loading event knowledge: {e}")
            # Fallback to empty knowledge base
            return {"event_types": {}, "contexts": {}, "formats": []}

    # MCP Resource Methods
    def list_resources(self) -> Dict[str, Any]:
        """MCP resources/list endpoint implementation"""
        resources = []
        
        # Add direct resources for each event type
        for event_id, event_data in self.events_data.get("event_types", {}).items():
            resources.append({
                "uri": f"event://{event_id}",
                "name": f"event-{event_id}",
                "title": f"Event Type: {event_data.get('name', event_id)}",
                "description": f"Speaking guidelines for {event_data.get('name', event_id)} events",
                "mimeType": "application/json"
            })
        
        # Add resource for event contexts
        for context_id, context_data in self.events_data.get("contexts", {}).items():
            resources.append({
                "uri": f"event://context/{context_id}",
                "name": f"event-context-{context_id}",
                "title": f"Event Context: {context_data.get('name', context_id)}",
                "description": f"Speaking context information for {context_data.get('name', context_id)}",
                "mimeType": "application/json"
            })
        
        # Add resource for event formats
        resources.append({
            "uri": "event://formats",
            "name": "event-formats",
            "title": "Event Formats",
            "description": "Available event formats and their specifications",
            "mimeType": "application/json"
        })
        
        # Add resource for all event types
        resources.append({
            "uri": "event://types",
            "name": "event-types",
            "title": "Event Types",
            "description": "List of all event types with basic information",
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
                "uriTemplate": "event://{event_id}/requirements",
                "name": "event-requirements",
                "title": "Event Requirements",
                "description": "Specific requirements for an event type",
                "mimeType": "application/json",
                "parameters": [
                    {
                        "name": "event_id",
                        "description": "Event type identifier",
                        "required": True,
                        "schema": {"type": "string", "enum": list(self.events_data.get("event_types", {}).keys())}
                    }
                ]
            },
            {
                "uriTemplate": "event://{event_id}/best-practices",
                "name": "event-best-practices",
                "title": "Event Best Practices",
                "description": "Best practices for a specific event type",
                "mimeType": "application/json",
                "parameters": [
                    {
                        "name": "event_id",
                        "description": "Event type identifier",
                        "required": True,
                        "schema": {"type": "string", "enum": list(self.events_data.get("event_types", {}).keys())}
                    }
                ]
            },
            {
                "uriTemplate": "event://comparison/{event_id1}/{event_id2}",
                "name": "event-comparison",
                "title": "Event Type Comparison",
                "description": "Compare requirements and practices between two event types",
                "mimeType": "application/json",
                "parameters": [
                    {
                        "name": "event_id1",
                        "description": "First event type identifier",
                        "required": True,
                        "schema": {"type": "string", "enum": list(self.events_data.get("event_types", {}).keys())}
                    },
                    {
                        "name": "event_id2",
                        "description": "Second event type identifier",
                        "required": True,
                        "schema": {"type": "string", "enum": list(self.events_data.get("event_types", {}).keys())}
                    }
                ]
            },
            {
                "uriTemplate": "event://format/{format_id}",
                "name": "event-format",
                "title": "Event Format",
                "description": "Details about a specific event format",
                "mimeType": "application/json",
                "parameters": [
                    {
                        "name": "format_id",
                        "description": "Event format identifier",
                        "required": True,
                        "schema": {"type": "string", "enum": self.events_data.get("formats", [])}
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
            # Handle direct event type resources
            if uri.startswith("event://") and not uri.startswith("event://context/") and not uri.endswith("formats") and not uri.endswith("types"):
                parts = uri.replace("event://", "").split("/")
                event_id = parts[0]
                
                if event_id in self.events_data.get("event_types", {}):
                    event_data = self.events_data["event_types"][event_id]
                    
                    # Return complete event data
                    if len(parts) == 1:
                        return {
                            "jsonrpc": "2.0",
                            "result": {
                                "uri": uri,
                                "mimeType": "application/json",
                                "content": event_data
                            }
                        }
                    
                    # Return event requirements
                    elif len(parts) == 2 and parts[1] == "requirements":
                        if "requirements" in event_data:
                            return {
                                "jsonrpc": "2.0",
                                "result": {
                                    "uri": uri,
                                    "mimeType": "application/json",
                                    "content": {
                                        "event_id": event_id,
                                        "event_name": event_data.get("name", event_id),
                                        "requirements": event_data["requirements"]
                                    }
                                }
                            }
                    
                    # Return event best practices
                    elif len(parts) == 2 and parts[1] == "best-practices":
                        if "best_practices" in event_data:
                            return {
                                "jsonrpc": "2.0",
                                "result": {
                                    "uri": uri,
                                    "mimeType": "application/json",
                                    "content": {
                                        "event_id": event_id,
                                        "event_name": event_data.get("name", event_id),
                                        "best_practices": event_data["best_practices"]
                                    }
                                }
                            }
                    
                    # Handle event comparison
                    elif len(parts) == 3 and parts[0] == "comparison":
                        event_id1 = parts[1]
                        event_id2 = parts[2]
                        
                        if (event_id1 in self.events_data.get("event_types", {}) and 
                            event_id2 in self.events_data.get("event_types", {})):
                            
                            event_data1 = self.events_data["event_types"][event_id1]
                            event_data2 = self.events_data["event_types"][event_id2]
                            
                            comparison = self._compare_events(event_id1, event_id2, event_data1, event_data2)
                            
                            return {
                                "jsonrpc": "2.0",
                                "result": {
                                    "uri": uri,
                                    "mimeType": "application/json",
                                    "content": comparison
                                }
                            }
            
            # Handle event context resources
            elif uri.startswith("event://context/"):
                context_id = uri.replace("event://context/", "")
                
                if context_id in self.events_data.get("contexts", {}):
                    context_data = self.events_data["contexts"][context_id]
                    
                    return {
                        "jsonrpc": "2.0",
                        "result": {
                            "uri": uri,
                            "mimeType": "application/json",
                            "content": context_data
                        }
                    }
            
            # Handle event format resources
            elif uri == "event://formats":
                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "uri": uri,
                        "mimeType": "application/json",
                        "content": {
                            "available_formats": self.events_data.get("formats", []),
                            "format_details": self._get_format_details()
                        }
                    }
                }
            
            # Handle specific format resource
            elif uri.startswith("event://format/"):
                format_id = uri.replace("event://format/", "")
                
                if format_id in self.events_data.get("formats", []):
                    format_details = self._get_format_details().get(format_id, {})
                    
                    return {
                        "jsonrpc": "2.0",
                        "result": {
                            "uri": uri,
                            "mimeType": "application/json",
                            "content": format_details
                        }
                    }
            
            # Handle event types list
            elif uri == "event://types":
                types = {}
                for event_id, event_data in self.events_data.get("event_types", {}).items():
                    types[event_id] = {
                        "name": event_data.get("name", event_id),
                        "description": event_data.get("description", ""),
                        "typical_duration": event_data.get("typical_duration", ""),
                        "common_contexts": event_data.get("common_contexts", [])
                    }
                
                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "uri": uri,
                        "mimeType": "application/json",
                        "content": {
                            "event_types_count": len(types),
                            "event_types": types
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
                "name": "getEventRequirements",
                "description": "Get detailed requirements for a specific event type",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "event_id": {
                            "type": "string",
                            "description": "Event type identifier",
                            "enum": list(self.events_data.get("event_types", {}).keys())
                        }
                    },
                    "required": ["event_id"]
                }
            },
            {
                "name": "suggestEventType",
                "description": "Suggest the best event type based on parameters",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "audience_size": {
                            "type": "string",
                            "description": "Size of the audience",
                            "enum": ["small", "medium", "large"]
                        },
                        "formality": {
                            "type": "string",
                            "description": "Formality level of the event",
                            "enum": ["casual", "semiformal", "formal"]
                        },
                        "duration_minutes": {
                            "type": "number",
                            "description": "Available time in minutes"
                        },
                        "purpose": {
                            "type": "string",
                            "description": "Primary purpose of the speech",
                            "enum": ["inform", "persuade", "entertain", "inspire", "instruct"]
                        }
                    },
                    "required": ["purpose"]
                }
            },
            {
                "name": "formatGuidelines",
                "description": "Get guidelines for a specific event format",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "format_id": {
                            "type": "string",
                            "description": "Format identifier",
                            "enum": self.events_data.get("formats", [])
                        },
                        "include_examples": {
                            "type": "boolean",
                            "description": "Whether to include examples"
                        }
                    },
                    "required": ["format_id"]
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
            if tool_name == "getEventRequirements":
                return self._get_event_requirements_tool(parameters)
            elif tool_name == "suggestEventType":
                return self._suggest_event_type_tool(parameters)
            elif tool_name == "formatGuidelines":
                return self._format_guidelines_tool(parameters)
            else:
                return self._error_response(f"Unknown tool: {tool_name}", -32601)
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return self._error_response(f"Error calling tool: {str(e)}")
    
    def _get_event_requirements_tool(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Implementation of getEventRequirements tool"""
        event_id = parameters.get("event_id")
        
        if not event_id or event_id not in self.events_data.get("event_types", {}):
            return self._error_response("Invalid event_id")
        
        event_data = self.events_data["event_types"][event_id]
        
        # Format the response with detailed requirements
        requirements = {
            "event_id": event_id,
            "event_name": event_data.get("name", event_id),
            "basic_requirements": {
                "typical_duration": event_data.get("typical_duration", ""),
                "recommended_structure": event_data.get("structure", {}),
                "audience_expectations": event_data.get("audience_expectations", [])
            },
            "detailed_requirements": event_data.get("requirements", {}),
            "preparation_checklist": event_data.get("preparation_checklist", [])
        }
        
        return {
            "jsonrpc": "2.0",
            "result": requirements
        }
    
    def _suggest_event_type_tool(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Implementation of suggestEventType tool"""
        audience_size = parameters.get("audience_size", "medium")
        formality = parameters.get("formality", "semiformal")
        duration_minutes = parameters.get("duration_minutes", 30)
        purpose = parameters.get("purpose")
        
        if not purpose:
            return self._error_response("Missing required parameter: purpose")
        
        # Filter events by parameters
        matches = []
        for event_id, event_data in self.events_data.get("event_types", {}).items():
            score = 0
            
            # Match on purpose
            if purpose.lower() in event_data.get("purposes", []):
                score += 3
            
            # Match on duration
            typical_duration = event_data.get("typical_duration", "")
            if typical_duration:
                try:
                    # Extract typical duration range (simple parsing)
                    parts = typical_duration.replace("minutes", "").replace("min", "").strip().split("-")
                    if len(parts) == 2:
                        min_dur = int(parts[0].strip())
                        max_dur = int(parts[1].strip())
                        
                        if min_dur <= duration_minutes <= max_dur:
                            score += 2
                        elif abs(min_dur - duration_minutes) <= 10 or abs(max_dur - duration_minutes) <= 10:
                            score += 1
                except ValueError:
                    pass
            
            # Match on audience size
            if audience_size in event_data.get("audience_sizes", []):
                score += 1
            
            # Match on formality
            if formality in event_data.get("formality", []):
                score += 1
            
            if score > 0:
                matches.append({
                    "event_id": event_id,
                    "event_name": event_data.get("name", event_id),
                    "match_score": score,
                    "description": event_data.get("description", ""),
                    "typical_duration": event_data.get("typical_duration", ""),
                    "requirements": event_data.get("requirements", {})
                })
        
        # Sort by match score
        matches.sort(key=lambda x: x["match_score"], reverse=True)
        
        # Format the response
        suggestion = {
            "parameters": {
                "audience_size": audience_size,
                "formality": formality,
                "duration_minutes": duration_minutes,
                "purpose": purpose
            },
            "suggested_events": matches[:3] if len(matches) > 3 else matches,
            "best_match": matches[0] if matches else None,
            "alternatives_count": len(matches) - 1 if len(matches) > 1 else 0
        }
        
        return {
            "jsonrpc": "2.0",
            "result": suggestion
        }
    
    def _format_guidelines_tool(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Implementation of formatGuidelines tool"""
        format_id = parameters.get("format_id")
        include_examples = parameters.get("include_examples", False)
        
        if not format_id or format_id not in self.events_data.get("formats", []):
            return self._error_response("Invalid format_id")
        
        format_details = self._get_format_details().get(format_id, {})
        
        # Add examples if requested
        if include_examples:
            examples = self._get_format_examples(format_id)
            format_details["examples"] = examples
        
        # Format the response
        guidelines = {
            "format_id": format_id,
            "format_name": format_details.get("name", format_id),
            "guidelines": format_details,
            "common_event_types": self._find_events_with_format(format_id)
        }
        
        return {
            "jsonrpc": "2.0",
            "result": guidelines
        }
    
    # MCP Prompts Methods
    def list_prompts(self) -> Dict[str, Any]:
        """MCP prompts/list endpoint implementation"""
        prompts = [
            {
                "name": "event-specific-guidelines",
                "title": "Event-Specific Speaking Guidelines",
                "description": "Get guidelines for speaking at a specific event type",
                "arguments": [
                    {
                        "name": "event_id",
                        "type": "string",
                        "description": "Event type identifier",
                        "enum": list(self.events_data.get("event_types", {}).keys()),
                        "required": True
                    },
                    {
                        "name": "include_requirements",
                        "type": "boolean",
                        "description": "Whether to include detailed requirements",
                        "required": False
                    }
                ]
            },
            {
                "name": "prepare-for-event",
                "title": "Prepare for Specific Event",
                "description": "Get preparation guidance for an upcoming event",
                "arguments": [
                    {
                        "name": "event_id",
                        "type": "string",
                        "description": "Event type identifier",
                        "enum": list(self.events_data.get("event_types", {}).keys()),
                        "required": True
                    },
                    {
                        "name": "days_until_event",
                        "type": "number",
                        "description": "Days remaining until the event",
                        "required": True
                    },
                    {
                        "name": "experience_level",
                        "type": "string",
                        "description": "Speaker's experience level",
                        "enum": ["beginner", "intermediate", "advanced", "expert"],
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
        if prompt_name == "event-specific-guidelines":
            return {
                "jsonrpc": "2.0",
                "result": {
                    "name": "event-specific-guidelines",
                    "title": "Event-Specific Speaking Guidelines",
                    "description": "Get guidelines for speaking at a specific event type",
                    "template": "Provide speaking guidelines for a {{event_name}} presentation.{{#include_requirements}} Include detailed requirements for this event type.{{/include_requirements}}",
                    "arguments": [
                        {
                            "name": "event_id",
                            "type": "string",
                            "description": "Event type identifier",
                            "enum": list(self.events_data.get("event_types", {}).keys()),
                            "required": True
                        },
                        {
                            "name": "event_name",
                            "type": "string",
                            "description": "Name of the event type",
                            "required": True
                        },
                        {
                            "name": "include_requirements",
                            "type": "boolean",
                            "description": "Whether to include detailed requirements",
                            "required": False
                        }
                    ]
                }
            }
        elif prompt_name == "prepare-for-event":
            return {
                "jsonrpc": "2.0",
                "result": {
                    "name": "prepare-for-event",
                    "title": "Prepare for Specific Event",
                    "description": "Get preparation guidance for an upcoming event",
                    "template": "I'm preparing for a {{event_name}} in {{days_until_event}} days. {{#experience_level}}I'm a {{experience_level}} speaker. {{/experience_level}}What should I focus on to prepare effectively?",
                    "arguments": [
                        {
                            "name": "event_id",
                            "type": "string",
                            "description": "Event type identifier",
                            "enum": list(self.events_data.get("event_types", {}).keys()),
                            "required": True
                        },
                        {
                            "name": "event_name",
                            "type": "string",
                            "description": "Name of the event type",
                            "required": True
                        },
                        {
                            "name": "days_until_event",
                            "type": "number",
                            "description": "Days remaining until the event",
                            "required": True
                        },
                        {
                            "name": "experience_level",
                            "type": "string",
                            "description": "Speaker's experience level",
                            "enum": ["beginner", "intermediate", "advanced", "expert"],
                            "required": False
                        }
                    ]
                }
            }
        else:
            return self._error_response(f"Prompt not found: {prompt_name}", -32001)
    
    # Helper methods for event knowledge
    def _compare_events(self, event_id1: str, event_id2: str, event_data1: Dict[str, Any], event_data2: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two event types"""
        comparison = {
            "events": [
                {
                    "id": event_id1,
                    "name": event_data1.get("name", event_id1),
                    "description": event_data1.get("description", "")
                },
                {
                    "id": event_id2,
                    "name": event_data2.get("name", event_id2),
                    "description": event_data2.get("description", "")
                }
            ],
            "similarities": [],
            "differences": [],
            "requirements_comparison": {}
        }
        
        # Compare durations
        duration1 = event_data1.get("typical_duration", "")
        duration2 = event_data2.get("typical_duration", "")
        if duration1 == duration2:
            comparison["similarities"].append(f"Both have similar durations: {duration1}")
        else:
            comparison["differences"].append(f"Duration: {event_data1.get('name', event_id1)} is {duration1}, while {event_data2.get('name', event_id2)} is {duration2}")
        
        # Compare structure
        structure1 = event_data1.get("structure", {})
        structure2 = event_data2.get("structure", {})
        
        structure_similarities = []
        structure_differences = []
        
        # Simple structure comparison
        structure_keys = set(structure1.keys()) | set(structure2.keys())
        for key in structure_keys:
            if key in structure1 and key in structure2:
                if structure1[key] == structure2[key]:
                    structure_similarities.append(f"Similar {key}")
                else:
                    structure_differences.append(f"Different {key} approach")
            elif key in structure1:
                structure_differences.append(f"{event_data1.get('name', event_id1)} has {key}, {event_data2.get('name', event_id2)} does not")
            else:
                structure_differences.append(f"{event_data2.get('name', event_id2)} has {key}, {event_data1.get('name', event_id1)} does not")
        
        if structure_similarities:
            comparison["similarities"].append(f"Similar structure elements: {', '.join(structure_similarities)}")
        if structure_differences:
            comparison["differences"].append(f"Structure differences: {', '.join(structure_differences)}")
        
        # Compare audience expectations
        audience1 = event_data1.get("audience_expectations", [])
        audience2 = event_data2.get("audience_expectations", [])
        
        common_expectations = set(audience1) & set(audience2)
        if common_expectations:
            comparison["similarities"].append(f"Common audience expectations: {', '.join(common_expectations)}")
        
        unique_expectations1 = set(audience1) - set(audience2)
        unique_expectations2 = set(audience2) - set(audience1)
        
        if unique_expectations1:
            comparison["differences"].append(f"{event_data1.get('name', event_id1)} unique audience expectations: {', '.join(unique_expectations1)}")
        
        if unique_expectations2:
            comparison["differences"].append(f"{event_data2.get('name', event_id2)} unique audience expectations: {', '.join(unique_expectations2)}")
        
        # Requirements comparison
        req1 = event_data1.get("requirements", {})
        req2 = event_data2.get("requirements", {})
        
        comparison["requirements_comparison"] = {
            event_id1: req1,
            event_id2: req2
        }
        
        return comparison
    
    def _get_format_details(self) -> Dict[str, Any]:
        """Get details about each event format"""
        # This would be replaced with actual JSON data, but for this example we'll define hardcoded values
        format_details = {
            "presentation": {
                "name": "Presentation",
                "description": "Formal delivery of information to an audience",
                "structure": ["Introduction", "Main Points", "Supporting Details", "Conclusion"],
                "media_requirements": ["Slides", "Visual Aids"],
                "typical_duration": "15-30 minutes"
            },
            "panel_discussion": {
                "name": "Panel Discussion",
                "description": "Moderated conversation between multiple experts",
                "structure": ["Introductions", "Moderated Questions", "Cross-panel Discussion", "Audience Q&A"],
                "media_requirements": ["Microphones", "Name Cards"],
                "typical_duration": "45-90 minutes"
            },
            "workshop": {
                "name": "Workshop",
                "description": "Interactive session with practical learning outcomes",
                "structure": ["Introduction", "Concept Explanation", "Practical Exercises", "Reflection", "Next Steps"],
                "media_requirements": ["Handouts", "Exercise Materials"],
                "typical_duration": "1-3 hours"
            },
            "keynote": {
                "name": "Keynote",
                "description": "Inspirational or visionary speech that sets the tone for an event",
                "structure": ["Attention-grabbing Opening", "Vision Statement", "Supporting Stories", "Call to Action"],
                "media_requirements": ["High-quality Slides", "Professional Audio/Visual"],
                "typical_duration": "30-60 minutes"
            },
            "lightning_talk": {
                "name": "Lightning Talk",
                "description": "Very short, focused presentation on a single topic",
                "structure": ["Thesis Statement", "Key Point", "Demonstration/Example", "Conclusion"],
                "media_requirements": ["Few/No Slides", "Timer"],
                "typical_duration": "5-10 minutes"
            }
        }
        
        return format_details
    
    def _get_format_examples(self, format_id: str) -> List[Dict[str, str]]:
        """Get examples of a specific event format"""
        examples = {
            "presentation": [
                {"title": "Product Launch Presentation", "description": "Introducing a new product with features, benefits, and pricing"},
                {"title": "Research Findings Presentation", "description": "Sharing results of a study with methodology and conclusions"},
                {"title": "Project Status Update", "description": "Reporting on project progress, challenges, and next steps"}
            ],
            "panel_discussion": [
                {"title": "Industry Trends Panel", "description": "Experts discussing current and future trends in their field"},
                {"title": "Diversity in Leadership Panel", "description": "Leaders sharing experiences and strategies for inclusive workplaces"},
                {"title": "Technology Ethics Panel", "description": "Debating ethical implications of emerging technologies"}
            ],
            "workshop": [
                {"title": "Design Thinking Workshop", "description": "Hands-on application of design thinking methodology to a problem"},
                {"title": "Team Building Workshop", "description": "Activities to improve team communication and collaboration"},
                {"title": "Technical Skills Workshop", "description": "Step-by-step instruction on using a specific technology"}
            ],
            "keynote": [
                {"title": "Conference Opening Keynote", "description": "Setting the theme and tone for a multi-day event"},
                {"title": "Vision for the Future Keynote", "description": "CEO outlining strategic vision for company's next five years"},
                {"title": "Inspirational Leadership Keynote", "description": "Sharing personal journey and lessons learned"}
            ],
            "lightning_talk": [
                {"title": "Quick Productivity Hack", "description": "Single technique to improve daily productivity"},
                {"title": "New Tool Introduction", "description": "Brief demonstration of a useful new tool or resource"},
                {"title": "Concept Explanation", "description": "Clear explanation of one important concept in 5 minutes"}
            ]
        }
        
        return examples.get(format_id, [])
    
    def _find_events_with_format(self, format_id: str) -> List[Dict[str, str]]:
        """Find event types that commonly use the specified format"""
        events_with_format = []
        
        for event_id, event_data in self.events_data.get("event_types", {}).items():
            if "formats" in event_data and format_id in event_data["formats"]:
                events_with_format.append({
                    "event_id": event_id,
                    "event_name": event_data.get("name", event_id)
                })
        
        return events_with_format
    
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
        events_count = len(self.events_data.get("event_types", {}))
        return {
            "status": "healthy" if events_count > 0 else "degraded",
            "server_name": self.server_name,
            "server_version": self.server_version,
            "protocol_version": self.protocol_version,
            "event_types_loaded": events_count,
            "timestamp": datetime.now().isoformat()
        }

# For testing purposes
if __name__ == "__main__":
    server = EventKnowledgeMCPServer()
    
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
    read_response = server.handle_request("resources/read", {"uri": "event://conference_talk"})
    print(json.dumps(read_response, indent=2))
    
    # Test MCP tools list
    print("\n=== MCP Tools List ===")
    tools_response = server.handle_request("tools/list", {})
    print(json.dumps(tools_response, indent=2))
    
    # Test MCP tool call
    print("\n=== MCP Tool Call ===")
    tool_response = server.handle_request("tools/call", {
        "name": "suggestEventType", 
        "parameters": {
            "audience_size": "large",
            "purpose": "inform"
        }
    })
    print(json.dumps(tool_response, indent=2))
