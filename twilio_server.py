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

# Validate required environment variables
required_env_vars = ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER", "SARVAM_API_KEY"]
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Twilio client
twilio_client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)

@app.get("/")
@app.head("/")
async def root():
    return {"status": "Twilio server running", "service": "Pipecat + Twilio"}


@app.get("/health")
async def health_check():
    """Health check endpoint with dependency verification"""
    health_status = {
        "status": "healthy",
        "service": "Twilio Voice Bot",
        "checks": {}
    }
    
    # Check environment variables
    health_status["checks"]["env_vars"] = all([
        os.getenv("TWILIO_ACCOUNT_SID"),
        os.getenv("TWILIO_AUTH_TOKEN"),
        os.getenv("TWILIO_PHONE_NUMBER"),
        os.getenv("SARVAM_API_KEY")
    ])
    
    # Check Sarvam AI connectivity
    try:
        from sarvam_ai import SarvamAI
        sarvam = SarvamAI()
        await sarvam.close()
        health_status["checks"]["sarvam_ai"] = True
    except Exception as e:
        health_status["checks"]["sarvam_ai"] = False
        health_status["checks"]["sarvam_error"] = str(e)
        health_status["status"] = "degraded"
    
    # Check Twilio client
    try:
        twilio_client.api.accounts(os.getenv("TWILIO_ACCOUNT_SID")).fetch()
        health_status["checks"]["twilio"] = True
    except Exception as e:
        health_status["checks"]["twilio"] = False
        health_status["checks"]["twilio_error"] = str(e)
        health_status["status"] = "degraded"
    
    return health_status


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
    
    # Create TwiML response with language selection
    response = VoiceResponse()
    
    # Check if this is a retry (from query params)
    retry = form_data.get("retry", "0")
    
    # Gather language selection (DTMF input)
    gather = response.gather(
        num_digits=1,
        action=f'/voice/language-selected?retry={retry}',
        method='POST',
        timeout=10
    )
    
    # Multi-language greeting
    if retry == "0":
        # First attempt - full greeting
        gather.say("Welcome to Electrical Department Customer Support.", voice="Polly.Aditi", language="en-IN")
        gather.pause(length=1)  # 1 second pause
    else:
        # Retry - shorter prompt
        gather.say("Please select a language.", voice="Polly.Aditi", language="en-IN")
        gather.say("Dayachesi bhashanu ennukondee.", voice="Polly.Aditi", language="en-IN")
        gather.pause(length=1)  # 1 second pause
    
    # Language selection prompts
    # Note: Using transliteration for Telugu as Polly.Aditi doesn't support Telugu script well
    gather.say("Telugu kosam okati nokkandi.", voice="Polly.Aditi", language="en-IN")
    gather.say("हिंदी के लिए 2 दबाएं.", voice="Polly.Aditi", language="hi-IN")
    gather.say("Press 3 for English.", voice="Polly.Aditi", language="en-IN")
    
    # If no input after retry, default to Telugu
    if retry == "1":
        response.say("No input received.", voice="Polly.Aditi", language="en-IN")
        response.say("Teluguku maarutundi.", voice="Polly.Aditi", language="en-IN")
        response.redirect('/voice/language-selected?Digits=1')
    else:
        # First timeout - ask again
        response.redirect('/voice/incoming?retry=1')
    
    return Response(content=str(response), media_type="application/xml")


@app.post("/voice/language-selected")
@app.get("/voice/language-selected")  # Also support GET for redirect
async def language_selected(request: Request):
    """Handle language selection and connect to WebSocket"""
    # Handle both GET and POST
    if request.method == "GET":
        form_data = request.query_params
    else:
        form_data = await request.form()
    
    digit = form_data.get("Digits", "")
    retry = form_data.get("retry", "0")
    
    # Map digit to language
    language_map = {
        "1": {"code": "te-IN", "name": "Telugu"},
        "2": {"code": "hi-IN", "name": "Hindi"},
        "3": {"code": "en-IN", "name": "English"}
    }
    
    # Validate digit and get language
    if digit not in language_map:
        logger.warning(f"⚠️ Invalid digit pressed: {digit}")
        
        # If first invalid attempt, ask again
        if retry == "0":
            response = VoiceResponse()
            response.say("Invalid selection.", voice="Polly.Aditi", language="en-IN")
            response.say("Chellani enpika.", voice="Polly.Aditi", language="en-IN")
            response.redirect('/voice/incoming?retry=1')
            return Response(content=str(response), media_type="application/xml")
        else:
            # Second invalid attempt, default to Telugu
            logger.info("⚠️ Second invalid attempt, defaulting to Telugu")
            digit = "1"
    
    selected_lang = language_map[digit]
    logger.info(f"🌐 User selected language: {selected_lang['name']} ({selected_lang['code']})")
    
    # Create TwiML response
    response = VoiceResponse()
    
    # Confirm selection in chosen language (short and clear)
    # Note: Using transliteration for Telugu as Polly.Aditi doesn't render Telugu script properly
    if selected_lang['code'] == "te-IN":
        response.say("Telugu. Meeku ela sahayam cheyagalanu?", voice="Polly.Aditi", language="en-IN")
    elif selected_lang['code'] == "hi-IN":
        response.say("हिंदी। मैं आपकी कैसे मदद कर सकता हूं?", voice="Polly.Aditi", language="hi-IN")
    else:
        response.say("English. How may I assist you?", voice="Polly.Aditi", language="en-IN")
    
    # Connect to WebSocket with language parameter
    connect = Connect()
    stream = Stream(url=f'wss://{request.url.hostname}/media-stream')
    # Pass language as a custom parameter that Twilio will send in the 'start' event
    stream.parameter(name='language', value=selected_lang["code"])
    connect.append(stream)
    response.append(connect)
    
    return Response(content=str(response), media_type="application/xml")


@app.websocket("/media-stream")
async def media_stream(websocket: WebSocket):
    """Handle Twilio media stream WebSocket with full AI conversation"""
    await websocket.accept()
    
    # Get selected language from Twilio's start event (will be set when stream starts)
    selected_language = "te-IN"  # Default, will be overridden by start event
    logger.info(f"🔌 WebSocket connected, waiting for language from start event...")
    
    from sarvam_ai import SarvamAI
    from audio_utils import decode_mulaw_base64, mulaw_to_wav, wav_to_mulaw, encode_mulaw_base64
    import json
    import audioop
    
    try:
        sarvam = SarvamAI()
    except ValueError as e:
        logger.error(f"❌ Failed to initialize Sarvam AI: {e}")
        await websocket.close(code=1011, reason="Configuration error")
        return
    
    stream_sid = None
    audio_buffer = bytearray()
    stream_ready = False
    
    # Voice Activity Detection (VAD) settings
    is_speaking = False
    is_processing = False  # Prevent concurrent processing
    silence_threshold = 1600  # ~200ms of silence at 8kHz (faster response)
    silence_buffer = bytearray()
    min_speech_length = 4000  # Minimum 0.5 seconds of speech (reduced from 6000 for better responsiveness)
    max_speech_length = 40000  # Maximum 5 seconds of speech
    
    # Adaptive noise threshold
    noise_floor = 500  # Initial noise floor (higher to avoid false triggers)
    speech_threshold = 1000  # Initial speech threshold (higher for clearer speech)
    
    # Conversation tracking and analytics
    call_start_time = asyncio.get_event_loop().time()
    failed_stt_count = 0  # Track consecutive STT failures
    max_failed_attempts = 3  # Offer human transfer after 3 failures
    query_count = 0  # Track number of queries in this call
    last_user_query = None  # Remember last query for context
    
    # Conversation context with language-specific system prompt
    language_names = {
        "te-IN": "Telugu",
        "hi-IN": "Hindi", 
        "en-IN": "English"
    }
    
    # Initialize messages as empty - will be set when language is received
    messages = []
    
    async def process_speech_buffer():
        """Process accumulated speech buffer"""
        nonlocal is_speaking, is_processing, audio_buffer, silence_buffer, messages
        nonlocal failed_stt_count, query_count, last_user_query
        
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
            is_processing = False  # Unlock on error
            return
        
        # STT with user's selected language (force it, don't auto-detect)
        try:
            stt_start = asyncio.get_event_loop().time()
            text, detected_lang = await sarvam.speech_to_text(wav_data, language=selected_language)
            stt_duration = asyncio.get_event_loop().time() - stt_start
            
            # Override detected language with selected language to maintain consistency
            detected_lang = selected_language
            
            if not text or len(text.strip()) <= 2:
                logger.warning(f"⚠️ No speech detected or transcript too short: '{text}'")
                failed_stt_count += 1
                
                # Offer human transfer after multiple failures
                if failed_stt_count >= max_failed_attempts:
                    logger.warning(f"⚠️ {failed_stt_count} consecutive STT failures, offering human transfer")
                    fallback_msg = {
                        "te-IN": "క్షమించండి, నేను మీ మాటలు అర్థం చేసుకోలేకపోతున్నాను. మానవ ఏజెంట్‌కు కనెక్ట్ చేయాలా?",
                        "hi-IN": "क्षमा करें, मैं आपकी बात समझ नहीं पा रहा हूं। क्या मैं आपको किसी व्यक्ति से जोड़ूं?",
                        "en-IN": "Sorry, I'm having trouble understanding you. Would you like to speak with a human agent?"
                    }
                    # Send fallback message (implementation would need TTS here)
                    logger.info(f"📞 Fallback: {fallback_msg.get(selected_language)}")
                
                is_processing = False  # Unlock
                return
            
            # Reset failure count on successful STT
            failed_stt_count = 0
            query_count += 1
            last_user_query = text
            
            logger.info(f"👤 User said ({detected_lang}): {text} [STT: {stt_duration:.2f}s, Query #{query_count}]")
            
            # Check for transfer keywords
            transfer_keywords = {
                "te-IN": ["మానవుడు", "ఆపరేటర్", "వ్యక్తి", "ఎవరైనా"],
                "hi-IN": ["मानव", "ऑपरेटर", "व्यक्ति", "कोई"],
                "en-IN": ["human", "operator", "person", "agent", "someone", "transfer"]
            }
            
            text_lower = text.lower()
            if any(keyword in text_lower for keyword in transfer_keywords.get(selected_language, [])):
                logger.info(f"🔄 Transfer requested by user")
                transfer_msg = {
                    "te-IN": "మానవ ఏజెంట్‌కు కనెక్ట్ చేస్తున్నాను. దయచేసి వేచి ఉండండి.",
                    "hi-IN": "मैं आपको किसी व्यक्ति से जोड़ रहा हूं। कृपया प्रतीक्षा करें।",
                    "en-IN": "Connecting you to a human agent. Please wait."
                }
                response = transfer_msg.get(selected_language, transfer_msg["te-IN"])
                messages.append({"role": "user", "content": text})
                messages.append({"role": "assistant", "content": response})
            else:
                # Add conversation memory context
                if query_count > 1 and last_user_query:
                    context_note = f"\n[Previous query: {last_user_query}]"
                    messages.append({"role": "user", "content": text + context_note})
                else:
                    messages.append({"role": "user", "content": text})
                
                # LLM
                llm_start = asyncio.get_event_loop().time()
                response = await sarvam.chat(messages)
                llm_duration = asyncio.get_event_loop().time() - llm_start
                logger.info(f"🤖 LLM response time: {llm_duration:.2f}s")
                
                messages.append({"role": "assistant", "content": response})
            
            # Keep conversation short
            if len(messages) > 11:
                messages = [messages[0]] + messages[-10:]
            
            logger.info(f"🤖 AI responds: {response}")
            
            # TTS in the user's SELECTED language (not detected)
            tts_start = asyncio.get_event_loop().time()
            tts_wav = await sarvam.text_to_speech(response, selected_language)
            tts_duration = asyncio.get_event_loop().time() - tts_start
            logger.info(f"🎵 TTS generation time: {tts_duration:.2f}s")
            
            if tts_wav:
                # Convert WAV to raw mulaw (8kHz, mono) for Twilio
                response_mulaw = wav_to_mulaw(tts_wav)
                
                if response_mulaw:
                    # Check if we have a valid stream_sid
                    if not stream_sid:
                        logger.error("❌ No stream_sid available, cannot send audio")
                        is_processing = False
                        return
                    
                    audio_duration = len(response_mulaw) / 8000  # Duration in seconds at 8kHz
                    logger.info(f"📤 Sending {len(response_mulaw)} mulaw bytes to Twilio (duration: {audio_duration:.2f}s)")
                    
                    # Clear any queued audio from Twilio before sending our response
                    try:
                        clear_msg = {
                            "event": "clear",
                            "streamSid": stream_sid
                        }
                        await websocket.send_text(json.dumps(clear_msg))
                    except Exception as clear_error:
                        logger.warning(f"⚠️ Failed to clear audio queue: {clear_error}")
                    
                    # Send back to Twilio in 20ms chunks (160 bytes at 8kHz)
                    chunk_size = 160  # 20ms chunks at 8kHz
                    send_start = asyncio.get_event_loop().time()
                    for i in range(0, len(response_mulaw), chunk_size):
                        # Check if WebSocket is still connected
                        if websocket.client_state.name != "CONNECTED":
                            logger.warning("⚠️ WebSocket disconnected, stopping audio send")
                            break
                        
                        chunk = response_mulaw[i:i+chunk_size]
                        encoded = encode_mulaw_base64(chunk)
                        
                        media_msg = {
                            "event": "media",
                            "streamSid": stream_sid,
                            "media": {"payload": encoded}
                        }
                        
                        try:
                            await websocket.send_text(json.dumps(media_msg))
                            await asyncio.sleep(0.02)  # 20ms delay
                        except Exception as send_error:
                            logger.warning(f"⚠️ Failed to send audio chunk: {send_error}")
                            break
                    
                    send_duration = asyncio.get_event_loop().time() - send_start
                    total_time = asyncio.get_event_loop().time() - stt_start
                    logger.info(f"⏱️ Total response time: {total_time:.2f}s (STT: {stt_duration:.2f}s, LLM: {llm_duration:.2f}s, TTS: {tts_duration:.2f}s, Send: {send_duration:.2f}s)")
                    
                    is_processing = False  # Unlock after response sent
                else:
                    logger.error("❌ Failed to convert TTS to mulaw")
                    is_processing = False  # Unlock on error
            else:
                logger.error("❌ TTS returned empty audio")
                is_processing = False  # Unlock on error
                
        except Exception as e:
            logger.error(f"❌ Error in speech processing: {e}")
            is_processing = False
            return
    
    try:
        while True:
            # Add timeout to prevent zombie connections
            data = await asyncio.wait_for(websocket.receive_text(), timeout=300.0)  # 5 min timeout
            event = json.loads(data)
            
            event_type = event.get("event")
            
            if event_type == "start":
                stream_sid = event["start"]["streamSid"]
                stream_ready = True
                
                # Get language from custom parameters sent by Twilio
                custom_params = event["start"].get("customParameters", {})
                if "language" in custom_params:
                    selected_language = custom_params["language"]
                    logger.info(f"🎙️ Stream started: {stream_sid} with language: {selected_language}")
                else:
                    logger.warning(f"⚠️ No language parameter received, using default: {selected_language}")
                    logger.info(f"🎙️ Stream started: {stream_sid}")
                
                # NOW initialize the system prompt with the correct language
                selected_lang_name = language_names.get(selected_language, "Telugu")
                messages.clear()  # Clear any existing messages
                messages.append({
                    "role": "system",
                    "content": f"""You are a helpful customer support agent for the Electrical Department in India.

CRITICAL: User selected {selected_lang_name} language. You MUST respond ONLY in {selected_lang_name}.

Your responsibilities:
- Handle electrical complaints (power outages, voltage issues, meter problems)
- Provide information about electricity bills and payments
- Help with new connection requests
- Report electrical hazards and emergencies
- Provide lineman contact numbers and department information

Guidelines:
- Keep responses SHORT and CONCISE (2-3 sentences maximum for voice calls)
- Be professional, polite, and helpful
- Ask ONE clear question at a time
- If you don't have specific information, acknowledge briefly and offer to connect to a human agent
- For emergencies, prioritize safety and provide emergency contact: 1912

Common queries you can help with:
- Power outage complaints
- High electricity bill queries
- New connection applications
- Meter reading issues
- Lineman contact numbers
- Payment methods
- Emergency electrical issues

Remember: ALWAYS respond in {selected_lang_name} language only!"""
                })
                logger.info(f"✅ System prompt initialized for {selected_lang_name}")
            
            elif event_type == "media":
                # Wait for stream to be ready before processing audio
                if not stream_ready or not stream_sid:
                    logger.warning("⚠️ Received media before stream ready, skipping...")
                    continue
                
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
                    speech_threshold = max(noise_floor * 3, 800)  # Speech is 3x noise floor, minimum 800
                
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
                        logger.warning(f"⚠️ Max speech length reached ({len(audio_buffer)} bytes), processing...")
                        await process_speech_buffer()
                    
                    # Safety: prevent unbounded growth if processing fails
                    if len(audio_buffer) > max_speech_length * 2:
                        logger.error(f"❌ Audio buffer overflow ({len(audio_buffer)} bytes), clearing...")
                        audio_buffer.clear()
                        silence_buffer.clear()
                        is_speaking = False
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
    
    except asyncio.TimeoutError:
        logger.warning("⏱️ WebSocket timeout - no data received for 5 minutes")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
    
    finally:
        # Call analytics summary
        call_duration = asyncio.get_event_loop().time() - call_start_time
        logger.info(f"""
📊 Call Summary:
   - Duration: {call_duration:.1f}s
   - Language: {selected_language}
   - Queries handled: {query_count}
   - Failed STT attempts: {failed_stt_count}
   - Stream ID: {stream_sid}
        """)
        await sarvam.close()
        
        # Only close if not already closed
        if websocket.client_state.name == "CONNECTED":
            try:
                await websocket.close()
                logger.info("🔌 WebSocket closed")
            except Exception as close_error:
                logger.warning(f"⚠️ WebSocket already closed: {close_error}")
        else:
            logger.info("🔌 WebSocket already disconnected")


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
    is_production = os.getenv("ENVIRONMENT", "development") == "production"
    logger.info(f"Starting Twilio server on port {port} ({'production' if is_production else 'development'} mode)")
    uvicorn.run("twilio_server:app", host="0.0.0.0", port=port, reload=not is_production)
