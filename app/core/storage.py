"""
BhashaAI Backend - MinIO Storage Service

Handles file upload/download to MinIO S3-compatible storage.
"""

import logging
from typing import BinaryIO, Optional
from uuid import uuid4

from minio import Minio
from minio.error import S3Error

from app.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """
    MinIO storage service for file operations.
    
    Handles document uploads, downloads, and URL generation.
    
    Attributes:
        client: MinIO client instance
        bucket: Default bucket name
    """
    
    def __init__(self):
        """Initialize MinIO client."""
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        self.bucket = settings.minio_bucket
        self._ensure_bucket()
    
    def _ensure_bucket(self) -> None:
        """Create bucket if it doesn't exist."""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                logger.info(f"Created bucket: {self.bucket}")
        except S3Error as e:
            logger.error(f"Error ensuring bucket: {e}")
            raise
    
    def upload_file(
        self,
        file_data: BinaryIO,
        filename: str,
        content_type: str,
        folder: str = "documents",
    ) -> str:
        """
        Upload a file to MinIO.
        
        Args:
            file_data: File content as binary stream
            filename: Original filename
            content_type: MIME type
            folder: Storage folder/prefix
        
        Returns:
            str: Object name (path in bucket)
        
        Raises:
            S3Error: If upload fails
        """
        # Generate unique object name
        ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
        object_name = f"{folder}/{uuid4().hex}.{ext}" if ext else f"{folder}/{uuid4().hex}"
        
        try:
            # Get file size
            file_data.seek(0, 2)
            file_size = file_data.tell()
            file_data.seek(0)
            
            self.client.put_object(
                self.bucket,
                object_name,
                file_data,
                file_size,
                content_type=content_type,
            )
            logger.info(f"Uploaded file: {object_name}")
            return object_name
            
        except S3Error as e:
            logger.error(f"Upload failed: {e}")
            raise
    
    def download_file(self, object_name: str) -> bytes:
        """
        Download a file from MinIO.
        
        Args:
            object_name: Object path in bucket
        
        Returns:
            bytes: File content
        
        Raises:
            S3Error: If download fails
        """
        try:
            response = self.client.get_object(self.bucket, object_name)
            return response.read()
        except S3Error as e:
            logger.error(f"Download failed: {e}")
            raise
        finally:
            response.close()
            response.release_conn()
    
    def get_presigned_url(
        self,
        object_name: str,
        expires_hours: int = 1,
    ) -> str:
        """
        Generate a presigned URL for file access.
        
        Args:
            object_name: Object path in bucket
            expires_hours: URL validity in hours
        
        Returns:
            str: Presigned URL
        """
        from datetime import timedelta
        
        try:
            url = self.client.presigned_get_object(
                self.bucket,
                object_name,
                expires=timedelta(hours=expires_hours),
            )
            return url
        except S3Error as e:
            logger.error(f"Presigned URL generation failed: {e}")
            raise
    
    def delete_file(self, object_name: str) -> bool:
        """
        Delete a file from MinIO.
        
        Args:
            object_name: Object path in bucket
        
        Returns:
            bool: True if deleted successfully
        """
        try:
            self.client.remove_object(self.bucket, object_name)
            logger.info(f"Deleted file: {object_name}")
            return True
        except S3Error as e:
            logger.error(f"Delete failed: {e}")
            return False
    
    def file_exists(self, object_name: str) -> bool:
        """
        Check if file exists in MinIO.
        
        Args:
            object_name: Object path in bucket
        
        Returns:
            bool: True if file exists
        """
        try:
            self.client.stat_object(self.bucket, object_name)
            return True
        except S3Error:
            return False
    
    def get_file_url(self, object_name: str) -> str:
        """
        Get the full URL for a file.
        
        Args:
            object_name: Object path in bucket
        
        Returns:
            str: Full file URL
        """
        protocol = "https" if settings.minio_secure else "http"
        return f"{protocol}://{settings.minio_endpoint}/{self.bucket}/{object_name}"


# Singleton instance
_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """
    Get or create the storage service singleton.
    
    Returns:
        StorageService: Storage service instance
    """
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
