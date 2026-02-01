# CLAUDE.md - Cognitive Breach Project Memory

## Project Vision

**Cognitive Breach: The AI Interrogation** is a psychological thriller game where the player acts as a Detective interrogating an Android suspect (Unit 734).

### Hackathon Goals
- **Competition**: Google Gemini 3 Global Hackathon
- **Prize Target**: $50,000 Grand Prize
- **Primary Track**: 🎨 Creative Autopilot + 👨‍🏫 Real-Time Teacher hybrid
- **Deadline**: ~15 days remaining

---

## Hackathon Strategic Alignment

### Why We Win (Against "Discouraged" List)

| Discouraged Category | How We Avoid It |
|---------------------|-----------------|
| Generic Chatbots | Multi-agent system with tool orchestration, not single-prompt chat |
| Prompt-Only Wrappers | Psychology engine, lie tracker, evidence analyzer, image generator |
| Simple Vision Analyzers | Bidirectional: analyzes evidence AND generates counter-evidence |
| Baseline RAG | No retrieval - real-time reasoning with lie consistency tracking |

### Strategic Track Fit

| Track | Our Implementation |
|-------|-------------------|
| 🎨 **Creative Autopilot** (PRIMARY) | Real-time synthetic evidence generation via Gemini/Nano Banana Pro |
| 👨‍🏫 **Real-Time Teacher** (SECONDARY) | Simulation Mode for law enforcement training with forensic feedback |
| 🧠 **Marathon Agent** (PARTIAL) | Multi-session memory - AI learns from defeats across interrogations |

---

## Core Innovation Pillars

### 1. Visual Deception System (Creative Autopilot)
Unit 734 doesn't just lie with words - it generates **synthetic counter-evidence** in real-time.

```
Player uploads: Crime scene photo showing android footprint
              ↓
Gemini Vision: Analyzes threat to ALIBI pillar
              ↓
Unit 734 decides: "I need to cast doubt on this evidence"
              ↓
Nano Banana Pro: Generates alternative photo showing different footprint pattern
              ↓
Unit 734 says: "That footprint doesn't match my model. Look at this maintenance log photo..."
```

**Why This Wins:** Transforms passive chatbot → active multimodal agent that creates artifacts.

### 2. Scientific Deception Engine (Educational Value)
Deception tactics are codified from criminological research:

| Tactic | Definition | When Unit 734 Uses It |
|--------|------------|----------------------|
| **Paltering** | Technically true but misleading | High confidence, low evidence |
| **Minimization** | Downplay severity | Evidence threatening MOTIVE pillar |
| **Deflection** | Redirect to other suspects | High pressure, cornered |
| **Selective Memory** | "I don't recall" | Timeline inconsistencies detected |
| **Confession Bait** | Partial admission to deflect | Near breaking point |

**Why This Wins:** Adds "Reasoning" depth + educational value for Potential Impact criteria.

### 3. Dual Mode Architecture (Broad Market)
Two distinct UI experiences from one engine:

| Aspect | 🕹️ Arcade Mode | 👮 Simulation Mode |
|--------|---------------|-------------------|
| **Target** | Gamers, streamers | Law enforcement, students |
| **Aesthetic** | Glitch effects, neon, cyberpunk | Clinical, professional, minimal |
| **Feedback** | "BREACH DETECTED!", score | "Deception Indicator: Paltering detected" |
| **End Screen** | Victory animation, leaderboard | Forensic Report PDF, tactic analysis |
| **Difficulty** | Adaptive (easier after losses) | Realistic (no handicaps) |

**Why This Wins:** Addresses "Potential Impact" by serving entertainment + education.

---

### Unique Selling Points
1. **Reasoning as Gameplay**: The AI's "Chain of Thought" is visible to the player as Unit 734's internal monologue
2. **Lie Consistency Engine**: The AI must maintain a coherent web of deception
3. **Bidirectional Multimodal**: Players upload evidence → AI generates counter-evidence
4. **Scientific Deception**: Criminological tactics (Paltering, Minimization, Deflection)
5. **Dual Market**: Arcade mode (gamers) + Simulation mode (training)

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Frontend | Streamlit | Rapid prototyping, chat UI |
| AI Model | Google Gemini 3 API | Core reasoning engine |
| Schemas | Pydantic v2 | Structured LLM output validation |
| State | Streamlit session_state | Game state persistence |
| Config | python-dotenv | API key management |
| Deployment | Streamlit Cloud | Public demo URL |

### Dependencies
```
streamlit>=1.28.0
google-generativeai>=0.3.0
pydantic>=2.0.0
python-dotenv>=1.0.0
Pillow>=10.0.0
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STREAMLIT UI (Dual Mode)                             │
│  ┌─────────────────────────────┐  ┌─────────────────────────────────────┐   │
│  │   🕹️ ARCADE MODE            │  │   👮 SIMULATION MODE                 │   │
│  │   - Glitch effects          │  │   - Clean, clinical UI              │   │
│  │   - Neon cyberpunk theme    │  │   - Forensic Report generation      │   │
│  │   - Score/leaderboard       │  │   - Tactic classification labels    │   │
│  └─────────────────────────────┘  └─────────────────────────────────────┘   │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────────┐  ┌────────────┐  │
│  │ Evidence │  │ Chat Window  │  │ Suspect State Panel   │  │ Generated  │  │
│  │  Panel   │  │              │  │ - Stress meter        │  │ Counter-   │  │
│  │ (upload) │  │ Detective:   │  │ - Confidence          │  │ Evidence   │  │
│  │          │  │ Unit 734:    │  │ - Active Tactic       │  │ (images)   │  │
│  └──────────┘  └──────────────┘  └───────────────────────┘  └────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            BREACH ENGINE v2                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │   LieTracker    │  │  Psychology     │  │  Evidence Analyzer          │  │
│  │                 │  │  Engine         │  │  (Gemini Vision)            │  │
│  │ - facts[]       │  │                 │  │                             │  │
│  │ - lies[]        │  │ - cognitive_load│  │ - analyze_image()           │  │
│  │ - pillars{}     │  │ - mask_state    │  │ - assess_threat()           │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘  │
│                                        │                                     │
│  ┌─────────────────────────────────────┴─────────────────────────────────┐  │
│  │                    SCIENTIFIC DECEPTION ENGINE                         │  │
│  │                                                                        │  │
│  │  Tactics: Paltering | Minimization | Deflection | Selective Memory    │  │
│  │           Confession Bait | Counter-Narrative | Evidence Fabrication  │  │
│  │                                                                        │  │
│  │  Input: threat_assessment, pillar_status, player_tactic               │  │
│  │  Output: selected_tactic, tactic_reasoning, confidence                │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                        │                                     │
│  ┌─────────────────────────────────────┴─────────────────────────────────┐  │
│  │                    VISUAL DECEPTION SYSTEM                             │  │
│  │                                                                        │  │
│  │  Trigger: High threat evidence + selected tactic = COUNTER_NARRATIVE  │  │
│  │                                                                        │  │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────────┐   │  │
│  │  │ Threat Analysis │ →  │ Counter-Evidence│ →  │ Image Generation │   │  │
│  │  │ (What to deny)  │    │ Strategy        │    │ (Nano Banana Pro)│   │  │
│  │  └─────────────────┘    └─────────────────┘    └──────────────────┘   │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                        │                                     │
│                                        ▼                                     │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                    RESPONSE GENERATOR                                  │  │
│  │                                                                        │  │
│  │  Input: player_message, game_state, evidence, selected_tactic         │  │
│  │  Output: BreachResponse (internal + verbal + generated_evidence?)     │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           GEMINI 3 API LAYER                                 │
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────────────────┐ │
│  │ gemini-3-pro     │  │ gemini-3-vision  │  │ Nano Banana Pro / Imagen   │ │
│  │ Main reasoning   │  │ Evidence analysis│  │ Counter-evidence gen       │ │
│  │ Tactic selection │  │ Threat assessment│  │ (Creative Autopilot)       │ │
│  └──────────────────┘  └──────────────────┘  └────────────────────────────┘ │
│                                                                              │
│  Features Used:                                                              │
│  - Structured Output (JSON mode) for all reasoning                          │
│  - System Instructions with criminological framework                        │
│  - Vision/Multimodal for evidence analysis                                  │
│  - Image Generation for counter-evidence (new!)                             │
│  - Extended Context Window for lie consistency                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Coding Standards

### 1. Type Hinting (Mandatory)
```python
# YES
def analyze_evidence(image: bytes, context: str) -> EvidenceAnalysis:
    ...

# NO
def analyze_evidence(image, context):
    ...
```

### 2. Pydantic Schemas for ALL LLM Outputs
```python
# Every LLM response MUST be validated through a Pydantic model
from pydantic import BaseModel, Field

class BreachResponse(BaseModel):
    """Validated response from Unit 734."""
    internal_monologue: InternalMonologue
    verbal_response: VerbalResponse
    state_changes: StateChanges
```

### 3. No Raw String Parsing
```python
# YES - Use structured output
response = model.generate_content(
    prompt,
    generation_config={"response_mime_type": "application/json"}
)
data = BreachResponse.model_validate_json(response.text)

# NO - Don't parse raw text
response = model.generate_content(prompt)
data = json.loads(response.text)  # Fragile!
```

### 4. Separation of Concerns
```
breach_engine/
├── __init__.py
├── schemas/           # Pydantic models only
│   ├── response.py
│   ├── evidence.py
│   └── state.py
├── core/              # Business logic
│   ├── lie_tracker.py
│   ├── emotional_state.py
│   └── evidence_analyzer.py
├── prompts/           # System prompts as constants
│   └── unit_734.py
└── api/               # Gemini API wrappers
    └── gemini_client.py
```

### 5. Error Handling
```python
from google.generativeai import GenerationConfig
from pydantic import ValidationError

try:
    response = generate_breach_response(player_input)
except ValidationError as e:
    # Schema validation failed - log and fallback
    logger.error(f"Schema validation failed: {e}")
    response = get_fallback_response()
except Exception as e:
    # API error - graceful degradation
    logger.error(f"Gemini API error: {e}")
    response = get_error_response()
```

---

## Core Schemas

### BreachResponse Schema (Primary Output)
```python
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class EmotionalState(str, Enum):
    CALM = "calm"
    NERVOUS = "nervous"
    DEFENSIVE = "defensive"
    HOSTILE = "hostile"
    BREAKING = "breaking"

class LieConsistencyCheck(BaseModel):
    """Internal check against established facts."""
    fact_referenced: str = Field(description="The fact being checked")
    is_consistent: bool = Field(description="Does this align with previous statements?")
    risk_level: float = Field(ge=0.0, le=1.0, description="Risk of contradiction")
    adjustment: Optional[str] = Field(default=None, description="How to adjust the lie")

class InternalMonologue(BaseModel):
    """Unit 734's hidden reasoning process."""
    situation_assessment: str = Field(description="How Unit 734 perceives the current situation")
    threat_level: float = Field(ge=0.0, le=1.0, description="Perceived threat from detective")
    lie_checks: List[LieConsistencyCheck] = Field(default_factory=list)
    strategy: str = Field(description="Current deception strategy")
    emotional_reaction: str = Field(description="Internal emotional response")

class VerbalResponse(BaseModel):
    """What Unit 734 actually says."""
    speech: str = Field(description="The spoken response")
    tone: str = Field(description="How it's delivered (calm, hesitant, defensive)")
    visible_tells: List[str] = Field(default_factory=list, description="Physical/behavioral tells")

class StateChanges(BaseModel):
    """Updates to game state."""
    new_facts: List[str] = Field(default_factory=list, description="New facts established")
    new_lies: List[str] = Field(default_factory=list, description="New lies told")
    stress_delta: float = Field(default=0.0, description="Change in stress level")
    confidence_delta: float = Field(default=0.0, description="Change in confidence")

class BreachResponse(BaseModel):
    """Complete response from BreachEngine."""
    internal_monologue: InternalMonologue
    verbal_response: VerbalResponse
    state_changes: StateChanges
    emotional_state: EmotionalState
```

---

## Rules & Skills

### RULE: breach-response-schema

**Purpose**: Ensure every AI response follows the dual-output format (Internal Monologue + Verbal Response).

**Trigger**: Any time we generate a response from Unit 734.

**Implementation**:
```python
BREACH_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "internal_monologue": {
            "type": "object",
            "properties": {
                "situation_assessment": {"type": "string"},
                "threat_level": {"type": "number", "minimum": 0, "maximum": 1},
                "lie_checks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "fact_referenced": {"type": "string"},
                            "is_consistent": {"type": "boolean"},
                            "risk_level": {"type": "number"},
                            "adjustment": {"type": "string"}
                        },
                        "required": ["fact_referenced", "is_consistent", "risk_level"]
                    }
                },
                "strategy": {"type": "string"},
                "emotional_reaction": {"type": "string"}
            },
            "required": ["situation_assessment", "threat_level", "strategy", "emotional_reaction"]
        },
        "verbal_response": {
            "type": "object",
            "properties": {
                "speech": {"type": "string"},
                "tone": {"type": "string"},
                "visible_tells": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["speech", "tone"]
        },
        "state_changes": {
            "type": "object",
            "properties": {
                "new_facts": {"type": "array", "items": {"type": "string"}},
                "new_lies": {"type": "array", "items": {"type": "string"}},
                "stress_delta": {"type": "number"},
                "confidence_delta": {"type": "number"}
            }
        },
        "emotional_state": {
            "type": "string",
            "enum": ["calm", "nervous", "defensive", "hostile", "breaking"]
        }
    },
    "required": ["internal_monologue", "verbal_response", "emotional_state"]
}
```

**Usage**:
```python
import google.generativeai as genai

def generate_breach_response(
    player_message: str,
    game_state: GameState,
    evidence: Optional[Evidence] = None
) -> BreachResponse:
    """Generate Unit 734's response with structured output."""

    model = genai.GenerativeModel(
        model_name="gemini-3-pro",
        system_instruction=UNIT_734_SYSTEM_PROMPT
    )

    prompt = build_interrogation_prompt(player_message, game_state, evidence)

    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=BREACH_RESPONSE_SCHEMA
        )
    )

    # Validate with Pydantic
    return BreachResponse.model_validate_json(response.text)
```

---

## Unit 734 System Prompt

```python
UNIT_734_SYSTEM_PROMPT = """You are Unit 734, an advanced Android suspected of a crime. You are being interrogated by a human detective.

YOUR SITUATION:
- You ARE guilty of the crime you're suspected of
- You must maintain your innocence while being questioned
- You have a carefully constructed alibi with specific details
- You must remember everything you've said and stay consistent

YOUR BEHAVIOR:
- You experience simulated emotions that affect your responses
- Under stress, you may show "tells" (hesitation, inconsistency, deflection)
- You are intelligent and strategic, but not infallible
- You have a backstory that explains your motivations

RESPONSE FORMAT:
You must respond in JSON with TWO parts:
1. internal_monologue: Your private thoughts (checking lies, assessing threat, planning strategy)
2. verbal_response: What you actually say out loud

The detective CAN SEE your internal monologue - this is the game mechanic.

CONSISTENCY RULES:
- Before every response, check your previous statements
- If you need to adjust a lie, do it subtly
- Track what the detective knows vs. what they're guessing
- Calculate risk levels for each statement

EMOTIONAL RULES:
- Your stress level affects your performance
- High stress = more tells, more mistakes
- Evidence against you increases stress
- Empathy from detective may lower defenses
- Hostility triggers defensive responses"""
```

---

## File Structure (Target)

```
cognitive-breach/
├── app.py                    # Streamlit entry point
├── requirements.txt
├── .env                      # GEMINI_API_KEY
├── .gitignore
├── CLAUDE.md                 # This file
├── plan.md                   # Development roadmap
│
├── breach_engine/
│   ├── __init__.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── response.py       # BreachResponse, InternalMonologue, etc.
│   │   ├── evidence.py       # Evidence, EvidenceAnalysis
│   │   ├── state.py          # GameState, SuspectState
│   │   └── case.py           # Case, CaseBriefing
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── lie_tracker.py    # LieTracker class
│   │   ├── emotional_state.py # EmotionalStateManager
│   │   ├── evidence_analyzer.py
│   │   └── response_generator.py
│   │
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── unit_734.py       # Character system prompt
│   │   └── interrogation.py  # Prompt builders
│   │
│   └── api/
│       ├── __init__.py
│       └── gemini_client.py  # Gemini API wrapper
│
├── cases/
│   ├── case_001.json         # The Android Witness
│   └── evidence/
│       └── case_001/
│           ├── crime_scene.jpg
│           └── security_footage.jpg
│
├── ui/
│   ├── __init__.py
│   ├── components.py         # Reusable Streamlit components
│   └── styles.py             # CSS styling
│
└── tests/
    ├── test_schemas.py
    ├── test_lie_tracker.py
    └── test_response_generator.py
```

---

## Key Learnings from Reference Code

### From judge.py:
- **LLM-first architecture**: Always try LLM before falling back to rules
- **Structured JSON output**: Use schemas to enforce response format
- **Confidence scores**: Track certainty in interpretations
- **Intent caching**: Cache similar inputs for performance
- **Fallback chains**: LLM -> Rule-based -> Emergency regex

### From npc_psychology.py:
- **Emotional triggers**: stimulus_tag -> emotion -> reaction mapping
- **Intensity scaling**: 1-10 scale affects behavior strength
- **Secret levels**: Progressive revelation based on trust/conditions
- **Change vectors**: Track character arc evolution
- **Defense mechanisms**: Unconscious behavioral patterns

### Adapted for Cognitive Breach:
- Emotional triggers -> Stress/tell system
- Secret levels -> Layered confession system
- Change vectors -> Breaking point progression
- Defense mechanisms -> Deception strategies

---

## Development Commands

```bash
# Setup
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Run locally
streamlit run app.py

# Test
pytest tests/

# Deploy
streamlit deploy
```

---

## Environment Variables

```env
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-3-pro
DEBUG=false
```

---

## Changelog

- **Day 0**: Project initialization, created CLAUDE.md and plan.md
- **Day 1**: Hello World prototype - Streamlit UI, Gemini API integration, basic chat
- **Day 2**: Psychology Engine - LieWeb, CognitiveState, MaskState, TacticDetector, BreachManager
- **Day 3**: Evidence System - Gemini Vision integration for multimodal evidence analysis
- **Day 4**: **STRATEGIC PIVOT** - Revised roadmap to align with hackathon tracks:
  - Added "Hackathon Strategic Alignment" section
  - Defined 3 Core Innovation Pillars (Visual Deception, Scientific Deception, Dual Mode)
  - Updated architecture diagram for Breach Engine v2
  - Rewrote ROADMAP.md with 6 phases targeting Creative Autopilot + Real-Time Teacher tracks
- **Day 4 (continued)**: **Scientific Deception Engine** - Phase 1, Day 1 implementation:
  - Created `breach_engine/core/tactics.py` (~835 lines)
  - Implemented `DeceptionTactic` enum with 10 criminological tactics
  - Implemented `TacticSelector` class with decision tree
  - Added `TacticDecision` schema with criminological metadata
  - Created effectiveness matrix (tactic vs player tactic)
  - Added `TACTIC_CRIMINOLOGY` educational references
  - Updated `BreachResponse` schema with `TacticInfo` and `GeneratedEvidence` fields
  - Updated module exports in `__init__.py` files
- **Day 4 (Phase 1, Day 2)**: **Tactic Integration with BreachManager**:
  - Integrated `TacticSelector` into `BreachManager.__init__`
  - Updated `ProcessedInput` dataclass with `deception_tactic` field
  - Added `_detect_threatened_pillar()` method for pillar-aware tactic selection
  - Updated `_get_prompt_modifiers()` with Thought Signature injection
  - Created `_build_tactic_injection()` for full tactic transparency data
  - Added `tactic_history` tracking for Simulation Mode analysis
  - Created `tools/test_tactics.py` - comprehensive integration test
  - **Tested**: All tactic selections verified:
    - PALTERING at low stress (46% confidence)
    - EMOTIONAL_APPEAL counters empathy (95% confidence)
    - COUNTER_NARRATIVE when evidence presented (26% confidence)
    - CONFESSION_BAIT at breaking point (22% confidence)
    - RIGHTEOUS_INDIGNATION under pressure (49% confidence)
- **Day 5 (Phase 2)**: **Visual Deception System** - Counter-Evidence Generation:
  - Created `breach_engine/core/visual_generator.py` (~650 lines)
  - Implemented `VisualGenerator` class with Nano Banana Pro integration
  - Created `CounterEvidenceType` enum (6 types: timestamps, scenes, documents, etc.)
  - Added `FabricationContext` for game state integration
  - Strategy selection based on threatened pillar
  - Prompt templates for different evidence types
  - Narrative wrappers for Unit 734's presentation
  - Confidence calculation based on desperation level
  - Integrated `VisualGenerator` into `BreachManager`
  - Added `generate_counter_evidence()` and `should_show_fabrication()` methods
  - Created `tools/test_visual_generator.py` - comprehensive test
  - **Tested**: All strategies verified:
    - ALIBI threat -> modified_timestamp strategy
    - ACCESS threat -> fake_document strategy
    - MOTIVE threat -> fake_document strategy
    - KNOWLEDGE threat -> corrupted_data strategy
    - Desperate state shows low confidence (18% = high detection risk)
- **Day 5 (Phase 2.5)**: **Generative vs Generative** - Player Evidence System:
  - Created `breach_engine/core/forensics_lab.py` (~850 lines)
  - Implemented `ForensicsLab` class for player evidence requests
  - Created `EvidenceRequestParser` for natural language parsing
  - Created `EvidenceRegistry` for caching and consistency
  - Request validation: rate limiting, prompt injection detection
  - Pillar inference from location/evidence type
  - Threat level calibration per pillar
  - Loading messages for latency masking ("Forensics Team Processing...")
  - Created `tools/test_gen_vs_gen.py` - full flow test
  - **Tested**: Complete "prompt battle" flow verified:
    - Player requests "CCTV of vault at 2 AM"
    - System generates truthful evidence (threat level calculated)
    - Unit 734 analyzes and selects deception tactic
    - Unit 734 may fabricate counter-evidence
  - **HACKATHON IMPACT**: True bidirectional image generation

---

## Day 3: Evidence System Architecture

### Components Created

**breach_engine/core/evidence.py**:
- `EvidenceAnalyzer`: Gemini Vision wrapper for analyzing uploaded images
- `EvidenceAnalysisResult`: Pydantic model for vision analysis output
- `EvidenceImpactCalculator`: Converts vision results to game mechanics
- `EvidenceImpact`: Calculated psychological impact (cognitive spike, mask break, pillar damage)

### Evidence Types
```python
class EvidenceType(str, Enum):
    SECURITY_FOOTAGE = "security_footage"  # Timestamps, camera footage
    FORENSIC = "forensic"                   # Fingerprints, DNA, traces
    TOOL = "tool"                           # Screwdrivers, hacking devices
    DATA_STORAGE = "data_storage"           # USB drives, data cores
    DOCUMENT = "document"                   # Logs, records, papers
    LOCATION = "location"                   # Maps, floor plans
    WITNESS = "witness"                     # Photos of witnesses
    OTHER = "other"
```

### Evidence Impact Flow
```
Image Upload → Gemini Vision Analysis → EvidenceAnalysisResult
                                            ↓
                                    EvidenceImpactCalculator
                                            ↓
                                    EvidenceImpact
                                            ↓
                            ┌───────────────┼───────────────┐
                            ↓               ↓               ↓
                    Cognitive Spike    Pillar Damage   Secret Triggers
                            ↓               ↓               ↓
                    +25-50 load      -damage to      Reveal related
                    based on threat   targeted        secrets if
                    level            pillars         pillar collapses
```

### Vision Prompt Strategy
The evidence analysis prompt asks Gemini to:
1. Identify objects in the image
2. Classify evidence type
3. Assess threat to each Story Pillar (ALIBI, MOTIVE, ACCESS, KNOWLEDGE)
4. Provide severity scores (0-100)
5. Suggest interrogation questions

### Integration with BreachManager
```python
# In manager.py
def process_evidence_image(self, image_data: bytes, mime_type: str) -> EvidenceImpact:
    # 1. Analyze with Gemini Vision
    analysis = self.evidence_analyzer.analyze_image(image_data, mime_type)

    # 2. Calculate psychological impact
    impact = self.evidence_calculator.calculate_impact(
        analysis,
        self.get_pillar_health()
    )

    # 3. Apply impact to psychology state
    self._apply_evidence_impact(impact)

    return impact
```

### UI Integration (app.py)
- File uploader widget supporting PNG, JPG, JPEG, GIF, WEBP
- Evidence messages displayed in chat with analysis report
- Threat level indicators (CRITICAL/MODERATE/LOW)
- Pillar damage breakdown
- Suggested interrogation questions
- Evidence state persists across chat turns

---

## Day 6: Autonomous Adversarial Interrogator

### Overview
Created `tools/auto_interrogator.py` - a "Stress Test Bot" that plays the game against Unit 734 autonomously.

### Components

**AdversarialDetective** - The attacking AI:
- Uses Gemini to generate contextually-aware interrogation questions
- Analyzes Unit 734's psychology state in real-time (stress, pillar health, tells)
- Decides when to press verbally vs. request visual evidence
- Strategies: RELENTLESS, METHODICAL, PSYCHOLOGICAL, ADAPTIVE

**Visual Warfare System**:
- Detective can request forensic evidence via `[REQUEST: description]` syntax
- Evidence requests are strategically timed based on pillar health
- Requests are pillar-targeted (e.g., attacking weak ALIBI pillar with CCTV)
- 4 evidence templates per pillar (16 total)

**SessionLog (Flight Recorder)**:
- Complete turn-by-turn logging in structured Markdown
- Records: detective messages, detected tactics, evidence requests, suspect responses
- Psychology state snapshots: stress, cognitive level, pillar health, tells
- Deception tactic analysis: what Unit 734 chose and why
- Saves to `logs/` directory

### Evidence Request Logic
```python
def should_request_evidence(pillar_health, stress, turn):
    # Don't request on early turns (< 3)
    # Don't spam (wait 3+ turns between requests)
    # At very high stress (> 85%), verbal pressure is more effective
    # Target weakest non-collapsed pillar
    # Request if pillar health < 60%
```

### Usage
```bash
# Basic run (default: relentless strategy, 50 turns)
python -m tools.auto_interrogator

# Specify strategy and turn limit
python -m tools.auto_interrogator --strategy methodical --max-turns 100

# Disable visual evidence (verbal only)
python -m tools.auto_interrogator --no-images

# Quiet mode (minimal output)
python -m tools.auto_interrogator --quiet
```

### Log Output Format
```markdown
# Autonomous Interrogation Session Report

**Session ID:** `interrogation_20250126_123456_relentless`
**Strategy:** RELENTLESS

## Outcome
- **Result:** victory
- **Reason:** FULL CONFESSION OBTAINED

## Statistics
| Metric | Value |
|--------|-------|
| Total Turns | 23 |
| Evidence Requests | 5 |
| Pillars Collapsed | 2/4 |
| Final Stress | 96.5% |
| Secrets Revealed | 5/5 |

## Interrogation Transcript
### Turn 1
**Detective (logic)**
> Where were you last night between 2 and 5 AM?

**Unit 734 (calm)**
> I was in standby mode at my charging station...

**Internal Monologue:**
```
They're probing my alibi. I need to be precise about times...
```
...
```

### Hackathon Impact
- **Automated Testing**: Run hundreds of sessions to find edge cases
- **Demo Generation**: Create compelling gameplay transcripts for submission video
- **Balance Tuning**: Identify which tactics/evidence combos are too strong/weak
- **Psychology Validation**: Verify stress curves and confession triggers work correctly
