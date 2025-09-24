"""
Configuration settings for the Speech Coach application.
This module centralizes all configuration settings and allows for environment variable overrides.
"""

import os

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
MCP_DOMAIN_SERVER_URL = os.environ.get("MCP_DOMAIN_SERVER_URL", "")  # Empty string means use direct instance
MCP_USER_SERVER_URL = os.environ.get("MCP_USER_SERVER_URL", "")
MCP_EVENT_SERVER_URL = os.environ.get("MCP_EVENT_SERVER_URL", "")
MCP_AUDIENCE_SERVER_URL = os.environ.get("MCP_AUDIENCE_SERVER_URL", "")

# Service Account Configuration 
SERVICE_ACCOUNT_KEY_PATH = os.environ.get("SERVICE_ACCOUNT_KEY_PATH", "key.json")
REGION = os.environ.get("REGION", "us-central1")

# Audio Test Data
TEST_AUDIO_FILE_PATH = os.environ.get("TEST_AUDIO_FILE_PATH", "test_data/test2.wav")
