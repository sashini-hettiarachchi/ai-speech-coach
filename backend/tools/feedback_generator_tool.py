"""
FeedbackGeneratorTool: Generates structured feedback based on speech analysis.

This tool creates personalized feedback with strengths, issues, suggestions,
exercises, and motivational content based on the speaking context and analysis results.
Uses LLM to generate more personalized and context-aware feedback.
"""

import os
import json
import requests
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from tools.base import BaseTool

# Import configuration with fallback
try:
    from config import LLM_ENDPOINT, LLM_MODEL, LLM_TEMPERATURE
except ImportError:
    LLM_ENDPOINT = "http://localhost:11434/api/generate"
    LLM_MODEL = "llama3"
    LLM_TEMPERATURE = 0.3
    
# Import filler detector
from utils.filler_detector import count_filler_words

class FeedbackGeneratorToolInput(BaseModel):
    """Input schema for FeedbackGeneratorTool"""
    context_label: str = Field(
        ..., 
        description="Speaking context (Academic, Persuasive, Storytelling, etc.)"
    )
    overall_score: float = Field(
        ...,
        description="Overall speaking effectiveness score (0-1)"
    )
    competency_scores: Dict[str, float] = Field(
        ...,
        description="Scores for each competency area (0-1)"
    )
    strengths: List[str] = Field(
        default_factory=list,
        description="List of identified strengths"
    )
    areas_for_improvement: List[str] = Field(
        default_factory=list,
        description="List of areas for improvement"
    )
    speech_duration: float = Field(
        ...,
        description="Duration of speech in seconds"
    )
    filler_percentage: float = Field(
        ...,
        description="Percentage of filler words"
    )
    words_per_minute: float = Field(
        ...,
        description="Speaking pace in words per minute"
    )
    transcript: Optional[str] = Field(
        None,
        description="Transcription of the speech content for LLM-based feedback generation"
    )
    filler_analysis: Optional[Dict[str, Any]] = Field(
        None,
        description="Detailed analysis of filler words from filler_detector"
    )

class FeedbackItem(BaseModel):
    """Schema for a specific feedback item"""
    title: str = Field(..., description="Short title/heading for this feedback")
    details: str = Field(..., description="Detailed explanation of the feedback")
    evidence: Optional[str] = Field(None, description="Specific evidence or examples")

class Exercise(BaseModel):
    """Schema for a practice exercise"""
    title: str = Field(..., description="Name of the exercise")
    description: str = Field(..., description="How to perform the exercise")
    duration: str = Field(..., description="Recommended duration/repetitions")
    focus_area: str = Field(..., description="Which skill this targets")

class FeedbackGeneratorToolOutput(BaseModel):
    """Output schema for FeedbackGeneratorTool"""
    summary: str = Field(
        ..., 
        description="Brief summary of overall performance"
    )
    strengths: List[FeedbackItem] = Field(
        default_factory=list,
        description="Detailed breakdown of strengths"
    )
    issues: List[FeedbackItem] = Field(
        default_factory=list,
        description="Detailed breakdown of issues to address"
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="Actionable suggestions for improvement"
    )
    micro_exercises: List[Exercise] = Field(
        default_factory=list,
        description="Specific exercises to practice"
    )
    motivation: str = Field(
        ...,
        description="Motivational message tailored to the speaker's performance"
    )
    context_specific_tips: List[str] = Field(
        default_factory=list,
        description="Tips specific to the speaking context"
    )

class FeedbackGeneratorTool(BaseTool[FeedbackGeneratorToolInput, FeedbackGeneratorToolOutput]):
    """
    Tool for generating structured feedback based on speech analysis.
    
    Creates personalized feedback with strengths, issues, suggestions,
    exercises, and motivational content based on the speaking context 
    and analysis results. Uses LLM for more personalized feedback when available.
    """
    
    name = "feedback_generator_tool"
    description = "Generates structured feedback based on speech analysis using LLM"
    
    # Define schemas for type checking
    InputSchema = FeedbackGeneratorToolInput
    OutputSchema = FeedbackGeneratorToolOutput
    
    def __init__(self):
        """Initialize the FeedbackGeneratorTool with LLM config"""
        self.llm_endpoint = LLM_ENDPOINT
        self.llm_model = LLM_MODEL
        self.llm_temperature = LLM_TEMPERATURE
    
    # Context-specific feedback templates
    CONTEXT_TIPS = {
        "academic": [
            "Use precise terminology relevant to your field",
            "Structure your talk with clear sections: intro, methods, results, discussion",
            "Include visual aids for complex data or concepts",
            "Address potential counterarguments to strengthen your position"
        ],
        "persuasive": [
            "Open with a compelling hook or statistic",
            "Use the problem-solution-benefit structure",
            "Include personal stories that resonate with your audience",
            "End with a clear, actionable call to action"
        ],
        "storytelling": [
            "Establish setting and characters early",
            "Create tension through conflict or challenge",
            "Use vivid sensory details to engage the audience",
            "Ensure your story has a meaningful resolution or takeaway"
        ],
    }
    
    def run(self, inputs: FeedbackGeneratorToolInput) -> FeedbackGeneratorToolOutput:
        """
        Generate structured feedback based on speech analysis.
        
        Args:
            inputs (FeedbackGeneratorToolInput): Input parameters with analysis results
        
        Returns:
            FeedbackGeneratorToolOutput: Structured feedback
        """
        # Normalize context label
        context = inputs.context_label.lower()
        if context not in self.CONTEXT_TIPS:
            context = "academic"  # Default context
            
        # Try to generate LLM-based feedback first if transcript is available
        llm_feedback = None
        if inputs.transcript:
            llm_feedback = self._generate_llm_feedback(inputs)
        
        # If LLM feedback is available, use it; otherwise, fall back to rule-based generation
        if llm_feedback:
            # Convert LLM feedback to output schema format
            try:
                # Process strengths
                strengths = []
                for strength in llm_feedback.get("strengths", []):
                    if isinstance(strength, dict):
                        strengths.append(
                            FeedbackItem(
                                title=strength.get("title", "Strength"),
                                details=strength.get("details", ""),
                                evidence=strength.get("evidence", None)
                            )
                        )
                
                # Process issues
                issues = []
                for issue in llm_feedback.get("issues", []):
                    if isinstance(issue, dict):
                        issues.append(
                            FeedbackItem(
                                title=issue.get("title", "Area for Improvement"),
                                details=issue.get("details", ""),
                                evidence=issue.get("evidence", None)
                            )
                        )
                
                # Process exercises
                exercises = []
                for exercise in llm_feedback.get("exercises", []):
                    if isinstance(exercise, dict):
                        exercises.append(
                            Exercise(
                                title=exercise.get("title", "Practice Exercise"),
                                description=exercise.get("description", ""),
                                duration=exercise.get("duration", "10 minutes daily"),
                                focus_area=exercise.get("focus_area", "Speaking skills")
                            )
                        )
                
                # Extract other fields
                summary = llm_feedback.get("summary", self._generate_summary(
                    inputs.overall_score, 
                    inputs.speech_duration,
                    inputs.context_label
                ))
                
                suggestions = llm_feedback.get("suggestions", [])
                motivation = llm_feedback.get("motivation", self._generate_motivation(
                    inputs.overall_score, 
                    inputs.areas_for_improvement
                ))
                context_tips = llm_feedback.get("context_tips", self.CONTEXT_TIPS.get(context, self.CONTEXT_TIPS["academic"]))
                
                # Ensure we have at least some content in each section
                if not strengths:
                    # Fall back to rule-based generation for strengths
                    for strength in inputs.strengths[:3]:
                        strengths.append(
                            FeedbackItem(
                                title=f"Strong {strength}",
                                details=self._generate_strength_detail(strength, inputs),
                                evidence=None
                            )
                        )
                
                if not issues:
                    # Fall back to rule-based generation for issues
                    for area in inputs.areas_for_improvement[:3]:
                        issues.append(
                            FeedbackItem(
                                title=f"Improve your {area}",
                                details=self._generate_issue_detail(area, inputs),
                                evidence=None
                            )
                        )
                
            except Exception as e:
                print(f"Error processing LLM feedback: {e}")
                # Fall back to rule-based generation
                llm_feedback = None
        
        # If LLM feedback failed or wasn't available, use rule-based generation
        if not llm_feedback:
            # Generate summary based on overall score
            summary = self._generate_summary(
                inputs.overall_score,
                inputs.speech_duration,
                inputs.context_label
            )
            
            # Generate strengths feedback
            strengths = []
            for strength in inputs.strengths:
                strengths.append(
                    FeedbackItem(
                        title=f"Strong {strength}",
                        details=self._generate_strength_detail(strength, inputs),
                        evidence=None  # Would use specific evidence from transcript in real implementation
                    )
                )
            
            # Generate issues feedback
            issues = []
            for area in inputs.areas_for_improvement:
                issues.append(
                    FeedbackItem(
                        title=f"Improve your {area}",
                        details=self._generate_issue_detail(area, inputs),
                        evidence=None  # Would use specific evidence from transcript in real implementation
                    )
                )
            
            # Generate suggestions based on areas for improvement
            suggestions = self._generate_suggestions(inputs.areas_for_improvement, inputs)
            
            # Generate exercises
            exercises = self._generate_exercises(inputs.areas_for_improvement, inputs)
            
            # Generate motivation message
            motivation = self._generate_motivation(inputs.overall_score, inputs.areas_for_improvement)
            
            # Get context-specific tips
            context_tips = self.CONTEXT_TIPS.get(context, self.CONTEXT_TIPS["academic"])
        
        return FeedbackGeneratorToolOutput(
            summary=summary,
            strengths=strengths,
            issues=issues,
            suggestions=suggestions,
            micro_exercises=exercises,
            motivation=motivation,
            context_specific_tips=context_tips
        )
        
    def _generate_summary(self, overall_score, duration, context_label):
        """Generate performance summary"""
        minutes = int(duration / 60)
        seconds = int(duration % 60)
        
        if overall_score >= 0.9:
            quality = "excellent"
        elif overall_score >= 0.8:
            quality = "very good"
        elif overall_score >= 0.7:
            quality = "good"
        elif overall_score >= 0.6:
            quality = "satisfactory"
        elif overall_score >= 0.5:
            quality = "fair"
        else:
            quality = "developing"
            
        return (f"Your {context_label} presentation ({minutes}m {seconds}s) demonstrated {quality} "
                f"overall speaking skills with an effectiveness score of {overall_score:.2f}.")
    
    def _generate_strength_detail(self, strength, inputs):
        """Generate detailed feedback for a strength"""
        strength = strength.lower()
        
        if "clarity" in strength:
            return ("Your message was clear and easy to follow. You used precise language and maintained "
                    f"a good speaking pace of {inputs.words_per_minute:.1f} words per minute.")
        elif "confidence" in strength:
            return ("You projected confidence throughout your presentation, with good voice modulation and minimal "
                    "hesitation. This helps establish credibility with your audience.")
        elif "structure" in strength:
            return ("Your presentation had a logical flow with clear sections. The organization helped your audience "
                    "follow your main points and supporting arguments effectively.")
        elif "delivery" in strength:
            return ("Your delivery was engaging, with good vocal variety and energy. You maintained a consistent "
                    "pace and used emphasis effectively to highlight key points.")
        elif "language" in strength:
            return ("You demonstrated strong language skills with appropriate vocabulary and grammatical structures. "
                    "Your word choices were precise and enhanced your message.")
        else:
            return ("This was one of your strongest areas in the presentation. Continue to leverage this "
                    "skill in future speaking opportunities.")
    
    def _generate_issue_detail(self, issue, inputs):
        """Generate detailed feedback for an issue"""
        issue = issue.lower()
        
        # Get filler analysis if available
        filler_analysis = getattr(inputs, 'filler_analysis', None)
        
        if "clarity" in issue:
            filler_feedback = ""
            if filler_analysis:
                percentage = filler_analysis.get("filler_percentage", inputs.filler_percentage)
                most_common = filler_analysis.get("most_common_filler")
                
                if most_common:
                    filler_feedback = f" Your most common filler word was '{most_common}' - try replacing it with strategic pauses."
                    
            return ("Your message could be clearer. Consider simplifying complex ideas and using more "
                    f"concrete examples. Your filler word usage ({inputs.filler_percentage:.1f}%) "
                    f"may be reducing clarity.{filler_feedback}")
                    
        elif "confidence" in issue:
            return ("Your confidence could be improved. Practice more to reduce hesitations and "
                    "speak with more authority. Maintain a stronger posture and voice projection.")
                    
        elif "structure" in issue:
            return ("Your presentation structure could be more organized. Consider using a clear framework "
                    "with distinct introduction, main points, and conclusion to help your audience follow along.")
                    
        elif "delivery" in issue:
            # Include filler word feedback if it's a delivery issue
            filler_note = ""
            if filler_analysis and filler_analysis.get("filler_percentage", 0) > 3:
                top_fillers = sorted(
                    filler_analysis.get("fillers", {}).items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:2]
                
                if top_fillers:
                    filler_words = ", ".join([f"'{w}'" for w, _ in top_fillers])
                    filler_note = f" Pay attention to filler words like {filler_words} that appeared frequently."
            
            if inputs.words_per_minute > 170:
                return (f"Your speaking pace was quite fast at {inputs.words_per_minute:.1f} words per minute. "
                        f"Try slowing down and using more strategic pauses for emphasis.{filler_note}")
            elif inputs.words_per_minute < 130:
                return (f"Your speaking pace was somewhat slow at {inputs.words_per_minute:.1f} words per minute. "
                        f"Try picking up the pace slightly to maintain audience engagement.{filler_note}")
            else:
                return ("Your delivery could be more dynamic. Try varying your tone, pace, and volume "
                        f"to emphasize important points and maintain audience interest.{filler_note}")
                        
        elif "language" in issue or "filler" in issue:
            filler_feedback = ""
            if filler_analysis:
                percentage = filler_analysis.get("filler_percentage", inputs.filler_percentage)
                most_common = filler_analysis.get("most_common_filler")
                analysis = filler_analysis.get("analysis", "")
                
                if most_common and percentage > 1:
                    filler_feedback = f" In particular, the word '{most_common}' appeared frequently. {analysis}"
                    
            return ("Your language use could be more precise. Work on vocabulary choices and reducing filler words "
                    f"to express your ideas more effectively and professionally.{filler_feedback}")
                    
        else:
            return ("This area would benefit from focused practice. Small improvements here "
                    "could significantly enhance your overall speaking effectiveness.")
    
    def _generate_suggestions(self, areas_for_improvement, inputs):
        """Generate actionable suggestions based on areas for improvement"""
        suggestions = []
        
        # Get filler analysis if available
        filler_analysis = getattr(inputs, 'filler_analysis', None)
        
        # Generic suggestions based on common areas
        if any("clarity" in area.lower() for area in areas_for_improvement):
            suggestions.append("Simplify complex ideas by using analogies and concrete examples")
            
            # Enhanced filler word suggestion with specific data
            filler_pct = inputs.filler_percentage
            most_common = ""
            if filler_analysis:
                filler_pct = filler_analysis.get("filler_percentage", inputs.filler_percentage)
                most_common = filler_analysis.get("most_common_filler", "")
                
            if most_common:
                suggestions.append(f"Practice replacing '{most_common}' with intentional pauses")
            else:
                suggestions.append(f"Reduce filler words (currently {filler_pct:.1f}%) by practicing with pauses instead")
            
        if any("confidence" in area.lower() for area in areas_for_improvement):
            suggestions.append("Record yourself practicing and review to identify confidence indicators")
            suggestions.append("Practice power posing for 2 minutes before speaking to boost confidence")
            
        if any("structure" in area.lower() for area in areas_for_improvement):
            suggestions.append("Create a clear outline with 3-5 main points before your next presentation")
            suggestions.append("Use signposting phrases like 'First,' 'Next,' and 'In conclusion' to guide listeners")
            
        if any("delivery" in area.lower() or "filler" in area.lower() for area in areas_for_improvement):
            # Add filler word specific exercise if needed
            if filler_analysis and filler_analysis.get("filler_percentage", 0) > 2:
                suggestions.append("Practice the 'pause and breathe' technique: when tempted to use a filler word, pause instead")
                
                # Add specific suggestion for top filler words
                top_fillers = sorted(
                    filler_analysis.get("fillers", {}).items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:3]
                
                if top_fillers:
                    filler_list = ", ".join([f"'{w}'" for w, _ in top_fillers])
                    suggestions.append(f"Be mindful of your most common fillers: {filler_list}")
            
            if inputs.words_per_minute > 170:
                suggestions.append(f"Slow down your pace (currently {inputs.words_per_minute:.1f} WPM) by marking pauses in your notes")
            elif inputs.words_per_minute < 130:
                suggestions.append(f"Increase your pace slightly (currently {inputs.words_per_minute:.1f} WPM) through practice with a timer")
            
            suggestions.append("Record your voice and practice emphasizing key words in each sentence")
            
        # Ensure we have at least 3 suggestions
        generic_suggestions = [
            "Practice your introduction and conclusion until you can deliver them flawlessly",
            "Join a public speaking group like Toastmasters to get regular practice and feedback",
            "Record yourself and analyze your own speaking patterns",
            "Have a friend ask you unexpected questions to practice thinking on your feet",
            "Study speakers you admire and identify specific techniques you can incorporate"
        ]
        
        while len(suggestions) < 3:
            if generic_suggestions:
                suggestions.append(generic_suggestions.pop(0))
            else:
                break
                
        return suggestions[:5]  # Return at most 5 suggestions
    
    def _generate_exercises(self, areas_for_improvement, inputs=None):
        """Generate practice exercises based on areas for improvement"""
        exercises = []
        
        # Get filler analysis if available
        filler_analysis = getattr(inputs, 'filler_analysis', None) if inputs else None
        filler_exercise_description = "Read a passage aloud and replace filler words with deliberate pauses"
        
        # Customize filler exercise if analysis is available
        if filler_analysis and filler_analysis.get("most_common_filler"):
            most_common = filler_analysis.get("most_common_filler")
            filler_exercise_description = f"Practice speaking while being mindful of '{most_common}'. Each time you're about to say it, pause for 1-2 seconds instead."
        
        # Map areas to exercises
        exercise_map = {
            "clarity": Exercise(
                title="Simplification Challenge",
                description="Explain a complex topic from your field to a 12-year-old",
                duration="10 minutes daily",
                focus_area="Message clarity"
            ),
            "confidence": Exercise(
                title="Mirror Practice",
                description="Speak while maintaining eye contact with yourself in a mirror",
                duration="5 minutes, 3x weekly",
                focus_area="Confidence and presence"
            ),
            "structure": Exercise(
                title="Outline Mastery",
                description="Create 5-point outlines for various topics, then deliver 1-minute speeches from them",
                duration="15 minutes, twice weekly",
                focus_area="Speech organization"
            ),
            "delivery": Exercise(
                title="Pace and Pause",
                description="Read a passage aloud with deliberate pauses after key points",
                duration="3 minutes daily",
                focus_area="Speech rhythm"
            ),
            "language": Exercise(
                title="Word Precision",
                description="Replace generic words in a speech with more specific, vivid alternatives",
                duration="10 minutes, 3x weekly",
                focus_area="Vocabulary and precision"
            ),
            "nonverbal": Exercise(
                title="Gesture Integration",
                description="Practice a short speech while deliberately incorporating 3 planned gestures",
                duration="5 minutes daily",
                focus_area="Body language"
            ),
            "filler": Exercise(
                title="Filler Word Elimination",
                description=filler_exercise_description,
                duration="5 minutes daily",
                focus_area="Speech clarity"
            )
        }
        
        # Add relevant exercises
        for area in areas_for_improvement:
            area_lower = area.lower()
            for key in exercise_map:
                if key in area_lower and len(exercises) < 3:
                    exercises.append(exercise_map[key])
                    break
        
        # Add a general exercise if we don't have enough
        if len(exercises) < 1:
            exercises.append(
                Exercise(
                    title="60-Second Speech",
                    description="Deliver an impromptu 60-second speech on a random topic",
                    duration="5 minutes daily",
                    focus_area="Overall speaking skills"
                )
            )
            
        return exercises
    
    def _generate_motivation(self, overall_score, areas_for_improvement):
        """Generate a motivational message based on performance"""
        if overall_score >= 0.8:
            return ("You're already demonstrating excellent speaking skills! Focus on refining your technique "
                    "and adding advanced elements to stand out as a truly exceptional communicator.")
        elif overall_score >= 0.7:
            return ("You've developed strong speaking fundamentals! With focused practice on your areas for improvement, "
                    "you'll soon reach the next level of public speaking effectiveness.")
        elif overall_score >= 0.6:
            return ("You're showing good progress in your speaking journey. Remember that every great speaker "
                    "started somewhere - consistent practice with these focus areas will yield significant results.")
        elif overall_score >= 0.5:
            return ("You have a solid foundation to build upon. The most successful speakers are those who "
                    "persistently work on improvement. Tackle one area at a time and you'll see steady progress.")
        else:
            return ("Public speaking is a learned skill that improves with practice. Focus on small, incremental "
                    "improvements in these key areas, and you'll be surprised how quickly you can develop.")
                    
    def _analyze_filler_words(self, transcript: str) -> Dict[str, Any]:
        """
        Analyze filler words in the transcript using the filler_detector.
        
        Args:
            transcript: The speech transcript to analyze
            
        Returns:
            Dict containing detailed filler word analysis
        """
        if not transcript:
            return {
                "total_fillers": 0,
                "filler_percentage": 0.0,
                "fillers": {},
                "filler_details": [],
                "word_count": 0,
                "analysis": "No transcript provided for filler word analysis."
            }
        
        try:
            # Use the filler_detector utility for comprehensive analysis
            return count_filler_words(transcript)
        except Exception as e:
            print(f"Error in filler word analysis: {e}")
            # Provide basic fallback
            return {
                "total_fillers": 0,
                "filler_percentage": 0.0,
                "fillers": {},
                "filler_details": [],
                "word_count": len(transcript.split()),
                "analysis": "Filler word analysis unavailable."
            }
    
    def _generate_llm_feedback(self, inputs: FeedbackGeneratorToolInput) -> Dict:
        """
        Generate personalized feedback using LLM based on transcript and context.
        
        Args:
            inputs: FeedbackGeneratorToolInput containing transcript and other analysis data
            
        Returns:
            Dict containing LLM-generated feedback sections
        """
        if not inputs.transcript:
            return None
            
        # Get detailed filler analysis if not already provided
        filler_analysis = inputs.filler_analysis
        if not filler_analysis and inputs.transcript:
            filler_analysis = self._analyze_filler_words(inputs.transcript)
            
        # Get filler analysis info
        filler_details = ""
        if filler_analysis:
            most_common = filler_analysis.get("most_common_filler", "")
            filler_percentage = filler_analysis.get("filler_percentage", inputs.filler_percentage)
            
            # Format top filler words for the prompt
            top_fillers = sorted(
                filler_analysis.get("fillers", {}).items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
            
            if top_fillers:
                filler_details = "TOP FILLER WORDS:\n" + "\n".join([
                    f"- '{word}': {count} times" for word, count in top_fillers
                ])
            
            if most_common:
                filler_details += f"\nMOST COMMON FILLER: '{most_common}'"
        
        # Prepare the prompt for LLM
        prompt = f"""
You are an expert public speaking coach specializing in {inputs.context_label} presentations.
Analyze this speech transcript and provide detailed, personalized feedback.

CONTEXT: {inputs.context_label} presentation
OVERALL SCORE: {inputs.overall_score:.2f}/1.00
SPEECH DURATION: {int(inputs.speech_duration // 60)} minutes {int(inputs.speech_duration % 60)} seconds
SPEAKING PACE: {inputs.words_per_minute:.1f} words per minute
FILLER WORD PERCENTAGE: {filler_analysis.get("filler_percentage", inputs.filler_percentage):.1f}%

{filler_details}

IDENTIFIED STRENGTHS: {', '.join(inputs.strengths)}
AREAS FOR IMPROVEMENT: {', '.join(inputs.areas_for_improvement)}

TRANSCRIPT:
{inputs.transcript[:1000]}  # Limit transcript length to avoid token limits

Based on this information, provide:
1. A brief summary of overall performance (2-3 sentences)
2. Three detailed strengths with specific examples from the transcript
3. Three detailed areas for improvement with specific examples
4. Four actionable suggestions for improvement
5. Two specific exercises to practice
6. A motivational message tailored to this speaker's performance and context
7. Three tips specifically for {inputs.context_label} presentations

Format your response as a JSON object with the following keys:
"summary", "strengths", "issues", "suggestions", "exercises", "motivation", "context_tips"

For "strengths" and "issues", each item should be a dict with "title" and "details" keys.
For "exercises", each item should be a dict with "title", "description", "duration", and "focus_area" keys.
"""

        # Call the LLM API
        headers = {"Content-Type": "application/json"}
        data = {
            "model": self.llm_model,
            "prompt": prompt,
            "temperature": self.llm_temperature,
            "stream": False
        }

        try:
            response = requests.post(self.llm_endpoint, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            llm_response = result.get("response", "")
            
            # Extract JSON from the response
            try:
                # Find JSON content between ```json and ``` or just parse the whole thing
                import re
                json_match = re.search(r'```json\n(.*?)\n```', llm_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = llm_response
                    
                feedback_data = json.loads(json_str)
                return feedback_data
            except json.JSONDecodeError:
                print("Failed to parse LLM response as JSON")
                return None
                
        except (requests.RequestException, KeyError) as e:
            print(f"Error calling LLM API: {e}")
            return None
