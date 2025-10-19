# Speech Coach

A comprehensive speech coaching application that analyzes audio and video to provide feedback and recommendations for improving public speaking skills.

## Overview

Speech Coach is an AI-powered platform that helps users improve their public speaking through automated analysis and personalized feedback. It integrates LLM-based recommendations with context from specialized knowledge servers through the Model Context Protocol (MCP).

## Simplified Version

A simplified version of the application is available that focuses on the core `/api/v1/analyze` endpoint. It maintains the MCP architecture while streamlining the implementation. To use the simplified version:

1. Run `./backend/start_simplified.sh`
2. Access the API at `http://localhost:5000/api/v1/analyze`

See `backend/SIMPLIFIED_README.md` for detailed documentation on the simplified version.

## Architecture

The application is composed of:

- **Backend API**: Flask server providing speech analysis endpoints
- **Frontend**: Next.js application providing the user interface
- **MCP Knowledge Servers**: Specialized context providers (Domain, User, Event, Audience)
- **LLM Integration**: Integration with Ollama for generating personalized recommendations

### Model Context Protocol (MCP)

This application implements the Model Context Protocol (MCP), allowing intelligent coordination between:

- **Core Speech Processing**: Analyzing audio features like pace, filler words, etc.
- **Knowledge Servers**: Providing domain-specific guidance
- **LLM Integration**: Generating personalized recommendations

## Setup

### Backend

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Start the Flask API:
   ```
   python app.py
   ```

### Frontend

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Run the development server:
   ```
   npm run dev
   ```

## Configuration

The application uses a centralized configuration system in `backend/config.py`. Key settings can be overridden using environment variables:

| Config Variable | Environment Variable | Default | Description |
|----------------|---------------------|---------|-------------|
| `SERVER_HOST` | `SERVER_HOST` | `0.0.0.0` | Host IP for Flask server |
| `SERVER_PORT` | `SERVER_PORT` | `5005` | Port for Flask server |
| `FRONTEND_URL` | `FRONTEND_URL` | `http://localhost:3000` | URL for CORS origins |
| `LLM_ENDPOINT` | `LLM_ENDPOINT` | `http://localhost:11434/api/generate` | Ollama API endpoint |
| `LLM_MODEL` | `LLM_MODEL` | `llama3` | LLM model to use |
| `LLM_TEMPERATURE` | `LLM_TEMPERATURE` | `0.3` | Creativity parameter |

## API Endpoints

### Main Analysis Endpoint

```
POST /api/v1/analyze
```
Analyzes an audio file with optional context parameters:
- `file`: Audio file
- `user_id`: User identifier
- `domain`: Speaking domain (e.g., public_speaking, corporate)
- `event_id`: Event context
- `audience_id`: Audience context

### MCP Endpoints

```
POST /api/v1/mcp/context
```
Get comprehensive context from knowledge servers

```
POST /api/v1/mcp/feedback
```
Get contextual feedback with personalized recommendations

```
GET /api/v1/mcp/health
```
Check MCP server health

### Other Endpoints

```
GET /api/v1/health
```
Check server health

```
GET /api/v1/options
```
Get available options for users, domains, events, etc.

```
POST /api/v1/test-llm
```
Test LLM recommendations with sample data

## License

[MIT License](LICENSE)
