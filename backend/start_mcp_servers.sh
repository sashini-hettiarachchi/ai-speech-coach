#!/bin/bash

# Speech Coach MCP Servers Startup Script
# This script starts all three MCP servers for the Speech Coach application

echo "🚀 Starting Speech Coach MCP Servers..."

# Set the script directory as base path
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR"

# Function to start a server in the background
start_server() {
    local server_name=$1
    local server_file=$2
    local port=$3
    
    echo "📡 Starting $server_name on port $port..."
    
    # Change to backend directory and start server
    cd "$BACKEND_DIR"
    python "mcp_servers/$server_file" &
    
    # Store the process ID
    echo $! > "${server_name}_server.pid"
    
    # Give server time to start
    sleep 2
}

# Function to check if server is running
check_server() {
    local port=$1
    local server_name=$2
    
    if curl -s "http://localhost:$port/health" > /dev/null; then
        echo "✅ $server_name is running on port $port"
        return 0
    else
        echo "❌ $server_name failed to start on port $port"
        return 1
    fi
}

# Start all servers
start_server "event" "event_server.py" 5001
start_server "user" "user_server.py" 5002
start_server "domain" "domain_server.py" 5003

echo ""
echo "⏳ Waiting for servers to initialize..."
sleep 3

echo ""
echo "🔍 Checking server status..."

# Check if all servers are running
check_server 5001 "Event Context Server"
check_server 5002 "User Context Server" 
check_server 5003 "Domain Context Server"

echo ""
echo "📋 Server Summary:"
echo "   Event Context Server:  http://localhost:5001"
echo "   User Context Server:   http://localhost:5002"
echo "   Domain Context Server: http://localhost:5003"
echo ""
echo "💡 To stop all servers, run: ./stop_mcp_servers.sh"
echo "📊 Main Speech Coach App: Run 'python app.py' in the backend directory"
echo ""
echo "🎉 All MCP servers are ready!"
