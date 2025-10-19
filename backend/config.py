"""
Configuration settings for the Speech Coach application.
This module centralizes all configuration settings and allows for environment variable overrides.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Server Configuration
SERVER_HOST = os.environ.get("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.environ.get("SERVER_PORT", 5000))
DEBUG_MODE = os.environ.get("DEBUG_MODE", "True").lower() == "true"

# Frontend URLs for CORS
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
CORS_ORIGINS = ["http://localhost:3000", "http://localhost:3001"]
CORS_METHODS = ["GET", "POST", "OPTIONS", "PUT", "DELETE", "PATCH"]
CORS_HEADERS = [
    "Content-Type", 
    "Authorization", 
    "X-Requested-With",
    "Accept",
    "Origin",
    "Cache-Control",
    "X-File-Name"
]
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

# Database Configuration
DATABASE_HOST = os.environ.get('DATABASE_HOST', 'localhost')
DATABASE_PORT = os.environ.get('DATABASE_PORT', '5432')
DATABASE_NAME = os.environ.get('DATABASE_NAME', 'speech_coach')
DATABASE_USER = os.environ.get('DATABASE_USER', 'postgres')
DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD', 'password')

# Build database URL
if os.environ.get('DATABASE_URL'):
    # Use DATABASE_URL if provided (for production/Heroku)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    # Handle postgres:// vs postgresql:// scheme
    if SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql+psycopg://', 1)
    elif SQLALCHEMY_DATABASE_URI.startswith('postgresql://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgresql://', 'postgresql+psycopg://', 1)
else:
    # Build URL from individual components (using psycopg3)
    SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"

# SQLAlchemy settings
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_timeout': 20,
    'max_overflow': 0
}

# Auth0 Configuration
AUTH0_DOMAIN = os.environ.get('AUTH0_DOMAIN')
AUTH0_AUDIENCE = os.environ.get('AUTH0_AUDIENCE') 
AUTH0_ALGORITHMS = os.environ.get('AUTH0_ALGORITHMS', 'RS256').split(',')

# Auth0 Management API (optional - for fetching user profiles)
AUTH0_MANAGEMENT_CLIENT_ID = os.environ.get('AUTH0_MANAGEMENT_CLIENT_ID')
AUTH0_MANAGEMENT_CLIENT_SECRET = os.environ.get('AUTH0_MANAGEMENT_CLIENT_SECRET')
