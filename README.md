# NeuralMirror

A real-time AI wellness companion that analyzes your heart rate and stress signals via webcam to provide personalized, empathic insights powered by GPT-4o and Murf Falcon voice synthesis.

## Features

- **Remote Photoplethysmography (rPPG)**: Detects heart rate from facial video without hardware sensors
- **AI-Powered Insights**: Sends biometric data to GPT-4o for contextual wellness advice with rolling conversation history
- **Live Voice Output**: Converts AI responses to natural speech using Murf Falcon
- **Multiple Response Styles**: Switch between oracle, tactical, and poetic voices
- **FutureCast Mode**: Tracks trends and provides forward-looking wellness forecasts
- **Session Intelligence Report**: Optionally exports a JSON report with stress trends, peaks, and AI events
- **Interactive Controls**: Chat, reset history, adjust settings in real-time

## Quick Start

### Prerequisites
- Python 3.10+
- Webcam
- [Murf API key](https://www.murf.ai/)
- [OpenAI API key](https://platform.openai.com/account/api-keys)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/jaysid97/NeuralMirror.git
cd NeuralMirror
```

2. Create a virtual environment:
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate     # macOS/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
```

Then edit `.env` and add your credentials:
```
MURF_API_KEY=your_murf_api_key_here
MURF_VOICE_ID=en-US-natalie
MURF_MODEL=FALCON
MURF_REGION=GLOBAL
MURF_LOCALE=en-US
OPENAI_API_KEY=your_openai_api_key_here
```

### Usage

Run the main application:
```bash
python mirror.py
```

#### Command-line Options
- `--no-voice`: Disable Murf TTS output (text-only mode)
- `--interval 30`: Set seconds between automatic AI insights (default: 30)
- `--futurecast`: Start in FutureCast mode
- `--save-report reports/session.json`: Export session summary + event timeline at exit

#### Live Controls (while webcam window is open)
| Key | Action |
|-----|--------|
| **Q** | Quit application |
| **SPACE** | Trigger an immediate AI insight |
| **C** | Open live chat prompt in terminal |
| **R** | Reset AI conversation history |
| **F** | Toggle FutureCast mode |
| **V** | Cycle voice style (oracle → tactical → poetic) |

### Run Tests

```bash
.\run_all_tests.ps1  # Windows
python test_system.py
```

## Project Structure

```
├── mirror.py              # Main entry point — orchestrates the live loop
├── ai_brain.py           # LLM interface (GPT-4o) with conversation memory
├── pulse_detector.py     # rPPG algorithm — extracts heart rate from webcam
├── voice_output.py       # Murf TTS interface for voice synthesis
├── config.py             # Centralized configuration and API keys
├── requirements.txt      # Python dependencies
├── notebooks/            # Jupyter notebooks for analysis
├── Context-Syphon/       # VS Code extension (optional, for development)
└── test_system.py        # System integration tests
```

## How It Works

1. **Pulse Detection**: The webcam captures your face and detects subtle color changes in blood flow to calculate real-time heart rate
2. **Stress Analysis**: Your current BPM is compared against baseline thresholds to estimate stress levels
3. **AI Analysis**: Heart rate + stress data is sent to GPT-4o with conversation history for contextual insights
4. **Voice Synthesis**: The AI response is converted to speech via Murf Falcon and played back in real-time

## Configuration

Edit `config.py` to adjust:
- BPM stress thresholds
- Camera and frame buffer settings
- AI model and prompt behavior
- Default voice and response style

## Security

⚠️ **Important**: Never commit `.env` to Git. It contains API keys and is in `.gitignore`.
- Always use `.env.example` as a template
- Rotate API keys if accidentally exposed
- Use environment-specific configurations in production

## Requirements

See [requirements.txt](requirements.txt) for all dependencies:
- `opencv-python`: Video capture and processing
- `openai`: GPT-4o API calls
- `requests`: HTTP requests for Murf TTS
- `heartpy`: Heart rate analysis utilities
- `pyaudio`: Audio I/O for voice playback
- And more (see requirements.txt)

## Troubleshooting

### No pulse detected
- Ensure adequate lighting on your face
- Try adjusting `FRAME_BUFFER_SECONDS` in `config.py`
- Check that the webcam has permission to access

### API errors
- Verify `.env` file has valid keys
- Check API quotas on [OpenAI](https://platform.openai.com/account/billing/overview) and [Murf](https://www.murf.ai/)
- Ensure stable internet connection

### Audio not playing
- Check system audio is not muted
- Verify `MURF_API_KEY` is set
- Try `--no-voice` flag for debugging

## Future Enhancements

- Wearable integration (Apple Watch, Fitbit)
- Historical trend analysis dashboard
- Customizable wellness goals and notifications
- Multi-user support with personal profiles

## License

[Add your license here]

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Submit a pull request

## Support

For issues, questions, or feedback:
- Open a GitHub issue
- Check [discussions](../../discussions)

---

**NeuralMirror** — Your AI wellness mirror, always listening. 🔮
