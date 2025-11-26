"""
Sarvam AI integration for STT, LLM, and TTS
"""

import os
import aiohttp
import base64
from loguru import logger


class SarvamAI:
    """Sarvam AI client for speech and language processing"""
    
    def __init__(self):
        self.api_key = os.getenv("SARVAM_API_KEY")
        self.stt_url = os.getenv("SARVAM_STT_URL", "https://api.sarvam.ai/speech-to-text")
        self.tts_url = os.getenv("SARVAM_TTS_URL", "https://api.sarvam.ai/text-to-speech")
        self.llm_url = os.getenv("SARVAM_LLM_URL", "https://api.sarvam.ai/v1/chat/completions")
        self.session = None
    
    async def get_session(self):
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    "API-Subscription-Key": self.api_key,
                    "Content-Type": "application/json"
                }
            )
        return self.session
    
    async def speech_to_text(self, audio_bytes: bytes, language: str = None) -> tuple:
        """Convert speech to text with language detection
        Returns: (text, detected_language)
        """
        try:
            session = await self.get_session()
            
            # If no language specified, try multiple languages to find best match
            if language is None:
                languages = ["te-IN", "hi-IN", "en-IN", "ur-IN"]
            else:
                languages = [language]
            
            best_result = ""
            best_language = "hi-IN"
            
            for lang in languages:
                data = aiohttp.FormData()
                data.add_field('file', audio_bytes, filename='audio.wav', content_type='audio/wav')
                data.add_field('language_code', lang)
                data.add_field('model', 'saarika:v2')
                
                async with session.post(self.stt_url, data=data, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        result = await response.json()
                        text = result.get("transcript", "")
                        
                        # If we get a good transcription, use it
                        if text and len(text.strip()) > len(best_result.strip()):
                            best_result = text
                            best_language = lang
                            
                            # If language was specified, stop here
                            if language:
                                break
            
            logger.info(f"STT ({best_language}): {best_result}")
            return best_result, best_language
        
        except Exception as e:
            logger.error(f"STT exception: {e}")
            return "", "hi-IN"
    
    async def chat(self, messages: list) -> str:
        """Get LLM response"""
        try:
            session = await self.get_session()
            
            payload = {
                "model": "sarvam-2b",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 100,  # Keep responses short for voice
                "top_p": 0.9
            }
            
            # Use Authorization header for LLM endpoint
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            async with session.post(self.llm_url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    result = await response.json()
                    text = result["choices"][0]["message"]["content"]
                    logger.info(f"LLM: {text}")
                    return text
                else:
                    error_text = await response.text()
                    logger.error(f"LLM error {response.status}: {error_text}")
                    return "I'm having trouble thinking right now."
        
        except Exception as e:
            logger.error(f"LLM exception: {e}")
            return "Sorry, I encountered an error."
    
    async def text_to_speech(self, text: str, language: str = "hi-IN") -> bytes:
        """Convert text to speech"""
        try:
            session = await self.get_session()
            
            payload = {
                "inputs": [text],
                "target_language_code": language,
                "speaker": "anushka",  # Valid speaker from API
                "pitch": 0,
                "pace": 1.0,
                "loudness": 1.5,
                "speech_sample_rate": 8000,  # 8kHz for Twilio
                "enable_preprocessing": True,
                "model": "bulbul:v2"  # Valid model version
            }
            
            async with session.post(self.tts_url, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status == 200:
                    result = await response.json()
                    audio_base64 = result["audios"][0]
                    audio_bytes = base64.b64decode(audio_base64)
                    logger.info(f"TTS: Generated {len(audio_bytes)} bytes")
                    return audio_bytes
                else:
                    error_text = await response.text()
                    logger.error(f"TTS error {response.status}: {error_text}")
                    return b""
        
        except Exception as e:
            logger.error(f"TTS exception: {e}")
            return b""
    
    async def close(self):
        """Close session"""
        if self.session and not self.session.closed:
            await self.session.close()
