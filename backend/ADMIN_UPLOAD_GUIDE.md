# Admin Speech Upload Guide

This guide shows how to upload speech audio for any user using the admin endpoint.

## Overview

The `/api/v1/admin/analyze` endpoint allows you to upload and analyze speech audio for any user without requiring authentication. This is useful for:
- Admin operations
- Batch uploads
- Testing
- Data migration

## Prerequisites

You need the following information:
1. **user_id**: The database ID of the user (from the `users` table)
2. **speech_id**: The database ID of the speech (from the `speeches` table)
3. **audio_file**: Path to the audio file to upload
4. **session_title** (optional): A title for this practice session

## Finding User ID and Speech ID

### Option 1: Query the Database
```sql
-- Find user by Auth0 ID
SELECT id, auth0_user_id FROM users WHERE auth0_user_id = 'auth0|xxxxx';

-- Find speeches for a user
SELECT id, title, context, goal FROM speeches WHERE user_id = 1;
```

### Option 2: Use the API (requires Auth0 token)
```bash
# Get current user info
curl -X GET http://localhost:5000/api/v1/auth/user \
  -H "Authorization: Bearer YOUR_AUTH0_TOKEN"

# Get speeches for authenticated user
curl -X GET http://localhost:5000/api/v1/speeches \
  -H "Authorization: Bearer YOUR_AUTH0_TOKEN"
```

## cURL Command Template

### Basic Upload
```bash
curl -X POST http://localhost:5000/api/v1/admin/analyze \
  -F "file=@/path/to/audio.wav" \
  -F "user_id=1" \
  -F "speech_id=5"
```

### Upload with Session Title
```bash
curl -X POST http://localhost:5000/api/v1/admin/analyze \
  -F "file=@/path/to/audio.wav" \
  -F "user_id=1" \
  -F "speech_id=5" \
  -F "session_title=Practice Session 1"
```

### Full Example with All Details
```bash
curl -X POST http://localhost:5000/api/v1/admin/analyze \
  -F "file=@/Users/sashini/Documents/audio_recordings/speech1.wav" \
  -F "user_id=1" \
  -F "speech_id=5" \
  -F "session_title=First Practice Attempt" \
  -v
```

## Production URL

If your backend is deployed, replace `http://localhost:5000` with your production URL:

```bash
curl -X POST https://your-backend-url.com/api/v1/admin/analyze \
  -F "file=@/path/to/audio.wav" \
  -F "user_id=1" \
  -F "speech_id=5"
```

## Response Format

### Success Response
```json
{
  "status": "success",
  "timestamp": "2025-11-25T10:30:00.123456",
  "user_id": "1",
  "speech_id": "5",
  "session_id": 42
}
```

### Error Responses

**Missing file:**
```json
{
  "error": "No file provided"
}
```

**User not found:**
```json
{
  "error": "User with id 1 not found"
}
```

**Speech not found or doesn't belong to user:**
```json
{
  "error": "Speech with id 5 not found for user 1"
}
```

## Step-by-Step Example

Let's say you have:
- User ID: `3`
- Speech ID: `7`
- Audio file: `/Users/sashini/Documents/recordings/my_speech.wav`

### 1. Verify the file exists
```bash
ls -lh /Users/sashini/Documents/recordings/my_speech.wav
```

### 2. Upload the audio
```bash
curl -X POST http://localhost:5000/api/v1/admin/analyze \
  -F "file=@/Users/sashini/Documents/recordings/my_speech.wav" \
  -F "user_id=3" \
  -F "speech_id=7" \
  -F "session_title=Admin Upload - Nov 25" \
  -v
```

### 3. Check the response
If successful, you'll receive a JSON response with the `session_id`. You can then view this session via:
```bash
curl -X GET http://localhost:5000/api/v1/sessions/{session_id} \
  -H "Authorization: Bearer USER_AUTH0_TOKEN"
```

## Supported Audio Formats

The system supports:
- WAV (.wav)
- MP3 (.mp3)
- M4A (.m4a)
- MP4 (.mp4) - audio extraction
- WebM (.webm) - audio extraction

## Processing Details

When you upload via the admin endpoint, the system will:
1. ✅ Transcribe the audio using Whisper
2. ✅ Analyze prosody (pitch, volume, speed, pauses)
3. ✅ Detect filler words
4. ✅ Evaluate all 7 CSSEF competencies (C1-C7)
5. ✅ Calculate overall score
6. ✅ Generate AI feedback summary
7. ✅ Create revised speech text and audio
8. ✅ Save everything to the database
9. ✅ Upload media files to Google Cloud Storage

## Security Notes

⚠️ **IMPORTANT**: This endpoint does NOT require authentication. In a production environment, you should:
1. Add authentication (API key, admin token, etc.)
2. Implement IP whitelisting
3. Add rate limiting
4. Monitor usage logs

## Troubleshooting

### "Speech not found for user"
- Verify the speech belongs to the specified user
- Check that both user_id and speech_id are correct

### "File upload failed"
- Ensure Google Cloud Storage credentials are configured
- Check GCS bucket permissions
- Verify `key.json` exists in the backend directory

### "No file provided"
- Make sure you're using `-F "file=@/path/to/file.wav"` (note the `@` symbol)
- Verify the file path is correct and absolute

### Large files timeout
- For files > 50MB, consider increasing timeout:
```bash
curl -X POST http://localhost:5000/api/v1/admin/analyze \
  -F "file=@/path/to/large_audio.wav" \
  -F "user_id=1" \
  -F "speech_id=5" \
  --max-time 600
```

## Alternative: Using Postman

1. Open Postman
2. Create a new POST request to `http://localhost:5000/api/v1/admin/analyze`
3. Go to Body tab → form-data
4. Add these fields:
   - `file` (type: File) → Select your audio file
   - `user_id` (type: Text) → Enter user ID
   - `speech_id` (type: Text) → Enter speech ID
   - `session_title` (type: Text, optional) → Enter session title
5. Click Send

## Batch Upload Script

For uploading multiple files, create a bash script:

```bash
#!/bin/bash

USER_ID=1
SPEECH_ID=5
AUDIO_DIR="/path/to/audio/files"

for audio_file in "$AUDIO_DIR"/*.wav; do
  filename=$(basename "$audio_file")
  echo "Uploading $filename..."
  
  curl -X POST http://localhost:5000/api/v1/admin/analyze \
    -F "file=@$audio_file" \
    -F "user_id=$USER_ID" \
    -F "speech_id=$SPEECH_ID" \
    -F "session_title=Auto Upload - $filename"
  
  echo "Completed $filename"
  echo "---"
done
```

Save as `batch_upload.sh`, make executable with `chmod +x batch_upload.sh`, then run `./batch_upload.sh`.
