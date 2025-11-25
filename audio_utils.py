"""
Audio utilities for Twilio media stream processing
"""

import audioop
import io
import wave
import base64
from loguru import logger


def mulaw_to_wav(mulaw_data: bytes) -> bytes:
    """Convert mulaw audio to WAV format"""
    try:
        # Convert mulaw to linear PCM
        pcm_data = audioop.ulaw2lin(mulaw_data, 2)
        
        # Create WAV file
        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wav_file:
            wav_file.setnchannels(1)  # mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(8000)  # 8kHz
            wav_file.writeframes(pcm_data)
        
        return wav_io.getvalue()
    
    except Exception as e:
        logger.error(f"mulaw_to_wav error: {e}")
        return b""


def wav_to_mulaw(wav_data: bytes) -> bytes:
    """Convert WAV to mulaw format"""
    try:
        # Parse WAV file
        with io.BytesIO(wav_data) as wav_io:
            with wave.open(wav_io, 'rb') as wav_file:
                pcm_data = wav_file.readframes(wav_file.getnframes())
                sample_width = wav_file.getsampwidth()
        
        # Convert to mulaw
        mulaw_data = audioop.lin2ulaw(pcm_data, sample_width)
        
        return mulaw_data
    
    except Exception as e:
        logger.error(f"wav_to_mulaw error: {e}")
        return b""


def encode_mulaw_base64(mulaw_data: bytes) -> str:
    """Encode mulaw data to base64 for Twilio"""
    return base64.b64encode(mulaw_data).decode('utf-8')


def decode_mulaw_base64(base64_data: str) -> bytes:
    """Decode base64 mulaw data from Twilio"""
    return base64.b64decode(base64_data)
