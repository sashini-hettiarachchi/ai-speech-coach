# Google Cloud Storage Integration

This document describes the Google Cloud Storage (GCS) integration added to the Speech Coach application for storing uploaded audio/video files.

## Overview

The application now stores 4. **Frontend Playback Issues**:
   - Verify GCS CORS is configured
   - Check browser console for errors
   - Test direct URL access
   - Check if signed URL has expired (6 days)
   - Use the "Refresh Link" button in the media player

5. **Expired Signed URLs**:
   - Signed URLs expire after 6 days
   - Frontend automatically detects media load errors
   - Users can click "Refresh Link" to get a new URL
   - Backend `/refresh-media-url` endpoint generates new URLs

6. **GCS Expiration Limit Error**:
   ```
   Max allowed expiration interval is seven days 604800
   ```
   **Solution**: This occurs when trying to set signed URL expiration to exactly 7 days or more. Current implementation uses 6 days (144 hours) to stay within limits.

7. **Database String Length Error**:
   ```
   value too long for type character varying(500)
   ```
   **Solution**: GCS signed URLs can be very long. Run the database migration to increase the `media_url` field length:
   ```sql
   ALTER TABLE sessions ALTER COLUMN media_url TYPE VARCHAR(2000);
   ```ded speech recording files in Google Cloud Storage instead of local file system, providing:
- **Scalability**: No local storage limitations
- **Durability**: Built-in redundancy and backup
- **Accessibility**: Files accessible from anywhere via public URLs
- **Security**: Configurable access controls
- **Cost-effectiveness**: Pay only for what you use

## Setup Instructions

### 1. Google Cloud Project Setup

1. **Create a Google Cloud Project** (if you don't have one):
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one

2. **Enable Cloud Storage API**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Cloud Storage API"
   - Click "Enable"

3. **Create a Storage Bucket**:
   - Go to "Cloud Storage" > "Buckets"
   - Click "Create Bucket"
   - Choose a unique name (e.g., `speech-coach-files-your-suffix`)
   - Select location (recommend same region as your server)
   - Choose "Standard" storage class
   - Set access control to "Fine-grained"

### 2. Service Account Setup

1. **Create Service Account**:
   - Go to "IAM & Admin" > "Service Accounts"
   - Click "Create Service Account"
   - Name: `speech-coach-storage`
   - Description: `Service account for Speech Coach file uploads`

2. **Assign Permissions**:
   - Add role: "Storage Object Admin" (for the specific bucket)
   - Or "Storage Admin" (for broader access)

3. **Generate Key**:
   - Click on the service account
   - Go to "Keys" tab
   - Click "Add Key" > "Create new key"
   - Choose JSON format
   - Download the file and save as `key.json` in your backend directory

### 3. Backend Configuration

1. **Install Dependencies**:
   ```bash
   cd backend
   pip install google-cloud-storage
   ```

2. **Environment Configuration**:
   Update your `.env` file:
   ```bash
   # Google Cloud Storage Configuration
   GCS_BUCKET_NAME=your-bucket-name
   GCS_CREDENTIALS_PATH=key.json
   
   # Optional: Custom public URL base
   # GCS_PUBLIC_URL_BASE=https://storage.googleapis.com/your-bucket-name
   ```

3. **Security Note**:
   - Never commit `key.json` to version control
   - Add `key.json` to your `.gitignore` file
   - For production, consider using workload identity or instance service accounts

## How It Works

### File Upload Process

1. **Client uploads file** → Backend receives file
2. **Temporary storage** → File saved temporarily in local `uploads/` folder
3. **GCS upload** → File uploaded to Google Cloud Storage with unique name
4. **Generate signed URL** → Create temporary access URL (6 days expiration)
5. **Database storage** → Signed URL saved to database
6. **Cleanup** → Temporary local file deleted
7. **Client receives** → Signed URL returned in API response

### File Naming Convention

Files are stored with the following naming pattern:
```
speech-recordings/YYYYMMDD_HHMMSS_[8-char-uuid]_[original-filename]
```

Example: `speech-recordings/20241027_143022_a1b2c3d4_my-speech.mp3`

### File Access

- **Signed URLs**: Files are accessible via temporary signed URLs (6 days expiration)
- **Frontend Display**: Audio/video players use signed URLs directly
- **Download**: Users can download original files using the signed URLs
- **URL Refresh**: When URLs expire, frontend can request new signed URLs

## Code Components

### Backend Components

1. **`utils/gcs_storage.py`**: Core GCS functionality
   - `GCSManager`: Main class for GCS operations
   - `upload_speech_file()`: Convenience function for uploads
   - `delete_speech_file()`: File deletion
   - `get_signed_url()`: Generate temporary signed URLs (if needed)

2. **Updated `app.py`**:
   - Modified `analyze_speech` endpoint to use GCS
   - Updated session deletion to remove GCS files
   - Error handling for GCS operations

3. **Database Model**:
   - `Session.media_url`: Now stores GCS signed URL (increased to 2000 characters)
   - `Session.full_analysis_results`: Includes GCS blob name for file management

### Database Schema Changes

**Important**: GCS signed URLs can be very long (often 1000+ characters). The database schema has been updated:

```sql
-- Increase media_url column length for GCS signed URLs
ALTER TABLE sessions ALTER COLUMN media_url TYPE VARCHAR(2000);
```

If you encounter database errors about string length, run the migration:
```bash
# Apply the database migration
flask db upgrade

# Or run the SQL directly in PostgreSQL
psql -d your_database -f fix_media_url_length.sql
```

### API Endpoints

1. **POST `/api/v1/analyze`**: Upload and analyze speech files
   - Uploads file to GCS
   - Returns session data with signed URL

2. **POST `/api/v1/sessions/{id}/refresh-media-url`**: Refresh expired signed URL
   - Generates new 6-day signed URL
   - Updates session with new URL
   - Returns new URL to frontend

3. **DELETE `/api/v1/sessions/{id}`**: Delete session and associated GCS file
   - Removes file from GCS bucket
   - Deletes session from database

### Frontend Components

1. **`components/MediaPlayer.tsx`**: Enhanced media player component
   - Supports both audio and video playback
   - Download functionality
   - Fallback options for compatibility issues

2. **Updated Session Detail Page**:
   - Uses new MediaPlayer component
   - Updated TypeScript interfaces
   - Better error handling

## Security Considerations

### Current Configuration
- Files are stored in **private buckets** with Public Access Prevention enabled
- Access is provided through **signed URLs** with 6-day expiration
- No permanent public access to files
- URLs automatically expire for enhanced security

### Signed URLs vs Public URLs

This implementation uses **signed URLs** instead of public URLs for enhanced security:

**Signed URLs:**
- ✅ Temporary access (6 days by default)
- ✅ No permanent public access
- ✅ Compatible with Public Access Prevention
- ✅ Can be refreshed when expired
- ❌ URLs expire and need refreshing

**Public URLs (not used):**
- ❌ Permanent public access
- ❌ Incompatible with Public Access Prevention
- ❌ Less secure
- ✅ Never expire

### Enhanced Security Options

For production deployments, consider:

1. **Private Buckets with Signed URLs**:
   ```python
   # Generate temporary signed URLs instead of public URLs
   signed_url = gcs_manager.generate_signed_url(blob_name, hours=24)
   ```

2. **CORS Configuration**:
   ```bash
   gsutil cors set cors-config.json gs://your-bucket-name
   ```

3. **Lifecycle Policies**:
   ```json
   {
     "rule": [{
       "action": {"type": "Delete"},
       "condition": {"age": 90}
     }]
   }
   ```

## Troubleshooting

### Common Issues

1. **Public Access Prevention Error**:
   ```
   412 PATCH https://storage.googleapis.com/.../: The member bindings allUsers and allAuthenticatedUsers are not allowed since public access prevention is enforced.
   ```
   
   **Solution**: This error occurs when trying to make files public in a bucket with Public Access Prevention enabled. The current implementation uses signed URLs instead of public access, which resolves this issue.

2. **Authentication Errors**:
   - Verify `key.json` file exists and is valid
   - Check service account has proper permissions
   - Ensure bucket name is correct

3. **Upload Failures**:
   - Check bucket exists and is accessible
   - Verify internet connectivity
   - Check file size limits

4. **Frontend Playback Issues**:
   - Verify GCS CORS is configured
   - Check browser console for errors
   - Test direct URL access
   - Check if signed URL has expired (7 days)

### Debug Commands

```bash
# Test GCS connection
python -c "from utils.gcs_storage import gcs_manager; print(gcs_manager.bucket_name)"

# List bucket contents
gsutil ls gs://your-bucket-name

# Check bucket permissions
gsutil iam get gs://your-bucket-name
```

## Cost Optimization

### Storage Costs
- **Standard Storage**: ~$0.020 per GB per month
- **Nearline Storage**: ~$0.010 per GB per month (for infrequent access)
- **Operations**: ~$0.005 per 1,000 operations

### Cost Optimization Tips
1. **Lifecycle Policies**: Automatically delete old files
2. **Storage Classes**: Use cheaper classes for older files
3. **Compression**: Compress audio files when possible
4. **Monitoring**: Set up billing alerts

## Monitoring and Maintenance

### Metrics to Monitor
- Storage usage
- Number of operations
- Data transfer costs
- Error rates

### Maintenance Tasks
- Regular cleanup of old files
- Monitor storage costs
- Update access policies as needed
- Backup critical configuration

## Migration from Local Storage

If migrating from local file storage:

1. **Backup existing files**
2. **Upload to GCS** using batch upload scripts
3. **Update database URLs** to point to GCS
4. **Test thoroughly** before removing local files
5. **Monitor** for any broken links

## Support

For issues with this integration:
1. Check the troubleshooting section above
2. Review Google Cloud Storage documentation
3. Check application logs for specific error messages
4. Verify environment configuration

---

**Note**: This integration requires a Google Cloud account and may incur storage costs. Please review Google Cloud Storage pricing before deploying to production.