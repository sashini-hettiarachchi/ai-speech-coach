"""
Google Cloud Storage utilities for handling file uploads and management.
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple
from google.cloud import storage
import mimetypes

from config import GCS_BUCKET_NAME, GCS_CREDENTIALS_PATH, GCS_PUBLIC_URL_BASE


class GCSManager:
    """Manager class for Google Cloud Storage operations"""
    
    def __init__(self):
        """Initialize GCS client with credentials"""
        try:
            # Initialize the storage client
            if os.path.exists(GCS_CREDENTIALS_PATH):
                self.client = storage.Client.from_service_account_json(GCS_CREDENTIALS_PATH)
            else:
                # Fallback to default credentials (useful for production environments)
                self.client = storage.Client()
            
            self.bucket_name = GCS_BUCKET_NAME
            self.bucket = self.client.bucket(self.bucket_name)
            
        except Exception as e:
            print(f"❌ Failed to initialize GCS client: {str(e)}")
            raise
    
    def upload_file(self, file_path: str, original_filename: str, 
                   folder: str = "speech-uploads") -> Tuple[str, str]:
        """
        Upload a file to Google Cloud Storage
        
        Args:
            file_path: Path to the local file to upload
            original_filename: Original name of the file
            folder: Folder/prefix in the GCS bucket
            
        Returns:
            Tuple of (blob_name, signed_url)
        """
        try:
            # Generate a unique filename to avoid conflicts
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            file_extension = os.path.splitext(original_filename)[1]
            
            # Create blob name with folder structure
            blob_name = f"{folder}/{timestamp}_{unique_id}_{original_filename}"
            
            # Create blob object
            blob = self.bucket.blob(blob_name)
            
            # Determine content type
            content_type, _ = mimetypes.guess_type(original_filename)
            if not content_type:
                # Default content types for common audio/video files
                if file_extension.lower() in ['.mp3', '.wav', '.m4a', '.aac']:
                    content_type = f'audio/{file_extension[1:]}'
                elif file_extension.lower() in ['.mp4', '.webm', '.avi', '.mov']:
                    content_type = f'video/{file_extension[1:]}'
                else:
                    content_type = 'application/octet-stream'
            
            # Upload file with metadata
            blob.metadata = {
                'original_filename': original_filename,
                'upload_timestamp': datetime.now().isoformat(),
                'file_type': 'speech_recording'
            }
            
            # Upload the file
            with open(file_path, 'rb') as file_obj:
                blob.upload_from_file(file_obj, content_type=content_type)
            
            # Generate a signed URL instead of making the blob public
            # This creates a temporary URL that works for 6 days (to stay within GCS limits)
            signed_url = blob.generate_signed_url(
                version="v4",
                expiration=datetime.now() + timedelta(days=6),
                method="GET"
            )
            
            print(f"✅ File uploaded to GCS: {blob_name}")
            return blob_name, signed_url
            
        except Exception as e:
            print(f"❌ GCS upload error: {str(e)}")
            raise
    
    def delete_file(self, blob_name: str) -> bool:
        """
        Delete a file from Google Cloud Storage
        
        Args:
            blob_name: Name of the blob to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            blob = self.bucket.blob(blob_name)
            blob.delete()
            print(f"✅ File deleted from GCS: {blob_name}")
            return True
        except Exception as e:
            print(f"❌ GCS delete error: {str(e)}")
            return False
    
    def generate_signed_url(self, blob_name: str, expiration_hours: int = 24) -> Optional[str]:
        """
        Generate a signed URL for temporary access to a private file
        
        Args:
            blob_name: Name of the blob
            expiration_hours: Hours until the URL expires
            
        Returns:
            Signed URL string or None if error
        """
        try:
            blob = self.bucket.blob(blob_name)
            
            # Generate signed URL that expires in specified hours
            url = blob.generate_signed_url(
                version="v4",
                expiration=datetime.now() + timedelta(hours=expiration_hours),
                method="GET"
            )
            
            return url
        except Exception as e:
            print(f"❌ Error generating signed URL: {str(e)}")
            return None
    
    def get_file_info(self, blob_name: str) -> Optional[dict]:
        """
        Get information about a file in GCS
        
        Args:
            blob_name: Name of the blob
            
        Returns:
            Dictionary with file information or None if not found
        """
        try:
            blob = self.bucket.blob(blob_name)
            blob.reload()  # Fetch current metadata
            
            return {
                'name': blob.name,
                'size': blob.size,
                'content_type': blob.content_type,
                'created': blob.time_created.isoformat() if blob.time_created else None,
                'updated': blob.updated.isoformat() if blob.updated else None,
                'metadata': blob.metadata or {},
                'public_url': blob.public_url if blob.public_url_set else None
            }
        except Exception as e:
            print(f"❌ Error getting file info: {str(e)}")
            return None


# Global instance for easy access
gcs_manager = GCSManager()


def upload_speech_file(file_path: str, original_filename: str) -> Tuple[str, str]:
    """
    Convenience function to upload a speech file
    
    Args:
        file_path: Path to the local file
        original_filename: Original filename
        
    Returns:
        Tuple of (blob_name, signed_url)
    """
    return gcs_manager.upload_file(file_path, original_filename, "speech-recordings")


def delete_speech_file(blob_name: str) -> bool:
    """
    Convenience function to delete a speech file
    
    Args:
        blob_name: GCS blob name to delete
        
    Returns:
        True if successful
    """
    return gcs_manager.delete_file(blob_name)


def get_signed_url(blob_name: str, hours: int = 24) -> Optional[str]:
    """
    Convenience function to get a signed URL for a speech file
    
    Args:
        blob_name: GCS blob name
        hours: Hours until expiration
        
    Returns:
        Signed URL or None
    """
    return gcs_manager.generate_signed_url(blob_name, hours)


def refresh_media_url(blob_name: str, hours: int = 144) -> Optional[str]:
    """
    Generate a fresh signed URL for a media file (6 days default)
    
    Args:
        blob_name: GCS blob name from session data
        hours: Hours until expiration (default 6 days = 144 hours)
        
    Returns:
        New signed URL or None if error
    """
    return gcs_manager.generate_signed_url(blob_name, hours)