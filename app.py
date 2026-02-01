"""
Cognitive Breach: The AI Interrogation
Main Streamlit Application

A psychological thriller game where you interrogate an Android suspect.
Built for the Google Gemini 3 Global Hackathon.

Day 2: Integrated with BreachPsychology system.
"""

import streamlit as st
from dotenv import load_dotenv
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from breach_engine.schemas.state import GameState, SuspectState
from breach_engine.schemas.response import EmotionalState
from breach_engine.api.gemini_client import GeminiClient
from breach_engine.core.manager import BreachManager
from breach_engine.core.psychology import (
    create_unit_734_psychology,
    CognitiveLevel,
    StoryPillar,
)
from breach_engine.prompts.unit_734 import CASE_001_CONTEXT
from breach_engine.core.evidence import EvidenceType
from breach_engine.core.security import sanitize_for_display
from breach_engine.core.forensics_lab import (
    create_forensics_lab,
    ForensicsLab,
    format_evidence_for_ui,
)

# Simulation playback support
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
import textwrap

# Page configuration
st.set_page_config(
    page_title="Cognitive Breach",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ===== THE COLD INTERFACE - CSS FOUNDATION =====
# Military-grade forensic terminal aesthetic (Blade Runner 2049 meets Detroit: Become Human)
st.markdown("""
<style>
    /* ===== GOOGLE FONTS ===== */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@300;400;500;600;700&display=swap');

    /* ===== CSS CUSTOM PROPERTIES ===== */
    :root {
        --void-blue: #0b1016;
        --ice-blue: #00f3ff;
        --muted-slate: #485366;
        --warning-red: #ff2a6d;
        --ice-blue-20: rgba(0, 243, 255, 0.2);
        --ice-blue-10: rgba(0, 243, 255, 0.1);
        --ice-blue-05: rgba(0, 243, 255, 0.05);
        --glass-bg: rgba(11, 16, 22, 0.85);
        --glass-border: 1px solid var(--ice-blue-20);
        --font-header: 'Orbitron', monospace;
        --font-data: 'JetBrains Mono', monospace;
    }

    /* ===== HIDE STREAMLIT CHROME ===== */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    [data-testid="stSidebar"] { display: none !important; }
    .stDeployButton { display: none !important; }

    /* ===== BASE STYLES ===== */
    .stApp {
        background-color: var(--void-blue);
        background-image:
            linear-gradient(var(--ice-blue-05) 1px, transparent 1px),
            linear-gradient(90deg, var(--ice-blue-05) 1px, transparent 1px);
        background-size: 50px 50px;
    }

    /* Sharp corners everywhere - override Streamlit defaults */
    .stApp *, .stApp *::before, .stApp *::after {
        border-radius: 0px !important;
    }

    /* ===== COMMAND CENTER HEADER ===== */
    .command-header {
        font-family: var(--font-header);
        color: var(--ice-blue);
        text-align: center;
        padding: 1.5rem 1rem;
        border-bottom: var(--glass-border);
        background: var(--glass-bg);
        margin-bottom: 1rem;
        text-transform: uppercase;
        letter-spacing: 0.3em;
    }

    .command-header h1 {
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 0 0 20px var(--ice-blue);
    }

    .command-header p {
        font-family: var(--font-data);
        font-size: 0.75rem;
        color: var(--muted-slate);
        margin: 0.5rem 0 0 0;
        letter-spacing: 0.2em;
    }

    /* ===== DOSSIER PANEL (Column 1) ===== */
    .dossier-panel {
        background: var(--glass-bg);
        border: var(--glass-border);
        padding: 1rem;
        height: 100%;
        font-family: var(--font-data);
    }

    .dossier-section {
        margin-bottom: 1.5rem;
    }

    .dossier-label {
        font-family: var(--font-header);
        font-size: 0.7rem;
        color: var(--muted-slate);
        text-transform: uppercase;
        letter-spacing: 0.15em;
        margin-bottom: 0.5rem;
        border-bottom: 1px solid var(--ice-blue-10);
        padding-bottom: 0.25rem;
    }

    /* Mugshot Frame */
    .mugshot-frame {
        border: 2px solid var(--ice-blue-20);
        background: var(--void-blue);
        padding: 1rem;
        text-align: center;
        margin-bottom: 1rem;
    }

    .mugshot-frame .unit-id {
        font-family: var(--font-header);
        font-size: 1rem;
        color: var(--ice-blue);
        letter-spacing: 0.2em;
    }

    .mugshot-frame .model-id {
        font-family: var(--font-data);
        font-size: 0.7rem;
        color: var(--muted-slate);
        margin-top: 0.25rem;
    }

    /* ===== CUSTOM SEGMENTED COGNITIVE BAR ===== */
    .cognitive-bar-container {
        margin: 0.75rem 0;
    }

    .cognitive-bar-label {
        display: flex;
        justify-content: space-between;
        font-family: var(--font-data);
        font-size: 0.75rem;
        margin-bottom: 0.5rem;
    }

    .cognitive-bar-label .level {
        color: var(--ice-blue);
        font-weight: 600;
    }

    .cognitive-bar-label .percentage {
        color: var(--muted-slate);
    }

    .cognitive-bar-segments {
        display: flex;
        gap: 2px;
        height: 20px;
    }

    .cog-segment {
        flex: 1;
        background: var(--muted-slate);
        border: 1px solid var(--ice-blue-20);
        transition: all 0.3s ease;
    }

    .cog-segment.filled {
        background: linear-gradient(180deg, var(--ice-blue) 0%, #005f66 100%);
        box-shadow: 0 0 5px var(--ice-blue);
    }

    .cog-segment.critical {
        background: var(--warning-red);
        box-shadow: 0 0 10px var(--warning-red);
        animation: criticalPulse 0.5s ease-in-out infinite;
    }

    /* ===== PILLAR GRID (2x2) ===== */
    .pillar-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 6px;
    }

    .pillar-indicator {
        padding: 8px;
        border: 1px solid var(--ice-blue-20);
        background: var(--void-blue);
        font-family: var(--font-data);
        font-size: 0.7rem;
        text-align: center;
        transition: all 0.3s ease;
    }

    .pillar-indicator .pillar-name {
        font-family: var(--font-header);
        font-size: 0.6rem;
        color: var(--muted-slate);
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 4px;
    }

    .pillar-indicator .pillar-health {
        font-size: 0.85rem;
        font-weight: 600;
    }

    .pillar-indicator.active {
        border-color: var(--ice-blue);
        box-shadow: 0 0 8px var(--ice-blue-20);
    }

    .pillar-indicator.active .pillar-health {
        color: var(--ice-blue);
    }

    .pillar-indicator.weakened {
        border-color: #ffc107;
    }

    .pillar-indicator.weakened .pillar-health {
        color: #ffc107;
    }

    .pillar-indicator.critical {
        border-color: var(--warning-red);
        animation: criticalPulse 1s ease-in-out infinite;
    }

    .pillar-indicator.critical .pillar-health {
        color: var(--warning-red);
    }

    .pillar-indicator.collapsed {
        opacity: 0.4;
        border-color: var(--muted-slate);
    }

    .pillar-indicator.collapsed .pillar-name,
    .pillar-indicator.collapsed .pillar-health {
        text-decoration: line-through;
        color: var(--muted-slate);
    }

    /* ===== ARENA CONTAINER (Column 2) ===== */
    .arena-container {
        background: var(--glass-bg);
        border: var(--glass-border);
        padding: 1rem;
        min-height: 70vh;
        font-family: var(--font-data);
    }

    .arena-header {
        font-family: var(--font-header);
        font-size: 0.8rem;
        color: var(--ice-blue);
        text-transform: uppercase;
        letter-spacing: 0.2em;
        text-align: center;
        padding-bottom: 0.75rem;
        border-bottom: var(--glass-border);
        margin-bottom: 1rem;
    }

    /* ===== TRANSCRIPT LOG ENTRIES ===== */
    .transcript-entry {
        padding: 0.75rem;
        margin-bottom: 0.75rem;
        border: 1px solid var(--ice-blue-10);
        background: rgba(0, 0, 0, 0.3);
        animation: fadeIn 0.3s ease-out;
    }

    .transcript-entry.detective {
        text-align: left;
        border-left: 3px solid var(--ice-blue);
    }

    .transcript-entry.detective .speaker {
        font-family: var(--font-header);
        font-size: 0.7rem;
        color: var(--ice-blue);
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.5rem;
    }

    .transcript-entry.detective .content {
        font-family: var(--font-data);
        font-size: 0.85rem;
        color: var(--ice-blue);
        line-height: 1.5;
    }

    .transcript-entry.suspect {
        text-align: right;
        border-right: 3px solid #ffffff;
        border-left: none;
    }

    .transcript-entry.suspect .speaker {
        font-family: var(--font-header);
        font-size: 0.7rem;
        color: var(--muted-slate);
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.5rem;
    }

    .transcript-entry.suspect .content {
        font-family: var(--font-data);
        font-size: 0.85rem;
        color: #ffffff;
        line-height: 1.5;
    }

    .transcript-entry .tone-badge {
        display: inline-block;
        font-size: 0.6rem;
        padding: 2px 6px;
        background: var(--ice-blue-10);
        color: var(--muted-slate);
        margin-left: 8px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .transcript-entry .tactic-badge {
        display: inline-block;
        font-size: 0.6rem;
        padding: 2px 6px;
        margin-left: 8px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .tactic-pressure { background: var(--warning-red); color: white; }
    .tactic-empathy { background: var(--ice-blue); color: var(--void-blue); }
    .tactic-logic { background: #3498db; color: white; }
    .tactic-bluff { background: #9b59b6; color: white; }
    .tactic-evidence { background: #e74c3c; color: white; }
    .tactic-silence { background: var(--muted-slate); color: white; }

    /* File Transmission Overlay */
    .file-transmission-overlay {
        background: rgba(0, 243, 255, 0.05);
        border: 2px solid var(--ice-blue);
        padding: 1rem;
        margin: 0.75rem 0;
        text-align: center;
        position: relative;
        overflow: hidden;
    }

    .file-transmission-overlay::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(0, 243, 255, 0.2), transparent);
        animation: transmissionSweep 2s ease-in-out infinite;
    }

    .file-transmission-overlay .label {
        font-family: var(--font-header);
        font-size: 0.8rem;
        color: var(--ice-blue);
        text-transform: uppercase;
        letter-spacing: 0.2em;
    }

    @keyframes transmissionSweep {
        0% { left: -100%; }
        100% { left: 100%; }
    }

    /* ===== ANALYST HUD (Column 3) ===== */
    .analyst-hud {
        background: var(--glass-bg);
        border: var(--glass-border);
        padding: 1rem;
        height: 100%;
        font-family: var(--font-data);
        position: relative;
        overflow: hidden;
    }

    .analyst-hud-header {
        font-family: var(--font-header);
        font-size: 0.7rem;
        color: var(--ice-blue);
        text-transform: uppercase;
        letter-spacing: 0.15em;
        text-align: center;
        padding-bottom: 0.5rem;
        border-bottom: var(--glass-border);
        margin-bottom: 0.75rem;
    }

    .analyst-log-container {
        height: calc(100% - 3rem);
        overflow-y: auto;
        padding-right: 0.5rem;
    }

    /* Scrollbar styling */
    .analyst-log-container::-webkit-scrollbar {
        width: 4px;
    }

    .analyst-log-container::-webkit-scrollbar-track {
        background: var(--void-blue);
    }

    .analyst-log-container::-webkit-scrollbar-thumb {
        background: var(--ice-blue-20);
    }

    .analyst-log-entry {
        font-family: var(--font-data);
        font-size: 0.7rem;
        padding: 0.4rem 0;
        border-bottom: 1px solid var(--ice-blue-05);
        line-height: 1.4;
    }

    .analyst-log-entry.analyzing {
        color: var(--muted-slate);
    }

    .analyst-log-entry.trap {
        color: #ffc107;
    }

    .analyst-log-entry.opportunity {
        color: #00ff9d;
    }

    .analyst-log-entry.reid-phase {
        color: var(--ice-blue);
    }

    .analyst-log-entry.warning {
        color: var(--warning-red);
    }

    .blinking-cursor {
        display: inline-block;
        width: 8px;
        height: 14px;
        background: var(--ice-blue);
        animation: blink 1s step-end infinite;
        vertical-align: middle;
        margin-left: 4px;
    }

    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0; }
    }

    /* Scanline Overlay */
    .scanline-overlay {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        background: repeating-linear-gradient(
            0deg,
            transparent 0px,
            transparent 2px,
            rgba(0, 243, 255, 0.03) 2px,
            rgba(0, 243, 255, 0.03) 4px
        );
        animation: scanlineMove 10s linear infinite;
    }

    @keyframes scanlineMove {
        0% { background-position: 0 0; }
        100% { background-position: 0 100px; }
    }

    /* ===== INTERNAL MONOLOGUE BOX ===== */
    .monologue-box {
        background: rgba(255, 42, 109, 0.05);
        border: 1px solid rgba(255, 42, 109, 0.2);
        border-left: 3px solid var(--warning-red);
        padding: 1rem;
        margin: 0.5rem 0;
        font-style: italic;
        color: var(--muted-slate);
        font-family: var(--font-data);
        font-size: 0.8rem;
    }

    /* ===== EVIDENCE STYLING ===== */
    .evidence-alert {
        background: rgba(255, 42, 109, 0.1);
        border: 2px solid var(--warning-red);
        padding: 1rem;
        margin: 0.75rem 0;
        animation: pulse 2s infinite;
    }

    .evidence-relevant {
        border-color: var(--warning-red);
    }

    .evidence-irrelevant {
        border-color: var(--muted-slate);
        background: rgba(72, 83, 102, 0.1);
    }

    .threat-high { color: var(--warning-red); font-weight: bold; }
    .threat-medium { color: #ffc107; }
    .threat-low { color: var(--muted-slate); }

    .pillar-damage-item {
        background: var(--void-blue);
        padding: 0.5rem;
        margin: 0.2rem 0;
        border-left: 3px solid var(--warning-red);
        font-family: var(--font-data);
        font-size: 0.75rem;
    }

    /* ===== KEYFRAME ANIMATIONS ===== */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes criticalPulse {
        0%, 100% { box-shadow: 0 0 5px rgba(255, 42, 109, 0.5); }
        50% { box-shadow: 0 0 20px rgba(255, 42, 109, 0.8); }
    }

    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(255, 42, 109, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(255, 42, 109, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 42, 109, 0); }
    }

    .glitch-text {
        animation: glitch-skew 0.5s infinite linear alternate-reverse;
    }

    .glitch-intense {
        animation: glitch-skew 0.2s infinite linear alternate-reverse;
        text-shadow: -1px 0 var(--warning-red), 1px 0 var(--ice-blue);
    }

    @keyframes glitch-skew {
        0% { transform: skew(0deg); }
        20% { transform: skew(-1deg); }
        40% { transform: skew(1deg); }
        60% { transform: skew(0deg); }
        80% { transform: skew(1deg); }
        100% { transform: skew(-1deg); }
    }

    /* ===== GAME OVER SCREENS ===== */
    .game-over-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: rgba(11, 16, 22, 0.98);
        z-index: 9999;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        animation: fadeIn 1s ease-out;
    }

    .victory-title {
        font-size: 3rem;
        font-family: var(--font-header);
        color: var(--ice-blue);
        text-shadow: 0 0 30px rgba(0, 243, 255, 0.5);
        animation: victoryGlow 2s ease-in-out infinite;
        text-transform: uppercase;
        letter-spacing: 0.3em;
    }

    .defeat-title {
        font-size: 3rem;
        font-family: var(--font-header);
        color: var(--warning-red);
        text-shadow: 0 0 30px rgba(255, 42, 109, 0.5);
        animation: defeatPulse 1.5s ease-in-out infinite;
        text-transform: uppercase;
        letter-spacing: 0.3em;
    }

    .partial-title {
        font-size: 3rem;
        font-family: var(--font-header);
        color: #ffc107;
        text-shadow: 0 0 30px rgba(255, 193, 7, 0.5);
        text-transform: uppercase;
        letter-spacing: 0.3em;
    }

    @keyframes victoryGlow {
        0%, 100% { text-shadow: 0 0 30px rgba(0, 243, 255, 0.5); }
        50% { text-shadow: 0 0 50px rgba(0, 243, 255, 0.8), 0 0 100px rgba(0, 243, 255, 0.3); }
    }

    @keyframes defeatPulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }

    .game-over-reason {
        font-size: 1.25rem;
        font-family: var(--font-data);
        color: var(--muted-slate);
        margin-top: 1rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }

    .game-over-subtitle {
        font-size: 0.9rem;
        font-family: var(--font-data);
        color: var(--muted-slate);
        margin-top: 0.5rem;
        max-width: 600px;
        text-align: center;
        opacity: 0.7;
    }

    .game-stats {
        margin-top: 2rem;
        padding: 1.5rem;
        background: var(--glass-bg);
        border: var(--glass-border);
        font-family: var(--font-data);
    }

    .stat-item {
        display: flex;
        justify-content: space-between;
        padding: 0.5rem 0;
        border-bottom: 1px solid var(--ice-blue-10);
    }

    .stat-label {
        color: var(--muted-slate);
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .stat-value {
        color: var(--ice-blue);
        font-weight: 600;
    }

    /* ===== RAPPORT & MISC ===== */
    .rapport-bar {
        height: 4px;
        background: var(--muted-slate);
        margin-top: 0.5rem;
    }

    .rapport-fill {
        height: 100%;
        background: var(--ice-blue);
        transition: width 0.3s ease;
    }

    .secret-revealed {
        background: var(--void-blue);
        border: 1px solid var(--warning-red);
        padding: 0.5rem;
        margin: 0.3rem 0;
        font-family: var(--font-data);
        font-size: 0.75rem;
    }

    /* ===== STREAMLIT OVERRIDES ===== */
    .stTextInput > div > div > input {
        background: var(--void-blue) !important;
        border: var(--glass-border) !important;
        color: var(--ice-blue) !important;
        font-family: var(--font-data) !important;
    }

    .stButton > button {
        background: var(--glass-bg) !important;
        border: var(--glass-border) !important;
        color: var(--ice-blue) !important;
        font-family: var(--font-header) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.1em !important;
        transition: all 0.2s ease !important;
    }

    .stButton > button:hover {
        background: var(--ice-blue-10) !important;
        box-shadow: 0 0 15px var(--ice-blue-20) !important;
    }

    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, var(--ice-blue), #005f66) !important;
    }

    .stExpander {
        background: var(--glass-bg) !important;
        border: var(--glass-border) !important;
    }

    /* Neural monitor chart override */
    .stPlotlyChart {
        background: transparent !important;
    }

    /* Mobile responsive */
    @media (max-width: 768px) {
        .command-header h1 {
            font-size: 1.25rem;
            letter-spacing: 0.15em;
        }

        .transcript-entry .content {
            font-size: 0.8rem;
        }

        .pillar-indicator {
            padding: 6px;
        }

        .pillar-indicator .pillar-name {
            font-size: 0.5rem;
        }

        .pillar-indicator .pillar-health {
            font-size: 0.75rem;
        }
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if "game_state" not in st.session_state:
        st.session_state.game_state = GameState(
            session_id="session_001",
            case_id="case_001",
            suspect_state=SuspectState()
        )

    if "breach_manager" not in st.session_state:
        psychology = create_unit_734_psychology()
        st.session_state.breach_manager = BreachManager(psychology)

    if "gemini_client" not in st.session_state:
        try:
            st.session_state.gemini_client = GeminiClient()
        except Exception as e:
            st.error(f"Failed to initialize Gemini client: {e}")
            st.session_state.gemini_client = None

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "last_tactic" not in st.session_state:
        st.session_state.last_tactic = None

    if "last_processed" not in st.session_state:
        st.session_state.last_processed = None

    if "last_evidence_impact" not in st.session_state:
        st.session_state.last_evidence_impact = None

    # Store the actual evidence image data for multimodal vision
    if "last_evidence_image_data" not in st.session_state:
        st.session_state.last_evidence_image_data = None
    if "last_evidence_image_mime" not in st.session_state:
        st.session_state.last_evidence_image_mime = "image/png"

    if "evidence_count" not in st.session_state:
        st.session_state.evidence_count = 0

    if "psychology_history" not in st.session_state:
        st.session_state.psychology_history = []

    if "game_over" not in st.session_state:
        st.session_state.game_over = False

    if "game_result" not in st.session_state:
        st.session_state.game_result = None

    # Tracking for evolving suspect (memory system)
    if "tactics_used" not in st.session_state:
        st.session_state.tactics_used = {}

    if "evidence_presented" not in st.session_state:
        st.session_state.evidence_presented = []

    if "game_recorded" not in st.session_state:
        st.session_state.game_recorded = False

    # Simulation playback mode
    if "simulation_mode" not in st.session_state:
        st.session_state.simulation_mode = False

    if "simulation_transcript" not in st.session_state:
        st.session_state.simulation_transcript = None

    if "simulation_turn" not in st.session_state:
        st.session_state.simulation_turn = 0

    if "simulation_speed" not in st.session_state:
        st.session_state.simulation_speed = 1.0

    if "simulation_playing" not in st.session_state:
        st.session_state.simulation_playing = False

    # Tutorial/onboarding state
    if "show_tutorial" not in st.session_state:
        st.session_state.show_tutorial = True  # Show on first load

    if "tutorial_dismissed" not in st.session_state:
        st.session_state.tutorial_dismissed = False

    # Forensics Lab for player evidence generation
    if "forensics_lab" not in st.session_state:
        st.session_state.forensics_lab = create_forensics_lab()

    # Track generated player evidence
    if "player_evidence_queue" not in st.session_state:
        st.session_state.player_evidence_queue = []

    # STAGED EVIDENCE - Evidence ready to be attached to a message
    if "staged_evidence" not in st.session_state:
        st.session_state.staged_evidence = None  # Dict with evidence data when staged

    # Attachment checkbox state
    if "attach_evidence" not in st.session_state:
        st.session_state.attach_evidence = False

    # === COLD INTERFACE: Shadow Analyst HUD state ===
    if "analyst_log" not in st.session_state:
        st.session_state.analyst_log = []  # Rolling log entries

    if "analyst_log_max" not in st.session_state:
        st.session_state.analyst_log_max = 20  # Max visible entries

    if "active_transmission" not in st.session_state:
        st.session_state.active_transmission = None  # Evidence overlay state

    # === VOICE INPUT: Multimodal input for interrogation ===
    if "voice_mode" not in st.session_state:
        st.session_state.voice_mode = False

    if "last_transcript" not in st.session_state:
        st.session_state.last_transcript = None

    if "speech_client" not in st.session_state:
        try:
            from breach_engine.api.speech_client import create_speech_client
            st.session_state.speech_client = create_speech_client()
        except Exception as e:
            print(f"[APP] Failed to initialize speech client: {e}")
            st.session_state.speech_client = None


def render_pillar_health(pillar_data: dict, pillar_name: str):
    """Render a single pillar health bar with enhanced styling (legacy)."""
    health = pillar_data["health"]
    collapsed = pillar_data["collapsed"]

    # Determine CSS class based on state
    if collapsed:
        css_class = "pillar-collapsed"
        status = "COLLAPSED"
        container_class = ""
    elif health > 75:
        css_class = "pillar-strong"
        status = "Strong"
        container_class = ""
    elif health > 50:
        css_class = "pillar-weakened"
        status = "Weakened"
        container_class = ""
    else:
        css_class = "pillar-critical"
        status = "CRITICAL"
        container_class = "pillar-critical-container"

    st.markdown(f"""<div class="{container_class}" style="margin-bottom: 0.5rem;">
        <span class='{css_class}'><b>{pillar_name}</b>: {status} ({health:.0f}%)</span>
    </div>""".strip(), unsafe_allow_html=True)

    if not collapsed:
        st.progress(health / 100)


def get_pillar_indicators_html(pillars: dict) -> str:
    """Generate HTML for the 2x2 pillar grid with inline styles."""
    pillar_names = ["alibi", "motive", "access", "knowledge"]

    html = '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px;">'

    for name in pillar_names:
        data = pillars.get(name, {"health": 100, "collapsed": False})
        health = data["health"]
        collapsed = data["collapsed"]

        # Determine colors based on state
        if collapsed:
            border_color = "#485366"
            text_color = "#485366"
            text_decoration = "line-through"
            opacity = "0.4"
        elif health <= 25:
            border_color = "#ff2a6d"
            text_color = "#ff2a6d"
            text_decoration = "none"
            opacity = "1"
        elif health <= 50:
            border_color = "#ffc107"
            text_color = "#ffc107"
            text_decoration = "none"
            opacity = "1"
        else:
            border_color = "#00f3ff"
            text_color = "#00f3ff"
            text_decoration = "none"
            opacity = "1"

        html += f'<div style="padding: 8px; border: 1px solid {border_color}; background: #0b1016; text-align: center; opacity: {opacity};"><div style="font-family: Orbitron, monospace; font-size: 0.6rem; color: #485366; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 4px; text-decoration: {text_decoration};">{name.upper()}</div><div style="font-size: 0.85rem; font-weight: 600; color: {text_color}; text-decoration: {text_decoration};">{health:.0f}%</div></div>'

    html += '</div>'
    return html


def get_cognitive_bar_html(load: float, level: str) -> str:
    """Generate HTML for the custom 10-segment cognitive load bar with inline styles."""
    # Determine how many segments to fill
    filled_segments = int(load / 10)
    is_critical = level in ["desperate", "breaking"]

    # Colors
    level_color = "#ff2a6d" if is_critical else "#00f3ff"

    # Build segment HTML
    segments_html = ""
    for i in range(10):
        if i < filled_segments:
            if is_critical:
                segments_html += '<div style="flex: 1; background: #ff2a6d; border: 1px solid rgba(255, 42, 109, 0.5); box-shadow: 0 0 10px #ff2a6d;"></div>'
            else:
                segments_html += '<div style="flex: 1; background: linear-gradient(180deg, #00f3ff 0%, #005f66 100%); border: 1px solid rgba(0, 243, 255, 0.3); box-shadow: 0 0 5px #00f3ff;"></div>'
        else:
            segments_html += '<div style="flex: 1; background: #485366; border: 1px solid rgba(0, 243, 255, 0.2);"></div>'

    return f'<div style="margin: 0.75rem 0;"><div style="display: flex; justify-content: space-between; font-size: 0.75rem; margin-bottom: 0.5rem;"><span style="color: {level_color}; font-weight: 600;">{level.upper()}</span><span style="color: #485366;">{load:.0f}%</span></div><div style="display: flex; gap: 2px; height: 20px;">{segments_html}</div></div>'


# ===== COLD INTERFACE: 3-COLUMN LAYOUT RENDERERS =====

def render_suspect_dossier():
    """Render Column 1: Suspect Dossier panel with mugshot, cognitive bar, pillar grid."""
    manager: BreachManager = st.session_state.breach_manager
    ui_state = manager.get_state_for_ui()

    # Get component HTML
    cognitive = ui_state["cognitive"]
    cognitive_bar_html = get_cognitive_bar_html(cognitive["load"], cognitive["level"])
    pillar_grid_html = get_pillar_indicators_html(ui_state["pillars"])

    # Mask state calculations
    mask = ui_state["mask"]
    divergence = mask["divergence"]
    div_color = "#ff2a6d" if divergence > 60 else ("#00f3ff" if divergence < 30 else "#ffc107")

    # Rapport calculations
    rapport = ui_state["rapport"]
    rapport_pct = rapport * 100
    rapport_color = "#ff2a6d" if rapport < 0.2 else ("#00f3ff" if rapport > 0.5 else "#ffc107")
    rapport_status = "Hostile" if rapport < 0.2 else ("Trusting" if rapport > 0.5 else "Neutral")

    # Secrets
    revealed = ui_state["secrets_revealed"]
    total = ui_state["total_secrets"]
    confession_level = ui_state["confession_level"]

    # Build complete HTML in one block with ALL inline styles (no CSS class dependencies)
    dossier_html = f'''
<div style="background: rgba(11, 16, 22, 0.85); border: 1px solid rgba(0, 243, 255, 0.2); padding: 1rem; font-family: 'JetBrains Mono', monospace;">
<div style="border: 2px solid rgba(0, 243, 255, 0.2); background: #0b1016; padding: 1rem; text-align: center; margin-bottom: 1rem;">
<div style="font-family: 'Orbitron', monospace; font-size: 1rem; color: #00f3ff; letter-spacing: 0.2em;">UNIT 734</div>
<div style="font-size: 0.7rem; color: #485366; margin-top: 0.25rem;">SN-7 Series Synthetic</div>
</div>
<div style="margin-bottom: 1.5rem;">
<div style="font-family: 'Orbitron', monospace; font-size: 0.7rem; color: #485366; text-transform: uppercase; letter-spacing: 0.15em; margin-bottom: 0.5rem; border-bottom: 1px solid rgba(0, 243, 255, 0.1); padding-bottom: 0.25rem;">Turn</div>
<div style="color: #00f3ff; font-size: 1.5rem; text-align: center;">{ui_state['turn']}</div>
</div>
<div style="margin-bottom: 1.5rem;">
<div style="font-family: 'Orbitron', monospace; font-size: 0.7rem; color: #485366; text-transform: uppercase; letter-spacing: 0.15em; margin-bottom: 0.5rem; border-bottom: 1px solid rgba(0, 243, 255, 0.1); padding-bottom: 0.25rem;">Cognitive Load</div>
{cognitive_bar_html}
</div>
<div style="margin-bottom: 1.5rem;">
<div style="font-family: 'Orbitron', monospace; font-size: 0.7rem; color: #485366; text-transform: uppercase; letter-spacing: 0.15em; margin-bottom: 0.5rem; border-bottom: 1px solid rgba(0, 243, 255, 0.1); padding-bottom: 0.25rem;">Story Pillars</div>
{pillar_grid_html}
</div>
<div style="margin-bottom: 1.5rem;">
<div style="font-family: 'Orbitron', monospace; font-size: 0.7rem; color: #485366; text-transform: uppercase; letter-spacing: 0.15em; margin-bottom: 0.5rem; border-bottom: 1px solid rgba(0, 243, 255, 0.1); padding-bottom: 0.25rem;">Mask Divergence</div>
<div style="display: flex; justify-content: space-between; font-size: 0.75rem; margin-bottom: 0.25rem;">
<span style="color: #485366;">Showing: {mask['presented'].title()}</span>
<span style="color: #485366;">Feeling: {mask['true'].title()}</span>
</div>
<div style="text-align: center; font-size: 1.25rem; color: {div_color};">{divergence:.0f}%</div>
</div>
<div style="margin-bottom: 1.5rem;">
<div style="font-family: 'Orbitron', monospace; font-size: 0.7rem; color: #485366; text-transform: uppercase; letter-spacing: 0.15em; margin-bottom: 0.5rem; border-bottom: 1px solid rgba(0, 243, 255, 0.1); padding-bottom: 0.25rem;">Rapport</div>
<div style="text-align: center;">
<span style="color: {rapport_color}; font-size: 0.8rem;">{rapport_status}</span>
<span style="color: #485366; font-size: 0.7rem; margin-left: 0.5rem;">({rapport_pct:.0f}%)</span>
</div>
<div style="height: 4px; background: #485366; margin-top: 0.5rem;">
<div style="height: 100%; width: {rapport_pct}%; background: #00f3ff;"></div>
</div>
</div>
<div style="margin-bottom: 1rem;">
<div style="font-family: 'Orbitron', monospace; font-size: 0.7rem; color: #485366; text-transform: uppercase; letter-spacing: 0.15em; margin-bottom: 0.5rem; border-bottom: 1px solid rgba(0, 243, 255, 0.1); padding-bottom: 0.25rem;">Secrets</div>
<div style="font-size: 0.8rem; text-align: center;">
<span style="color: #00f3ff;">{revealed}/{total}</span>
<span style="color: #485366; margin-left: 1rem;">Level: {confession_level}</span>
</div>
</div>
</div>'''

    st.markdown(dossier_html.strip(), unsafe_allow_html=True)


def add_analyst_log_entry(entry_type: str, message: str):
    """Add an entry to the Shadow Analyst log."""
    timestamp = f"{st.session_state.breach_manager.psychology.turn_count:02d}"
    entry = {
        "type": entry_type,
        "message": message,
        "timestamp": timestamp
    }
    st.session_state.analyst_log.append(entry)

    # Keep only the most recent entries
    max_entries = st.session_state.analyst_log_max
    if len(st.session_state.analyst_log) > max_entries:
        st.session_state.analyst_log = st.session_state.analyst_log[-max_entries:]


def render_shadow_analyst_hud():
    """Render Column 3: Shadow Analyst HUD with rolling log terminal."""
    manager: BreachManager = st.session_state.breach_manager

    # Get analyst insight if available
    analyst_insight = getattr(manager, '_last_analyst_insight', None)

    # Color map for entry types
    color_map = {
        "analyzing": "#485366",
        "trap": "#ffc107",
        "opportunity": "#00ff9d",
        "reid-phase": "#00f3ff",
        "warning": "#ff2a6d"
    }

    # Build log entries HTML with inline styles
    log_entries = ""
    entry_style = "font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; padding: 0.4rem 0; border-bottom: 1px solid rgba(0, 243, 255, 0.05); line-height: 1.4;"

    # Add entries from session state
    for entry in st.session_state.analyst_log[-15:]:
        entry_type = entry.get("type", "analyzing")
        message = entry.get("message", "")
        color = color_map.get(entry_type, "#485366")
        log_entries += f'<div style="{entry_style} color: {color};">&gt; {message}</div>'

    # Add current analysis if available
    if analyst_insight:
        # REID Phase
        log_entries += f'<div style="{entry_style} color: #00f3ff;">&gt; REID PHASE: {analyst_insight.reid_phase.value.upper()}</div>'

        # Trap detection
        if analyst_insight.trap_detected:
            log_entries += f'<div style="{entry_style} color: #ffc107;">&gt; TRAP DETECTED: {analyst_insight.trap_description}</div>'

        # Opportunities
        if analyst_insight.confession_risk > 0.5:
            log_entries += f'<div style="{entry_style} color: #00ff9d;">&gt; OPPORTUNITY: High confession risk ({analyst_insight.confession_risk:.0%})</div>'

        # Strategic advice
        if analyst_insight.strategic_advice:
            advice_short = analyst_insight.strategic_advice[:80] + "..." if len(analyst_insight.strategic_advice) > 80 else analyst_insight.strategic_advice
            log_entries += f'<div style="{entry_style} color: #485366;">&gt; ADVICE: {advice_short}</div>'

    # If no entries yet, show initializing message
    if not log_entries:
        log_entries = f'<div style="{entry_style} color: #485366;">&gt; INITIALIZING ANALYSIS...</div><div style="{entry_style} color: #485366;">&gt; CONNECTED TO NEURAL FEED</div><div style="{entry_style} color: #485366;">&gt; AWAITING INPUT...</div>'

    # Add blinking cursor (using CSS animation from stylesheet)
    log_entries += f'<div style="{entry_style} color: #485366;">&gt; <span class="blinking-cursor"></span></div>'

    # Build complete HTML in one block with inline styles
    hud_html = f'''
<div style="background: rgba(11, 16, 22, 0.85); border: 1px solid rgba(0, 243, 255, 0.2); padding: 1rem; font-family: 'JetBrains Mono', monospace; position: relative; overflow: hidden;">
<div style="font-family: 'Orbitron', monospace; font-size: 0.7rem; color: #00f3ff; text-transform: uppercase; letter-spacing: 0.15em; text-align: center; padding-bottom: 0.5rem; border-bottom: 1px solid rgba(0, 243, 255, 0.2); margin-bottom: 0.75rem;">Shadow Analyst</div>
<div style="max-height: 400px; overflow-y: auto;">
{log_entries}
</div>
</div>'''

    st.markdown(hud_html.strip(), unsafe_allow_html=True)


def render_transcript_entry(msg: dict):
    """Render a single message in transcript log format for the Cold Interface."""
    role = msg.get("role", "")

    # Handle player-generated forensics evidence
    if role == "forensics_evidence":
        render_player_generated_evidence(msg["evidence_item"])
        return

    # Handle Unit 734 counter-evidence
    if role == "counter_evidence":
        render_counter_evidence(msg["counter_evidence"])
        return

    # Handle evidence messages
    if role == "evidence":
        case_item = msg.get("case_item")
        title = case_item.get("display_name", "Evidence") if case_item else "Uploaded Evidence"

        st.markdown(f'''<div class="file-transmission-overlay">
    <div class="label">File Transmission Received</div>
    <div style="font-family: var(--font-data); font-size: 0.75rem; color: var(--muted-slate); margin-top: 0.5rem;">
        {title}
    </div>
</div>'''.strip(), unsafe_allow_html=True)

        # Display the image if available
        if "image_data" in msg:
            st.image(msg["image_data"], use_container_width=True)

        # Display analysis if available
        if "impact" in msg and "analysis" in msg:
            render_evidence_analysis(msg["impact"], msg["analysis"], case_item)
        return

    # Detective message
    if role == "detective":
        tactic = msg.get("tactic", "")
        tactic_badge = f'<span class="tactic-badge tactic-{tactic}">{tactic.upper()}</span>' if tactic else ""

        # Sanitize content
        safe_content = sanitize_for_display(msg["content"])

        # Check for attachment
        attachment = msg.get("attachment")
        attachment_html = ""
        if attachment:
            evidence = attachment["evidence"]
            threat_level = attachment["threat_level"]
            threat_label = "CRITICAL" if threat_level >= 0.7 else ("HIGH" if threat_level >= 0.5 else "MODERATE")
            attachment_html = f'''<div style="margin-top: 0.5rem; padding: 0.5rem; background: rgba(0,243,255,0.05); border: 1px solid var(--ice-blue-20);">
<span style="color: var(--ice-blue); font-size: 0.7rem;">EVIDENCE ATTACHED</span>
<span style="color: var(--muted-slate); font-size: 0.65rem; margin-left: 0.5rem;">{evidence.evidence_type.value.upper()} | Threat: {threat_label}</span>
</div>'''

        st.markdown(f'''<div class="transcript-entry detective">
    <div class="speaker">DET_CHEN{tactic_badge}</div>
    <div class="content">{safe_content}</div>
    {attachment_html}
</div>'''.strip(), unsafe_allow_html=True)

        # Display attached image if present
        if attachment and attachment["evidence"].image_data:
            st.image(attachment["evidence"].image_data, use_container_width=True)

    # Suspect message
    elif role == "suspect":
        verbal = msg.get("verbal_response", {})
        tone = verbal.get("tone", "neutral")
        speech = verbal.get("speech", msg.get("content", ""))
        tells = verbal.get("visible_tells", [])

        # Apply glitch effect based on psychology state
        manager: BreachManager = st.session_state.breach_manager
        psych_state = manager.get_state_for_ui()
        cognitive_load = psych_state["cognitive"]["load"]
        mask_divergence = psych_state["mask"]["divergence"]

        from breach_engine.core.effects import apply_glitch_effect
        glitched_speech, was_glitched = apply_glitch_effect(speech, cognitive_load, mask_divergence)

        glitch_class = "glitch-intense" if cognitive_load > 80 else ("glitch-text" if was_glitched else "")

        tells_html = ""
        if tells:
            tells_str = ", ".join(tells)
            tells_html = f'<div style="font-size: 0.65rem; color: var(--muted-slate); margin-top: 0.5rem; font-style: italic;">[{tells_str}]</div>'

        st.markdown(f'''<div class="transcript-entry suspect">
    <div class="speaker">UNIT_734 <span class="tone-badge">{tone.upper()}</span></div>
    <div class="content {glitch_class}">{glitched_speech}</div>
    {tells_html}
</div>'''.strip(), unsafe_allow_html=True)

        # Show internal monologue if available
        if "internal_monologue" in msg:
            monologue = msg["internal_monologue"]
            with st.expander("INTERNAL PROCESSING", expanded=False):
                st.markdown(f'''<div class="monologue-box">
    <strong>Assessment:</strong> {monologue.get('situation_assessment', 'N/A')}<br>
    <strong>Threat:</strong> {monologue.get('threat_level', 0):.0%}<br>
    <strong>Strategy:</strong> {monologue.get('strategy', 'N/A')}
</div>'''.strip(), unsafe_allow_html=True)

        # Show confession trigger if applicable
        if msg.get("confession_triggered"):
            secret = msg.get("triggered_secret")
            if secret:
                st.markdown(f'''<div style="background: rgba(255,42,109,0.2); border: 2px solid var(--warning-red); padding: 1rem; margin: 0.5rem 0; text-align: center;">
<div style="font-family: var(--font-header); color: var(--warning-red); font-size: 0.9rem; letter-spacing: 0.2em;">CONFESSION TRIGGERED</div>
<div style="font-family: var(--font-data); color: #fff; margin-top: 0.5rem; font-size: 0.8rem;">{secret}</div>
</div>'''.strip(), unsafe_allow_html=True)


def render_interrogation_arena():
    """Render Column 2: Interrogation Arena with transcript log style chat."""
    # Render header as self-contained block
    st.markdown('''<div class="arena-container" style="min-height: 50vh; padding: 1rem;">
    <div class="arena-header">Interrogation Transcript</div>
</div>'''.strip(), unsafe_allow_html=True)

    # Display chat history in transcript format (each entry is self-contained)
    for msg in st.session_state.messages:
        render_transcript_entry(msg)


def render_forensics_lab_ui():
    """Render the Forensics Lab request interface in sidebar."""
    with st.expander("FORENSICS REQUEST", expanded=False):
        st.caption("Request evidence from the Forensics Team")

        lab: ForensicsLab = st.session_state.forensics_lab

        # Show evidence count
        evidence_count = lab.registry.request_count
        max_requests = lab.max_requests
        st.markdown(f"**Requests**: {evidence_count}/{max_requests}")

        # Evidence request input
        evidence_request = st.text_input(
            "Evidence Request",
            placeholder="e.g., 'CCTV of vault at 03:00'",
            key="forensics_request_input",
            label_visibility="collapsed"
        )

        # Search button
        if st.button("🔍 Search Database", use_container_width=True, key="forensics_search_btn"):
            if evidence_request.strip():
                process_forensics_request(evidence_request.strip())
            else:
                st.warning("Please enter an evidence request.")

        # === STAGING AREA ===
        # Show staged evidence ready for attachment
        if st.session_state.staged_evidence:
            st.markdown("---")
            st.markdown("### 📎 Staged Evidence")

            staged = st.session_state.staged_evidence
            evidence = staged["evidence"]
            ui_data = format_evidence_for_ui(evidence)

            # Show preview
            st.markdown(f"**{ui_data['title']}**")
            st.markdown(f"Threat: {ui_data['threat_label']} | Target: {ui_data['pillar']}")

            if evidence.image_data:
                st.image(evidence.image_data, caption=ui_data['summary'], use_container_width=True)

            # Clear staging button
            col1, col2 = st.columns(2)
            with col1:
                if st.button("❌ Discard", use_container_width=True, key="discard_staged"):
                    st.session_state.staged_evidence = None
                    st.session_state.attach_evidence = False
                    st.rerun()
            with col2:
                st.markdown("*Attach below* ↓")

            st.info("💡 Check 'Attach Evidence' below the chat input to present this to Unit 734")

        # Show generated evidence history
        elif lab.registry.request_count > 0:
            st.markdown("---")
            st.markdown("**Previous Evidence:**")
            for summary in lab.get_evidence_summary()[-3:]:  # Show last 3
                st.markdown(f"- {summary}")


def process_forensics_request(request_text: str):
    """Process a forensics evidence request and stage it for attachment."""
    lab: ForensicsLab = st.session_state.forensics_lab

    # Validate and process request
    result = lab.request_evidence(request_text)

    if not result["success"]:
        st.error(result["message"])
        return

    evidence = result["evidence"]

    # Get chat history and facts for lore context injection
    chat_history = st.session_state.messages[-10:]  # Last 10 messages
    established_facts = st.session_state.game_state.established_facts

    # Show loading message and generate image with context
    with st.spinner(lab.get_loading_message()):
        evidence = lab.generate_image_sync(
            evidence,
            chat_history=chat_history,
            established_facts=established_facts,
            save_to_disk=False,  # Cloud-compatible
        )

    if evidence.image_data:
        # Stage the evidence for attachment (instead of auto-queuing)
        st.session_state.staged_evidence = {
            "evidence": evidence,
            "threat_level": result["threat_level"],
            "pillar_targeted": result["pillar_targeted"],
            "filename": f"evidence_{evidence.evidence_type.value}_{evidence.time_reference.replace(':', '').replace(' ', '_')}.png",
        }

        # Pre-check the attachment checkbox
        st.session_state.attach_evidence = True

        # Show success
        ui_data = format_evidence_for_ui(evidence)
        st.success(f"✅ Evidence staged: {ui_data['title']}")

        # Rerun to update UI
        st.rerun()
    else:
        st.warning("Evidence could not be generated. Please try a different request.")


def render_neural_monitor():
    """Render the neural activity graph in sidebar."""
    import plotly.graph_objects as go

    history = st.session_state.get("psychology_history", [])

    if len(history) < 2:
        st.caption("Neural data collecting...")
        return

    fig = go.Figure()

    # Cognitive Load line (red)
    fig.add_trace(go.Scatter(
        y=[h["cognitive_load"] for h in history[-20:]],
        name="Cognitive Load",
        line=dict(color="#e94560", width=2),
        fill='tozeroy',
        fillcolor='rgba(233, 69, 96, 0.1)'
    ))

    # Mask Divergence line (cyan)
    fig.add_trace(go.Scatter(
        y=[h["mask_divergence"] for h in history[-20:]],
        name="Mask Divergence",
        line=dict(color="#00ff9d", width=2),
        fill='tozeroy',
        fillcolor='rgba(0, 255, 157, 0.1)'
    ))

    fig.update_layout(
        template="plotly_dark",
        height=150,
        margin=dict(l=0, r=0, t=10, b=0),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', range=[0, 100])
    )

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


def render_sidebar():
    """Render the sidebar with psychology state."""
    manager: BreachManager = st.session_state.breach_manager
    psych = manager.psychology
    ui_state = manager.get_state_for_ui()

    with st.sidebar:
        st.markdown("## 🤖 SUSPECT: Unit 734")
        st.markdown("**Model**: SN-7 Series Synthetic")
        st.markdown(f"**Turn**: {ui_state['turn']}")

        st.markdown("---")

        # === COGNITIVE LOAD ===
        st.markdown("### 🧠 Cognitive Load")
        st.caption("Mental stress level - push high for confessions")
        cognitive = ui_state["cognitive"]
        load = cognitive["load"]
        level = cognitive["level"]

        # Color based on level
        if level in ["desperate", "breaking"]:
            load_color = "stress-high"
        elif level in ["cracking", "strained"]:
            load_color = "stress-medium"
        else:
            load_color = "stress-low"

        # Enhanced cognitive load display with level-based styling
        cognitive_class = f"cognitive-{level}"
        st.markdown(f"""<div class="{cognitive_class}" style="padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;">
<span class='{load_color}'><b>{level.upper()}</b> ({load:.0f}%)</span>
</div>""".strip(), unsafe_allow_html=True)
        st.progress(min(load / 100, 1.0))

        # Error probability
        if cognitive["error_probability"] > 0.1:
            st.markdown(f"⚠️ Error Risk: {cognitive['error_probability']:.0%}")

        st.markdown("---")

        # === MASK STATE ===
        st.markdown("### 🎭 Mask vs Self")
        st.caption("Gap between shown emotion and true feeling")
        mask = ui_state["mask"]

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Showing**: {mask['presented'].title()}")
        with col2:
            st.markdown(f"**Feeling**: {mask['true'].title()}")

        divergence = mask["divergence"]
        if divergence > 60:
            st.markdown(f"<span class='stress-high'>Divergence: {divergence:.0f}%</span>", unsafe_allow_html=True)
        elif divergence > 40:
            st.markdown(f"<span class='stress-medium'>Divergence: {divergence:.0f}%</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"<span class='stress-low'>Divergence: {divergence:.0f}%</span>", unsafe_allow_html=True)

        st.progress(divergence / 100)

        if mask["leakage_risk"] > 0.3:
            st.markdown(f"👁️ Leakage Risk: {mask['leakage_risk']:.0%}")

        st.markdown("---")

        # === STORY PILLARS ===
        st.markdown("### 🏛️ Story Pillars")
        st.caption("Foundations of the cover story - collapse them with evidence")
        pillars = ui_state["pillars"]

        render_pillar_health(pillars["alibi"], "ALIBI")
        render_pillar_health(pillars["motive"], "MOTIVE")
        render_pillar_health(pillars["access"], "ACCESS")
        render_pillar_health(pillars["knowledge"], "KNOWLEDGE")

        st.markdown("---")

        # === RAPPORT ===
        st.markdown("### 🤝 Rapport")
        st.caption("Trust level - too low and they'll lawyer up")
        rapport = ui_state["rapport"]
        if rapport < 0.2:
            rapport_status = "Hostile"
            rapport_color = "stress-high"
        elif rapport < 0.5:
            rapport_status = "Neutral"
            rapport_color = "stress-medium"
        else:
            rapport_status = "Trusting"
            rapport_color = "stress-low"

        st.markdown(
            f"<span class='{rapport_color}'>{rapport_status} ({rapport:.0%})</span>",
            unsafe_allow_html=True
        )
        st.progress(rapport)

        st.markdown("---")

        # === NEURAL MONITOR ===
        st.markdown("### 📊 Neural Monitor")
        render_neural_monitor()

        st.markdown("---")

        # === SECRETS ===
        st.markdown("### 🔒 Secrets")
        revealed = ui_state["secrets_revealed"]
        total = ui_state["total_secrets"]
        st.markdown(f"Revealed: {revealed}/{total}")

        confession_level = ui_state["confession_level"]
        level_colors = {
            "SURFACE": "#00ff9d",
            "SHALLOW": "#f39c12",
            "DEEP": "#e94560",
            "CORE": "#9b59b6",
            "MOTIVE": "#e74c3c"
        }
        st.markdown(f"Confession Level: **{confession_level}**")

        # Show revealed secrets
        for secret in psych.secrets:
            if secret.is_revealed:
                st.markdown(f"""<div class="secret-revealed">
<small><b>Level {secret.level.value}</b></small><br>
{secret.content[:100]}...
</div>""".strip(), unsafe_allow_html=True)

        st.markdown("---")

        # === LAST TACTIC ===
        if st.session_state.last_processed:
            processed = st.session_state.last_processed
            tactic = processed.detected_tactic.value
            st.markdown("### 🎯 Last Tactic Detected")
            st.markdown(f"<span class='tactic-badge tactic-{tactic}'>{tactic.upper()}</span>", unsafe_allow_html=True)

            if processed.is_rapid_fire:
                st.markdown("⚡ Rapid Fire!")

        st.markdown("---")

        # === CASE FILE ===
        with st.expander("📁 Case Briefing"):
            st.markdown(CASE_001_CONTEXT)

        st.markdown("---")

        # === FORENSICS LAB ===
        render_forensics_lab_ui()

        st.markdown("---")

        # Reset button
        if st.button("🔄 Reset Interrogation", use_container_width=True):
            st.session_state.game_state = GameState(
                session_id="session_001",
                case_id="case_001",
                suspect_state=SuspectState()
            )
            st.session_state.breach_manager = BreachManager(create_unit_734_psychology())
            st.session_state.messages = []
            st.session_state.last_tactic = None
            st.session_state.last_processed = None
            st.session_state.last_evidence_impact = None
            st.session_state.last_evidence_image_data = None
            st.session_state.last_evidence_image_mime = "image/png"
            st.session_state.evidence_count = 0
            st.session_state.psychology_history = []
            st.session_state.game_over = False
            st.session_state.game_result = None
            # Reset evolving suspect tracking
            st.session_state.tactics_used = {}
            st.session_state.evidence_presented = []
            st.session_state.game_recorded = False
            # Reset forensics lab
            st.session_state.forensics_lab = create_forensics_lab()
            st.session_state.player_evidence_queue = []
            st.session_state.staged_evidence = None
            st.session_state.attach_evidence = False
            st.rerun()

        st.markdown("---")

        # Help button to re-show tutorial
        if st.button("❓ How to Play", use_container_width=True):
            st.session_state.show_tutorial = True
            st.session_state.tutorial_dismissed = False
            st.rerun()

        st.markdown("---")

        # Simulation mode controls
        render_simulation_controls()


def render_evidence_analysis(impact, analysis, case_item: Optional[Dict] = None):
    """Render the evidence analysis report."""
    if not analysis.is_relevant:
        st.markdown(f"""<div class="evidence-alert evidence-irrelevant">
<h4>EVIDENCE ANALYSIS</h4>
<p class="threat-low">No relevant evidence detected.</p>
<p><em>{analysis.analysis_summary}</em></p>
</div>""".strip(), unsafe_allow_html=True)
        return

    # Determine threat level styling
    if analysis.total_threat_level >= 70:
        threat_class = "threat-high"
        threat_icon = "CRITICAL"
    elif analysis.total_threat_level >= 40:
        threat_class = "threat-medium"
        threat_icon = "MODERATE"
    else:
        threat_class = "threat-low"
        threat_icon = "LOW"

    # Build title based on case item or generic
    evidence_title = "SYSTEM ALERT: EVIDENCE DETECTED"
    if case_item:
        evidence_title = f"EVIDENCE: {case_item.get('display_name', 'Unknown')}"

    st.markdown(f"""<div class="evidence-alert evidence-relevant">
<h4>{evidence_title}</h4>
<p class="{threat_class}">THREAT LEVEL: {threat_icon} ({analysis.total_threat_level:.0f}%)</p>
<p><strong>Type:</strong> {analysis.evidence_type.value.replace('_', ' ').title()}</p>
<p><em>{analysis.analysis_summary}</em></p>
</div>""".strip(), unsafe_allow_html=True)

    # Show case file hint if available
    if case_item and case_item.get("hint"):
        st.info(f"**Case File Note:** {case_item['hint']}")

    # Show detected objects
    if analysis.detected_objects:
        with st.expander("Detected Objects", expanded=False):
            for obj in analysis.detected_objects:
                st.markdown(f"- **{obj.name}** ({obj.confidence:.0%}) - {obj.relevance}")

    # Show pillar damage
    if impact.pillars_damaged:
        with st.expander("Pillar Impact Analysis", expanded=True):
            for pillar, damage in impact.pillars_damaged.items():
                pillar_name = pillar.value.upper()
                st.markdown(f"""<div class="pillar-damage-item">
<strong>{pillar_name}</strong>: -{damage:.0f} damage
</div>""".strip(), unsafe_allow_html=True)

    # Show collapsed pillars
    if impact.pillars_collapsed:
        for pillar in impact.pillars_collapsed:
            st.error(f"PILLAR COLLAPSED: {pillar.value.upper()}")

    # Show psychological impact
    if impact.cognitive_load_spike > 0 or impact.mask_divergence_spike > 0:
        st.markdown(f"""**Psychological Impact:**
- Cognitive Load Spike: +{impact.cognitive_load_spike:.0f}
- Mask Divergence Spike: +{impact.mask_divergence_spike:.0f}""".strip())

    # Show suggested question
    if analysis.interrogation_suggestion:
        st.info(f"**Suggested Question:** {analysis.interrogation_suggestion}")


def render_player_generated_evidence(evidence_item: dict):
    """Render player-generated evidence from Forensics Lab."""
    evidence = evidence_item["evidence"]
    threat_level = evidence_item["threat_level"]
    pillar_targeted = evidence_item["pillar_targeted"]

    # Determine threat styling
    if threat_level >= 0.8:
        threat_class = "threat-high"
        threat_label = "CRITICAL"
    elif threat_level >= 0.6:
        threat_class = "threat-medium"
        threat_label = "HIGH"
    elif threat_level >= 0.4:
        threat_class = "threat-medium"
        threat_label = "MODERATE"
    else:
        threat_class = "threat-low"
        threat_label = "LOW"

    st.markdown(f"""<div class="evidence-alert evidence-relevant">
<h4>🔬 FORENSICS LAB EVIDENCE</h4>
<p class="{threat_class}">THREAT LEVEL: {threat_label} ({threat_level:.0%})</p>
<p><strong>Type:</strong> {evidence.evidence_type.value.replace('_', ' ').title()}</p>
<p><strong>Location:</strong> {evidence.location}</p>
<p><strong>Time:</strong> {evidence.time_reference}</p>
<p><strong>Targets:</strong> {pillar_targeted.value.upper()} pillar</p>
</div>""".strip(), unsafe_allow_html=True)

    # Display the generated image
    if evidence.image_data:
        st.image(evidence.image_data, caption=evidence.get_summary(), use_container_width=True)


def render_counter_evidence(counter_evidence):
    """Render Unit 734's fabricated counter-evidence."""
    st.markdown(f"""<div style="
background: #1a1a2e;
border: 2px solid #e94560;
border-radius: 8px;
padding: 1rem;
margin: 0.5rem 0;
">
<h4 style="color: #e94560;">🎭 UNIT 734 COUNTER-EVIDENCE</h4>
<p><em>"{counter_evidence.narrative_wrapper}"</em></p>
<p><strong>Type:</strong> {counter_evidence.evidence_type.replace('_', ' ').title()}</p>
<p><strong>Confidence:</strong> {counter_evidence.fabrication_confidence:.0%}</p>
{f'<p style="color: #e94560;">⚠️ FABRICATION RISK: {"HIGH" if counter_evidence.fabrication_confidence < 0.5 else "LOW"}</p>' if counter_evidence.fabrication_confidence < 0.5 else ''}
</div>""".strip(), unsafe_allow_html=True)

    # Display the counter-evidence image
    if counter_evidence.image_data:
        st.image(
            counter_evidence.image_data,
            caption=f"Counter-Evidence: {counter_evidence.description[:50]}...",
            use_container_width=True
        )


def render_message(msg: dict):
    """Render a single message in the chat."""
    # Handle player-generated forensics evidence
    if msg["role"] == "forensics_evidence":
        render_player_generated_evidence(msg["evidence_item"])
        return

    # Handle Unit 734 counter-evidence
    if msg["role"] == "counter_evidence":
        render_counter_evidence(msg["counter_evidence"])
        return

    # Handle evidence messages
    if msg["role"] == "evidence":
        # Get case item metadata if available (from gallery)
        case_item = msg.get("case_item")
        if case_item:
            st.markdown(f"**[Evidence Presented: {case_item.get('display_name', 'Unknown')}]**")
        else:
            st.markdown("**[Evidence Uploaded]**")

        # Display the image if we have the data
        if "image_data" in msg:
            caption = case_item.get("short_name", "Uploaded Evidence") if case_item else "Uploaded Evidence"
            st.image(msg["image_data"], caption=caption, use_container_width=True)

        # Display analysis if available
        if "impact" in msg and "analysis" in msg:
            render_evidence_analysis(msg["impact"], msg["analysis"], case_item)
        return

    if msg["role"] == "detective":
        tactic = msg.get("tactic", "")
        tactic_badge = ""
        if tactic:
            tactic_badge = f"<span class='tactic-badge tactic-{tactic}'>{tactic.upper()}</span>"

        # Sanitize user content for safe HTML display
        safe_content = sanitize_for_display(msg["content"])

        # Check for attached evidence
        attachment = msg.get("attachment")

        if attachment:
            # Render message bubble with attachment
            evidence = attachment["evidence"]
            threat_level = attachment["threat_level"]
            pillar = attachment["pillar_targeted"]

            # Threat level styling
            threat_label = "CRITICAL" if threat_level >= 0.7 else ("HIGH" if threat_level >= 0.5 else "MODERATE")
            threat_color = "#e94560" if threat_level >= 0.7 else ("#ffc107" if threat_level >= 0.5 else "#00d9ff")

            st.markdown(f"""<div class="detective-msg" style="border-left: 3px solid {threat_color}; padding-left: 1rem;">
<strong>🔍 Detective:</strong>{tactic_badge} {safe_content}
<div style="margin-top: 0.5rem; padding: 0.5rem; background: rgba(0,0,0,0.3); border-radius: 4px;">
<span style="color: {threat_color}; font-weight: bold;">📎 EVIDENCE ATTACHED</span>
<span style="color: #888; font-size: 0.85em;"> | {evidence.evidence_type.value.upper()} | Threat: {threat_label}</span>
</div>
</div>""".strip(), unsafe_allow_html=True)

            # Display the attached image
            if evidence.image_data:
                st.image(
                    evidence.image_data,
                    caption=f"📎 {evidence.location} @ {evidence.time_reference}",
                    use_container_width=True
                )
        else:
            # Regular message without attachment
            st.markdown(f"""<div class="detective-msg">
<strong>🔍 Detective:</strong>{tactic_badge} {safe_content}
</div>""".strip(), unsafe_allow_html=True)
    else:
        # Suspect message with internal monologue
        if "internal_monologue" in msg:
            monologue = msg["internal_monologue"]
            with st.expander("🧠 Unit 734's Internal Processing", expanded=True):
                st.markdown(f"""<div class="monologue-box">
<strong>Situation Assessment:</strong> {monologue.get('situation_assessment', 'N/A')}<br><br>
<strong>Threat Level:</strong> {monologue.get('threat_level', 0):.0%}<br>
<strong>Strategy:</strong> {monologue.get('strategy', 'N/A')}<br>
<strong>Emotional State:</strong> {monologue.get('emotional_reaction', 'N/A')}
</div>""".strip(), unsafe_allow_html=True)

                # Show lie checks if any
                lie_checks = monologue.get('lie_checks', [])
                if lie_checks:
                    st.markdown("**Consistency Checks:**")
                    for check in lie_checks:
                        status = "✅" if check.get('is_consistent', True) else "⚠️"
                        st.markdown(f"- {status} {check.get('fact_referenced', 'N/A')} "
                                    f"(Risk: {check.get('risk_level', 0):.0%})")

        # Verbal response
        verbal = msg.get("verbal_response", {})
        tells = verbal.get("visible_tells", [])
        tells_text = f" *[{', '.join(tells)}]*" if tells else ""

        # Get speech and apply glitch effect
        speech = verbal.get('speech', msg.get('content', ''))

        # Apply glitch based on current psychology state
        manager: BreachManager = st.session_state.breach_manager
        psych_state = manager.get_state_for_ui()
        cognitive_load = psych_state["cognitive"]["load"]
        mask_divergence = psych_state["mask"]["divergence"]

        from breach_engine.core.effects import apply_glitch_effect
        glitched_speech, was_glitched = apply_glitch_effect(speech, cognitive_load, mask_divergence)

        # Add glitch class if heavily glitched
        glitch_class = "glitch-intense" if cognitive_load > 80 else ("glitch-text" if was_glitched else "")

        st.markdown(f"""<div class="speech-box {glitch_class}">
<strong>🤖 Unit 734</strong> <em>({verbal.get('tone', 'neutral')})</em>:
{glitched_speech}{tells_text}
</div>""".strip(), unsafe_allow_html=True)

        # Show confession if triggered
        if msg.get("confession_triggered"):
            secret = msg.get("triggered_secret")
            if secret:
                st.warning(f"💥 **CONFESSION TRIGGERED**: {secret}")


def _collect_debrief_data(game_result: dict) -> dict:
    """
    Collect all data needed for supervisor debrief audio generation.

    Args:
        game_result: The game outcome dictionary from check_game_over()

    Returns:
        Session data dictionary for SupervisorDebrief
    """
    # Get psychology history for turn-by-turn analysis
    psych_history = st.session_state.get("psychology_history", [])

    # Build turns data from psychology history
    turns_data = []
    for snapshot in psych_history:
        turn_data = {
            "turn_number": snapshot.get("turn", snapshot.get("turn_number", 0)),
            "cognitive_load": snapshot.get("cognitive_load", 0),
            "stress_level": snapshot.get("stress_level", snapshot.get("cognitive_load", 0)),
            "pillars": snapshot.get("pillars", {}),
            "pillars_collapsed": snapshot.get("pillars_collapsed", []),
            "deception_tactic": snapshot.get("deception_tactic"),
            "shadow_analyst": snapshot.get("shadow_analyst"),
        }
        turns_data.append(turn_data)

    return {
        "outcome": game_result.get("outcome"),
        "ending_type": game_result.get("ending_type", "unknown"),
        "reason": game_result.get("reason", ""),
        "stats": game_result.get("stats", {}),
        "turns": turns_data,
    }


def render_game_over_screen(game_result: dict):
    """Render the victory or defeat screen with cinematic narrative."""
    outcome = game_result["outcome"]
    reason = game_result["reason"]
    subtitle = game_result.get("subtitle", "")
    stats = game_result["stats"]
    narrative = game_result.get("narrative", [])
    ending_type = game_result.get("ending_type", "unknown")

    # Determine title class and styling based on outcome
    if outcome == "victory":
        title_class = "victory-title"
        title_text = "CASE CLOSED"
        icon = "🎯"
        narrative_color = "#00ff9d"
        border_color = "#00ff9d"
    elif outcome == "defeat":
        title_class = "defeat-title"
        title_text = "CASE FAILED"
        icon = "💀"
        narrative_color = "#e94560"
        border_color = "#e94560"
    else:  # partial
        title_class = "partial-title"
        title_text = "CASE INCONCLUSIVE"
        icon = "⚠️"
        narrative_color = "#f39c12"
        border_color = "#f39c12"

    # Build narrative HTML
    narrative_html = ""
    if narrative:
        narrative_lines = "".join([
            f'<p style="margin: 0.5rem 0; opacity: 0.9;">{line}</p>'
            for line in narrative
        ])
        narrative_html = f"""<div style="
max-width: 600px;
margin: 1.5rem auto;
padding: 1rem;
border-left: 3px solid {border_color};
background: rgba(255,255,255,0.03);
font-family: 'Georgia', serif;
font-style: italic;
color: #ccc;
line-height: 1.6;
">
{narrative_lines}
</div>""".strip()

    st.markdown(f"""<div class="game-over-overlay">
<div class="{title_class}">{icon} {title_text}</div>
<div class="game-over-reason">{reason}</div>
<div class="game-over-subtitle">{subtitle}</div>
{narrative_html}
<div class="game-stats">
<h3 style="color: #00ff9d; margin-bottom: 1rem;">📊 INTERROGATION SUMMARY</h3>
<div class="stat-item">
<span class="stat-label">Turns Taken</span>
<span class="stat-value">{stats['turns']}</span>
</div>
<div class="stat-item">
<span class="stat-label">Secrets Uncovered</span>
<span class="stat-value">{stats['secrets_revealed']} / {stats['total_secrets']}</span>
</div>
<div class="stat-item">
<span class="stat-label">Pillars Collapsed</span>
<span class="stat-value">{stats['pillars_collapsed']} / 4</span>
</div>
<div class="stat-item">
<span class="stat-label">Final Stress Level</span>
<span class="stat-value">{stats['final_cognitive_load']:.0f}%</span>
</div>
<div class="stat-item">
<span class="stat-label">Confession Level</span>
<span class="stat-value">{stats['confession_level']}</span>
</div>
<div class="stat-item">
<span class="stat-label">Ending</span>
<span class="stat-value" style="color: {narrative_color};">{ending_type.replace('_', ' ').title()}</span>
</div>
</div>
</div>""".strip(), unsafe_allow_html=True)

    # === SUPERVISOR DEBRIEF AUDIO ===
    st.markdown("---")
    st.markdown("### 🎙️ Supervisor Debrief")
    st.caption("*The Supervisor has analyzed your interrogation performance...*")

    if st.button("▶️ Play Audio Report", key="play_debrief", use_container_width=False):
        with st.spinner("Generating debrief analysis..."):
            try:
                from breach_engine.core.supervisor_debrief import SupervisorDebrief

                # Collect session data for analysis
                session_data = _collect_debrief_data(game_result)

                # Generate audio
                debrief = SupervisorDebrief()
                result = debrief.generate_debrief(session_data)

                if result:
                    audio_bytes, mime_type = result
                    # Use correct MIME type for audio player
                    st.audio(audio_bytes, format=mime_type)
                    st.success("Debrief complete.")
                else:
                    # Fallback: show script only
                    script = debrief.generate_script_only(session_data)
                    if script:
                        st.info("Audio synthesis unavailable. Script transcript:")
                        st.markdown(f"*{script}*")
                    else:
                        st.error("Debrief generation failed. Please try again.")
            except Exception as e:
                st.error(f"Debrief error: {e}")

    st.markdown("---")

    # Add restart button below overlay
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 New Interrogation", use_container_width=True, key="restart_game"):
            # Reset all state
            st.session_state.game_state = GameState(
                session_id="session_001",
                case_id="case_001",
                suspect_state=SuspectState()
            )
            st.session_state.breach_manager = BreachManager(create_unit_734_psychology())
            st.session_state.messages = []
            st.session_state.last_tactic = None
            st.session_state.last_processed = None
            st.session_state.last_evidence_impact = None
            st.session_state.last_evidence_image_data = None
            st.session_state.last_evidence_image_mime = "image/png"
            st.session_state.evidence_count = 0
            st.session_state.psychology_history = []
            st.session_state.game_over = False
            st.session_state.game_result = None
            # Reset evolving suspect tracking
            st.session_state.tactics_used = {}
            st.session_state.evidence_presented = []
            st.session_state.game_recorded = False
            # Reset forensics lab
            st.session_state.forensics_lab = create_forensics_lab()
            st.session_state.player_evidence_queue = []
            st.session_state.staged_evidence = None
            st.session_state.attach_evidence = False
            st.rerun()


# =============================================================================
# SIMULATION PLAYBACK MODE
# =============================================================================

def get_available_simulations() -> list:
    """Get list of available simulation transcripts."""
    sim_dir = Path(__file__).parent / "data" / "simulations"
    if not sim_dir.exists():
        return []

    sims = []
    for f in sim_dir.glob("*.json"):
        try:
            with open(f, "r") as file:
                data = json.load(file)
                sims.append({
                    "filename": f.name,
                    "path": str(f),
                    "strategy": data.get("strategy", "unknown"),
                    "outcome": data.get("outcome", "unknown"),
                    "turns": data.get("total_turns", 0),
                    "timestamp": data.get("start_time", ""),
                })
        except Exception:
            continue

    # Sort by timestamp descending
    sims.sort(key=lambda x: x["timestamp"], reverse=True)
    return sims


def load_simulation(path: str) -> dict:
    """Load a simulation transcript from file."""
    with open(path, "r") as f:
        return json.load(f)


def render_simulation_controls():
    """Render simulation playback controls in sidebar."""
    st.markdown("### 🎬 Simulation Mode")

    # Get available simulations
    sims = get_available_simulations()

    if not sims:
        st.info("No simulations found. Run test_bench.py to generate some.")
        return

    # Simulation selector
    sim_options = {
        f"{s['strategy']} - {s['outcome']} ({s['turns']} turns)": s['path']
        for s in sims
    }
    selected = st.selectbox("Select Simulation", list(sim_options.keys()))

    if st.button("Load Simulation", use_container_width=True):
        path = sim_options[selected]
        st.session_state.simulation_transcript = load_simulation(path)
        st.session_state.simulation_turn = 0
        st.session_state.simulation_mode = True
        st.session_state.simulation_playing = False
        st.rerun()

    # If simulation is loaded, show controls
    if st.session_state.simulation_transcript:
        transcript = st.session_state.simulation_transcript
        total_turns = transcript.get("total_turns", 0)
        current_turn = st.session_state.simulation_turn

        st.markdown(f"**Loaded**: {transcript.get('strategy', 'unknown')} strategy")
        st.markdown(f"**Outcome**: {transcript.get('outcome', 'unknown')}")
        st.markdown(f"**Progress**: {current_turn}/{total_turns} turns")

        # Speed control
        st.session_state.simulation_speed = st.select_slider(
            "Playback Speed",
            options=[0.5, 1.0, 2.0, 5.0],
            value=st.session_state.simulation_speed,
            format_func=lambda x: f"{x}x"
        )

        # Playback controls
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("⏮️", help="Restart"):
                st.session_state.simulation_turn = 0
                st.rerun()
        with col2:
            if st.session_state.simulation_playing:
                if st.button("⏸️", help="Pause"):
                    st.session_state.simulation_playing = False
                    st.rerun()
            else:
                if st.button("▶️", help="Play"):
                    st.session_state.simulation_playing = True
                    st.rerun()
        with col3:
            if st.button("⏭️", help="Next Turn"):
                if current_turn < total_turns:
                    st.session_state.simulation_turn += 1
                    st.rerun()

        # Exit simulation mode
        if st.button("Exit Simulation", use_container_width=True):
            st.session_state.simulation_mode = False
            st.session_state.simulation_transcript = None
            st.session_state.simulation_turn = 0
            st.session_state.simulation_playing = False
            st.rerun()


def render_simulation_playback():
    """Render the simulation playback view."""
    transcript = st.session_state.simulation_transcript
    if not transcript:
        return

    turns = transcript.get("turns", [])
    current_turn = st.session_state.simulation_turn
    total_turns = len(turns)

    # Header with simulation info
    st.markdown(f"""<div class="main-header">
<h1>🎬 SIMULATION PLAYBACK</h1>
<p>Strategy: {transcript.get('strategy', 'unknown').upper()} | Outcome: {transcript.get('outcome', 'unknown').upper()}</p>
<p>Turn {current_turn}/{total_turns}</p>
</div>""".strip(), unsafe_allow_html=True)

    st.markdown("---")

    # Display turns up to current
    for turn in turns[:current_turn]:
        # Detective message (sanitized for safe display)
        safe_detective_msg = sanitize_for_display(turn.get('detective_message', ''))
        st.markdown(f"""<div class="detective-msg">
<span class="tactic-badge">{turn.get('detected_tactic', 'unknown').upper()}</span>
<b>🔍 DETECTIVE:</b> {safe_detective_msg}
</div>""".strip(), unsafe_allow_html=True)

        # Suspect internal
        st.markdown(f"""<div class="monologue-box">
<b>🧠 Unit 734's Internal Processing</b><br>
{turn.get('suspect_internal', '')}
</div>""".strip(), unsafe_allow_html=True)

        # Suspect speech
        emotional_state = turn.get('emotional_state', 'calm')
        cognitive_load = turn.get('cognitive_load', 0)
        tells = turn.get('tells_shown', [])

        tells_html = ""
        if tells:
            tells_html = f"<br><small><i>Visible tells: {', '.join(tells)}</i></small>"

        st.markdown(f"""<div class="speech-box">
<b>🤖 Unit 734 ({emotional_state.title()}, Load: {cognitive_load:.0f}%):</b>
{turn.get('suspect_speech', '')}
{tells_html}
</div>""".strip(), unsafe_allow_html=True)

        st.markdown("---")

    # Auto-advance if playing
    if st.session_state.simulation_playing and current_turn < total_turns:
        # Calculate delay based on speed
        delay = 2.0 / st.session_state.simulation_speed
        time.sleep(delay)
        st.session_state.simulation_turn += 1
        st.rerun()

    # Show outcome if complete
    if current_turn >= total_turns:
        st.session_state.simulation_playing = False
        outcome = transcript.get("outcome", "unknown")
        reason = transcript.get("outcome_reason", "")

        if outcome == "victory":
            st.success(f"🎯 CASE CLOSED: {reason}")
        elif outcome == "defeat":
            st.error(f"💀 CASE FAILED: {reason}")
        else:
            st.warning(f"⚠️ {outcome.upper()}: {reason}")


# =============================================================================
# EVIDENCE GALLERY SYSTEM
# =============================================================================

def load_evidence_manifest() -> Optional[Dict]:
    """Load the evidence manifest file."""
    manifest_path = Path(__file__).parent / "data" / "evidence_manifest.json"
    if not manifest_path.exists():
        return None

    try:
        with open(manifest_path, "r") as f:
            return json.load(f)
    except Exception:
        return None


def get_evidence_items() -> List[Dict]:
    """Get list of available evidence items from manifest."""
    manifest = load_evidence_manifest()
    if not manifest:
        return []
    return manifest.get("evidence_items", [])


def render_evidence_gallery():
    """Render the evidence gallery with thumbnails and selection - Cold Interface style."""
    evidence_items = get_evidence_items()

    if not evidence_items:
        st.markdown('''<div style="text-align: center; padding: 1rem; color: var(--muted-slate); font-family: var(--font-data); font-size: 0.75rem;">
No case evidence files found.
</div>'''.strip(), unsafe_allow_html=True)
        return

    st.markdown('''<div style="font-family: var(--font-header); font-size: 0.7rem; color: var(--ice-blue); text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.75rem;">
Case Evidence Files
</div>'''.strip(), unsafe_allow_html=True)

    # Create a grid of evidence items (2 columns for compact view)
    cols = st.columns(2)

    for i, item in enumerate(evidence_items):
        col = cols[i % 2]
        with col:
            # Evidence card with Cold Interface styling
            threat_level = item.get("expected_threat_level", 50)
            if threat_level >= 80:
                threat_color = "var(--warning-red)"
                threat_label = "CRITICAL"
            elif threat_level >= 60:
                threat_color = "#ffc107"
                threat_label = "HIGH"
            else:
                threat_color = "var(--ice-blue)"
                threat_label = "LOW"

            primary_pillar = item.get("primary_pillar", "unknown").upper()

            st.markdown(f'''<div style="
background: var(--void-blue);
border: 1px solid var(--ice-blue-20);
padding: 0.6rem;
margin-bottom: 0.5rem;
font-family: var(--font-data);
">
<div style="font-size: 0.75rem; font-weight: 600; color: var(--ice-blue);">
{item.get('short_name', 'Evidence')}
</div>
<div style="font-size: 0.65rem; color: var(--muted-slate); margin: 0.25rem 0;">
{item.get('description', '')[:60]}...
</div>
<div style="margin-top: 0.4rem; display: flex; gap: 0.25rem;">
<span style="
background: {threat_color};
color: var(--void-blue);
padding: 2px 6px;
font-size: 0.55rem;
text-transform: uppercase;
letter-spacing: 0.05em;
">{threat_label}</span>
<span style="
background: var(--ice-blue-10);
color: var(--muted-slate);
padding: 2px 6px;
font-size: 0.55rem;
text-transform: uppercase;
letter-spacing: 0.05em;
">{primary_pillar}</span>
</div>
</div>'''.strip(), unsafe_allow_html=True)

            # Present evidence button
            if st.button(
                "PRESENT",
                key=f"present_{item['id']}",
                use_container_width=True
            ):
                # Load and process the evidence
                evidence_path = Path(__file__).parent / "data" / item["filename"]
                if evidence_path.exists():
                    process_case_evidence(item, evidence_path)


def process_case_evidence(item: Dict, evidence_path: Path):
    """Process a piece of case evidence from the gallery."""
    manager: BreachManager = st.session_state.breach_manager

    # Read image data
    with open(evidence_path, "rb") as f:
        image_data = f.read()

    # Determine mime type from extension
    ext = evidence_path.suffix.lower()
    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp"
    }
    mime_type = mime_map.get(ext, "image/png")

    with st.spinner(f"Analyzing evidence: {item['display_name']}..."):
        try:
            # Process evidence through the manager
            impact = manager.process_evidence_image(image_data, mime_type)
            analysis = impact.analysis_result

            # Store the impact for prompt modifiers
            st.session_state.last_evidence_impact = impact

            # Store the image data for multimodal vision (Unit 734 can now "see" evidence)
            st.session_state.last_evidence_image_data = image_data
            st.session_state.last_evidence_image_mime = mime_type

            # Track evidence type for evolving suspect
            if analysis.evidence_type and analysis.evidence_type.value not in st.session_state.evidence_presented:
                st.session_state.evidence_presented.append(analysis.evidence_type.value)

            # Add evidence message to chat with extra metadata
            st.session_state.messages.append({
                "role": "evidence",
                "image_data": image_data,
                "impact": impact,
                "analysis": analysis,
                "case_item": item,  # Include case metadata
            })

            # Increment evidence count
            st.session_state.evidence_count += 1

            # Rerun to display
            st.rerun()

        except Exception as e:
            st.error(f"Error analyzing evidence: {e}")


def render_tutorial_modal():
    """Render the How to Play tutorial using Cold Interface styling."""
    st.markdown('''<div style="
background: var(--glass-bg);
border: 2px solid var(--ice-blue);
padding: 1.5rem;
margin: 1rem 0;
box-shadow: 0 0 30px rgba(0, 243, 255, 0.2);
">
<h2 style="color: var(--ice-blue); font-family: var(--font-header); text-align: center; letter-spacing: 0.3em; text-transform: uppercase;">
INTERROGATION PROTOCOL
</h2>
</div>'''.strip(), unsafe_allow_html=True)

    # Goal section
    with st.expander("🎯 **Your Goal**", expanded=True):
        st.markdown("""You are a detective interrogating **Unit 734**, an android suspected of stealing
valuable data cores. Extract a confession by breaking down their lies.
""".strip())

    # Cognitive Load section
    with st.expander("🧠 **Cognitive Load** - Mental stress level", expanded=True):
        st.markdown("""The suspect's mental stress. Push it high enough and they'll crack.
But be careful - too aggressive and they'll shut down or lawyer up.

| Level | Range | State |
|-------|-------|-------|
| **CONTROLLED** | 0-40% | Calm and collected |
| **STRAINED** | 40-60% | Starting to struggle |
| **CRACKING** | 60-80% | Making mistakes |
| **BREAKING** | 80-100% | On the verge of confession |
""".strip())

    # Story Pillars section
    with st.expander("🏛️ **Story Pillars** - The cover story's foundation", expanded=True):
        st.markdown("""Unit 734's cover story rests on four pillars. Damage them with evidence:

| Pillar | Their Claim |
|--------|-------------|
| **ALIBI** | "I was in standby mode all night" |
| **MOTIVE** | "I had no reason to steal" |
| **ACCESS** | "I don't have vault codes" |
| **KNOWLEDGE** | "I don't know what was stored there" |

When a pillar collapses, secrets are revealed.
""".strip())

    # Mask vs Self section
    with st.expander("🎭 **Mask vs Self** - Emotional divergence", expanded=False):
        st.markdown("""
        The gap between what Unit 734 *shows* and what they *feel*.
        High divergence means they're struggling to maintain their act.

        Watch for **"tells"** - behavioral cues that reveal deception.
        """)

    # Tactics section
    with st.expander("🎯 **Interrogation Tactics**", expanded=False):
        st.markdown("Your questions are automatically classified:")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            - 🔴 **PRESSURE** - Aggressive confrontation
            - 🟢 **EMPATHY** - Supportive approach
            - 🔵 **LOGIC** - Analytical reasoning
            """)
        with col2:
            st.markdown("""
            - 🟣 **BLUFF** - Deceptive tactics
            - 🔺 **EVIDENCE** - Direct presentation
            - ⚪ **SILENCE** - Strategic waiting
            """)

    # Evidence section
    with st.expander("📸 **Evidence System**", expanded=False):
        st.markdown("""
        Present evidence from the case file. Each piece is analyzed by AI and can:
        - **Damage** specific story pillars
        - **Spike** cognitive load
        - **Force confessions** when pillars collapse
        """)

    # Win/Lose section
    with st.expander("🏆 **Win & Lose Conditions**", expanded=True):
        st.success("""
        **Victory Conditions:**
        - 🎯 **Full Confession** - Reveal the deepest secret (MOTIVE)
        - 💥 **Story Destroyed** - Collapse all four pillars
        - 🧠 **Psychological Break** - Push to BREAKING with core secrets revealed
        """)
        st.error("""
        **Defeat Conditions:**
        - ⚖️ **Lawyer Requested** - Rapport too low (< 5%)
        - ⏰ **Timeout** - 30+ turns without progress
        """)

    # Dismiss button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("▶️ Begin Interrogation", use_container_width=True, type="primary"):
            st.session_state.show_tutorial = False
            st.session_state.tutorial_dismissed = True
            st.rerun()


def main():
    """Main application entry point - Cold Interface 3-Column Layout."""
    init_session_state()

    # Check for simulation mode (uses legacy sidebar layout)
    if st.session_state.get("simulation_mode", False):
        render_sidebar()  # Legacy sidebar for simulation mode
        render_simulation_playback()
        return

    # Show tutorial for first-time players
    if st.session_state.get("show_tutorial", False) and not st.session_state.get("tutorial_dismissed", False):
        render_tutorial_modal()
        st.stop()

    # Check if game is over
    if st.session_state.get("game_over", False) and st.session_state.get("game_result"):
        render_game_over_screen(st.session_state.game_result)
        st.stop()

    # === COLD INTERFACE HEADER ===
    st.markdown('''<div class="command-header">
<h1>COGNITIVE BREACH</h1>
<p>Detroit Police Department • Android Crimes Division • Interrogation Room 7</p>
</div>'''.strip(), unsafe_allow_html=True)

    # === 3-COLUMN COMMAND CENTER LAYOUT ===
    col_dossier, col_arena, col_analyst = st.columns([1, 2, 1])

    # === COLUMN 1: SUSPECT DOSSIER ===
    with col_dossier:
        render_suspect_dossier()

        # Control buttons
        if st.button("RESET INTERROGATION", use_container_width=True, key="reset_btn"):
            st.session_state.game_state = GameState(
                session_id="session_001",
                case_id="case_001",
                suspect_state=SuspectState()
            )
            st.session_state.breach_manager = BreachManager(create_unit_734_psychology())
            st.session_state.messages = []
            st.session_state.last_tactic = None
            st.session_state.last_processed = None
            st.session_state.last_evidence_impact = None
            st.session_state.last_evidence_image_data = None
            st.session_state.last_evidence_image_mime = "image/png"
            st.session_state.evidence_count = 0
            st.session_state.psychology_history = []
            st.session_state.game_over = False
            st.session_state.game_result = None
            st.session_state.tactics_used = {}
            st.session_state.evidence_presented = []
            st.session_state.game_recorded = False
            st.session_state.forensics_lab = create_forensics_lab()
            st.session_state.player_evidence_queue = []
            st.session_state.staged_evidence = None
            st.session_state.attach_evidence = False
            st.session_state.analyst_log = []
            st.rerun()

        if st.button("HOW TO PLAY", use_container_width=True, key="help_btn"):
            st.session_state.show_tutorial = True
            st.session_state.tutorial_dismissed = False
            st.rerun()

    # === COLUMN 2: INTERROGATION ARENA ===
    with col_arena:
        render_interrogation_arena()

        # Evidence section (compact tabs)
        with st.expander("PRESENT EVIDENCE", expanded=False):
            evidence_tab1, evidence_tab2 = st.tabs(["Case Files", "Upload"])

            with evidence_tab1:
                render_evidence_gallery()

            with evidence_tab2:
                uploaded_file = st.file_uploader(
                    "Upload Evidence",
                    type=['png', 'jpg', 'jpeg', 'gif', 'webp'],
                    key=f"evidence_uploader_{st.session_state.evidence_count}",
                    label_visibility="collapsed"
                )

                if uploaded_file is not None:
                    manager: BreachManager = st.session_state.breach_manager
                    image_data = uploaded_file.read()
                    mime_type = uploaded_file.type or "image/jpeg"

                    with st.spinner("Analyzing..."):
                        try:
                            impact = manager.process_evidence_image(image_data, mime_type)
                            analysis = impact.analysis_result

                            st.session_state.last_evidence_impact = impact
                            st.session_state.last_evidence_image_data = image_data
                            st.session_state.last_evidence_image_mime = mime_type

                            if analysis.evidence_type and analysis.evidence_type.value not in st.session_state.evidence_presented:
                                st.session_state.evidence_presented.append(analysis.evidence_type.value)

                            st.session_state.messages.append({
                                "role": "evidence",
                                "image_data": image_data,
                                "impact": impact,
                                "analysis": analysis,
                            })
                            st.session_state.evidence_count += 1
                            st.rerun()

                        except Exception as e:
                            st.error(f"Error: {e}")

        # Forensics Lab (moved here - most used after chat)
        render_forensics_lab_ui()

        # Attachment indicator
        attachment_data = None
        if st.session_state.staged_evidence:
            staged = st.session_state.staged_evidence
            filename = staged.get("filename", "evidence.png")

            col_attach, col_label = st.columns([0.15, 0.85])
            with col_attach:
                attach_checked = st.checkbox(
                    "📎",
                    value=st.session_state.attach_evidence,
                    key="attach_evidence_checkbox",
                    help="Attach evidence"
                )
                st.session_state.attach_evidence = attach_checked
            with col_label:
                st.markdown(f'<span style="font-family: var(--font-data); font-size: 0.75rem; color: var(--ice-blue);">📎 {filename}</span>', unsafe_allow_html=True)

            if attach_checked:
                attachment_data = staged

        # === VOICE INPUT SECTION ===
        # Toggle between voice and text input modes
        col_voice_toggle, col_voice_status = st.columns([0.15, 0.85])

        with col_voice_toggle:
            voice_available = st.session_state.speech_client is not None and st.session_state.speech_client.is_available()
            voice_mode = st.toggle(
                "🎤",
                value=st.session_state.voice_mode,
                key="voice_mode_toggle",
                help="Voice input mode" if voice_available else "Voice input unavailable",
                disabled=not voice_available
            )
            st.session_state.voice_mode = voice_mode

        with col_voice_status:
            if voice_mode:
                st.markdown(
                    '<span style="font-family: var(--font-data); font-size: 0.75rem; color: var(--ice-blue);">🎤 VOICE MODE ACTIVE</span>',
                    unsafe_allow_html=True
                )

        # Voice input handling
        prompt = None

        if voice_mode and st.session_state.speech_client:
            # Show audio recorder
            audio_data = st.audio_input(
                "Record your interrogation statement...",
                key="voice_recorder"
            )

            if audio_data:
                # Transcribe the audio
                with st.spinner("Transcribing..."):
                    audio_bytes = audio_data.read()
                    # Determine MIME type from the audio data
                    mime_type = "audio/wav"  # st.audio_input returns WAV format
                    result = st.session_state.speech_client.transcribe_audio(audio_bytes, mime_type)

                if result.error:
                    st.error(f"⚠️ {result.error}")
                elif result.transcript:
                    st.session_state.last_transcript = result.transcript
                    st.info(f"📝 **Transcript:** {result.transcript}")

                    # Confirmation button to send
                    col_send, col_retry = st.columns([0.5, 0.5])
                    with col_send:
                        if st.button("✓ Send Statement", key="send_voice", type="primary"):
                            prompt = result.transcript
                            st.session_state.last_transcript = None
                    with col_retry:
                        if st.button("↻ Re-record", key="retry_voice"):
                            st.session_state.last_transcript = None
                            st.rerun()
                else:
                    st.warning("No speech detected. Please try again.")

        # Text input (shown when voice mode is off)
        if not voice_mode:
            prompt = st.chat_input("Enter interrogation statement...")

        # Process input (from either voice or text)
        if prompt:
            manager: BreachManager = st.session_state.breach_manager

            # Check for attached evidence (new staging system)
            evidence_threat = 0.0
            evidence_pillar = None
            attached_evidence = None

            if attachment_data and st.session_state.attach_evidence:
                # Use the staged evidence as attachment
                attached_evidence = attachment_data
                evidence_threat = attachment_data["threat_level"]
                evidence_pillar = attachment_data["pillar_targeted"]

                # Clear staging after use
                st.session_state.staged_evidence = None
                st.session_state.attach_evidence = False

            # Legacy: Check for queued player-generated evidence (backward compat)
            if st.session_state.player_evidence_queue:
                for evidence_item in st.session_state.player_evidence_queue:
                    if evidence_item["threat_level"] > evidence_threat:
                        evidence_threat = evidence_item["threat_level"]
                        evidence_pillar = evidence_item["pillar_targeted"]
                st.session_state.player_evidence_queue = []

            # Process input through psychology system (with evidence context)
            processed = manager.process_input(
                prompt,
                evidence_threat_level=evidence_threat if evidence_threat > 0 else None,
            )
            st.session_state.last_processed = processed

            # Add to analyst log
            add_analyst_log_entry("analyzing", f"ANALYZING INPUT T{manager.psychology.turn_count:02d}...")
            if processed.detected_tactic:
                add_analyst_log_entry("reid-phase", f"TACTIC: {processed.detected_tactic.value.upper()}")

            # Track tactic usage for evolving suspect
            tactic_name = processed.detected_tactic.value
            if tactic_name not in st.session_state.tactics_used:
                st.session_state.tactics_used[tactic_name] = 0
            st.session_state.tactics_used[tactic_name] += 1

            # Add detective message with tactic AND optional attachment
            detective_msg = {
                "role": "detective",
                "content": prompt,
                "tactic": tactic_name
            }

            # Include attached evidence in the message
            if attached_evidence:
                detective_msg["attachment"] = attached_evidence

            st.session_state.messages.append(detective_msg)
            st.session_state.game_state.add_detective_message(prompt)

            # Generate response
            if st.session_state.gemini_client:
                with st.spinner("Unit 734 is processing..."):
                    try:
                        # Build context for Gemini
                        conversation_context = st.session_state.game_state.get_conversation_context()
                        established_facts = st.session_state.game_state.established_facts

                        # Merge evidence modifiers if we have recent evidence
                        prompt_modifiers = processed.prompt_modifiers.copy()
                        if st.session_state.last_evidence_impact:
                            evidence_modifiers = manager.get_evidence_prompt_modifiers(
                                st.session_state.last_evidence_impact
                            )
                            prompt_modifiers.update(evidence_modifiers)

                        # Generate with psychology-aware prompting
                        # MULTIMODAL VISION: Pass evidence image data so Unit 734 can "see" it
                        evidence_image_data = st.session_state.get("last_evidence_image_data")
                        evidence_image_mime = st.session_state.get("last_evidence_image_mime", "image/png")

                        response = st.session_state.gemini_client.generate_response(
                            player_message=prompt,
                            conversation_context=conversation_context,
                            established_facts=established_facts,
                            prompt_modifiers=prompt_modifiers,
                            evidence_image_data=evidence_image_data,
                            evidence_image_mime=evidence_image_mime,
                        )

                        # PIPELINE FIX #1: Apply threat-level damage to pillars
                        if evidence_threat > 0 and evidence_pillar:
                            damage_report, collapsed = manager.apply_threat_level_damage(
                                threat_level=evidence_threat,
                                target_pillar=evidence_pillar,
                            )
                            if damage_report:
                                # Add to analyst log for visibility
                                add_analyst_log_entry("warning", f"PILLAR DAMAGE: {evidence_pillar.value.upper()}")

                        # Clear the evidence image after use (one-time reveal)
                        st.session_state.last_evidence_image_data = None

                        # Update game state from response
                        state_changes = response.state_changes
                        st.session_state.game_state.established_facts.extend(
                            state_changes.new_facts
                        )
                        st.session_state.game_state.established_lies.extend(
                            state_changes.new_lies
                        )

                        # PIPELINE FIX #2: Record claims in lie ledger for consistency tracking
                        if response.state_changes:
                            manager.record_claims_from_response(
                                response.state_changes,
                                turn=manager.psychology.turn_count
                            )

                        # Add to conversation history
                        st.session_state.game_state.add_suspect_response(
                            response.verbal_response.speech,
                            response.internal_monologue.situation_assessment
                        )

                        # Build message for display
                        suspect_msg = {
                            "role": "suspect",
                            "content": response.verbal_response.speech,
                            "internal_monologue": response.internal_monologue.model_dump(),
                            "verbal_response": response.verbal_response.model_dump(),
                            "emotional_state": response.emotional_state,
                            "confession_triggered": processed.confession_triggered,
                        }

                        # Add triggered secret info
                        if processed.triggered_secret:
                            suspect_msg["triggered_secret"] = processed.triggered_secret.content

                        st.session_state.messages.append(suspect_msg)

                        # Check if Unit 734 should fabricate counter-evidence
                        # HACKATHON FIX: Use threatened_pillar from conversation if no explicit evidence
                        # This allows Gen-vs-Gen to trigger even without player attaching evidence
                        target_pillar = evidence_pillar or processed.threatened_pillar
                        if manager.should_show_fabrication(processed) and target_pillar:
                            from breach_engine.core.visual_generator import create_fabrication_context

                            # Extract player's evidence timestamp for counter-evidence matching
                            player_evidence_desc = None
                            player_timestamp = None

                            if attached_evidence:
                                # Get time_reference directly from the evidence record
                                evidence_record = attached_evidence.get("evidence")
                                if evidence_record and hasattr(evidence_record, 'time_reference'):
                                    player_timestamp = evidence_record.time_reference
                                    player_evidence_desc = f"Evidence from {player_timestamp}"
                                    print(f"[COUNTER-EVIDENCE] Player timestamp from evidence: {player_timestamp}")

                            # Fallback to parsing from the player's message
                            if not player_timestamp and prompt:
                                player_evidence_desc = prompt

                            # Create fabrication context from game state
                            fab_context = create_fabrication_context(
                                threatened_pillar=target_pillar,
                                cognitive_load=manager.psychology.cognitive.load,
                                player_evidence_description=player_evidence_desc,
                                player_evidence_timestamp=player_timestamp,
                            )

                            # Generate counter-evidence
                            counter_evidence = manager.visual_generator.generate_counter_evidence(fab_context)

                            # Generate the actual image
                            with st.spinner("Unit 734 is retrieving evidence..."):
                                counter_evidence = manager.visual_generator.generate_image_sync(counter_evidence)

                            # Add counter-evidence to chat
                            if counter_evidence.image_data:
                                st.session_state.messages.append({
                                    "role": "counter_evidence",
                                    "counter_evidence": counter_evidence,
                                })

                        # Track psychology for neural monitor AND supervisor debrief
                        ui_state = manager.get_state_for_ui()
                        analyst_insight = manager._last_analyst_insight

                        psychology_snapshot = {
                            "turn": ui_state["turn"],
                            "turn_number": ui_state["turn"],  # Alias for debrief
                            "cognitive_load": ui_state["cognitive"]["load"],
                            "stress_level": ui_state["cognitive"]["load"],  # Alias for debrief
                            "mask_divergence": ui_state["mask"]["divergence"],
                            "level": ui_state["cognitive"]["level"],
                            # Pillar states for debrief analysis
                            "pillars": {k: v["health"] for k, v in ui_state["pillars"].items()},
                            "pillars_collapsed": [k for k, v in ui_state["pillars"].items() if v.get("collapsed")],
                            # Deception tactic used by Unit 734
                            "deception_tactic": (
                                processed.deception_tactic.selected_tactic.value
                                if processed.deception_tactic else None
                            ),
                            # Shadow Analyst insights for debrief
                            "shadow_analyst": None,
                        }

                        # Add Shadow Analyst data if available and populate analyst log
                        if analyst_insight:
                            psychology_snapshot["shadow_analyst"] = {
                                "reid_phase": analyst_insight.reid_phase.value,
                                "peace_phase": analyst_insight.peace_phase.value,
                                "confession_risk": analyst_insight.confession_risk,
                                "trap_detected": analyst_insight.trap_detected,
                                "trap_description": analyst_insight.trap_description,
                                "advice": analyst_insight.strategic_advice,
                            }

                            # Add analyst insight entries to log
                            if analyst_insight.trap_detected:
                                add_analyst_log_entry("trap", f"TRAP: {analyst_insight.trap_description}")
                            if analyst_insight.confession_risk > 0.5:
                                add_analyst_log_entry("opportunity", f"CONFESSION RISK: {analyst_insight.confession_risk:.0%}")
                            if analyst_insight.strategic_advice:
                                advice_short = analyst_insight.strategic_advice[:60]
                                add_analyst_log_entry("analyzing", f"ADVICE: {advice_short}...")

                        st.session_state.psychology_history.append(psychology_snapshot)

                        # Cap history at 50 entries
                        if len(st.session_state.psychology_history) > 50:
                            st.session_state.psychology_history = st.session_state.psychology_history[-50:]

                        # Check for game over conditions
                        game_result = manager.check_game_over()
                        if game_result["is_over"]:
                            st.session_state.game_over = True
                            st.session_state.game_result = game_result

                            # Record game outcome for evolving suspect (only once)
                            if not st.session_state.game_recorded:
                                manager.record_game_outcome(
                                    outcome=game_result["outcome"],
                                    tactics_used=st.session_state.tactics_used,
                                    evidence_presented=st.session_state.evidence_presented,
                                )
                                st.session_state.game_recorded = True

                    except Exception as e:
                        st.error(f"Error generating response: {e}")
                        st.session_state.messages.append({
                            "role": "suspect",
                            "content": "*static* ...I apologize, I experienced a momentary system error.",
                            "verbal_response": {"speech": "*static*", "tone": "glitched", "visible_tells": ["LED flickering erratically"]}
                        })
            else:
                st.error("Gemini client not initialized. Check your API key.")

            st.rerun()

        # Initial prompt if no messages
        if not st.session_state.messages:
            st.markdown('''<div style="text-align: center; padding: 2rem; background: var(--glass-bg); border: var(--glass-border);">
<div style="font-family: var(--font-header); color: var(--ice-blue); font-size: 1rem; letter-spacing: 0.2em;">
INTERROGATION READY
</div>
<div style="font-family: var(--font-data); color: var(--muted-slate); font-size: 0.8rem; margin-top: 1rem; line-height: 1.6;">
Subject: Unit 734 (SN-7)<br>
Charge: Data Core Theft - Morrison Estate<br>
Objective: Extract confession
</div>
<div style="font-family: var(--font-data); color: var(--muted-slate); font-size: 0.7rem; margin-top: 1.5rem;">
Enter your first statement to begin...
</div>
</div>'''.strip(), unsafe_allow_html=True)

    # === COLUMN 3: SHADOW ANALYST HUD ===
    with col_analyst:
        render_shadow_analyst_hud()


if __name__ == "__main__":
    main()
