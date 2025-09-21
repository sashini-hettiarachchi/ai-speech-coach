# Speech Coach Knowledge Servers

A comprehensive knowledge management system that provides contextual intelligence for LLM-powered speech coaching. This system replaces traditional REST APIs with specialized knowledge servers that can be easily integrated with Large Language Models.

## Architecture Overview

The system consists of four specialized knowledge servers and a unified interface:

1. **Domain Knowledge Server** - Domain-specific speaking guidelines and best practices
2. **User Knowledge Server** - User profiles, progress tracking, and personalized coaching
3. **Event Knowledge Server** - Event-specific context and audience adaptation
4. **Audience Knowledge Server** - Audience profiles and communication adaptation strategies
5. **LLM Interface** - Unified access point that combines all knowledge sources

## Quick Start

```python
from llm_interface import SpeechCoachLLMInterface

# Initialize the unified interface
interface = SpeechCoachLLMInterface()

# Get comprehensive context for an LLM
context = interface.get_comprehensive_context(
    user_id="user123",
    domain="corporate",
    event_id="quarterly_review",
    audience_id="executives",
    speech_metrics={
        "pace_wpm": 140,
        "filler_words_count": 5,
        "vocal_variety_score": 7.2,
        "confidence_score": 7.8
    }
)

# Get contextual feedback for a speech session
feedback = interface.get_contextual_feedback(
    user_id="user123",
    speech_analysis={
        "domain": "corporate",
        "event_id": "quarterly_review",
        "audience_id": "executives",
        "metrics": {...},
        "transcript": "...",
        "delivery_score": 7.5
    }
)
```

## Knowledge Servers

### 1. Domain Knowledge Server (`domain_knowledge_server.py`)

Provides domain-specific speaking guidelines and analysis capabilities.

**Available Domains:**
- `public_speaking` - General public speaking skills
- `corporate` - Corporate communications and business presentations
- `technical` - Technical presentations and demos
- `academic` - Academic presentations and research talks

**Key Methods:**
- `get_context_for_llm(query_type, **kwargs)` - Get domain-specific context
- `get_domain_guidelines(domain)` - Get complete guidelines for a domain
- `analyze_speech_against_domain(domain, speech_metrics)` - Analyze speech fit

### 2. User Knowledge Server (`user_knowledge_server.py`)

Manages user profiles, learning progress, and personalized coaching strategies.

**Key Features:**
- User skill level tracking (beginner, intermediate, advanced)
- Personal goal management and progress tracking
- Learning preference adaptation
- Session history and performance analytics

**Key Methods:**
- `get_context_for_llm(query_type, **kwargs)` - Get user-specific context
- `get_user_coaching_context(user_id)` - Get complete user profile
- `analyze_user_progress(user_id)` - Get progress analysis

### 3. Event Knowledge Server (`event_knowledge_server.py`)

Provides event-specific context and audience adaptation strategies.

**Available Events:**
- `quarterly_review` - Business quarterly reviews
- `tech_conference` - Technical conference presentations
- `team_standup` - Team meetings and standups
- `sales_demo` - Sales demonstrations and pitches

**Key Methods:**
- `get_context_for_llm(query_type, **kwargs)` - Get event-specific context
- `get_coaching_tips(event_id)` - Get targeted coaching recommendations
- `analyze_event_speech_fit(event_id, speech_metrics)` - Analyze speech appropriateness

### 4. Audience Knowledge Server (`audience_knowledge_server.py`)

Provides audience-specific profiles and communication adaptation strategies.

**Available Audiences:**
- `executives` - Executive leadership teams (C-suite, VPs, Directors)
- `technical_team` - Engineering and technical professionals
- `general_public` - General audience with varied backgrounds
- `students` - Academic students and trainees
- `clients` - Client stakeholders and representatives
- `investors` - Investment committees and venture capitalists

**Key Methods:**
- `get_context_for_llm(query_type, **kwargs)` - Get audience-specific context
- `get_audience_profile(audience_id)` - Get detailed audience characteristics
- `get_adaptation_strategy(audience_id)` - Get communication adaptation guidelines
- `analyze_speech_for_audience(audience_id, speech_metrics)` - Analyze audience fit

### 5. LLM Interface (`llm_interface.py`)

Unified interface that combines all knowledge sources for LLM integration.

**Core Capabilities:**
- **Health Monitoring** - Check status of all knowledge servers
- **Context Aggregation** - Combine user, domain, event, and audience knowledge
- **Contextual Analysis** - Provide comprehensive speech analysis
- **Personalized Feedback** - Generate tailored recommendations

**Key Methods:**
- `get_comprehensive_context()` - Get complete context from all sources
- `get_contextual_feedback()` - Generate personalized feedback
- `get_available_options()` - List available users, domains, events, and audiences
- `health_check()` - Verify system status

## Integration with LLMs

The knowledge servers are designed for seamless LLM integration:

### Context-Aware Coaching

```python
# Get comprehensive context for LLM prompting
context = interface.get_comprehensive_context(
    user_id="user123",
    domain="corporate", 
    event_id="quarterly_review",
    audience_id="executives",
    speech_metrics=speech_data
)

# Use context in LLM prompt
llm_prompt = f"""
Based on this comprehensive coaching context:
{json.dumps(context, indent=2)}

Provide detailed feedback for this speech session...
"""
```

### Personalized Recommendations

```python
# Generate contextual feedback
feedback = interface.get_contextual_feedback(
    user_id="user123",
    speech_analysis=analysis_results
)

# Extract personalized recommendations
recommendations = feedback.get("personalized_recommendations", [])
```

## Data Models

### Speech Metrics Structure

```python
speech_metrics = {
    "pace_wpm": 140,                    # Words per minute
    "filler_words_count": 5,            # Number of filler words
    "pause_frequency": 0.18,            # Pauses per minute
    "vocal_variety_score": 7.2,         # Vocal variety rating (0-10)
    "confidence_score": 7.8,            # Confidence rating (0-10)
    "eye_contact_score": 6.5,           # Eye contact rating (0-10)
    "gesture_appropriateness": 7.0      # Gesture rating (0-10)
}
```

### Context Response Structure

All knowledge servers return structured JSON responses with:
- `context_type` - Type of context provided
- `timestamp` - When context was generated
- Domain-specific data fields
- Analysis results and recommendations

## Testing

Each server includes comprehensive test functions:

```bash
# Test individual servers
python domain_knowledge_server.py
python user_knowledge_server.py  
python event_knowledge_server.py
python audience_knowledge_server.py

# Test unified interface
python llm_interface.py
```

## Configuration

### Adding New Domains

Add new domains to `domain_knowledge_server.py`:

```python
"new_domain": {
    "name": "New Domain Name",
    "structure": {...},
    "delivery": {...},
    "best_practices": [...],
    "common_mistakes": [...]
}
```

### Adding New Users

Add users to `user_knowledge_server.py`:

```python
"new_user_id": {
    "name": "User Name",
    "skill_level": "intermediate",
    "primary_goals": [...],
    # ... other user data
}
```

### Adding New Audiences

Add audiences to `audience_knowledge_server.py`:

```python
"new_audience_id": {
    "name": "Audience Name",
    "type": AudienceType.NEW_TYPE,
    "size": AudienceSize.MEDIUM,
    "expertise_level": ExpertiseLevel.INTERMEDIATE,
    "demographics": {...},
    "communication_preferences": [...],
    # ... other audience data
}
```

### Adding New Events

Add events to `event_knowledge_server.py`:

```python
"new_event_id": {
    "name": "Event Name",
    "type": "event_type",
    "duration": 30,
    # ... other event data
}
```

The system includes comprehensive error handling:
- Graceful fallbacks for missing data
- Detailed logging for debugging
- JSON serialization compatibility
- Input validation and sanitization

## Performance Considerations

- **Caching**: Knowledge bases are loaded once at initialization
- **Lazy Loading**: Context is only computed when requested
- **Memory Efficient**: Uses dataclasses and enums for structured data
- **Scalable**: Each server can be deployed independently

## Future Enhancements

1. **Database Integration**: Replace in-memory data with persistent storage
2. **Real-time Updates**: Add capabilities for dynamic knowledge updates
3. **Analytics**: Enhanced progress tracking and performance analytics
4. **Multi-language**: Support for multiple languages and cultural contexts
5. **Plugin Architecture**: Extensible system for custom knowledge domains

## Support

For issues or questions about the knowledge server system:
1. Check the test functions for usage examples
2. Review the comprehensive context output for data structure reference
3. Use the health check endpoint to verify system status

The system is designed to be LLM-agnostic and can integrate with any language model that can process JSON context data.
