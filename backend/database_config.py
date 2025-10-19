"""
Database configuration for Speech Coach application.
Handles PostgreSQL connection and database initialization.
"""

import os
from urllib.parse import urlparse

class DatabaseConfig:
    """Database configuration class"""
    
    # PostgreSQL connection settings
    DATABASE_HOST = os.getenv('DATABASE_HOST', 'localhost')
    DATABASE_PORT = os.getenv('DATABASE_PORT', '5432')
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'speech_coach')
    DATABASE_USER = os.getenv('DATABASE_USER', 'postgres')
    DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD', 'password')
    
    # Build database URL
    if os.getenv('DATABASE_URL'):
        # Use DATABASE_URL if provided (for production/Heroku)
        SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
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

def get_database_config():
    """Get database configuration dictionary"""
    return {
        'SQLALCHEMY_DATABASE_URI': DatabaseConfig.SQLALCHEMY_DATABASE_URI,
        'SQLALCHEMY_TRACK_MODIFICATIONS': DatabaseConfig.SQLALCHEMY_TRACK_MODIFICATIONS,
        'SQLALCHEMY_ENGINE_OPTIONS': DatabaseConfig.SQLALCHEMY_ENGINE_OPTIONS
    }

def print_database_info():
    """Print database connection information (without sensitive data)"""
    parsed = urlparse(DatabaseConfig.SQLALCHEMY_DATABASE_URI)
    print(f"🗄️ Database Configuration:")
    print(f"   Host: {parsed.hostname}")
    print(f"   Port: {parsed.port}")
    print(f"   Database: {parsed.path[1:] if parsed.path else 'N/A'}")
    print(f"   User: {parsed.username}")
    print(f"   Connection: PostgreSQL")
