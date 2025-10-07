# Speech Coach MCP Implementation Guide

This guide explains the MCP (Model Context Protocol) implementation for the Speech Coach application. The backend exposes a speech analysis pipeline through a single endpoint (`POST /api/v1/analyze`), orchestrating various analysis tools.

## Architecture Overview

The Speech Coach backend follows the MCP pattern:
- Each analysis step is encapsulated in a dedicated Tool
- Tools have standardized input/output schemas (Pydantic models)
- The Flask app orchestrates tool execution in a pipeline
- Results are aggregated into a structured JSON response

## Tool Pipeline

1. **TranscribeTool**: Converts speech to text (using Whisper)
2. **AudioProsodyTool**: Analyzes prosodic features (pitch, pace, fillers)
3. **NLPStructureTool**: Analyzes transcript structure and coherence
4. **PronunciationTool**: Evaluates pronunciation and grammar
5. **VideoPoseTool** (optional): Analyzes nonverbal communication if video input
6. **ScorerTool**: Calculates competency scores using CSSEF framework
7. **FeedbackGeneratorTool**: Generates structured feedback

## Implementation Details

### Tools Implementation (`/backend/tools/`)
- **Base Tool**: Abstract base class with common functionality
- **Tool Schemas**: Pydantic models for input/output validation
- **Stub Implementations**: Placeholder implementations that return realistic dummy data
- **Production TODOs**: Comments indicating integration points for real models

### API Implementation (`/backend/app.py`)
- **Endpoint**: `POST /api/v1/analyze`
- **File Upload**: Saves audio/video to temporary storage
- **Pipeline Execution**: Sequential execution of tools
- **Response Generation**: Aggregated results in structured JSON
- **Error Handling**: Comprehensive error handling and logging

## Usage Guide

### API Request

```bash
curl -X POST http://localhost:5005/api/v1/analyze \
  -F "file=@/path/to/speech.mp3" \
  -F "user_id=user123" \
  -F "domain=public_speaking" \
  -F "context_label=professional"
```

### API Response

```json
{
  "status": "success",
  "timestamp": "2025-10-02T14:30:00Z",
  "request": {
    "user_id": "user123",
    "domain": "public_speaking",
    "context_label": "professional",
    "file_name": "speech.mp3"
  },
  "analysis": {
    "transcript": "...",
    "segments": [...],
    "audio_prosody": {...},
    "structure": {...},
    "pronunciation": {...},
    "scores": {
      "competency_scores": {...},
      "overall_score": 0.78,
      "strengths": [...],
      "areas_for_improvement": [...]
    },
    "feedback": {
      "summary": "...",
      "strengths": [...],
      "issues": [...],
      "suggestions": [...],
      "micro_exercises": [...],
      "motivation": "..."
    }
  }
}
```

## Future Enhancements

1. **Replace Stub Implementations**: Integrate real models for each analysis step
2. **Tool Registry**: Dynamic tool registration and discovery
3. **Asynchronous Processing**: Support for long-running analysis tasks
4. **Caching**: Results caching for improved performance
5. **Tool Versioning**: Support for multiple tool versions

## Implementation Notes

- TranscribeTool is the only tool currently using a real model (Whisper)
- Other tools return realistic dummy values for demonstration
- Tool implementations include TODOs for real model integration
- The Flask app handles file management (saving, cleanup)
