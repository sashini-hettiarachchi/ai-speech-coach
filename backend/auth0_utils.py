"""
Auth0 authentication utilities for Speech Coach application.
Handles JWT token verification and user synchronization.
"""

import os
import requests
from functools import wraps
from flask import request, jsonify, g
from jose import jwt, JWTError
import json
from datetime import datetime

# Auth0 Configuration
AUTH0_DOMAIN = os.getenv('AUTH0_DOMAIN')
AUTH0_AUDIENCE = os.getenv('AUTH0_AUDIENCE') 
AUTH0_ALGORITHMS = os.getenv('AUTH0_ALGORITHMS', 'RS256').split(',')

# Development mode flag - set to True to disable Auth0 requirement
DEVELOPMENT_MODE = os.getenv('DEVELOPMENT_MODE', 'True').lower() == 'true'



class AuthError(Exception):
    """Authentication error exception"""
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

def get_token_auth_header():
    """Obtains the Access Token from the Authorization Header"""
    auth = request.headers.get('Authorization', None)
    if not auth:
        raise AuthError({
            'code': 'authorization_header_missing',
            'description': 'Authorization header is expected.'
        }, 401)

    parts = auth.split()
    if parts[0].lower() != 'bearer':
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must start with "Bearer".'
        }, 401)

    elif len(parts) == 1:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Token not found.'
        }, 401)

    elif len(parts) > 2:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must be bearer token.'
        }, 401)

    token = parts[1]
    return token

JWKS_FILE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'jwks.json')
_JWKS_CACHE = None  # simple in-process cache

def _load_jwks():
    """Load JWKS from local json file with simple caching.

    The file should contain the exact JSON obtained from:
        https://<AUTH0_DOMAIN>/.well-known/jwks.json

    Returns the parsed JWKS dict.
    Raises AuthError if the file is missing or invalid.
    """
    global _JWKS_CACHE
    if _JWKS_CACHE is not None:
        return _JWKS_CACHE

    if not os.path.exists(JWKS_FILE_PATH):
        raise AuthError({
            'code': 'jwks_file_missing',
            'description': f'JWKS file not found at {JWKS_FILE_PATH}. Populate it with your tenant JWKS.'
        }, 500)

    try:
        with open(JWKS_FILE_PATH, 'r', encoding='utf-8') as f:
            _JWKS_CACHE = json.load(f)
    except json.JSONDecodeError as e:
        raise AuthError({
            'code': 'jwks_file_invalid',
            'description': f'Invalid JWKS JSON file: {e}'
        }, 500)

    if 'keys' not in _JWKS_CACHE:
        raise AuthError({
            'code': 'jwks_file_invalid',
            'description': 'JWKS JSON must contain a "keys" field.'
        }, 500)
    return _JWKS_CACHE

def get_rsa_key(token):
    """Get RSA key for token verification using local JWKS file.

    This implementation avoids a network call and depends on a locally stored
    JWKS. Ensure the file is kept up to date when Auth0 rotates keys.
    """
    if not AUTH0_DOMAIN:
        raise AuthError({
            'code': 'auth0_not_configured',
            'description': 'AUTH0_DOMAIN environment variable not set.'
        }, 500)

    jwks = _load_jwks()
    print(f"🔍 Loaded local JWKS: {JWKS_FILE_PATH}")

    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}

    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization malformed.'
        }, 401)

    for key in jwks.get('keys', []):
        if key.get('kid') == unverified_header['kid']:
            rsa_key = {
                'kty': key.get('kty'),
                'kid': key.get('kid'),
                'use': key.get('use'),
                'n': key.get('n'),
                'e': key.get('e')
            }
            break
    return rsa_key

def verify_decode_jwt(token):
    """Verify and decode JWT token"""
    print(f"🔍 Verifying JWT token...")
    rsa_key = get_rsa_key(token)
    print(f"🔍 RSA Key obtained for token verification: {rsa_key}")
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=AUTH0_ALGORITHMS,
                audience=AUTH0_AUDIENCE,
                issuer=f'https://{AUTH0_DOMAIN}/'
            )
            print(f"🔍 JWT payload obtained: {payload}")
            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired.'
            }, 401)

        except jwt.JWTClaimsError:
            raise AuthError({
                'code': 'invalid_claims',
                'description': 'Incorrect claims. Please, check the audience and issuer.'
            }, 401)
        except Exception:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'
            }, 400)

    raise AuthError({
        'code': 'invalid_header',
        'description': 'Unable to find the appropriate key.'
    }, 400)



def sync_user_with_database(auth0_user_id):
    """
    Sync user with database - create or update user record
    Returns User model instance
    """
    from models import db, User
    
    # Check if user exists
    user = User.query.filter_by(auth0_user_id=auth0_user_id).first()
    
    if not user:
        # Create new user record
        user = User(auth0_user_id=auth0_user_id)
        db.session.add(user)
        db.session.commit()
        print(f"✅ Created new user record for {auth0_user_id}")
    else:
        # Update sync timestamp
        user.synced_at = datetime.utcnow()
        db.session.commit()
        print(f"🔄 Updated sync timestamp for {auth0_user_id}")
    
    return user

def auth0_required(f):
    """
    Decorator for endpoints that require Auth0 authentication.
    Automatically creates/syncs user records on first access.
    In development mode, creates a mock user for testing.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Get and verify token
            print("🔍 Verifying Auth0 token...")
            token = get_token_auth_header()
            print(f"🔍 Token obtained: {token[:10]}...")  # Print first 10 chars for debugging
            payload = verify_decode_jwt(token)

            # Extract user ID from token
            auth0_user_id = payload.get('sub')
            print(f"🔍 Auth0 user ID from token: {auth0_user_id}")
            if not auth0_user_id:
                raise AuthError({
                    'code': 'invalid_token',
                    'description': 'User ID not found in token.'
                }, 401)
            
            # Sync user with database
            user = sync_user_with_database(auth0_user_id)
            print(f"✅ Authenticated user: {auth0_user_id}")
            
            # Add user info to Flask g object for use in endpoints
            g.current_user = user
            g.auth0_user_id = auth0_user_id
            g.auth0_payload = payload
            g.auth0_token = token
            
            return f(*args, **kwargs)
            
        except AuthError as e:
            return jsonify(e.error), e.status_code
        except Exception as e:
            return jsonify({
                'code': 'server_error',
                'description': f'Authentication error: {str(e)}'
            }), 500
    
    return decorated_function

def get_current_user():
    """Get current authenticated user from Flask g object"""
    print("🔍 Retrieving current user from g object")
    user = getattr(g, 'current_user', None)
    print(f"🔍 Retrieving current user from g: {user}")
    return user

def get_auth0_user_id():
    """Get current Auth0 user ID from Flask g object"""
    return getattr(g, 'auth0_user_id', None)

def get_auth0_payload():
    """Get current Auth0 token payload from Flask g object"""
    return getattr(g, 'auth0_payload', None)

# Error handler for AuthError
def handle_auth_error(ex):
    """Error handler for authentication errors"""
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response
