# 🎙️ Sarvam AI Voice Bot with Pipecat

Real-time voice AI bot powered by Sarvam AI and Pipecat framework. Supports browser calls (WebRTC) and phone calls (Twilio).

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Pipecat](https://img.shields.io/badge/Pipecat-0.0.95+-green.svg)](https://pipecat.ai/)
[![Sarvam AI](https://img.shields.io/badge/Sarvam%20AI-Latest-orange.svg)](https://www.sarvam.ai/)

---

## 🚀 Quick Start

```bash
# 1. Activate virtual environment
venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the bot
python bot.py
```

**For phone calls with Twilio:**
```bash
python bot_twilio.py --transport twilio
```

---

## ✨ Features

- 🎤 **Speech-to-Text** - Sarvam AI STT (saarika:v2.5)
- 🧠 **Language Model** - Sarvam AI LLM (sarvam-2b)
- 🔊 **Text-to-Speech** - Sarvam AI TTS (bulbul:v2)
- 🌐 **Multilingual** - English, Hindi, Telugu, Urdu
- 🌍 **WebRTC** - Browser-based calls
- 📞 **Twilio** - Phone call support (optional)
- ⚡ **Real-time** - Low latency responses

---

## 📁 Project Structure

```
AI_Voice_Agent/
├── bot.py                    # Main bot (WebRTC)
├── bot_twilio.py             # Phone call bot (Twilio)
├── docs/                     # Documentation
│   ├── TWILIO_WITH_PIPECAT.md  # Twilio integration guide
│   └── ...
├── requirements.txt          # Dependencies
├── .env                      # Configuration
└── README.md                 # This file
```

---

## 🎯 Two Ways to Use

### 1. Browser Calls (WebRTC) - Default

```bash
python bot.py
```

Then open http://localhost:7860/client in your browser.

### 2. Phone Calls (Twilio) - Optional

```bash
python bot_twilio.py --transport twilio
```

**See [docs/TWILIO_WITH_PIPECAT.md](docs/TWILIO_WITH_PIPECAT.md) for Twilio setup.**

---

## 🌐 Language Support

Automatically detects and responds in the user's language:

```
English → "Hello, how are you?"
Hindi   → "नमस्ते, आप कैसे हैं?"
Telugu  → "హలో, మీరు ఎలా ఉన్నారు?"
Urdu    → "ہیلو، آپ کیسے ہیں؟"
```

---

## ⚙️ Configuration

Edit `.env`:

```ini
# Sarvam AI (Required)
SARVAM_API_KEY=sk_sjr5xw5l_urtKksPsZ9ZBLydh6QdPcUyy

# Twilio (Optional - for phone calls)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
```

---

## 🔧 Customization

### Change Voice

Edit `bot.py` or `bot_twilio.py`:

```python
tts = SarvamTTSService(
    voice_id="meera",  # Options: meera, arvind, karun
    ...
)
```

### Change LLM Model

```python
llm = OpenAILLMService(
    model="sarvam-2b"  # Options: sarvam-2b, gemma-4b, gemma-12b
)
```

### Adjust Voice Parameters

```python
params=SarvamTTSService.InputParams(
    pitch=0.0,      # -0.75 to 0.75
    pace=1.0,       # 0.3 to 3.0
    loudness=1.0,   # 0.1 to 3.0
    temperature=0.6 # 0.01 to 1.0
)
```

---

## 📞 Twilio Integration

**Important:** Pipecat handles Twilio internally - you don't need the Twilio SDK!

Just:
1. Add Twilio credentials to `.env`
2. Run with `--transport twilio`

**See [docs/TWILIO_WITH_PIPECAT.md](docs/TWILIO_WITH_PIPECAT.md) for details.**

---

## 🐛 Troubleshooting

### Bot won't start
- Ensure venv is activated
- Install dependencies: `pip install -r requirements.txt`
- Check Python version: 3.10+

### No audio in browser
- Allow microphone permissions
- Click microphone icon to unmute
- Try Chrome browser

### Twilio not working
- Check credentials in `.env`
- Run with `--transport twilio` flag
- See [docs/TWILIO_WITH_PIPECAT.md](docs/TWILIO_WITH_PIPECAT.md)

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| **[TWILIO_WITH_PIPECAT.md](docs/TWILIO_WITH_PIPECAT.md)** | Twilio integration guide |
| **[docs/](docs/)** | Additional documentation |

---

## 📊 Performance

- **STT Latency**: 1-2 seconds
- **LLM Latency**: 0.4-0.8 seconds
- **TTS Latency**: 0.6-1.4 seconds
- **Total Response**: 2-4 seconds

---

## 🎓 How It Works

```
User Speech → Pipecat Transport → STT → LLM → TTS → User Hears
                                   ↓     ↓     ↓
                              Sarvam AI Services
```

Pipecat handles:
- Audio streaming
- Transport (WebRTC/Twilio)
- Pipeline management

You configure:
- STT, LLM, TTS services
- System prompts
- Voice parameters

---

## Features

- 🎤 **Speech-to-Text**: Sarvam AI STT with saarika:v2.5 model
- 🧠 **Language Model**: Sarvam AI LLM (sarvam-m model)
- 🔊 **Text-to-Speech**: Sarvam AI TTS with natural Karun voice
- 🌐 **Multi-language**: Supports English, Hindi, Telugu, and more Indian languages
- ⚡ **Real-time**: Fast response times with WebRTC transport
- 🎯 **Natural Voice**: Configured for natural-sounding speech with optimal parameters

## Prerequisites

- Python 3.10 or later
- Windows OS (WebRTC transport)
- Sarvam AI API key

## Quick Start

### 1. Clone and Setup

```bash
cd AI_Voice_Agent
python -m venv venv
venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API Key

The `.env` file is already configured with Sarvam AI credentials:

```ini
SARVAM_API_KEY=sk_sjr5xw5l_urtKksPsZ9ZBLydh6QdPcUyy
SARVAM_STT_URL=https://api.sarvam.ai/speech-to-text
SARVAM_TTS_URL=https://api.sarvam.ai/text-to-speech
```

### 4. Run the Bot

```bash
python bot.py
```

### 5. Connect and Talk

1. Open **http://localhost:7860/client** in your browser
2. Click the **"Connect"** button (top-right)
3. Allow microphone permissions
4. Click the **microphone icon** to enable audio
5. Start speaking!

## How It Works

The bot uses a pipeline architecture:

```
User Speech → Sarvam STT → LLM Processing → Sarvam TTS → Bot Speech
```

### Configuration

**STT (Speech-to-Text)**
- Model: `saarika:v2.5`
- Supports multiple Indian languages

**LLM (Language Model)**
- Model: `sarvam-m`
- Endpoint: `https://api.sarvam.ai/v1/chat/completions`
- Alternative models: `gemma-4b`, `gemma-12b`

**TTS (Text-to-Speech)**
- Voice: `karun` (male voice)
- Model: `bulbul:v2`
- Parameters:
  - Pitch: 0.0 (natural)
  - Pace: 1.0 (normal speed)
  - Loudness: 1.0 (normal volume)
  - Temperature: 0.6 (balanced naturalness)
  - Preprocessing: Enabled

**Available Voices:**
- Female: anushka, manisha, vidya, arya
- Male: abhilash, karun, hitesh

## Usage Examples

### Basic Conversation
```
You: "Hello, how are you?"
Bot: "Hi there! I'm just a computer program, but thanks for asking!"
```

### Multi-language Support
```
You: "తెలుగులో నాకు ఒక జోక్ చెప్పు" (Tell me a joke in Telugu)
Bot: [Responds with a joke in Telugu]

You: "Switch to Hindi"
Bot: [Continues conversation in Hindi]
```

## Customization

### Change Voice

Edit `bot.py` line 75:

```python
voice_id="karun",  # Change to: anushka, manisha, vidya, arya, abhilash, hitesh
```

### Change LLM Model

Edit `bot.py` line 93:

```python
model="sarvam-m"  # Change to: gemma-4b, gemma-12b
```

### Adjust Voice Parameters

Edit `bot.py` lines 77-82:

```python
params=SarvamTTSService.InputParams(
    pitch=0.0,      # Range: -0.75 to 0.75
    pace=1.0,       # Range: 0.3 to 3.0
    loudness=1.0,   # Range: 0.1 to 3.0
    temperature=0.6 # Range: 0.01 to 1.0
)
```

## Troubleshooting

### Bot won't start
- Ensure venv is activated: `venv\Scripts\activate`
- Install all dependencies: `pip install -r requirements.txt`
- Check Python version: `python --version` (needs 3.10+)

### No audio in browser
- Allow microphone permissions
- Click the microphone icon to unmute
- Check your microphone is selected in Devices panel

### 404 or 400 Errors
- Verify your Sarvam API key is correct in `.env`
- Check the model name is valid (sarvam-m, gemma-4b, or gemma-12b)

### Connection Issues
- Try a different browser (Chrome recommended)
- Disable VPN or firewall temporarily
- Check if port 7860 is available

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Browser Client                        │
│              http://localhost:7860/client                │
└────────────────────┬────────────────────────────────────┘
                     │ WebRTC
                     ↓
┌─────────────────────────────────────────────────────────┐
│                  Pipecat Pipeline                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ Sarvam   │→ │ Sarvam   │→ │ Sarvam   │→ │ WebRTC  │ │
│  │   STT    │  │   LLM    │  │   TTS    │  │ Output  │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│                  Sarvam AI API                           │
│  • Speech-to-Text (saarika:v2.5)                        │
│  • Chat Completions (sarvam-m)                          │
│  • Text-to-Speech (karun, bulbul:v2)                    │
└─────────────────────────────────────────────────────────┘
```

## Tech Stack

- **Framework**: Pipecat 0.0.95
- **AI Provider**: Sarvam AI
- **Transport**: WebRTC (SmallWebRTC)
- **Web Server**: FastAPI + Uvicorn
- **Audio Processing**: Silero VAD, Smart Turn Analyzer V3
- **ML Libraries**: PyTorch, Transformers

## Performance

- **STT Latency**: ~1-2 seconds
- **LLM Response**: ~0.4-0.8 seconds
- **TTS Generation**: ~0.6-1.4 seconds
- **Total Response Time**: ~2-4 seconds

## License

BSD 2-Clause License

## Support

For issues or questions:
- Check the [Pipecat Documentation](https://docs.pipecat.ai/)
- Visit [Sarvam AI Documentation](https://docs.sarvam.ai/)
- Join [Pipecat Discord](https://discord.gg/pipecat)

---

**Built with ❤️ using Sarvam AI and Pipecat**
