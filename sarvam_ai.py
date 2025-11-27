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
                    "API-Subscription-Key": self.api_key
                }
            )
        return self.session
    
    async def speech_to_text(self, audio_bytes: bytes, language: str = None) -> tuple:
        """Convert speech to text with language detection
        Returns: (text, detected_language)
        """
        try:
            logger.info(f"🎤 STT: Received {len(audio_bytes)} bytes of audio")
            session = await self.get_session()
            
            # If no language specified, try multiple languages to find best match
            if language is None:
                # Supported languages by Sarvam API (no Urdu support)
                languages = ["te-IN", "hi-IN", "en-IN"]  # Telugu, Hindi, English
            else:
                languages = [language]
            
            best_result = ""
            best_language = "te-IN"  # Default to Telugu
            
            # Store all results for comparison
            results = []
            
            for lang in languages:
                data = aiohttp.FormData()
                data.add_field('file', audio_bytes, filename='audio.wav', content_type='audio/wav')
                data.add_field('language_code', lang)
                data.add_field('model', 'saarika:v2')
                
                async with session.post(self.stt_url, data=data, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        result = await response.json()
                        text = result.get("transcript", "")
                        
                        if text and len(text.strip()) > 0:
                            results.append({
                                'lang': lang,
                                'text': text,
                                'length': len(text)
                            })
                            logger.info(f"🔍 STT attempt ({lang}): '{text}' (length: {len(text)})")
                            
                            # If language was specified, use first valid result
                            if language:
                                best_result = text
                                best_language = lang
                                break
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ STT API error for {lang}: {response.status} - {error_text}")
            
            # If no language specified, pick the first language (most likely correct)
            # First language in list gets priority since user's primary language is Telugu
            if not language and results:
                # Use first valid result (Telugu priority)
                best_result = results[0]['text']
                best_language = results[0]['lang']
                logger.info(f"✅ Using first result ({best_language}) as most likely correct")
            
            if best_result:
                logger.info(f"✅ STT Final ({best_language}): {best_result}")
            else:
                logger.warning(f"⚠️ STT: No speech detected in any language (tried: {', '.join(languages)})")
            
            return best_result, best_language
        
        except Exception as e:
            logger.error(f"❌ STT exception: {e}")
            return "", "te-IN"
    
    async def chat(self, messages: list) -> str:
        """Get LLM response"""
        try:
            session = await self.get_session()
            
            payload = {
                "model": "sarvam-2b",  # Using sarvam-2b for better multilingual support
                "messages": messages,
                "temperature": 0.5,  # Lower temperature for more focused, consistent responses
                "max_tokens": 150,  # Slightly more tokens for complete sentences
                "top_p": 0.85,  # Slightly lower for more deterministic responses
                "frequency_penalty": 0.3,  # Reduce repetitive responses
                "presence_penalty": 0.2  # Encourage diverse vocabulary
            }
            
            # Use Authorization header for LLM endpoint
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
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
            
            headers = {"Content-Type": "application/json"}
            
            async with session.post(self.tts_url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
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
