# Testing the MCP Implementation

This document provides instructions for testing the Model Context Protocol (MCP) implementation in the Speech Coach application.

## Starting the Backend

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Run the start script:
   ```bash
   ./start_backend.sh
   ```

## Testing MCP Endpoints

Here are some examples of how to test the MCP endpoints using curl:

### 1. Health Check

```bash
curl http://localhost:5005/api/v1/mcp/health
```

This should return a health status for all MCP servers.

### 2. List Available Options

```bash
curl http://localhost:5005/api/v1/options
```

This will return a list of available domains, users, events, and audiences.

### 3. Get a Specific Resource

```bash
# Get the technical domain resource
curl http://localhost:5005/api/v1/mcp/resources/domain/technical

# Get a user profile
curl http://localhost:5005/api/v1/mcp/resources/user/user123

# Get event guidelines
curl http://localhost:5005/api/v1/mcp/resources/event/presentation

# Get audience insights
curl http://localhost:5005/api/v1/mcp/resources/audience/technical
```

### 4. Execute a Tool

```bash
# Analyze speech for a specific domain
curl -X POST http://localhost:5005/api/v1/mcp/tools \
  -H "Content-Type: application/json" \
  -d '{
    "server_type": "domain",
    "tool_name": "analyzeSpeech",
    "parameters": {
      "domain": "technical",
      "speech_metrics": {
        "pace_wpm": 140,
        "filler_count": 5,
        "filler_percentage": 3.5,
        "vocal_variety": 7.0,
        "overall_score": 7.5
      }
    }
  }'
```

### 5. Get Contextual Feedback

```bash
curl -X POST http://localhost:5005/api/v1/mcp/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "domain": "technical",
    "event_id": "presentation",
    "audience_id": "technical",
    "speech_analysis": {
      "filler_analysis": {
        "total_fillers": 5,
        "filler_percentage": 3.5,
        "fillers": ["um", "uh", "like"]
      },
      "delivery_metrics": {
        "pace": 140,
        "vocal_variety": 7.0,
        "confidence": 7.5,
        "overall_score": 7.2
      }
    }
  }'
```

### 6. Test the MCP Resources and Tools

```bash
curl -X POST http://localhost:5005/api/v1/test-mcp \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "technical"
  }'
```

### 7. Analyze a Speech File

To test the full speech analysis with MCP integration:

```bash
curl -X POST http://localhost:5005/api/v1/analyze \
  -F "file=@test_data/test2.wav" \
  -F "user_id=user123" \
  -F "domain=technical" \
  -F "event_id=presentation" \
  -F "audience_id=technical"
```

## Expected Responses

All responses should be well-structured JSON with these common elements:

1. For MCP-specific endpoints:
   - `jsonrpc`: "2.0"
   - `result` or `error` object
   - Appropriate HTTP status code

2. For resource endpoints:
   - `uri`: Resource URI
   - `content`: Resource content object

3. For tool execution:
   - Tool-specific response structure
   - Success or error indicators

## Troubleshooting

If you encounter issues:

1. Check server logs for detailed error messages
2. Verify resource files exist in the correct location
3. Ensure the MCP client is properly initialized
4. Check for syntax errors in resource JSON files
