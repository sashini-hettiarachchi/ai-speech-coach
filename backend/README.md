# Speech Coach API with MCP Integration

Speech Coach is a comprehensive speech analysis and coaching API that uses the Model Context Protocol (MCP) architecture to provide personalized feedback and recommendations.

## Setup Instructions

1. **Create and activate a virtual environment:**
   Use Python 3.11+
   ```zsh
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies:**
   ```zsh
   pip install -r requirements.txt
   ```

3. **Configuration:**
   - All settings are centralized in `config.py`
   - Override settings via environment variables:
   ```zsh
   # Example: changing the port and LLM model
   export SERVER_PORT=8000
   export LLM_MODEL=llama3:8b
   ```
   
   Key configuration options:
   - `SERVER_HOST`: Host to bind the server to (default: 0.0.0.0)
   - `SERVER_PORT`: Port to run the server on (default: 5005)
   - `FRONTEND_URL`: Frontend URL for CORS (default: http://localhost:3000)
   - `LLM_ENDPOINT`: Endpoint for LLM API (default: http://localhost:11434/api/generate)
   - `LLM_MODEL`: Model to use for recommendations (default: llama3)

4. **Run the app:**
   ```zsh
   python app.py
   ```
   The API server will be available at http://localhost:5000/

## Architecture

The application uses the Model Context Protocol (MCP) architecture to provide a standardized way for LLMs to access knowledge sources.

### Key Components

- `app.py`: **Main entry point** - Flask API with MCP integration
- `mcp_servers/`: Knowledge servers (Domain, User, Event, Audience)
- `utils/`: Speech analysis utilities
- `uploads/`: Temporary storage for uploaded audio files
- `test_data/`: Test audio files for development

## API Endpoints

- `GET /api/v1/health` - Health check
- `GET /api/v1/options` - Available options
- `POST /api/v1/analyze` - Analyze speech with MCP integration
- `POST /api/v1/test-llm` - Test LLM recommendations
- `POST /api/v1/mcp/context` - Get MCP context
- `POST /api/v1/mcp/feedback` - Get MCP feedback
- `GET /api/v1/mcp/health` - MCP health check

## Using the API

### Analyze Speech

To analyze an audio file with MCP-integrated feedback:

```bash
curl -X POST http://localhost:5000/api/v1/analyze \
  -F "file=@/path/to/your/audiofile.wav" \
  -F "user_id=user123" \
  -F "domain=public_speaking" \
  -F "event_id=presentation" \
  -F "audience_id=technical"
```

### Get MCP Context

To get comprehensive context using the MCP protocol:

```bash
curl -X POST http://localhost:5000/api/v1/mcp/context \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "domain": "public_speaking",
    "event_id": "presentation",
    "audience_id": "technical"
  }'
```

### Get MCP Feedback

To get contextual feedback using the MCP protocol:

```bash
curl -X POST http://localhost:5000/api/v1/mcp/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "speech_analysis": {
      "transcript": "Hello everyone, thanks for joining today.",
      "filler_analysis": {
        "total_fillers": 0,
        "filler_percentage": 0
      },
      "delivery_metrics": {
        "pace": 135,
        "vocal_variety": 7.8,
        "confidence": 8.2,
        "overall_score": 8.0
      }
    }
  }'
```

## LLM Integration

The app integrates with LLM services for generating personalized recommendations.

### Setting up Ollama LLM Service

1. **Start Ollama in Docker:**
   ```bash
   docker run -d --name ollama -p 11434:11434 ollama/ollama
   ```

2. **Pull a model:**
   ```bash
   docker exec -it ollama ollama pull llama3
   ```

This will set up an HTTP endpoint for the LLM at port `11434`, which is used by default in the app configuration.

## MCP Architecture Benefits

- **Standardized Protocol**: Uses JSON-RPC 2.0 for knowledge server communication
- **Modular Design**: Separate knowledge servers for domain, user, event, and audience data
- **Extensible**: Easy to add new knowledge sources following the MCP pattern
- **Robust Error Handling**: Standard error responses and status reporting

## Notes

- For development, the app runs in debug mode by default
- Do not commit your `.env` file or `.venv/` folder to version control
- The MCP integration uses a wrapper pattern to preserve existing functionality

