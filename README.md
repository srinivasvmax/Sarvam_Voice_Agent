# 🎙️ Sarvam AI Voice Bot

Real-time voice AI bot powered by Sarvam AI and Pipecat framework. Supports phone calls via Twilio with multilingual support.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Sarvam AI](https://img.shields.io/badge/Sarvam%20AI-Latest-orange.svg)](https://www.sarvam.ai/)

---

## 🚀 Quick Start

```bash
# 1. Activate virtual environment
venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the Twilio server
python twilio_server.py
```

---

## ✨ Features

- 🎤 **Speech-to-Text** - Sarvam AI STT (saarika:v2.5)
- 🧠 **Language Model** - Sarvam AI LLM (sarvam-m)
- 🔊 **Text-to-Speech** - Sarvam AI TTS (bulbul:v2)
- 🌐 **Multilingual** - Telugu, Hindi, English, Gujarati
- 📞 **Twilio Integration** - Phone call support with IVR
- 🎯 **Language Selection** - User chooses language via IVR menu
- ⚡ **Real-time** - Low latency responses (2-4 seconds)

---

## 📁 Project Structure

```
AI_Voice_Agent/
├── twilio_server.py          # Main Twilio server
├── sarvam_ai.py              # Sarvam AI API integration
├── audio_utils.py            # Audio format conversion
├── requirements.txt          # Dependencies
├── .env                      # Configuration
├── docs/                     # Documentation
│   ├── LANGUAGE_SELECTION.md # IVR language menu
│   ├── AUDIO_CONVERSION.md   # Audio format details
│   ├── ARCHITECTURE.md       # System architecture
│   └── TROUBLESHOOTING.md    # Common issues
└── README.md                 # This file
```

---

## ⚙️ Configuration

Edit `.env`:

```ini
# Sarvam AI (Required)
SARVAM_API_KEY=your_api_key_here

# Twilio (Required)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
```

---

## 🌐 Language Support

Users select their language via IVR menu:
- **Telugu** (te-IN) - Press 1
- **Hindi** (hi-IN) - Press 2
- **English** (en-IN) - Press 3
- **Gujarati** (gu-IN) - Press 4

See [docs/LANGUAGE_SELECTION.md](docs/LANGUAGE_SELECTION.md) for details.

---

## 📊 Performance

- **STT Latency**: 1-2 seconds
- **LLM Latency**: 0.4-0.8 seconds
- **TTS Latency**: 0.6-1.4 seconds
- **Total Response**: 2-4 seconds

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [LANGUAGE_SELECTION.md](docs/LANGUAGE_SELECTION.md) | IVR language menu flow |
| [AUDIO_CONVERSION.md](docs/AUDIO_CONVERSION.md) | Audio format conversion details |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture and flow |
| [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Common issues and solutions |

---

## 🎓 How It Works

```
User Calls → IVR Menu → Language Selection → Voice Conversation
                                              ↓
                                    STT → LLM → TTS
                                    ↓     ↓     ↓
                              Sarvam AI Services
```

---

## 🐛 Troubleshooting

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for detailed solutions.

Quick fixes:
- **Server won't start**: Check Python 3.10+, activate venv
- **No audio**: Check Twilio webhook URL configuration
- **API errors**: Verify Sarvam API key in `.env`

---

## 📞 Deployment

1. Deploy to Render/Railway/Heroku
2. Configure Twilio webhook: `https://your-domain.com/voice/incoming`
3. Test by calling your Twilio number

---

**Built with ❤️ using Sarvam AI**
