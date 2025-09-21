#!/usr/bin/env python3
"""
Domain Knowledge Server for Speech Coach
Provides domain-specific speaking guidelines that can be queried by LLMs for context-aware feedback
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpeakingDomain(Enum):
    PUBLIC_SPEAKING = "public_speaking"
    CORPORATE = "corporate"
    TECHNICAL = "technical"
    ACADEMIC = "academic"

class FocusArea(Enum):
    STRUCTURE = "structure"
    DELIVERY = "delivery"
    LANGUAGE = "language"
    ENGAGEMENT = "engagement"
    BEST_PRACTICES = "best_practices"
    COMMON_MISTAKES = "common_mistakes"
    ALL = "all"

@dataclass
class DomainGuidelines:
    opening: str
    body: str
    closing: str

@dataclass
class DeliveryGuidelines:
    pace: str
    pauses: str
    vocal_variety: str
    gestures: str

@dataclass
class DomainData:
    domain: str
    name: str
    structure: DomainGuidelines
    delivery: DeliveryGuidelines
    best_practices: List[str]
    common_mistakes: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class DomainKnowledgeBase:
    """Knowledge base containing domain-specific speaking guidelines"""
    
    def __init__(self):
        self.domains = self._initialize_domains()
    
    def _initialize_domains(self) -> Dict[str, DomainData]:
        """Initialize the domain knowledge base"""
        return {
            SpeakingDomain.PUBLIC_SPEAKING.value: DomainData(
                domain="public_speaking",
                name="General Public Speaking",
                structure=DomainGuidelines(
                    opening="Strong hook, clear preview of content",
                    body="3-5 main points with supporting evidence",
                    closing="Summary and call to action"
                ),
                delivery=DeliveryGuidelines(
                    pace="120-140 words per minute",
                    pauses="Use strategic pauses for emphasis",
                    vocal_variety="Vary pitch, pace, and volume",
                    gestures="Natural, purposeful hand movements"
                ),
                best_practices=[
                    "Practice the 'rule of three' for memorable content",
                    "Use the 'PREP' structure: Point, Reason, Example, Point",
                    "Start strong with a compelling opening",
                    "End with a clear call to action",
                    "Know your audience and tailor content accordingly"
                ],
                common_mistakes=[
                    "Reading directly from slides",
                    "Overusing filler words (um, uh, like)",
                    "Speaking too fast when nervous",
                    "Lack of clear structure",
                    "Poor eye contact with audience"
                ]
            ),
            SpeakingDomain.CORPORATE.value: DomainData(
                domain="corporate",
                name="Corporate Communications",
                structure=DomainGuidelines(
                    opening="Executive summary approach",
                    body="Data-driven points with business impact",
                    closing="Clear next steps and ownership"
                ),
                delivery=DeliveryGuidelines(
                    pace="Professional, measured pace",
                    pauses="Use pauses to emphasize key metrics",
                    vocal_variety="Authoritative but approachable tone",
                    gestures="Controlled, professional movements"
                ),
                best_practices=[
                    "Lead with business value and ROI",
                    "Use data and metrics to support arguments", 
                    "Address potential objections proactively",
                    "Provide clear timeline and next steps",
                    "Maintain professional demeanor throughout"
                ],
                common_mistakes=[
                    "Too much technical detail for executives",
                    "Failing to connect to business outcomes",
                    "Not addressing budget or resource implications",
                    "Overly casual tone in formal settings",
                    "Lack of clear decision points"
                ]
            ),
            SpeakingDomain.TECHNICAL.value: DomainData(
                domain="technical",
                name="Technical Presentations",
                structure=DomainGuidelines(
                    opening="Problem statement and solution overview",
                    body="Technical deep-dive with logical progression",
                    closing="Implementation steps and technical implications"
                ),
                delivery=DeliveryGuidelines(
                    pace="Slower pace for complex concepts",
                    pauses="Allow time for technical concept absorption",
                    vocal_variety="Clear enunciation of technical terms",
                    gestures="Use hands to illustrate concepts and flows"
                ),
                best_practices=[
                    "Use visual aids extensively for complex concepts",
                    "Provide code examples or technical demonstrations",
                    "Layer information from simple to complex",
                    "Anticipate technical questions and prepare answers",
                    "Share relevant documentation and resources"
                ],
                common_mistakes=[
                    "Assuming all audience members have same technical level",
                    "Moving too quickly through complex concepts",
                    "Not providing enough visual or practical examples",
                    "Failing to explain the 'why' behind technical decisions",
                    "Overloading slides with too much technical detail"
                ]
            ),
            SpeakingDomain.ACADEMIC.value: DomainData(
                domain="academic",
                name="Academic Presentations",
                structure=DomainGuidelines(
                    opening="Research question and methodology overview",
                    body="Literature review, findings, analysis",
                    closing="Conclusions, limitations, future research"
                ),
                delivery=DeliveryGuidelines(
                    pace="Measured pace allowing for note-taking",
                    pauses="Pause after key findings or insights",
                    vocal_variety="Scholarly tone with appropriate enthusiasm",
                    gestures="Academic-appropriate, supportive gestures"
                ),
                best_practices=[
                    "Clearly state research question and methodology",
                    "Provide sufficient background and literature context",
                    "Present findings objectively with appropriate caveats",
                    "Acknowledge limitations and alternative interpretations",
                    "Suggest concrete areas for future research"
                ],
                common_mistakes=[
                    "Insufficient context for non-specialist audience",
                    "Overstating the significance of findings",
                    "Not acknowledging research limitations",
                    "Poor time management for academic format",
                    "Failing to engage with existing literature adequately"
                ]
            )
        }
    
    def get_domain_guidelines(self, domain: Union[str, SpeakingDomain], focus_area: Union[str, FocusArea] = FocusArea.ALL) -> Dict[str, Any]:
        """Get guidelines for a specific domain and focus area"""
        if isinstance(domain, str):
            domain = domain.lower()
        else:
            domain = domain.value
            
        if isinstance(focus_area, str):
            focus_area = focus_area.lower()
        else:
            focus_area = focus_area.value
        
        if domain not in self.domains:
            raise ValueError(f"Unknown domain: {domain}. Available: {list(self.domains.keys())}")
        
        domain_data = self.domains[domain]
        
        if focus_area == "all":
            return {
                "domain": domain_data.name,
                "guidelines": domain_data.to_dict(),
                "context_type": "complete_domain_knowledge"
            }
        elif focus_area == "structure":
            return {
                "domain": domain_data.name,
                "focus": "structure",
                "guidelines": asdict(domain_data.structure),
                "context_type": "structure_guidelines"
            }
        elif focus_area == "delivery":
            return {
                "domain": domain_data.name,
                "focus": "delivery", 
                "guidelines": asdict(domain_data.delivery),
                "context_type": "delivery_guidelines"
            }
        elif focus_area == "best_practices":
            return {
                "domain": domain_data.name,
                "focus": "best_practices",
                "practices": domain_data.best_practices,
                "context_type": "best_practices"
            }
        elif focus_area == "common_mistakes":
            return {
                "domain": domain_data.name,
                "focus": "common_mistakes",
                "mistakes": domain_data.common_mistakes,
                "context_type": "mistake_prevention"
            }
        else:
            raise ValueError(f"Unknown focus area: {focus_area}")
    
    def analyze_speech_against_domain(self, domain: Union[str, SpeakingDomain], speech_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze speech metrics against domain-specific criteria"""
        if isinstance(domain, str):
            domain = domain.lower()
        else:
            domain = domain.value
            
        if domain not in self.domains:
            raise ValueError(f"Unknown domain: {domain}")
        
        domain_data = self.domains[domain]
        
        analysis = {
            "domain": domain_data.name,
            "domain_id": domain,
            "analysis_timestamp": "2025-09-21",
            "overall_score": 0,
            "detailed_analysis": {},
            "domain_specific_recommendations": [],
            "context_type": "domain_analysis"
        }
        
        # Analyze pace against domain expectations
        pace_wpm = speech_metrics.get("pace_wpm", 0)
        target_pace = self._get_target_pace_for_domain(domain)
        
        pace_score = max(0, 100 - abs(pace_wpm - target_pace) * 2)
        analysis["detailed_analysis"]["pace"] = {
            "score": pace_score,
            "target_wpm": target_pace,
            "actual_wpm": pace_wpm,
            "domain_expectation": domain_data.delivery.pace,
            "evaluation": "Good pace" if pace_score > 80 else "Needs adjustment"
        }
        
        # Analyze filler words 
        filler_count = speech_metrics.get("filler_words_count", 0)
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
        
        # Generate domain-specific recommendations
        if analysis["overall_score"] < 70:
            analysis["domain_specific_recommendations"] = domain_data.best_practices[:3]
        elif analysis["overall_score"] < 85:
            analysis["domain_specific_recommendations"] = domain_data.best_practices[:2]
        else:
            analysis["domain_specific_recommendations"] = ["Continue practicing to maintain excellent performance"]
        
        return analysis
    
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
    
    def generate_improvement_plan(self, domain: Union[str, SpeakingDomain], skill_level: str, improvement_areas: List[str] = None) -> Dict[str, Any]:
        """Generate domain-specific improvement plan"""
        if isinstance(domain, str):
            domain = domain.lower()
        else:
            domain = domain.value
            
        if domain not in self.domains:
            raise ValueError(f"Unknown domain: {domain}")
        
        domain_data = self.domains[domain]
        improvement_areas = improvement_areas or ["structure", "delivery"]
        
        plan = {
            "domain": domain_data.name,
            "skill_level": skill_level,
            "improvement_focus": improvement_areas,
            "action_plan": [],
            "practice_exercises": [],
            "success_metrics": [],
            "context_type": "improvement_plan"
        }
        
        # Add domain-specific action items
        for area in improvement_areas:
            if area == "structure":
                plan["action_plan"].append({
                    "area": "Structure",
                    "domain_guidance": asdict(domain_data.structure),
                    "actions": [
                        f"Practice {domain_data.structure.opening}",
                        f"Develop {domain_data.structure.body}",
                        f"Master {domain_data.structure.closing}"
                    ]
                })
            elif area == "delivery":
                plan["action_plan"].append({
                    "area": "Delivery",
                    "domain_guidance": asdict(domain_data.delivery),
                    "actions": [
                        f"Work on {domain_data.delivery.pace}",
                        f"Practice {domain_data.delivery.vocal_variety}",
                        f"Develop {domain_data.delivery.gestures}"
                    ]
                })
        
        # Add skill-level specific exercises
        if skill_level.lower() == "beginner":
            plan["practice_exercises"] = [
                f"Study {domain_data.name.lower()} presentation examples",
                "Record yourself practicing domain-specific content",
                "Practice basic structure with domain guidelines"
            ]
        elif skill_level.lower() == "intermediate":
            plan["practice_exercises"] = [
                f"Practice {domain_data.name.lower()} presentations with feedback",
                "Work on domain-specific vocal techniques",
                "Join domain-relevant speaking opportunities"
            ]
        else:  # advanced
            plan["practice_exercises"] = [
                f"Mentor others in {domain_data.name.lower()}",
                f"Speak at {domain_data.name.lower()} events",
                "Develop signature style within domain guidelines"
            ]
        
        # Add domain-specific success metrics
        plan["success_metrics"] = [
            f"Follows {domain_data.name.lower()} structure guidelines",
            f"Meets {domain_data.name.lower()} delivery expectations", 
            "Demonstrates domain-appropriate best practices",
            "Avoids domain-specific common mistakes"
        ]
        
        return plan
    
    def compare_domains(self, domains: List[Union[str, SpeakingDomain]], aspect: Union[str, FocusArea] = FocusArea.STRUCTURE) -> Dict[str, Any]:
        """Compare guidelines across different domains"""
        if isinstance(aspect, str):
            aspect = aspect.lower()
        else:
            aspect = aspect.value
            
        comparison = {
            "comparison_aspect": aspect,
            "domains_compared": [],
            "similarities": [],
            "key_differences": [],
            "context_type": "domain_comparison"
        }
        
        domain_guidelines = {}
        for domain in domains:
            if isinstance(domain, str):
                domain = domain.lower()
            else:
                domain = domain.value
                
            if domain in self.domains:
                domain_data = self.domains[domain]
                comparison["domains_compared"].append(domain_data.name)
                
                if aspect == "structure":
                    domain_guidelines[domain] = asdict(domain_data.structure)
                elif aspect == "delivery":
                    domain_guidelines[domain] = asdict(domain_data.delivery)
                elif aspect == "best_practices":
                    domain_guidelines[domain] = domain_data.best_practices
                elif aspect == "common_mistakes":
                    domain_guidelines[domain] = domain_data.common_mistakes
        
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
        
        return comparison
    
    def export_knowledge_base(self, filepath: Optional[str] = None) -> str:
        """Export the complete knowledge base as JSON"""
        export_data = {
            "knowledge_base_version": "1.0",
            "export_timestamp": "2025-09-21",
            "domains": {domain_id: domain_data.to_dict() for domain_id, domain_data in self.domains.items()},
            "available_domains": list(self.domains.keys()),
            "available_focus_areas": [area.value for area in FocusArea]
        }
        
        json_data = json.dumps(export_data, indent=2)
        
        if filepath:
            Path(filepath).write_text(json_data)
            logger.info(f"Knowledge base exported to {filepath}")
        
        return json_data

# Knowledge server for LLM integration
class DomainKnowledgeServer:
    """Server interface for LLM integration with domain knowledge"""
    
    def __init__(self):
        self.knowledge_base = DomainKnowledgeBase()
        logger.info("Domain Knowledge Server initialized")
    
    def get_context_for_llm(self, query_type: str, **kwargs) -> Dict[str, Any]:
        """
        Main interface for LLM to get domain context
        
        Query types:
        - domain_guidelines: Get guidelines for specific domain
        - analyze_speech: Analyze speech against domain criteria  
        - improvement_plan: Generate improvement recommendations
        - compare_domains: Compare across domains
        """
        try:
            if query_type == "domain_guidelines":
                domain = kwargs.get("domain", "public_speaking")
                focus_area = kwargs.get("focus_area", "all")
                return self.knowledge_base.get_domain_guidelines(domain, focus_area)
            
            elif query_type == "analyze_speech":
                domain = kwargs.get("domain", "public_speaking")
                speech_metrics = kwargs.get("speech_metrics", {})
                return self.knowledge_base.analyze_speech_against_domain(domain, speech_metrics)
            
            elif query_type == "improvement_plan":
                domain = kwargs.get("domain", "public_speaking")
                skill_level = kwargs.get("skill_level", "intermediate")
                improvement_areas = kwargs.get("improvement_areas", [])
                return self.knowledge_base.generate_improvement_plan(domain, skill_level, improvement_areas)
            
            elif query_type == "compare_domains":
                domains = kwargs.get("domains", ["public_speaking", "corporate"])
                aspect = kwargs.get("aspect", "structure")
                return self.knowledge_base.compare_domains(domains, aspect)
            
            elif query_type == "available_domains":
                return {
                    "available_domains": list(self.knowledge_base.domains.keys()),
                    "domain_names": [data.name for data in self.knowledge_base.domains.values()],
                    "context_type": "available_options"
                }
            
            else:
                return {
                    "error": f"Unknown query type: {query_type}",
                    "available_query_types": ["domain_guidelines", "analyze_speech", "improvement_plan", "compare_domains", "available_domains"],
                    "context_type": "error"
                }
                
        except Exception as e:
            logger.error(f"Error processing query {query_type}: {str(e)}")
            return {
                "error": str(e),
                "query_type": query_type,
                "context_type": "error"
            }
    
    def get_full_knowledge_export(self) -> str:
        """Export complete knowledge base for LLM context"""
        return self.knowledge_base.export_knowledge_base()

# Example usage and testing
def main():
    """Test the domain knowledge server"""
    server = DomainKnowledgeServer()
    
    # Test domain guidelines
    print("=== Testing Domain Guidelines ===")
    guidelines = server.get_context_for_llm("domain_guidelines", domain="corporate", focus_area="structure")
    print(json.dumps(guidelines, indent=2))
    
    # Test speech analysis
    print("\n=== Testing Speech Analysis ===")
    test_metrics = {
        "pace_wpm": 140,
        "filler_words_count": 3,
        "pause_frequency": 0.2
    }
    analysis = server.get_context_for_llm("analyze_speech", domain="corporate", speech_metrics=test_metrics)
    print(json.dumps(analysis, indent=2))
    
    # Test improvement plan
    print("\n=== Testing Improvement Plan ===")
    plan = server.get_context_for_llm("improvement_plan", domain="technical", skill_level="intermediate", improvement_areas=["structure", "delivery"])
    print(json.dumps(plan, indent=2))

if __name__ == "__main__":
    main()
