# Configuration Changes

This document summarizes the configuration changes made to the Speech Coach application.

## 1. Configuration Centralization Changes

Originally, we extracted hard-coded URLs and centralized configuration in the Speech Coach application.

### Summary of Initial Changes

1. Created a central `config.py` file to store all configuration settings
2. Updated `app.py` to use configuration variables instead of hard-coded values
3. Modified utility modules to use centralized configuration
4. Updated documentation to reflect configuration changes

## 2. MCP Integration Changes

The second major update integrated the Model Context Protocol (MCP) into the Speech Coach application.

### Summary of MCP Integration Changes

1. Created MCP-compliant server implementations for four knowledge domains
2. Implemented structured JSON resources for each knowledge domain
3. Developed a unified MCP client for interacting with knowledge servers
4. Added MCP-specific API endpoints
5. Updated configuration to support MCP servers and resources

## Key Benefits

- **Environment Variable Support**: All settings can be overridden with environment variables
- **Consistent Configuration**: Single source of truth for application settings
- **Improved Maintainability**: Easier to change configuration across the application
- **Better Documentation**: Clear documentation of all available configuration options

## Configuration File Structure

```python
# Server Configuration
SERVER_HOST = os.environ.get("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.environ.get("SERVER_PORT", 5005))
DEBUG_MODE = os.environ.get("DEBUG_MODE", "True").lower() == "true"

# Frontend URLs for CORS
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
CORS_ORIGINS = [FRONTEND_URL]
CORS_METHODS = ["GET", "POST", "OPTIONS"]
CORS_HEADERS = ["Content-Type", "Authorization"]
CORS_SUPPORTS_CREDENTIALS = True

# File Storage
UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")

# LLM Configuration
LLM_ENDPOINT = os.environ.get("LLM_ENDPOINT", "http://localhost:11434/api/generate")
LLM_MODEL = os.environ.get("LLM_MODEL", "llama3")
LLM_TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", 0.3))

# MCP Protocol Configuration
MCP_PROTOCOL_VERSION = os.environ.get("MCP_PROTOCOL_VERSION", "2025-06-18")
MCP_RESOURCE_DIR = os.environ.get("MCP_RESOURCE_DIR", os.path.join(os.path.dirname(__file__), "mcp_servers", "resources"))

# MCP Server Configuration
MCP_DOMAIN_SERVER_URL = os.environ.get("MCP_DOMAIN_SERVER_URL", "")
MCP_USER_SERVER_URL = os.environ.get("MCP_USER_SERVER_URL", "")
MCP_EVENT_SERVER_URL = os.environ.get("MCP_EVENT_SERVER_URL", "")
MCP_AUDIENCE_SERVER_URL = os.environ.get("MCP_AUDIENCE_SERVER_URL", "")
```

## Files Modified

1. **app.py**: Updated to use centralized configuration
2. **utils/llm_recommendations.py**: Now imports configuration values
3. **utils/recommendations.py**: Uses centralized LLM endpoint and model
4. **utils/filler_detector.py**: Uses centralized LLM configuration
5. **README.md**: Updated with configuration documentation
6. **backend/README.md**: Enhanced with configuration details

## Usage Examples

### Basic Usage
```bash
python app.py
```

### Changing Server Port
```bash
export SERVER_PORT=8000
python app.py
```

### Using a Different LLM Model
```bash
export LLM_MODEL=llama3:8b
export LLM_ENDPOINT="http://another-server:11434/api/generate"
python app.py
```

### Pointing to a Different Frontend
```bash
export FRONTEND_URL="https://speech-coach-frontend.example.com"
python app.py
```

## MCP Integration Details

### MCP Server Implementation

- Created MCP-compliant server implementations for four knowledge domains:
  - **Domain Knowledge Server**: Speaking contexts (technical, corporate, academic, casual)
  - **User Knowledge Server**: User profiles and history
  - **Event Knowledge Server**: Event-specific guidelines (presentations, interviews, meetings)
  - **Audience Knowledge Server**: Audience insights (technical, executive, academic, general)

### Resource Management

- Created structured JSON resources for each knowledge domain
- Implemented resource URI scheme for standardized access:
  - `domain://<domain_id>`
  - `user://<user_id>`
  - `event://<event_id>`
  - `audience://<audience_id>`

### MCP Client Implementation

- Created a unified `MCPClient` class for interacting with MCP servers
- Implemented `MCPKnowledgeInterface` for coordinating across knowledge domains

### API Endpoints

Added new MCP-specific endpoints:
- `GET /api/v1/mcp/health` - MCP server health check
- `POST /api/v1/mcp/context` - Get comprehensive context from MCP servers
- `POST /api/v1/mcp/feedback` - Get contextual feedback using MCP
- `POST /api/v1/mcp/tools` - Execute specific MCP tools
- `GET /api/v1/mcp/resources/<type>/<id>` - Get specific MCP resource
- `POST /api/v1/test-mcp` - Test MCP resources and tools

### Files Created for MCP Implementation

1. **mcp_servers/mcp_client.py**: MCP client and knowledge interface
2. **mcp_servers/domain_server_mcp.py**: Domain knowledge MCP server
3. **mcp_servers/user_server_mcp.py**: User knowledge MCP server
4. **mcp_servers/event_server_mcp.py**: Event knowledge MCP server
5. **mcp_servers/audience_server_mcp.py**: Audience knowledge MCP server
6. **mcp_servers/resources/*.json**: JSON resources for each knowledge domain

### Files Modified for MCP Integration

1. **app.py**: Updated to use MCP servers and client
2. **config.py**: Added MCP configuration parameters

## Next Steps

1. Consider adding additional configuration options for:
   - Log levels and log file paths
   - File retention policies
   - Performance tuning parameters
   - Feature flags

2. Consider implementing a configuration validation system to ensure valid settings

3. Add configuration for authentication and security settings when implemented

4. Future MCP enhancements:
   - **Remote MCP Servers**: Support for hosting MCP servers separately
   - **Dynamic Resource Creation**: API endpoints for creating and updating resources
   - **Expanded Tool Sets**: Additional analysis tools for each knowledge domain
   - **Prompt Templates**: More sophisticated prompt templating for LLM integration
   - **Resource Versioning**: Track and manage resource versions over time
