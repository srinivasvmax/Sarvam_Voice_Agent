"""
Simple Twilio integration server for Pipecat bot
Handles Twilio webhooks and connects to your existing bot
"""

import os
import asyncio
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import Response
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

app = FastAPI()

# Twilio client
twilio_client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)

@app.get("/")
async def root():
    return {"status": "Twilio server running", "service": "Pipecat + Twilio"}


@app.post("/voice/incoming")
@app.get("/voice/incoming")  # Also support GET
async def incoming_call(request: Request):
    """Handle incoming Twilio calls"""
    logger.info(f"🔔 WEBHOOK HIT! Method: {request.method}, URL: {request.url}")
    
    # Handle both GET and POST
    if request.method == "GET":
        form_data = request.query_params
    else:
        form_data = await request.form()
    
    call_sid = form_data.get("CallSid", "TEST")
    from_number = form_data.get("From", "UNKNOWN")
    
    logger.info(f"📞 Incoming call: {call_sid} from {from_number}")
    
    # Create TwiML response
    response = VoiceResponse()
    response.say("Welcome to Electrical Department Customer Support. How may I assist you today?", voice="Polly.Aditi")
    
    # Connect to WebSocket for media streaming
    connect = Connect()
    stream = Stream(url=f'wss://{request.url.hostname}/media-stream')
    connect.append(stream)
    response.append(connect)
    
    return Response(content=str(response), media_type="application/xml")


@app.websocket("/media-stream")
async def media_stream(websocket: WebSocket):
    """Handle Twilio media stream WebSocket with full AI conversation"""
    await websocket.accept()
    logger.info("🔌 WebSocket connected")
    
    from sarvam_ai import SarvamAI
    from audio_utils import decode_mulaw_base64, mulaw_to_wav, wav_to_mulaw, encode_mulaw_base64
    import json
    import audioop
    
    sarvam = SarvamAI()
    stream_sid = None
    audio_buffer = bytearray()
    
    # Voice Activity Detection (VAD) settings
    is_speaking = False
    is_processing = False  # Prevent concurrent processing
    silence_threshold = 1600  # ~200ms of silence at 8kHz (faster response)
    silence_buffer = bytearray()
    min_speech_length = 8000  # Minimum 1 second of speech
    max_speech_length = 40000  # Maximum 5 seconds of speech
    
    # Adaptive noise threshold
    noise_floor = 300  # Initial noise floor
    speech_threshold = 600  # Initial speech threshold
    
    # Conversation context
    messages = [
        {
            "role": "system",
            "content": """You are a customer support agent for the Electrical Department. 

Key instructions:
- ALWAYS respond in the SAME language the user speaks (English, Hindi, Telugu, Urdu, etc.)
- Keep responses SHORT and clear (1-2 sentences for voice calls)
- Be professional and helpful
- Help with electrical department queries, complaints, and information
- If you don't know something, politely say so and offer to connect them to a human agent

Remember: Match the user's language automatically!"""
        }
    ]
    
    async def process_speech_buffer():
        """Process accumulated speech buffer"""
        nonlocal is_speaking, is_processing, audio_buffer, silence_buffer
        
        # Prevent concurrent processing
        if is_processing:
            logger.warning("⚠️ Already processing speech, ignoring new input")
            audio_buffer.clear()
            silence_buffer.clear()
            is_speaking = False
            return
        
        if len(audio_buffer) < min_speech_length:
            logger.warning(f"⚠️ Speech too short ({len(audio_buffer)} bytes), ignoring")
            audio_buffer.clear()
            silence_buffer.clear()
            is_speaking = False
            return
        
        is_processing = True  # Lock processing
        
        logger.info(f"🔊 Processing {len(audio_buffer)} bytes of speech")
        
        # Convert to WAV
        mulaw_bytes = bytes(audio_buffer)
        wav_data = mulaw_to_wav(mulaw_bytes)
        
        # Reset buffers
        audio_buffer.clear()
        silence_buffer.clear()
        is_speaking = False
        
        if not wav_data or len(wav_data) < 100:
            logger.warning("⚠️ WAV conversion failed or too small")
            return
        
        # STT with language detection
        try:
            text, detected_lang = await sarvam.speech_to_text(wav_data)
            
            if not text or len(text.strip()) <= 2:
                logger.warning(f"⚠️ No speech detected or transcript too short: '{text}'")
                is_processing = False  # Unlock
                return
            
            logger.info(f"👤 User said ({detected_lang}): {text}")
            
            # Add to conversation
            messages.append({"role": "user", "content": text})
            
            # LLM
            response = await sarvam.chat(messages)
            messages.append({"role": "assistant", "content": response})
        except Exception as e:
            logger.error(f"❌ Error in STT/LLM: {e}")
            is_processing = False
            return
        
        # Keep conversation short
        if len(messages) > 11:
            messages = [messages[0]] + messages[-10:]
        
        logger.info(f"🤖 AI responds: {response}")
        
        # TTS in the detected language
        tts_wav = await sarvam.text_to_speech(response, detected_lang)
        
        if tts_wav:
            # Convert WAV to raw mulaw (8kHz, mono) for Twilio
            response_mulaw = wav_to_mulaw(tts_wav)
            
            if response_mulaw:
                logger.info(f"📤 Sending {len(response_mulaw)} mulaw bytes to Twilio")
                
                # Send back to Twilio in 20ms chunks (160 bytes at 8kHz)
                chunk_size = 160  # 20ms chunks at 8kHz
                for i in range(0, len(response_mulaw), chunk_size):
                    chunk = response_mulaw[i:i+chunk_size]
                    encoded = encode_mulaw_base64(chunk)
                    
                    media_msg = {
                        "event": "media",
                        "streamSid": stream_sid,
                        "media": {"payload": encoded}
                    }
                    
                    await websocket.send_text(json.dumps(media_msg))
                    await asyncio.sleep(0.02)  # 20ms delay
                
                is_processing = False  # Unlock after response sent
            else:
                logger.error("❌ Failed to convert TTS to mulaw")
                is_processing = False  # Unlock on error
    
    try:
        while True:
            data = await websocket.receive_text()
            event = json.loads(data)
            
            event_type = event.get("event")
            
            if event_type == "start":
                stream_sid = event["start"]["streamSid"]
                logger.info(f"🎙️ Stream started: {stream_sid}")
            
            elif event_type == "media":
                # Receive audio from Twilio
                payload = event["media"]["payload"]
                mulaw_data = decode_mulaw_base64(payload)
                
                # Simple Voice Activity Detection (VAD)
                # Convert mulaw to PCM to check volume
                pcm_data = audioop.ulaw2lin(mulaw_data, 2)
                rms = audioop.rms(pcm_data, 2)  # Get volume level
                
                # Adaptive threshold: update noise floor when not speaking
                if not is_speaking and rms < noise_floor * 1.5:
                    noise_floor = int(noise_floor * 0.95 + rms * 0.05)  # Smooth update
                    speech_threshold = noise_floor * 2  # Speech is 2x noise floor
                
                # Detect if user is speaking (volume above adaptive threshold)
                is_speech = rms > speech_threshold
                
                if is_speech:
                    # User is speaking
                    if not is_speaking:
                        logger.info(f"🎤 Speech started (volume: {rms}, threshold: {speech_threshold})")
                        is_speaking = True
                    
                    audio_buffer.extend(mulaw_data)
                    silence_buffer.clear()
                    
                    # Prevent buffer from getting too large
                    if len(audio_buffer) > max_speech_length:
                        logger.info(f"⏱️ Max speech length reached, processing...")
                        await process_speech_buffer()
                else:
                    # Silence or low volume
                    if is_speaking:
                        # User was speaking, now silence
                        silence_buffer.extend(mulaw_data)
                        
                        # If enough silence after speech, process it
                        if len(silence_buffer) >= silence_threshold:
                            logger.info(f"🔇 Silence detected after speech")
                            await process_speech_buffer()
            
            elif event_type == "stop":
                logger.info("🛑 Stream stopped")
                break
    
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
    
    finally:
        await sarvam.close()
        await websocket.close()
        logger.info("🔌 WebSocket closed")


@app.post("/call/start")
async def start_outbound_call(to: str):
    """Start an outbound call"""
    logger.info(f"Starting outbound call to {to}")
    
    call = twilio_client.calls.create(
        to=to,
        from_=os.getenv("TWILIO_PHONE_NUMBER"),
        url=f"http://{os.getenv('BASE_URL', 'localhost:8000')}/voice/outbound"
    )
    
    return {"success": True, "call_sid": call.sid}


@app.post("/voice/outbound")
async def outbound_call(request: Request):
    """Handle outbound call TwiML"""
    response = VoiceResponse()
    response.say("Hello! This is an AI assistant calling.", voice="Polly.Aditi")
    
    connect = Connect()
    stream = Stream(url=f'wss://{request.url.hostname}/media-stream')
    connect.append(stream)
    response.append(connect)
    
    return Response(content=str(response), media_type="application/xml")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting Twilio server on port {port}")
    uvicorn.run("twilio_server:app", host="0.0.0.0", port=port, reload=True)
