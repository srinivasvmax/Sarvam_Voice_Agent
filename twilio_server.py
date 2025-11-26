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
    
    sarvam = SarvamAI()
    stream_sid = None
    audio_buffer = bytearray()
    buffer_threshold = 16000  # ~2 seconds of audio at 8kHz (more reliable)
    
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
                audio_buffer.extend(mulaw_data)
                
                # Process when buffer is full
                if len(audio_buffer) >= buffer_threshold:
                    logger.info(f"🎤 Processing {len(audio_buffer)} bytes of audio")
                    
                    # Convert to WAV
                    mulaw_bytes = bytes(audio_buffer)
                    logger.info(f"🔊 Converting {len(mulaw_bytes)} mulaw bytes to WAV")
                    wav_data = mulaw_to_wav(mulaw_bytes)
                    logger.info(f"🔊 WAV data: {len(wav_data)} bytes")
                    audio_buffer.clear()
                    
                    if wav_data and len(wav_data) > 100:
                        # STT with language detection
                        text, detected_lang = await sarvam.speech_to_text(wav_data)
                        
                        if text and len(text.strip()) > 2:
                            logger.info(f"👤 User said: {text}")
                            
                            # Add to conversation
                            messages.append({"role": "user", "content": text})
                            
                            # LLM
                            response = await sarvam.chat(messages)
                            messages.append({"role": "assistant", "content": response})
                            
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
                                else:
                                    logger.error("❌ Failed to convert TTS to mulaw")
            
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
