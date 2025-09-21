#!/bin/bash

# Speech Coach MCP Servers Stop Script
# This script stops all running MCP servers

echo "🛑 Stopping Speech Coach MCP Servers..."

# Set the script directory as base path
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to stop a server
stop_server() {
    local server_name=$1
    local pid_file="${server_name}_server.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        echo "🔄 Stopping $server_name (PID: $pid)..."
        
        if kill "$pid" 2>/dev/null; then
            echo "✅ $server_name stopped successfully"
        else
            echo "⚠️  $server_name process not found (may have already stopped)"
        fi
        
        # Remove PID file
        rm -f "$pid_file"
    else
        echo "ℹ️  No PID file found for $server_name"
    fi
}

# Change to script directory
cd "$SCRIPT_DIR"

# Stop all servers
stop_server "event"
stop_server "user"
stop_server "domain"

# Also kill any Python processes running our server files (backup method)
echo ""
echo "🔍 Checking for any remaining server processes..."

pkill -f "event_server.py" 2>/dev/null && echo "🗑️  Killed remaining event_server.py processes"
pkill -f "user_server.py" 2>/dev/null && echo "🗑️  Killed remaining user_server.py processes"
pkill -f "domain_server.py" 2>/dev/null && echo "🗑️  Killed remaining domain_server.py processes"

echo ""
echo "✅ All MCP servers have been stopped!"
echo "🚀 To restart servers, run: ./start_mcp_servers.sh"
