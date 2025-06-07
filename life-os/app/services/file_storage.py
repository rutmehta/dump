import os
import logging
import aiofiles
import httpx
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
import hashlib
import mimetypes
from pathlib import Path
from PIL import Image
import uuid
from ..config import settings

logger = logging.getLogger(__name__)

class FileStorageService:
    def __init__(self):
        self.storage_path = Path(settings.MEDIA_STORAGE_PATH)
        self.max_file_size = settings.MAX_FILE_SIZE
        self._ensure_storage_directories()
    
    def _ensure_storage_directories(self):
        """Create storage directories if they don't exist"""
        try:
            # Create main media directory
            self.storage_path.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories for different media types
            for media_type in ['images', 'audio', 'documents', 'temp']:
                (self.storage_path / media_type).mkdir(exist_ok=True)
            
            logger.info(f"Storage directories initialized at {self.storage_path}")
            
        except Exception as e:
            logger.error(f"Failed to create storage directories: {e}")
            raise
    
    async def download_media(self, 
                           media_url: str,
                           user_id: str,
                           message_id: Optional[str] = None) -> Tuple[Optional[str], str, Dict[str, Any]]:
        """Download media from Twilio and store locally"""
        
        try:
            if not media_url:
                return None, "text", {}
            
            # Generate unique filename
            file_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            
            # Download the file
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(media_url)
                response.raise_for_status()
                
                # Check file size
                content_length = len(response.content)
                if content_length > self.max_file_size:
                    logger.warning(f"File too large: {content_length} bytes")
                    return None, "text", {"error": "File too large"}
                
                # Detect content type
                content_type = response.headers.get('content-type', 'application/octet-stream')
                media_type, file_extension = self._detect_media_type(content_type, response.content)
                
                # Determine storage subdirectory
                subdir = self._get_storage_subdir(media_type)
                
                # Create filename
                filename = f"{user_id}_{timestamp}_{file_id}.{file_extension}"
                file_path = self.storage_path / subdir / filename
                
                # Save file
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(response.content)
                
                # Generate file metadata
                metadata = {
                    "original_url": media_url,
                    "filename": filename,
                    "file_size": content_length,
                    "content_type": content_type,
                    "media_type": media_type,
                    "user_id": user_id,
                    "message_id": message_id,
                    "upload_time": datetime.utcnow().isoformat(),
                    "file_hash": self._calculate_file_hash(response.content)
                }
                
                # Additional processing based on media type
                if media_type == "image":
                    image_metadata = await self._process_image(file_path)
                    metadata.update(image_metadata)
                elif media_type == "audio":
                    audio_metadata = await self._process_audio(file_path)
                    metadata.update(audio_metadata)
                
                logger.info(f"Downloaded media: {filename} ({content_length} bytes)")
                return str(file_path), media_type, metadata
                
        except httpx.RequestError as e:
            logger.error(f"Failed to download media from {media_url}: {e}")
            return None, "text", {"error": f"Download failed: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error downloading media: {e}")
            return None, "text", {"error": f"Processing failed: {str(e)}"}
    
    def _detect_media_type(self, content_type: str, content: bytes) -> Tuple[str, str]:
        """Detect media type and appropriate file extension"""
        
        # Map content types to media types and extensions
        type_mapping = {
            # Images
            'image/jpeg': ('image', 'jpg'),
            'image/jpg': ('image', 'jpg'),
            'image/png': ('image', 'png'),
            'image/gif': ('image', 'gif'),
            'image/webp': ('image', 'webp'),
            'image/bmp': ('image', 'bmp'),
            
            # Audio
            'audio/mpeg': ('audio', 'mp3'),
            'audio/mp3': ('audio', 'mp3'),
            'audio/ogg': ('audio', 'ogg'),
            'audio/wav': ('audio', 'wav'),
            'audio/amr': ('audio', 'amr'),
            'audio/aac': ('audio', 'aac'),
            'audio/m4a': ('audio', 'm4a'),
            
            # Documents
            'application/pdf': ('document', 'pdf'),
            'text/plain': ('document', 'txt'),
            'application/msword': ('document', 'doc'),
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ('document', 'docx'),
            'application/vnd.ms-excel': ('document', 'xls'),
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ('document', 'xlsx'),
            
            # Video (treated as documents for now)
            'video/mp4': ('document', 'mp4'),
            'video/quicktime': ('document', 'mov'),
            'video/avi': ('document', 'avi'),
        }
        
        # Try content type mapping first
        if content_type in type_mapping:
            return type_mapping[content_type]
        
        # Fallback: detect from file signature (magic bytes)
        media_type, extension = self._detect_by_signature(content)
        if media_type:
            return media_type, extension
        
        # Default fallback
        return "document", "bin"
    
    def _detect_by_signature(self, content: bytes) -> Tuple[Optional[str], str]:
        """Detect file type by magic bytes"""
        
        if len(content) < 8:
            return None, "bin"
        
        signatures = {
            # Images
            b'\xFF\xD8\xFF': ('image', 'jpg'),
            b'\x89PNG\r\n\x1a\n': ('image', 'png'),
            b'GIF87a': ('image', 'gif'),
            b'GIF89a': ('image', 'gif'),
            b'RIFF': ('image', 'webp'),  # Could also be audio/video
            
            # Audio
            b'ID3': ('audio', 'mp3'),
            b'\xFF\xFB': ('audio', 'mp3'),
            b'OggS': ('audio', 'ogg'),
            b'RIFF': ('audio', 'wav'),  # Ambiguous with webp
            b'#!AMR': ('audio', 'amr'),
            
            # Documents
            b'%PDF': ('document', 'pdf'),
            b'\xD0\xCF\x11\xE0': ('document', 'doc'),  # MS Office
            b'PK\x03\x04': ('document', 'docx'),  # ZIP-based (Office, etc.)
        }
        
        for signature, (media_type, ext) in signatures.items():
            if content.startswith(signature):
                return media_type, ext
        
        return None, "bin"
    
    def _get_storage_subdir(self, media_type: str) -> str:
        """Get storage subdirectory based on media type"""
        subdirs = {
            'image': 'images',
            'audio': 'audio', 
            'document': 'documents'
        }
        return subdirs.get(media_type, 'documents')
    
    def _calculate_file_hash(self, content: bytes) -> str:
        """Calculate SHA-256 hash of file content"""
        return hashlib.sha256(content).hexdigest()
    
    async def _process_image(self, file_path: Path) -> Dict[str, Any]:
        """Process image file and extract metadata"""
        try:
            with Image.open(file_path) as img:
                metadata = {
                    "image_width": img.width,
                    "image_height": img.height,
                    "image_mode": img.mode,
                    "image_format": img.format
                }
                
                # Extract EXIF data if available
                if hasattr(img, '_getexif') and img._getexif():
                    exif_data = img._getexif()
                    # Extract basic EXIF info (timestamp, GPS, etc.)
                    if exif_data:
                        metadata["has_exif"] = True
                        # Add specific EXIF fields as needed
                else:
                    metadata["has_exif"] = False
                
                return metadata
                
        except Exception as e:
            logger.error(f"Failed to process image {file_path}: {e}")
            return {"image_processing_error": str(e)}
    
    async def _process_audio(self, file_path: Path) -> Dict[str, Any]:
        """Process audio file and extract metadata"""
        try:
            # Basic audio file info
            metadata = {
                "audio_file": True,
                "file_size_mb": file_path.stat().st_size / (1024 * 1024)
            }
            
            # Could use libraries like mutagen for detailed audio metadata
            # For now, just basic file info
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to process audio {file_path}: {e}")
            return {"audio_processing_error": str(e)}
    
    async def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get information about a stored file"""
        try:
            path = Path(file_path)
            if not path.exists():
                return None
            
            stat = path.stat()
            content_type, _ = mimetypes.guess_type(str(path))
            
            return {
                "filename": path.name,
                "file_size": stat.st_size,
                "content_type": content_type,
                "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "exists": True
            }
            
        except Exception as e:
            logger.error(f"Failed to get file info for {file_path}: {e}")
            return None
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete a stored file"""
        try:
            path = Path(file_path)
            if path.exists() and path.is_file():
                path.unlink()
                logger.info(f"Deleted file: {file_path}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False
    
    async def cleanup_temp_files(self, older_than_hours: int = 24):
        """Clean up temporary files older than specified hours"""
        try:
            temp_dir = self.storage_path / 'temp'
            if not temp_dir.exists():
                return
            
            cutoff_time = datetime.utcnow().timestamp() - (older_than_hours * 3600)
            deleted_count = 0
            
            for file_path in temp_dir.iterdir():
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                    except Exception as e:
                        logger.error(f"Failed to delete temp file {file_path}: {e}")
            
            logger.info(f"Cleaned up {deleted_count} temporary files")
            
        except Exception as e:
            logger.error(f"Temp file cleanup failed: {e}")
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage usage statistics"""
        try:
            stats = {
                "total_files": 0,
                "total_size_mb": 0,
                "by_type": {}
            }
            
            for subdir in ['images', 'audio', 'documents', 'temp']:
                subdir_path = self.storage_path / subdir
                if not subdir_path.exists():
                    continue
                
                file_count = 0
                total_size = 0
                
                for file_path in subdir_path.iterdir():
                    if file_path.is_file():
                        file_count += 1
                        total_size += file_path.stat().st_size
                
                stats["by_type"][subdir] = {
                    "file_count": file_count,
                    "size_mb": total_size / (1024 * 1024)
                }
                
                stats["total_files"] += file_count
                stats["total_size_mb"] += total_size / (1024 * 1024)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {}
    
    def get_file_url(self, file_path: str) -> str:
        """Generate a URL for accessing a stored file (if web server is configured)"""
        # This would depend on your web server configuration
        # For now, return the local file path
        return f"file://{file_path}" 