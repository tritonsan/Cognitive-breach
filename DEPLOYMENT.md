# 🚀 Deployment Checklist - Cognitive Breach

## ✅ Pre-Deployment Status

### Files Created/Updated

#### ✅ `.gitignore`
**Status:** ✅ Created
**Purpose:** Protect secrets while showcasing AI testing logs

**What's BLOCKED (Protected):**
- ❌ `.env` (contains API key)
- ❌ `.streamlit/secrets.toml`
- ❌ `data/memory.json` (fresh start on cloud)
- ❌ `__pycache__/` and Python cache
- ❌ Virtual environments (`venv/`, `.venv/`)
- ❌ IDE files (`.vscode/`, `.idea/`)
- ❌ Audio files in logs (`*.mp3`, `*.wav` - too large)
- ❌ Windows temp files (`nul`)

**What's ALLOWED (Public):**
- ✅ `logs/*.md` - **Interrogation transcripts (hackathon showcase!)**
- ✅ `logs/*.json` - **Test results (proof of AI vs. AI testing)**
- ✅ `logs/images/*.png` - **Generated evidence images**
- ✅ `data/evidence_*.png` - Pre-generated evidence
- ✅ `data/evidence_manifest.json` - Evidence metadata
- ✅ All source code (`*.py`)
- ✅ Documentation (`README.md`, `CLAUDE.md`, etc.)
- ✅ Assets (`assets/**/*`)
- ✅ Screenshots

#### ✅ `requirements.txt`
**Status:** ✅ Updated
**Changes:**
- Removed Windows-specific packages (e.g., `pywin32`)
- Optimized for Streamlit Cloud (Linux environment)
- Kept only production dependencies
- Added inline documentation

**Dependencies:**
```
streamlit>=1.28.0
google-generativeai>=0.3.0
google-genai>=1.0.0
pydantic>=2.0.0
python-dotenv>=1.0.0
Pillow>=10.0.0
plotly>=5.18.0
SpeechRecognition>=3.10.0
```

#### ✅ `README.md`
**Status:** ✅ Created
**Contents:**
- Project overview and concept
- Quick start instructions (local + cloud)
- Testing methodology section (AI vs. AI)
- Explanation of logs/ directory for judges
- Game mechanics documentation
- Technical architecture diagram
- Hackathon alignment section
- Contact and license info

#### ✅ `.env.example`
**Status:** ✅ Created
**Purpose:** Template for users to create their own `.env`
**Contents:**
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3-flash-preview
DEBUG=false
```

---

## 📋 Deployment Steps

### Step 1: Verify Secrets are Protected
```bash
cd cognitive-breach-game

# Initialize git if not already done
git init

# Check what will be committed
git add -A
git status --short

# Verify .env is IGNORED
git status --ignored | grep ".env"  # Should show "!! .env"

# Verify logs are INCLUDED
git status --short | grep "logs/"   # Should show "A  logs/*.md"
```

**Expected Results:**
- `.env` should appear in ignored files (`!! .env`)
- Log markdown files should be staged (`A  logs/*.md`)
- Audio files should be ignored (`!! logs/*.wav`)

### Step 2: Remove Sensitive Data from Existing .env
Before committing, ensure your `.env` contains dummy values or is excluded:

```bash
# Your .env should look like:
GEMINI_API_KEY=your_key_here  # NOT the real key
```

Or better yet, the real `.env` should already be ignored by git.

### Step 3: Create GitHub Repository

**Option A: Via GitHub CLI**
```bash
cd cognitive-breach-game
gh repo create cognitive-breach-game --public --source=. --remote=origin
git push -u origin main
```

**Option B: Via GitHub Web UI**
1. Go to https://github.com/new
2. Name: `cognitive-breach-game`
3. Visibility: **Public** (required for Streamlit Cloud free tier)
4. Don't initialize with README (we already have one)
5. Create repository
6. Follow the commands provided:
```bash
cd cognitive-breach-game
git remote add origin https://github.com/yourusername/cognitive-breach-game.git
git branch -M main
git add -A
git commit -m "Initial commit: Cognitive Breach hackathon submission"
git push -u origin main
```

### Step 4: Deploy to Streamlit Cloud

1. **Go to:** https://share.streamlit.io
2. **Click:** "New app"
3. **Select:**
   - Repository: `yourusername/cognitive-breach-game`
   - Branch: `main`
   - Main file path: `app.py`
4. **Advanced settings:**
   - Python version: `3.10` or `3.11` (recommended)
5. **Click:** "Deploy"

### Step 5: Add Secrets to Streamlit Cloud

**CRITICAL STEP - The app won't work without this!**

1. In Streamlit Cloud, go to your app
2. Click the hamburger menu (⋮) → "Settings"
3. Go to the "Secrets" section
4. Add your secrets in TOML format:

```toml
GEMINI_API_KEY = "AIzaSyB7W791K30sTVPARNtc4LHh3gBmPXF1uyo"
GEMINI_MODEL = "gemini-3-flash-preview"
DEBUG = "false"
```

**⚠️ WARNING:** Replace the API key above with YOUR actual Gemini API key!

5. Click "Save"
6. The app will automatically redeploy with the secrets

### Step 6: Test the Deployment

1. Wait for the build to complete (~2-5 minutes)
2. Visit your app URL: `https://your-app-name.streamlit.app`
3. Test basic functionality:
   - ✅ Chat with Unit 734
   - ✅ Upload evidence (test image)
   - ✅ Check psychology state display
   - ✅ Generate counter-evidence (at high stress)

### Step 7: Update README with Live URL

Once deployed, update the README.md badge:

```markdown
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-actual-app-url.streamlit.app)
```

Commit and push:
```bash
git add README.md
git commit -m "Add live demo URL"
git push
```

---

## 🎯 Hackathon Submission Checklist

### Repository Must Include:
- ✅ Complete source code
- ✅ `README.md` with clear instructions
- ✅ `requirements.txt` for reproducibility
- ✅ `.gitignore` (no secrets in repo!)
- ✅ **logs/ directory with AI vs. AI transcripts**
- ✅ Evidence of testing methodology
- ✅ Documentation of Gemini features used

### Live Demo:
- ✅ Public Streamlit Cloud URL
- ✅ Working with real Gemini API
- ✅ Responsive and bug-free
- ✅ Mobile-friendly (Streamlit default)

### Submission Materials:
- ✅ GitHub repository URL
- ✅ Live demo URL
- ✅ Video demo (if required by hackathon rules)
- ✅ Project description highlighting:
  - 🎨 Creative Autopilot: Counter-evidence generation
  - 👨‍🏫 Real-Time Teacher: Forensic psychology training
  - 🧠 Reasoning: Scientific deception tactics
  - 🔍 Innovation: Bidirectional image generation

---

## 🐛 Troubleshooting

### Issue: "Module not found" on Streamlit Cloud
**Solution:** Check `requirements.txt` has correct package names and versions

### Issue: "API key not found"
**Solution:** Verify secrets are added in Streamlit Cloud settings (not in code!)

### Issue: "Rate limit exceeded"
**Solution:** Gemini API has rate limits. Add retry logic or use a paid tier.

### Issue: Logs not showing in repo
**Solution:** Check `.gitignore` whitelisting rules. Make sure `!logs/*.md` is present.

### Issue: App is slow on first load
**Expected behavior:** Streamlit Cloud "wakes up" apps after inactivity. First load may take 30s.

---

## 📊 What Judges Will See

### GitHub Repository:
1. **Source Code:** Full implementation of deception engine
2. **logs/ Directory:** Real interrogation transcripts showing:
   - Unit 734's internal monologue
   - Dynamic tactic selection
   - Counter-evidence generation
   - Psychological breaking points
3. **Documentation:** Clear architecture and methodology

### Live Demo:
1. **Interactive Gameplay:** Interrogate Unit 734 in real-time
2. **Visual Evidence Upload:** Test the Gemini Vision integration
3. **Counter-Evidence Generation:** See AI-generated defensive images
4. **Psychology Display:** Real-time stress, cognitive load, pillar health

### Hackathon Impact:
- **Not a wrapper:** Complex multi-agent system
- **Novel interaction:** AI as adversary, not assistant
- **Educational value:** Can train law enforcement
- **Technical depth:** Scientific deception tactics, lie consistency engine
- **Proof of quality:** Autonomous AI testing with documented results

---

## ✅ Final Checklist

Before submitting to hackathon:

- [ ] Git repository is public on GitHub
- [ ] No API keys or secrets in repository
- [ ] `.env` is in `.gitignore` and not tracked
- [ ] `logs/` directory is committed with transcripts
- [ ] README.md is complete and professional
- [ ] requirements.txt is accurate
- [ ] Streamlit Cloud deployment is live
- [ ] Gemini API key is added to Streamlit secrets
- [ ] Live demo URL is tested and working
- [ ] README badge points to live URL
- [ ] All features are functional (chat, evidence, counter-evidence)
- [ ] Mobile responsiveness is verified
- [ ] Project description highlights hackathon tracks
- [ ] Video demo is recorded (if required)

---

**Ready to deploy? Follow the steps above and good luck with the hackathon! 🚀**
