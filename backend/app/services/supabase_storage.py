import os
from typing import Optional
from datetime import datetime, timedelta
from supabase import create_client, Client
from loguru import logger


class SupabaseStorage:
    """
    Supabase Storage service for generating signed URLs
    """
    
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_ANON_KEY")
        self.bucket_name = os.getenv("SUPABASE_BUCKET", "assets")
        
        if not self.url or not self.key:
            logger.warning("Supabase credentials not configured, using mock URLs")
            self.client = None
        else:
            self.client: Client = create_client(self.url, self.key)
    
    def get_signed_url(self, image_key: str, expires_in: int = 3600) -> Optional[str]:
        """
        Generate signed URL for image_key
        
        Args:
            image_key: The image key (e.g., "acme_picture")
            expires_in: URL expiration time in seconds (default: 1 hour)
        
        Returns:
            Signed URL or None if not found
        """
        if not self.client:
            # Mock URL for development
            return f"https://via.placeholder.com/200x200?text={image_key}"
        
        try:
            # Try different file extensions
            extensions = ['.png', '.jpg', '.jpeg', '.webp']
            
            for ext in extensions:
                file_path = f"images/{image_key}{ext}"
                
                try:
                    # Check if file exists and get signed URL
                    response = self.client.storage.from_(self.bucket_name).create_signed_url(
                        file_path, 
                        expires_in
                    )
                    
                    if response and 'signedURL' in response:
                        logger.debug(f"Generated signed URL for {file_path}")
                        return response['signedURL']
                        
                except Exception as e:
                    logger.debug(f"File not found: {file_path} - {e}")
                    continue
            
            logger.warning(f"No image found for key: {image_key}")
            return None
            
        except Exception as e:
            logger.error(f"Error generating signed URL for {image_key}: {e}")
            return None
    
    def list_images(self, prefix: str = "images/") -> list[str]:
        """List all images in the bucket"""
        if not self.client:
            return []
        
        try:
            response = self.client.storage.from_(self.bucket_name).list(prefix)
            return [item['name'] for item in response if item.get('name')]
        except Exception as e:
            logger.error(f"Error listing images: {e}")
            return []


# Global instance
supabase_storage = SupabaseStorage()
