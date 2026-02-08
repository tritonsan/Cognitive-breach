"""
Visual Effects for Cognitive Breach
Text glitching, distortion effects based on psychology state.
"""
import random
from typing import Tuple

# Glitch character sets
GLITCH_CHARS = ["█", "▓", "░", "▒", "╳", "◊", "∆"]
GLITCH_WORDS = ["ERR", "NULL", "???", "---", "N/A", "VOID"]


def apply_glitch_effect(
    text: str,
    cognitive_load: float,
    mask_divergence: float
) -> Tuple[str, bool]:
    """
    Apply glitch effects to text based on psychological stress.

    Args:
        text: Original speech text
        cognitive_load: 0-100 stress level
        mask_divergence: 0-100 mask strain

    Returns:
        Tuple of (glitched_text, was_glitched)
    """
    # STRICT THRESHOLD: Only glitch when stress > 90% (near breaking)
    # Unit 734 must remain perfectly articulate until extreme stress
    if cognitive_load < 90:
        return text, False

    # Calculate glitch intensity (0.0 to 0.4)
    # Only triggers at 90%+, scales from there
    load_factor = max(0, (cognitive_load - 90)) / 25  # 0-0.4 (90% to 100%)
    mask_factor = max(0, (mask_divergence - 80)) / 50  # 0-0.4 (requires very high divergence)
    glitch_probability = min(load_factor + mask_factor, 0.4)

    if glitch_probability < 0.05:
        return text, False

    words = text.split()
    glitched_words = []
    was_glitched = False

    for word in words:
        if random.random() < glitch_probability:
            was_glitched = True
            effect = random.choice(["stutter", "corrupt", "replace", "static"])

            if effect == "stutter":
                # "word" -> "w-w-word"
                glitched_words.append(f"{word[0]}-{word[0]}-{word}")
            elif effect == "corrupt":
                # Insert glitch character mid-word
                if len(word) > 3:
                    pos = random.randint(1, len(word) - 2)
                    char = random.choice(GLITCH_CHARS)
                    glitched_words.append(f"{word[:pos]}`{char}`{word[pos:]}")
                else:
                    glitched_words.append(word)
            elif effect == "replace":
                # Replace with error word
                glitched_words.append(f"`{random.choice(GLITCH_WORDS)}`")
            else:  # static
                # Add static markers around word
                glitched_words.append(f"*{word}*")
        else:
            glitched_words.append(word)

    return " ".join(glitched_words), was_glitched


def get_glitch_css() -> str:
    """Return CSS for glitch animations."""
    return """
    .glitch-text {
        animation: glitch-skew 0.5s infinite linear alternate-reverse;
    }
    .glitch-intense {
        animation: glitch-skew 0.2s infinite linear alternate-reverse;
        text-shadow: -1px 0 #e94560, 1px 0 #00ff9d;
    }
    @keyframes glitch-skew {
        0% { transform: skew(0deg); }
        20% { transform: skew(-1deg); }
        40% { transform: skew(1deg); }
        60% { transform: skew(0deg); }
        80% { transform: skew(1deg); }
        100% { transform: skew(-1deg); }
    }
    .static-overlay::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: repeating-linear-gradient(
            0deg,
            rgba(0,0,0,0.1),
            rgba(0,0,0,0.1) 1px,
            transparent 1px,
            transparent 2px
        );
        pointer-events: none;
        opacity: 0.3;
    }
    """
