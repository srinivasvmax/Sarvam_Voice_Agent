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
    response.say("Congratulations! Your AI voice agent is working! This call successfully reached your server.", voice="Polly.Aditi")
    
    # Connect to WebSocket for media streaming
    connect = Connect()
    stream = Stream(url=f'wss://{request.url.hostname}/media-stream')
    connect.append(stream)
    response.append(connect)
    
    return Response(content=str(response), media_type="application/xml")


@app.websocket("/media-stream")
async def media_stream(websocket: WebSocket):
    """Handle Twilio media stream WebSocket"""
    await websocket.accept()
    logger.info("WebSocket connected")
    
    try:
        # Here you would integrate with your Pipecat bot
        # For now, just echo back
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received: {data[:100]}")
            # Process with Pipecat bot here
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()


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
