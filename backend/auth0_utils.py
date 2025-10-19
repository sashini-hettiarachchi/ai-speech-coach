"""
Auth0 authentication utilities for Speech Coach application.
Handles JWT token verification and user synchronization.
"""

import os
import requests
from functools import wraps
from flask import request, jsonify, g
from jose import jwt, JWTError
from urllib.request import urlopen
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

def get_rsa_key(token):
    """Get RSA key for token verification"""
    if not AUTH0_DOMAIN:
        raise AuthError({
            'code': 'auth0_not_configured',
            'description': 'AUTH0_DOMAIN environment variable not set.'
        }, 500)
        
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())
    
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}
    
    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization malformed.'
        }, 401)

    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    return rsa_key

def verify_decode_jwt(token):
    """Verify and decode JWT token"""
    rsa_key = get_rsa_key(token)
    print("RSA Key:", rsa_key)
    
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=AUTH0_ALGORITHMS,
                audience=AUTH0_AUDIENCE,
                issuer=f'https://{AUTH0_DOMAIN}/'
            )
            print("Auth0 Payload:", payload)
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
        # # Skip auth in development mode
        # if DEVELOPMENT_MODE:
        #     print("🚧 Development Mode: Skipping Auth0 verification")
        #     # Create a mock user for development
        #     from models import db, User
            
        #     mock_auth0_id = 'dev-user-123'
        #     user = User.query.filter_by(auth0_user_id=mock_auth0_id).first()
        #     if not user:
        #         user = User(auth0_user_id=mock_auth0_id)
        #         db.session.add(user)
        #         db.session.commit()
        #         print(f"✅ Created development user: {mock_auth0_id}")
            
        #     # Add user info to Flask g object
        #     g.current_user = user
        #     g.auth0_user_id = mock_auth0_id
        #     g.auth0_payload = {'sub': mock_auth0_id}
        #     g.auth0_token = 'dev-token'
            
        #     return f(*args, **kwargs)
        
        try:
            # Get and verify token
            token = get_token_auth_header()
            print("Auth0 Token:", token)
            payload = verify_decode_jwt(token)
            print("Auth0 Payload:", payload)

            # Extract user ID from token
            auth0_user_id = payload.get('sub')
            print("Auth0 User ID:", auth0_user_id)
            if not auth0_user_id:
                raise AuthError({
                    'code': 'invalid_token',
                    'description': 'User ID not found in token.'
                }, 401)
            
            # Sync user with database
            user = sync_user_with_database(auth0_user_id)
            print(f"✅ Synchronized user {auth0_user_id} with database")
            
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
    return getattr(g, 'current_user', None)

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
