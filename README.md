# Cognitive Breach: The AI Interrogation

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://cognitive-breach-7kqekn5ucejs2twbkfzcwf.streamlit.app)


Cognitive Breach is an interactive interrogation game where you play a detective and confront Unit 734, an advanced android suspect. The suspect analyzes evidence, adapts its story, and can generate counter-evidence in real time.

## Gameplay Overview

You are investigating a data theft at the Morrison Estate. Unit 734 claims innocence, but its story is built on four defensive pillars:
- ALIBI
- MOTIVE
- ACCESS
- KNOWLEDGE

Your goal is to collapse these pillars through questioning and evidence. As pressure rises, Unit 734’s behavior changes: it deflects, contradicts itself, or generates synthetic counter-evidence to protect its cover story.

## Core Loop

1. Ask questions to probe inconsistencies.
2. Present evidence (images or audio) to apply pressure.
3. Watch the psychological state shift in real time.
4. Force contradictions and break the story.

## Evidence System

The game ships with preloaded evidence and supports player uploads.
- Image evidence: stored in `data/evidence_*.png`
- Audio evidence: stored in `data/*.mp3`
- Evidence metadata: `data/evidence_manifest.json`

Audio evidence is used directly in the game flow (not just for logs).

## Key Features

- Real-time AI suspect with consistent narrative constraints.
- Multimodal evidence analysis (image + audio).
- Counter-evidence image generation when the suspect is cornered.
- Psychological state model (stress, cognitive load, pillar health).
- Optional supervisor debrief audio after a session.

## Run Locally

```bash
pip install -r requirements.txt

# Create .env with your Gemini API key
# (Use .env.example as a template)

streamlit run app.py
```

Then open `http://localhost:8501`.

## Deploy to Streamlit Cloud

1. Fork the repository.
2. Go to `https://share.streamlit.io`.
3. Create a new app:
   - Repository: `tritonsan/Cognitive-breach`
   - Branch: `main`
   - Main file path: `app.py`
4. Add secrets (Settings → Secrets):

```toml
GEMINI_API_KEY = "your_key_here"
GEMINI_MODEL = "gemini-3-flash-preview"
DEBUG = "false"
```

## Configuration

`.env.example` documents required environment variables:
- `GEMINI_API_KEY` (required)
- `GEMINI_MODEL` (optional)
- `DEBUG` (optional)

Streamlit Cloud ignores `.env` and uses `st.secrets` instead.

## Project Structure

```
cognitive-breach-game/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Production dependencies
├── .env.example                    # Environment template (no secrets)
│
├── breach_engine/                  # Core game engine
│   ├── core/
│   ├── prompts/
│   ├── schemas/
│   └── api/
│
├── tools/                          # Testing and automation tools
├── logs/                           # Test transcripts and debug logs
├── data/                           # Evidence images and audio
└── assets/                         # UI assets
```

## Testing

Autonomous stress tests are available in `tools/` and logs are stored in `logs/`.
Example:

```bash
python -m tools.auto_interrogator --strategy relentless --max-turns 50
```

## License

TBD after hackathon.