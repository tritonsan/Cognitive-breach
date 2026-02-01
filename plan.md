# Cognitive Breach: 19-Day Development Roadmap

## Project Overview
**Hackathon**: Google Gemini 3 Global Hackathon
**Prize Pool**: $100,000
**Deadline**: 19 days from start

## Phase 1: Foundation (Days 1-3)

### Day 1: Hello World Prototype
- [ ] Set up Python environment with dependencies
- [ ] Create `requirements.txt` (streamlit, google-generativeai, pydantic)
- [ ] Build minimal Streamlit UI with chat interface
- [ ] Connect to Gemini 3 API with basic generation
- [ ] Test "Unit 734 speaks" - basic response generation
- **Deliverable**: Working chat that talks to Gemini 3

### Day 2: BreachEngine Core
- [ ] Create `breach_engine/` package structure
- [ ] Define Pydantic schemas for AI responses:
  - `InternalMonologue` (reasoning, lie-checking)
  - `VerbalResponse` (what Unit 734 says)
  - `BreachResponse` (combined output)
- [ ] Implement structured output with Gemini 3
- [ ] System prompt for Unit 734's persona
- **Deliverable**: AI responds with visible "thinking" + speech

### Day 3: Memory & Consistency
- [ ] Create `LieTracker` class to store established facts
- [ ] Implement fact extraction from AI responses
- [ ] Add lie consistency checking in internal monologue
- [ ] Build contradiction detection system
- **Deliverable**: AI maintains consistent story across turns

## Phase 2: Game Mechanics (Days 4-7)

### Day 4: Evidence System (Multimodal)
- [ ] Add image upload to Streamlit UI
- [ ] Integrate Gemini 3 Vision for evidence analysis
- [ ] Create `Evidence` schema (type, description, implications)
- [ ] AI reacts to visual evidence (nervousness, deflection)
- **Deliverable**: Upload images as "evidence" that AI analyzes

### Day 5: Emotional State System
- [ ] Adapt emotional triggers from reference code
- [ ] Create `SuspectState` model (stress, confidence, hostility)
- [ ] Emotional responses affect internal monologue
- [ ] Visible "tells" in verbal responses when stressed
- **Deliverable**: AI shows emotional reactions

### Day 6: Interrogation Tactics
- [ ] Implement player tactic detection
- [ ] Tactics: Pressure, Empathy, Evidence, Bluff, Silence
- [ ] Different AI reactions per tactic
- [ ] Effectiveness varies based on suspect state
- **Deliverable**: Strategic interrogation gameplay

### Day 7: Secret & Confession System
- [ ] Adapt secret levels from reference code
- [ ] Create Unit 734's backstory with layered secrets
- [ ] Implement confession triggers
- [ ] Victory conditions (full confession vs partial)
- **Deliverable**: Win/lose conditions working

## Phase 3: Polish & Depth (Days 8-12)

### Day 8: Case File System
- [ ] Create pre-built case scenarios
- [ ] Case briefing screen before interrogation
- [ ] Evidence library per case
- [ ] Multiple suspects/cases for replayability
- **Deliverable**: Complete case structure

### Day 9: UI/UX Enhancement
- [ ] Dark interrogation room aesthetic
- [ ] Split view: Evidence panel | Chat | Suspect state
- [ ] Typing indicators and response timing
- [ ] Sound design (ambient, stress cues)
- **Deliverable**: Immersive interface

### Day 10: Reasoning Visualization
- [ ] Collapsible "AI Thinking" panel
- [ ] Highlight contradictions in real-time
- [ ] Show lie confidence percentages
- [ ] Evidence correlation display
- **Deliverable**: Transparent AI reasoning (showcase Gemini 3)

### Day 11: Advanced Lie Mechanics
- [ ] Nested lies (lies to cover lies)
- [ ] Alibi timeline system
- [ ] Character relationships graph
- [ ] Memory recall with inconsistency risk
- **Deliverable**: Deep deception mechanics

### Day 12: Multiple Endings
- [ ] Implement ending states:
  - Full confession (best ending)
  - Partial truth
  - Suspect breaks down
  - Detective fails
  - Plot twist endings
- [ ] Ending cinematics/summaries
- **Deliverable**: Narrative payoff

## Phase 4: Content & Testing (Days 13-16)

### Day 13: Case Content
- [ ] Write 3 complete case scenarios
- [ ] Create evidence image assets
- [ ] Character backstory documents
- [ ] Dialogue variety and personality

### Day 14: Playtesting Round 1
- [ ] Internal testing of all cases
- [ ] Bug fixes and edge cases
- [ ] Balance interrogation difficulty
- [ ] Prompt engineering refinement

### Day 15: Playtesting Round 2
- [ ] External playtester feedback
- [ ] UX improvements
- [ ] Performance optimization
- [ ] Mobile responsiveness check

### Day 16: Content Polish
- [ ] Writing pass on all AI responses
- [ ] Add tutorial/hints for new players
- [ ] Accessibility features
- [ ] Loading states and error handling

## Phase 5: Submission (Days 17-19)

### Day 17: Documentation
- [ ] Write Gemini Integration description (~200 words)
- [ ] Create architecture diagram
- [ ] Document key features
- [ ] Prepare code repository

### Day 18: Demo Video
- [ ] Script 3-minute demo
- [ ] Record gameplay footage
- [ ] Edit with voiceover
- [ ] Highlight Gemini 3 features:
  - Reasoning capabilities (internal monologue)
  - Multimodal (evidence analysis)
  - Consistency maintenance

### Day 19: Final Submission
- [ ] Deploy to public URL (Streamlit Cloud or AI Studio)
- [ ] Final testing of deployed version
- [ ] Submit to Devpost
- [ ] Celebrate!

## Technical Stack
- **Frontend**: Streamlit
- **AI**: Google Gemini 3 API (gemini-3-pro)
- **Schemas**: Pydantic v2
- **State**: Streamlit session state
- **Deployment**: Streamlit Cloud / AI Studio Apps

## Key Innovation Points
1. **Reasoning as Gameplay**: Internal monologue visible to player
2. **Lie Consistency Engine**: AI maintains coherent deception
3. **Multimodal Evidence**: Image analysis affects interrogation
4. **Emotional AI State**: Stress/confidence affects responses
5. **Structured Output**: JSON schemas ensure game-compatible responses

## Risk Mitigation
- **API Rate Limits**: Implement caching, optimize prompts
- **Hallucination**: Strong schema enforcement, fact tracking
- **Latency**: Async calls, streaming responses
- **Cost**: Use gemini-3-flash for development, pro for demo
