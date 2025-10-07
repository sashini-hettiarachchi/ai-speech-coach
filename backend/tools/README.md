# MCP Tools for Speech Coach

This directory contains tool implementations following the Model Context Protocol (MCP) pattern for the Speech Coach application.

## Overview

Each tool follows a standardized structure:
- Input/output schemas defined as Pydantic models
- A `run()` method that takes input parameters and returns results
- Clear error handling
- Documentation of functionality and limitations

## Available Tools

### TranscribeTool
- **Input**: Audio/video file path
- **Output**: Full transcript and timed segments
- Uses OpenAI's Whisper for speech recognition

### AudioProsodyTool
- **Input**: Audio/video file path
- **Output**: Prosody features (pitch, pace, fillers, pauses)
- Currently a stub implementation; would use librosa/pyAudioAnalysis

### NLPStructureTool
- **Input**: Speech transcript
- **Output**: Structure metrics (thesis, transitions, readability)
- Currently a stub implementation; would use spaCy

### PronunciationTool
- **Input**: Audio file path, transcript
- **Output**: Pronunciation score, grammar errors
- Currently a stub implementation; would use speech recognition

### VideoPoseTool
- **Input**: Video file path
- **Output**: Nonverbal metrics (eye contact, gestures)
- Currently a stub implementation; would use computer vision

### ScorerTool
- **Input**: Metrics from all analysis tools
- **Output**: Scores for 8 CSSEF competencies (0-1)
- Implements the Communication Skills and Speaker Effectiveness Framework

### FeedbackGeneratorTool
- **Input**: Context label, competency scores, evidence
- **Output**: JSON with feedback structure (strengths, issues, etc.)
- Provides context-aware feedback based on analysis

## Implementation Notes

Most tools currently provide stub implementations with dummy values. In a production implementation:

1. **TranscribeTool**: Already functional with Whisper
2. **AudioProsodyTool**: Would integrate librosa/pyAudioAnalysis
3. **NLPStructureTool**: Would integrate spaCy for NLP analysis
4. **PronunciationTool**: Would integrate pronunciation evaluation APIs
5. **VideoPoseTool**: Would integrate OpenCV/MediaPipe for video analysis
6. **ScorerTool**: Would refine scoring algorithms with ML models
7. **FeedbackGeneratorTool**: Would integrate LLMs for personalized feedback

## Usage Example

```python
from tools.transcribe_tool import TranscribeTool

# Initialize tool
transcribe_tool = TranscribeTool(model_size="tiny")

# Run tool
result = transcribe_tool.run({"file_path": "path/to/audio.mp3"})

# Access results
transcript = result.transcript
segments = result.segments
```
