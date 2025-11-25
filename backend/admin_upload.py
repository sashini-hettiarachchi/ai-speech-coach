#!/usr/bin/env python3
"""
Admin Speech Upload Script
A simple script to upload speech audio for any user via the admin endpoint.

Usage:
    python admin_upload.py --user-id 1 --speech-id 5 --file /path/to/audio.wav
    python admin_upload.py --user-id 1 --speech-id 5 --file /path/to/audio.wav --title "Practice 1"
"""

import argparse
import requests
import os
import sys
from pathlib import Path


def upload_speech(file_path: str, user_id: int, speech_id: int, 
                  session_title: str = None, backend_url: str = "http://localhost:5000"):
    """
    Upload speech audio file for a specific user and speech via admin endpoint.
    
    Args:
        file_path: Path to the audio file
        user_id: Database ID of the user
        speech_id: Database ID of the speech
        session_title: Optional title for the session
        backend_url: Backend server URL (default: http://localhost:5000)
    
    Returns:
        dict: Response from the server
    """
    # Validate file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found: {file_path}")
    
    # Get file size
    file_size = os.path.getsize(file_path)
    file_size_mb = file_size / (1024 * 1024)
    
    print(f"📁 File: {Path(file_path).name}")
    print(f"📏 Size: {file_size_mb:.2f} MB")
    print(f"👤 User ID: {user_id}")
    print(f"📢 Speech ID: {speech_id}")
    if session_title:
        print(f"📝 Session Title: {session_title}")
    print(f"🌐 Backend: {backend_url}")
    print()
    
    # Prepare the request
    endpoint = f"{backend_url}/api/v1/admin/analyze"
    
    # Prepare form data
    files = {
        'file': open(file_path, 'rb')
    }
    
    data = {
        'user_id': str(user_id),
        'speech_id': str(speech_id)
    }
    
    if session_title:
        data['session_title'] = session_title
    
    print("🚀 Uploading and analyzing speech...")
    print("⏳ This may take a few minutes depending on file size...")
    print()
    
    try:
        # Make the request
        response = requests.post(endpoint, files=files, data=data, timeout=600)
        
        # Close the file
        files['file'].close()
        
        # Check response
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS!")
            print()
            print(f"Session ID: {result.get('session_id')}")
            print(f"Timestamp: {result.get('timestamp')}")
            print()
            print("The speech has been uploaded and analyzed successfully.")
            print(f"You can view the session via the API or frontend using session ID: {result.get('session_id')}")
            return result
        else:
            print(f"❌ ERROR: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error message: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out. The file might be too large or the server is slow.")
        print("Try again with a smaller file or increase the timeout.")
        return None
    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to backend at {backend_url}")
        print("Make sure the backend server is running.")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description='Upload speech audio for any user via admin endpoint',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python admin_upload.py --user-id 1 --speech-id 5 --file my_speech.wav
  python admin_upload.py -u 1 -s 5 -f my_speech.wav -t "Practice Session 1"
  python admin_upload.py -u 1 -s 5 -f my_speech.wav --url https://api.example.com
        """
    )
    
    parser.add_argument('-u', '--user-id', type=int, required=True,
                        help='Database ID of the user')
    parser.add_argument('-s', '--speech-id', type=int, required=True,
                        help='Database ID of the speech')
    parser.add_argument('-f', '--file', type=str, required=True,
                        help='Path to the audio file')
    parser.add_argument('-t', '--title', type=str, default=None,
                        help='Session title (optional)')
    parser.add_argument('--url', type=str, default='http://localhost:5000',
                        help='Backend URL (default: http://localhost:5000)')
    
    args = parser.parse_args()
    
    # Upload the speech
    result = upload_speech(
        file_path=args.file,
        user_id=args.user_id,
        speech_id=args.speech_id,
        session_title=args.title,
        backend_url=args.url
    )
    
    # Exit with appropriate code
    sys.exit(0 if result else 1)


if __name__ == '__main__':
    main()
