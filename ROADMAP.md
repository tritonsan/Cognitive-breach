# Cognitive Breach - Hackathon Sprint Roadmap (REVISED)

## Project Status
- **Competition:** Google Gemini 3 Global Hackathon
- **Days Remaining:** ~15 days
- **Current State:** Core BreachEngine v1 complete (Psychology + Logic + Vision + Effects)
- **Strategic Pivot:** Align with "Creative Autopilot" + "Real-Time Teacher" tracks

---

## Strategic Pivot Summary

### What Changed
The original roadmap focused on polish and content. The **revised roadmap** prioritizes features that:
1. **Escape "Discouraged" list** - No longer a "generic chatbot"
2. **Hit Strategic Tracks** - Creative Autopilot (image gen) + Real-Time Teacher (training mode)
3. **Maximize Innovation Score** - Visual deception is novel, not incremental

### New Core Features
| Feature | Track Alignment | Priority |
|---------|-----------------|----------|
| Visual Deception System | 🎨 Creative Autopilot | **P0** |
| Scientific Deception Engine | Innovation/Impact | **P0** |
| Dual Mode UI (Arcade/Simulation) | 👨‍🏫 Real-Time Teacher | **P1** |
| Forensic Report Generator | Impact (Education) | **P2** |

---

## Revised 15-Day Development Roadmap

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   COGNITIVE BREACH - HACKATHON SPRINT (REVISED)              │
│                         ~15 Days Remaining                                   │
└─────────────────────────────────────────────────────────────────────────────┘

╔═════════════════════════════════════════════════════════════════════════════╗
║  PHASE 1: SCIENTIFIC DECEPTION ENGINE (Days 1-3)                            ║
║  Priority: P0 | Track: Innovation + Impact                                  ║
╠═════════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║  Day 1: Tactic System Architecture                                          ║
║         - Create breach_engine/core/tactics.py                              ║
║         - Define DeceptionTactic enum:                                      ║
║           PALTERING, MINIMIZATION, DEFLECTION, SELECTIVE_MEMORY,            ║
║           CONFESSION_BAIT, COUNTER_NARRATIVE, EVIDENCE_FABRICATION          ║
║         - Create TacticSelector class with decision tree                    ║
║         - Schema: TacticDecision (tactic, reasoning, confidence, trigger)   ║
║                                                                             ║
║  Day 2: Tactic Integration with Psychology                                  ║
║         - Connect TacticSelector to CognitiveState                          ║
║         - Tactic selection based on:                                        ║
║           • Pillar health (which defense is threatened)                     ║
║           • Cognitive load (high stress = simpler tactics)                  ║
║           • Player tactic history (adapt to interrogation style)            ║
║         - Update BreachResponse schema to include selected_tactic           ║
║                                                                             ║
║  Day 3: Tactic Visibility & Labels                                          ║
║         - Add tactic label to UI (Simulation Mode preview)                  ║
║         - Tactic reasoning in internal_monologue                            ║
║         - Unit tests for tactic selection logic                             ║
║                                                                             ║
╠═════════════════════════════════════════════════════════════════════════════╣
║  PHASE 2: VISUAL DECEPTION SYSTEM (Days 4-7)                                ║
║  Priority: P0 | Track: Creative Autopilot                                   ║
╠═════════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║  Day 4: Image Generation API Integration                                    ║
║         - Research: Nano Banana Pro availability in Gemini 3 API            ║
║         - Fallback: Imagen 3 via Vertex AI or gemini-2.0-flash-exp          ║
║         - Create breach_engine/api/image_generator.py                       ║
║         - Test basic image generation from text prompt                      ║
║                                                                             ║
║  Day 5: Counter-Evidence Strategy Engine                                    ║
║         - Create breach_engine/core/counter_evidence.py                     ║
║         - Schema: CounterEvidenceRequest (threat, denial_strategy, prompt)  ║
║         - Logic: Analyze uploaded evidence → Generate denial strategy       ║
║         - Example strategies:                                               ║
║           • Alibi photo: "Generate maintenance log showing different time"  ║
║           • Footprint: "Generate similar footprint from different model"    ║
║           • Document: "Generate alternative document with contradicting info"║
║                                                                             ║
║  Day 6: Counter-Evidence Integration                                        ║
║         - Connect to TacticSelector (trigger on COUNTER_NARRATIVE tactic)   ║
║         - Add generated_evidence field to BreachResponse                    ║
║         - UI: Display generated counter-evidence in chat                    ║
║         - Add "Unit 734 produces a document..." narrative wrapper           ║
║                                                                             ║
║  Day 7: Polish & Edge Cases                                                 ║
║         - Rate limiting for image generation                                ║
║         - Fallback when generation fails (text-only counter-narrative)      ║
║         - Cache generated images in session_state                           ║
║         - Test full flow: Upload evidence -> AI generates counter-evidence  ║
║                                                                             ║
╠═════════════════════════════════════════════════════════════════════════════╣
║  PHASE 2.5: GENERATIVE VS GENERATIVE (Day 7.5) [NEW - APPROVED]             ║
║  Priority: P0+ | Track: Creative Autopilot + Innovation                     ║
╠═════════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║  Day 7.5: Dynamic Player Evidence Generation (ForensicsLab)                 ║
║         - Player requests evidence via natural language:                    ║
║           "Get me CCTV footage of the server room at 3 AM"                  ║
║         - System generates TRUTHFUL evidence using Nano Banana Pro          ║
║         - Unit 734 analyzes generated evidence                              ║
║         - Unit 734 may fabricate COUNTER-evidence                           ║
║                                                                             ║
║  KEY INNOVATION: "Prompt Battle"                                            ║
║         - Player Evidence (Truth) vs Unit 734 Counter-Evidence (Lies)       ║
║         - Both sides use image generation                                   ║
║         - Latency masked as "Forensics Team Processing..."                  ║
║         - Unlimited replayability - no two playthroughs identical           ║
║                                                                             ║
║  Implementation: breach_engine/core/forensics_lab.py                        ║
║         - ForensicsLab class: Generates player-requested evidence           ║
║         - EvidenceRequestParser: NLP for evidence requests                  ║
║         - EvidenceRegistry: Cache & consistency tracking                    ║
║         - Request validation: Rate limiting, injection detection            ║
║                                                                             ║
╠═════════════════════════════════════════════════════════════════════════════╣
║  PHASE 3: DUAL MODE ARCHITECTURE (Days 8-10)                                ║
║  Priority: P1 | Track: Real-Time Teacher + Impact                           ║
╠═════════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║  Day 8: Mode Toggle Infrastructure                                          ║
║         - Add mode selector to UI (Arcade / Simulation)                     ║
║         - Create ui/themes/arcade.py and ui/themes/simulation.py            ║
║         - Mode stored in session_state.game_mode                            ║
║         - Conditional rendering based on mode                               ║
║                                                                             ║
║  Day 9: Arcade Mode Polish                                                  ║
║         - Glitch effects (already implemented) - ensure enabled             ║
║         - Neon/cyberpunk color scheme                                       ║
║         - Score system: Points for detecting lies, using evidence           ║
║         - "BREACH DETECTED!" animations                                     ║
║         - Victory/defeat screens with flair                                 ║
║                                                                             ║
║  Day 10: Simulation Mode Features                                           ║
║         - Clean, clinical UI theme (minimal, professional)                  ║
║         - Real-time tactic classification labels                            ║
║         - Deception indicators with confidence percentages                  ║
║         - No glitch effects, no gamification                                ║
║         - "Forensic Insight" sidebar with educational tooltips              ║
║                                                                             ║
╠═════════════════════════════════════════════════════════════════════════════╣
║  PHASE 4: FORENSIC REPORT SYSTEM (Days 11-12)                               ║
║  Priority: P2 | Track: Impact (Education)                                   ║
╠═════════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║  Day 11: Report Data Collection                                             ║
║         - Track all tactics used during session                             ║
║         - Record evidence presented and AI responses                        ║
║         - Calculate statistics: tactic frequency, success rate              ║
║         - Schema: ForensicReport (session_summary, tactic_analysis,         ║
║                                   evidence_timeline, recommendations)       ║
║                                                                             ║
║  Day 12: Report Generation & Export                                         ║
║         - Generate report at end of Simulation Mode session                 ║
║         - Render as formatted markdown in UI                                ║
║         - "Download Report" button (PDF via reportlab or markdown file)     ║
║         - Include: Tactic breakdown, timeline, learning points              ║
║                                                                             ║
╠═════════════════════════════════════════════════════════════════════════════╣
║  PHASE 5: HARDENING & INTEGRATION (Days 13-14)                              ║
║  Priority: P1 | Track: Technical Execution                                  ║
╠═════════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║  Day 13: Error Handling & Rate Limits                                       ║
║         - API timeout handling for all Gemini calls                         ║
║         - Rate limit protection (especially for image generation)           ║
║         - Graceful degradation when services unavailable                    ║
║         - Input validation and sanitization                                 ║
║                                                                             ║
║  Day 14: End-to-End Testing                                                 ║
║         - Full playthrough in Arcade Mode                                   ║
║         - Full playthrough in Simulation Mode                               ║
║         - Test counter-evidence generation with various inputs              ║
║         - Performance profiling and optimization                            ║
║         - Fix all critical bugs                                             ║
║                                                                             ║
╠═════════════════════════════════════════════════════════════════════════════╣
║  PHASE 6: DEMO PREP (Days 15+) [POSTPONED - Complete if time permits]       ║
║  Priority: P3 | Track: Presentation                                         ║
╠═════════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║  Day 15+: Demo Script & Video                                               ║
║         - Identify key "wow" moments for demo                               ║
║         - Script 3-minute video showing:                                    ║
║           1. Evidence upload → AI analyzes (Vision)                         ║
║           2. AI generates counter-evidence (Creative Autopilot highlight)   ║
║           3. Tactic classification in Simulation Mode (Educational value)   ║
║           4. Forensic Report generation (Impact)                            ║
║         - Record and edit demo video                                        ║
║                                                                             ║
║  Submission:                                                                ║
║         - Deploy to Streamlit Cloud / AI Studio                             ║
║         - Final README with Gemini Integration description                  ║
║         - Architecture diagram                                              ║
║         - Submit to Devpost                                                 ║
║                                                                             ║
╚═════════════════════════════════════════════════════════════════════════════╝
```

---

## Phase 1 Implementation Details

### Day 1: Tactic System Architecture

#### New Files to Create

**breach_engine/core/tactics.py**
```python
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List

class DeceptionTactic(str, Enum):
    """Criminological deception tactics based on research literature."""
    PALTERING = "paltering"              # Technically true but misleading
    MINIMIZATION = "minimization"        # Downplay severity
    DEFLECTION = "deflection"            # Redirect to other suspects
    SELECTIVE_MEMORY = "selective_memory" # "I don't recall"
    CONFESSION_BAIT = "confession_bait"  # Partial admission to deflect
    COUNTER_NARRATIVE = "counter_narrative" # Present alternative story
    EVIDENCE_FABRICATION = "evidence_fabrication" # Generate fake evidence

class TacticTrigger(BaseModel):
    """What triggered this tactic selection."""
    pillar_threatened: Optional[str] = Field(default=None)
    threat_level: float = Field(ge=0.0, le=1.0)
    player_tactic_detected: Optional[str] = Field(default=None)
    cognitive_load: float = Field(ge=0.0, le=100.0)

class TacticDecision(BaseModel):
    """AI's decision on which tactic to use."""
    selected_tactic: DeceptionTactic
    reasoning: str = Field(description="Why this tactic was chosen")
    confidence: float = Field(ge=0.0, le=1.0)
    trigger: TacticTrigger
    verbal_approach: str = Field(description="How to execute verbally")
    requires_evidence_generation: bool = Field(default=False)

class TacticSelector:
    """Selects appropriate deception tactic based on game state."""

    def select_tactic(
        self,
        pillar_health: dict[str, float],
        cognitive_load: float,
        player_tactic: Optional[str],
        evidence_threat: Optional[float]
    ) -> TacticDecision:
        # Implementation: Decision tree based on state
        pass
```

#### Schema Updates

**breach_engine/schemas/response.py** - Add to BreachResponse:
```python
class BreachResponse(BaseModel):
    internal_monologue: InternalMonologue
    verbal_response: VerbalResponse
    state_changes: StateChanges
    emotional_state: EmotionalState
    # NEW FIELDS
    selected_tactic: Optional[TacticDecision] = Field(default=None)
    generated_evidence: Optional[GeneratedEvidence] = Field(default=None)
```

---

## Phase 2 Implementation Details

### Day 4: Image Generation Research

#### API Options (Priority Order)

1. **Nano Banana Pro** (if available in Gemini 3 API)
   - Check: `gemini.google.com/api` for model availability
   - Ideal for hackathon alignment with "Creative Autopilot" track

2. **Imagen 3** via Vertex AI
   - Requires GCP project setup
   - `from google.cloud import aiplatform`
   - Higher quality but more setup

3. **gemini-2.0-flash-exp** with image generation
   - Native to Gemini API
   - May have experimental limitations

4. **Fallback: Text-only counter-narrative**
   - If all image gen fails, describe the fake evidence verbally

#### breach_engine/api/image_generator.py
```python
from typing import Optional
import google.generativeai as genai

class CounterEvidenceGenerator:
    """Generates synthetic evidence images to support Unit 734's lies."""

    def __init__(self, model_name: str = "nano-banana-pro"):
        self.model = genai.GenerativeModel(model_name)

    async def generate_counter_evidence(
        self,
        denial_strategy: str,
        original_evidence_description: str,
        style_hints: Optional[str] = None
    ) -> bytes:
        """Generate an image that contradicts the player's evidence."""
        prompt = self._build_generation_prompt(
            denial_strategy,
            original_evidence_description,
            style_hints
        )
        # Implementation depends on available API
        pass
```

---

## Risk Matrix (Updated)

| Feature | Impact | Risk | Effort | ROI | Notes |
|---------|--------|------|--------|-----|-------|
| Scientific Deception | HIGH | LOW | MEDIUM | **HIGH** | Differentiator, straightforward to implement |
| Visual Deception (Image Gen) | **VERY HIGH** | **HIGH** | HIGH | **VERY HIGH** | Creative Autopilot track, API availability uncertain |
| Dual Mode UI | HIGH | LOW | MEDIUM | **HIGH** | Addresses "broad market" criteria |
| Forensic Reports | MEDIUM | LOW | LOW | MEDIUM | Nice-to-have for education angle |
| Demo Video | HIGH | LOW | MEDIUM | HIGH | Required for submission |

---

## Success Metrics (Updated)

| Metric | Target | Why It Matters |
|--------|--------|----------------|
| Counter-Evidence Generation | Works in 80% of cases | Core "Creative Autopilot" feature |
| Tactic Classification Accuracy | 90%+ | Demonstrates reasoning depth |
| Mode Switch | Seamless UI toggle | Shows dual-market approach |
| Demo Video | 2-3 minutes | Required for judging |
| Judge "Wow" Moments | At least 4 | 1. Image gen, 2. Tactic labels, 3. Forensic report, 4. Glitch effects |

---

## Contingency Plans

### If Nano Banana Pro / Imagen unavailable:
1. Use gemini-2.0-flash-exp experimental image generation
2. Generate "document-style" images (text on paper background) which are easier
3. Fallback to text descriptions with [VISUAL: description] tags
4. Focus on other features, mention image gen as "future work" in submission

### If behind schedule:
- **Day 10:** Cut Forensic Report to basic text summary
- **Day 12:** Skip PDF export, keep markdown only
- **Day 14:** Focus demo on working features only

---

## Notes

- **Priority:** Visual Deception is the "headline feature" - gets us into Creative Autopilot track
- **Fallback:** Scientific Deception alone is still strong for Innovation criteria
- **Testing:** Use consistent evidence images in `data/` for reproducible demos
- **Deployment:** Target Streamlit Cloud for accessibility, AI Studio as backup
