from fastapi import APIRouter, Request, Response
from twilio.twiml.voice_response import VoiceResponse, Gather
import logging
from datetime import datetime
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/voice/incoming")
async def handle_incoming_call(request: Request):
    """Handle incoming voice calls"""
    try:
        form_data = await request.form()
        
        caller = form_data.get("From", "")
        called = form_data.get("To", "")
        call_sid = form_data.get("CallSid", "")
        
        logger.info(f"Incoming call from {caller} to {called}, CallSid: {call_sid}")
        
        # Create TwiML response
        response = VoiceResponse()
        
        # Welcome message
        response.say(
            "Hello! You've reached Life OS. I'm your AI assistant. "
            "Please speak your message after the beep, and I'll help you with whatever you need.",
            voice="alice"
        )
        
        # Record the message
        response.record(
            action="/voice/recording",
            method="POST",
            max_length=120,  # 2 minutes max
            play_beep=True,
            transcribe=True,
            transcribe_callback="/voice/transcription"
        )
        
        # Fallback if recording fails
        response.say("I didn't receive your message. Please try calling again.", voice="alice")
        response.hangup()
        
        return Response(content=str(response), media_type="text/xml")
        
    except Exception as e:
        logger.error(f"Error handling incoming call: {e}")
        
        # Error response
        response = VoiceResponse()
        response.say("I'm sorry, but I'm experiencing technical difficulties. Please try again later.", voice="alice")
        response.hangup()
        
        return Response(content=str(response), media_type="text/xml")

@router.post("/voice/recording")
async def handle_recording(request: Request):
    """Handle completed voice recording"""
    try:
        form_data = await request.form()
        
        recording_url = form_data.get("RecordingUrl", "")
        recording_duration = form_data.get("RecordingDuration", "0")
        call_sid = form_data.get("CallSid", "")
        caller = form_data.get("From", "")
        
        logger.info(f"Received recording from {caller}, duration: {recording_duration}s")
        
        # Create response
        response = VoiceResponse()
        
        if recording_url and int(recording_duration) > 1:
            response.say(
                "Thank you for your message. I'm processing it now and will get back to you shortly via WhatsApp if you have it set up, "
                "or you can call back in a few minutes for my response.",
                voice="alice"
            )
            
            # TODO: Process the recording with AI
            # This would involve:
            # 1. Downloading the recording
            # 2. Transcribing with AssemblyAI
            # 3. Processing with Gemini
            # 4. Storing in memory
            # 5. Optionally sending response via WhatsApp
            
        else:
            response.say(
                "I didn't receive a clear message. Please try calling again and speak after the beep.",
                voice="alice"
            )
        
        response.hangup()
        
        return Response(content=str(response), media_type="text/xml")
        
    except Exception as e:
        logger.error(f"Error handling recording: {e}")
        
        response = VoiceResponse()
        response.say("Thank you for calling. Goodbye!", voice="alice")
        response.hangup()
        
        return Response(content=str(response), media_type="text/xml")

@router.post("/voice/transcription")
async def handle_transcription(request: Request):
    """Handle transcription callback from Twilio"""
    try:
        form_data = await request.form()
        
        transcription_text = form_data.get("TranscriptionText", "")
        transcription_status = form_data.get("TranscriptionStatus", "")
        call_sid = form_data.get("CallSid", "")
        caller = form_data.get("From", "")
        
        logger.info(f"Transcription received for call {call_sid}: {transcription_text[:100]}...")
        
        if transcription_status == "completed" and transcription_text:
            # TODO: Process transcribed text with AI system
            # This would integrate with the same AI processing pipeline as WhatsApp
            pass
        
        # Return empty response (Twilio doesn't expect content)
        return Response(content="", status_code=200)
        
    except Exception as e:
        logger.error(f"Error handling transcription: {e}")
        return Response(content="", status_code=500)

@router.post("/voice/outbound")
async def make_outbound_call(call_data: dict):
    """Initiate an outbound call (for future proactive features)"""
    try:
        # This would use Twilio's API to make outbound calls
        # For now, just log the intent
        
        to_number = call_data.get("to_number")
        message = call_data.get("message", "")
        
        logger.info(f"Outbound call request to {to_number}: {message[:100]}...")
        
        return {
            "status": "not_implemented",
            "message": "Outbound calling not yet implemented",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error initiating outbound call: {e}")
        raise

@router.get("/voice/status")
async def voice_status():
    """Voice service health check"""
    return {
        "status": "healthy",
        "service": "voice_handler",
        "capabilities": [
            "incoming_calls",
            "voice_recording", 
            "transcription",
            "twiml_generation"
        ],
        "timestamp": datetime.utcnow().isoformat()
    } 