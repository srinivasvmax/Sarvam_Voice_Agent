# Audio Format Conversion Flow

## Twilio → Sarvam (Incoming Audio)

1. **Twilio sends**: Base64-encoded raw mulaw (8kHz, mono)
2. **Decode**: `decode_mulaw_base64()` → raw mulaw bytes
3. **Convert**: `mulaw_to_wav()` → WAV format (16kHz for better STT quality)
4. **Send to Sarvam STT**: WAV file

## Sarvam → Twilio (Outgoing Audio)

1. **Sarvam TTS returns**: WAV format (8kHz, mono, 16-bit PCM with RIFF headers)
2. **Convert**: `wav_to_mulaw()` → raw mulaw bytes (8kHz, mono, NO headers)
   - Extracts PCM data from WAV
   - Converts 16-bit PCM → 8-bit mulaw
   - Strips all WAV headers
3. **Encode**: `encode_mulaw_base64()` → base64 string
4. **Send to Twilio**: In 160-byte chunks (20ms at 8kHz)

### Verified Format
✅ Sarvam returns: WAV (8000Hz, 1ch, 16-bit PCM, NONE compression)
✅ Conversion output: Raw mulaw (8000Hz, 1ch, 8-bit)
✅ Chunk size: 160 bytes = 20ms at 8kHz

## Key Points

### Twilio Requirements (STRICT)
- **Sample rate**: 8000 Hz
- **Encoding**: μ-law (mulaw)
- **Channels**: Mono
- **Format**: Raw bytes (NO WAV headers)
- **Transport**: Base64-encoded

### Current Implementation
✅ Properly converts Sarvam WAV → raw mulaw
✅ Handles sample rate conversion (if needed)
✅ Handles stereo → mono conversion (if needed)
✅ Strips WAV headers before sending to Twilio
✅ Sends in proper 20ms chunks (160 bytes)

### Optimization Notes
- Sarvam TTS is configured to output 8kHz (matching Twilio)
- This minimizes resampling overhead
- STT uses 16kHz for better transcription quality
