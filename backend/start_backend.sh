#!/bin/bash
# Script to start the Speech Coach backend with MCP support

# Set the current directory to the script directory
cd "$(dirname "$0")"

# Create necessary directories
mkdir -p uploads

# Set environment variables (can be overridden with .env file if added)
export SERVER_HOST="0.0.0.0"
export SERVER_PORT="5005"
export DEBUG_MODE="true"
export MCP_PROTOCOL_VERSION="2025-06-18"

echo "🚀 Starting Speech Coach Backend with MCP Support..."
echo "📡 Server will be available at http://$SERVER_HOST:$SERVER_PORT"
echo "🔍 Debug mode: $DEBUG_MODE"
echo "⚙️ MCP Protocol version: $MCP_PROTOCOL_VERSION"

# Start the Flask app
python app.py
