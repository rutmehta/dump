from fastapi import APIRouter, Request, Response, HTTPException, BackgroundTasks
from twilio.twiml.messaging_response import MessagingResponse
import logging
from typing import Dict, Any, Optional
import asyncio
from datetime import datetime

from ..services.ai_processor import AIProcessor
from ..services.memory_manager import MemoryManager
from ..services.file_storage import FileStorageService
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
ai_processor = AIProcessor()
memory_manager = MemoryManager()
file_storage = FileStorageService()

@router.post("/whatsapp")
async def handle_whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle incoming WhatsApp messages via Twilio webhook"""
    
    try:
        # Parse form data from Twilio
        form_data = await request.form()
        
        # Extract message details
        user_id = form_data.get("WaId", "")  # WhatsApp ID
        from_number = form_data.get("From", "")
        to_number = form_data.get("To", "")
        message_body = form_data.get("Body", "")
        message_sid = form_data.get("MessageSid", "")
        
        # Check for media
        num_media = int(form_data.get("NumMedia", "0"))
        media_url = form_data.get("MediaUrl0") if num_media > 0 else None
        media_content_type = form_data.get("MediaContentType0") if num_media > 0 else None
        
        logger.info(f"Received WhatsApp message from {user_id}: {message_body[:100]}...")
        
        # Determine message type
        if media_url:
            if media_content_type and media_content_type.startswith('image/'):
                message_type = "image"
            elif media_content_type and media_content_type.startswith('audio/'):
                message_type = "audio"
            else:
                message_type = "document"
        else:
            message_type = "text"
        
        # Process the message
        response_data = await process_whatsapp_message(
            user_id=user_id,
            message_body=message_body,
            media_url=media_url,
            message_type=message_type,
            message_sid=message_sid,
            background_tasks=background_tasks
        )
        
        # Generate Twilio response
        twiml_response = generate_twiml_response(response_data)
        
        return Response(content=str(twiml_response), media_type="text/xml")
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {e}")
        
        # Return error response
        resp = MessagingResponse()
        resp.message("I'm experiencing technical difficulties. Please try again later.")
        return Response(content=str(resp), media_type="text/xml")

async def process_whatsapp_message(
    user_id: str,
    message_body: str,
    media_url: Optional[str],
    message_type: str,
    message_sid: str,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Process a WhatsApp message and generate response"""
    
    try:
        # Download and process media if present
        file_path = None
        file_metadata = {}
        
        if media_url:
            file_path, detected_type, file_metadata = await file_storage.download_media(
                media_url=media_url,
                user_id=user_id,
                message_id=message_sid
            )
            
            if detected_type != "text":
                message_type = detected_type
        
        # Get proactive context from memory
        context_memories = await memory_manager.get_proactive_context(
            user_id=user_id,
            current_input=message_body,
            max_memories=15
        )
        
        # Process with AI
        ai_response = await ai_processor.process_input(
            text=message_body,
            media_path=file_path,
            media_type=message_type,
            user_id=user_id,
            context_memories=context_memories
        )
        
        # Store memory in background
        background_tasks.add_task(
            store_memory_async,
            content=message_body or f"[{message_type.upper()} MESSAGE]",
            content_type=message_type,
            user_id=user_id,
            media_url=media_url,
            ai_response=ai_response,
            file_metadata=file_metadata
        )
        
        # Prepare response
        response_text = ai_response.get("response", "I processed your message.")
        
        # Add insights if available
        insights = ai_response.get("insights", [])
        if insights:
            insight_text = "\n\n💡 " + "\n💡 ".join(insights[:2])  # Limit to 2 insights
            response_text += insight_text
        
        return {
            "text": response_text,
            "media_url": None,  # Could add generated media here
            "ai_response": ai_response,
            "processing_time": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing message for user {user_id}: {e}")
        return {
            "text": "I had trouble processing your message. Could you try rephrasing it?",
            "media_url": None,
            "error": str(e)
        }

async def store_memory_async(
    content: str,
    content_type: str,
    user_id: str,
    media_url: Optional[str],
    ai_response: Dict[str, Any],
    file_metadata: Dict[str, Any]
):
    """Store memory asynchronously in background"""
    try:
        # Combine AI response metadata with file metadata
        combined_metadata = {**ai_response.get("metadata", {}), **file_metadata}
        ai_response["metadata"] = combined_metadata
        
        memory_id = await memory_manager.store_memory(
            content=content,
            content_type=content_type,
            user_id=user_id,
            media_url=media_url,
            ai_response=ai_response
        )
        
        logger.info(f"Stored memory {memory_id} for user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to store memory in background: {e}")

def generate_twiml_response(response_data: Dict[str, Any]) -> MessagingResponse:
    """Generate Twilio Markup Language (TwiML) response"""
    
    resp = MessagingResponse()
    message = resp.message()
    
    # Add main text
    message.body(response_data["text"])
    
    # Add media if present
    media_url = response_data.get("media_url")
    if media_url:
        message.media(media_url)
    
    return resp

@router.get("/whatsapp/status")
async def whatsapp_status():
    """Health check endpoint for WhatsApp integration"""
    try:
        # Test basic service connectivity
        ai_status = bool(ai_processor.model)
        memory_status = bool(memory_manager.vector_db.client)
        storage_stats = await file_storage.get_storage_stats()
        
        return {
            "status": "healthy",
            "services": {
                "ai_processor": ai_status,
                "memory_manager": memory_status,
                "file_storage": True
            },
            "storage_stats": storage_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Service unhealthy: {str(e)}")

@router.post("/whatsapp/send")
async def send_whatsapp_message(message_data: Dict[str, Any]):
    """Send a proactive WhatsApp message (for future use)"""
    try:
        # This would integrate with Twilio's API to send messages
        # Implementation depends on use case (notifications, reminders, etc.)
        
        user_id = message_data.get("user_id")
        text = message_data.get("text", "")
        media_url = message_data.get("media_url")
        
        # For now, just log the intent
        logger.info(f"Proactive message request for {user_id}: {text[:100]}...")
        
        return {
            "status": "queued",
            "message": "Proactive messaging not yet implemented",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to send proactive message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/whatsapp/insights/{user_id}")
async def get_user_insights(user_id: str):
    """Get memory insights for a specific user"""
    try:
        insights = await memory_manager.get_memory_insights(user_id)
        
        return {
            "user_id": user_id,
            "insights": insights,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get insights for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/whatsapp/cleanup")
async def cleanup_resources(background_tasks: BackgroundTasks):
    """Cleanup old files and memories"""
    try:
        # Add cleanup tasks to background
        background_tasks.add_task(file_storage.cleanup_temp_files, 24)
        background_tasks.add_task(memory_manager.cleanup_old_memories, 365)
        
        return {
            "status": "cleanup_scheduled",
            "message": "Resource cleanup tasks have been scheduled",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to schedule cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Graceful shutdown handler
@router.on_event("shutdown")
async def shutdown_whatsapp_service():
    """Clean up resources on shutdown"""
    try:
        memory_manager.close()
        logger.info("WhatsApp service shutdown complete")
    except Exception as e:
        logger.error(f"Error during WhatsApp service shutdown: {e}") 