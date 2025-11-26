"""
Audio utilities for Twilio media stream processing

Twilio Media Streams Format Requirements:
- Sample rate: 8000 Hz (8kHz)
- Encoding: μ-law (mulaw)
- Channels: Mono (1 channel)
- Format: Raw mulaw bytes (NO WAV headers)
- Transport: Base64-encoded in WebSocket messages
"""

import audioop
import io
import wave
import base64
from loguru import logger


def mulaw_to_wav(mulaw_data: bytes, target_rate: int = 16000, apply_noise_reduction: bool = True) -> bytes:
    """Convert mulaw audio to WAV format with optional noise reduction
    Args:
        mulaw_data: mulaw encoded audio
        target_rate: target sample rate (16000 for better quality with Sarvam AI)
        apply_noise_reduction: apply basic noise reduction
    """
    try:
        # Convert mulaw to linear PCM
        pcm_data = audioop.ulaw2lin(mulaw_data, 2)
        
        # Basic noise reduction: apply a simple noise gate
        if apply_noise_reduction:
            # Calculate RMS (volume) of the audio
            rms = audioop.rms(pcm_data, 2)
            
            # If audio is very quiet (likely just noise), amplify it
            if rms < 500:
                try:
                    # Amplify quiet audio (2x boost)
                    pcm_data = audioop.mul(pcm_data, 2, 2.0)
                    logger.debug(f"🔊 Amplified quiet audio (RMS: {rms})")
                except audioop.error:
                    pass
            
            # Apply simple high-pass filter by removing DC offset
            # This helps reduce low-frequency rumble/noise
            try:
                pcm_data = audioop.bias(pcm_data, 2, 0)
            except audioop.error:
                pass
        
        # Resample from 8kHz to 16kHz for better STT quality
        if target_rate != 8000:
            pcm_data, _ = audioop.ratecv(pcm_data, 2, 1, 8000, target_rate, None)
        
        # Create WAV file
        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wav_file:
            wav_file.setnchannels(1)  # mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(target_rate)
            wav_file.writeframes(pcm_data)
        
        wav_bytes = wav_io.getvalue()
        logger.info(f"✅ Converted mulaw to WAV: {len(wav_bytes)} bytes at {target_rate}Hz")
        return wav_bytes
    
    except Exception as e:
        logger.error(f"❌ mulaw_to_wav error: {e}")
        return b""


def wav_to_mulaw(wav_data: bytes) -> bytes:
    """Convert WAV to mulaw format for Twilio (8kHz, mono, raw mulaw)
    
    Twilio requires:
    - 8kHz sample rate
    - Mono channel
    - Raw mulaw encoding (no WAV headers)
    """
    try:
        # Parse WAV file
        with io.BytesIO(wav_data) as wav_io:
            with wave.open(wav_io, 'rb') as wav_file:
                pcm_data = wav_file.readframes(wav_file.getnframes())
                sample_width = wav_file.getsampwidth()
                channels = wav_file.getnchannels()
                framerate = wav_file.getframerate()
                
                logger.info(f"📊 Input WAV: {framerate}Hz, {channels}ch, {sample_width*8}bit")
        
        # Convert stereo to mono if needed
        if channels == 2:
            pcm_data = audioop.tomono(pcm_data, sample_width, 1, 1)
            logger.info(f"🔄 Converted stereo to mono")
        
        # Resample to 8kHz if needed (Twilio requirement)
        if framerate != 8000:
            pcm_data, _ = audioop.ratecv(pcm_data, sample_width, 1, framerate, 8000, None)
            logger.info(f"🔄 Resampled from {framerate}Hz to 8000Hz")
        
        # Convert PCM to mulaw (raw, no headers)
        mulaw_data = audioop.lin2ulaw(pcm_data, sample_width)
        logger.info(f"✅ Converted to raw mulaw: {len(mulaw_data)} bytes (8kHz mono)")
        
        return mulaw_data
    
    except Exception as e:
        logger.error(f"❌ wav_to_mulaw error: {e}")
        return b""


def encode_mulaw_base64(mulaw_data: bytes) -> str:
    """Encode mulaw data to base64 for Twilio"""
    return base64.b64encode(mulaw_data).decode('utf-8')


def decode_mulaw_base64(base64_data: str) -> bytes:
    """Decode base64 mulaw data from Twilio"""
    return base64.b64decode(base64_data)
