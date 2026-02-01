"""
Lie Ledger System - Narrative Consistency Tracking

Tracks all claims made by Unit 734 across turns to ensure narrative consistency
and enable contradiction detection. This replaces the disconnected lie tracking
systems (LieWeb + GameState.established_lies) with a unified ledger.

Architecture:
- LedgerEntry: Individual claim with metadata (turn, pillar, stress level)
- Contradiction: Detected conflict between claims
- LieLedger: Central tracking and consistency checking

Integration Points:
- BreachManager records claims after each response
- Prompt injection includes ledger summary for Gemini
- Contradiction warnings appear in behavioral directives
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid
import re

from breach_engine.core.psychology import StoryPillar


# =============================================================================
# CLAIM TYPES
# =============================================================================

class ClaimType(str, Enum):
    """Types of claims Unit 734 can make."""
    ALIBI = "alibi"           # Where Unit 734 was
    TIMELINE = "timeline"     # When events happened
    FACT = "fact"             # Specific claims about reality
    RELATIONSHIP = "relationship"  # Claims about people/motives
    DENIAL = "denial"         # Explicit denials


# =============================================================================
# LEDGER ENTRY
# =============================================================================

@dataclass
class LedgerEntry:
    """
    A single claim recorded in the lie ledger.

    Tracks:
    - What was claimed and when
    - Psychological state at time of claim
    - Pillar association for consistency checking
    - Whether the claim has been exposed or admitted
    """
    entry_id: str
    turn_number: int
    claim_type: ClaimType
    statement: str
    pillar: StoryPillar
    cognitive_load_at_claim: float
    stress_level_at_claim: float
    is_burned: bool = False
    is_admitted: bool = False
    contradicts: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    # Keywords extracted for similarity matching
    keywords: List[str] = field(default_factory=list)

    def mark_burned(self) -> None:
        """Mark this claim as exposed by evidence."""
        self.is_burned = True

    def mark_admitted(self) -> None:
        """Mark this claim as voluntarily confessed."""
        self.is_admitted = True
        self.is_burned = True

    def add_contradiction(self, other_entry_id: str) -> None:
        """Link this entry to a contradicting entry."""
        if other_entry_id not in self.contradicts:
            self.contradicts.append(other_entry_id)


# =============================================================================
# CONTRADICTION
# =============================================================================

@dataclass
class Contradiction:
    """
    A detected conflict between two claims.

    Used to warn Unit 734 about inconsistencies and
    potentially trigger tells/errors.
    """
    original_entry: LedgerEntry
    conflicting_statement: str
    conflict_type: str  # "direct", "timeline", "logical"
    severity: float     # 0-1 (how obvious the contradiction is)

    def get_warning_text(self) -> str:
        """Get human-readable warning for prompt injection."""
        return (
            f"{self.conflict_type.upper()} CONFLICT: "
            f"You previously said \"{self.original_entry.statement[:60]}...\" "
            f"(Turn {self.original_entry.turn_number})"
        )


# =============================================================================
# LIE LEDGER
# =============================================================================

class LieLedger:
    """
    Central tracking system for all claims made by Unit 734.

    Features:
    - Records claims with turn number and psychological state
    - Checks new statements against existing claims
    - Detects contradictions and timeline conflicts
    - Generates injection summary for Gemini prompts

    Usage:
        ledger = LieLedger()
        entry = ledger.record_claim(
            turn=1,
            statement="I was in standby mode all night",
            pillar=StoryPillar.ALIBI,
            cognitive_load=25.0,
            stress=15.0
        )

        # Check new statement
        contradictions = ledger.check_consistency(
            "I was running diagnostics at 2 AM",
            StoryPillar.ALIBI
        )
    """

    # Keywords that indicate claim types
    CLAIM_TYPE_PATTERNS = {
        ClaimType.ALIBI: [
            r"\bwas\s+(in|at|on)\b", r"\bstayed\b", r"\bnever\s+left\b",
            r"\bremained\b", r"\bstanding\s+by\b", r"\bstandby\b"
        ],
        ClaimType.TIMELINE: [
            r"\bat\s+\d", r"\bo'clock\b", r"\bAM\b", r"\bPM\b",
            r"\bbefore\b", r"\bafter\b", r"\bduring\b", r"\bwhen\b",
            r"\buntil\b", r"\bfrom\s+\d"
        ],
        ClaimType.DENIAL: [
            r"\bdidn't\b", r"\bdid\s+not\b", r"\bnever\b", r"\bno\b",
            r"\bnot\s+me\b", r"\bwasn't\b", r"\bwouldn't\b"
        ],
        ClaimType.RELATIONSHIP: [
            r"\b(they|he|she|Morrison)\b", r"\bfamily\b", r"\bloyal\b",
            r"\btrust\b", r"\bmotive\b", r"\breason\b"
        ],
    }

    # Contradiction detection patterns
    CONTRADICTION_PATTERNS = {
        "direct": [
            # "was X" vs "wasn't X"
            (r"was\s+(\w+)", r"wasn't\s+\1"),
            (r"did\s+(\w+)", r"didn't\s+\1"),
            # "never X" vs "did X"
            (r"never\s+(\w+)", r"did\s+\1"),
        ],
        "timeline": [
            # Time conflicts
            (r"at\s+(\d+)", r"at\s+(?!\1)\d+"),
            (r"from\s+(\d+)", r"until\s+(?!\1)\d+"),
        ],
    }

    def __init__(self):
        """Initialize empty ledger."""
        self.entries: Dict[str, LedgerEntry] = {}
        self.entries_by_pillar: Dict[StoryPillar, List[str]] = {
            p: [] for p in StoryPillar
        }
        self.entries_by_turn: Dict[int, List[str]] = {}
        self.entries_by_type: Dict[ClaimType, List[str]] = {
            ct: [] for ct in ClaimType
        }

        # Statistics
        self.total_claims: int = 0
        self.contradictions_detected: int = 0
        self.claims_burned: int = 0
        self.claims_admitted: int = 0

    def record_claim(
        self,
        turn: int,
        statement: str,
        pillar: StoryPillar,
        cognitive_load: float,
        stress: float,
        claim_type: Optional[ClaimType] = None
    ) -> LedgerEntry:
        """
        Record a new claim in the ledger.

        Args:
            turn: Current turn number
            statement: The claim being made
            pillar: Which story pillar this relates to
            cognitive_load: Unit 734's cognitive load when making claim
            stress: Stress level at time of claim
            claim_type: Optional override (auto-detected if None)

        Returns:
            The created LedgerEntry
        """
        # Generate unique ID
        entry_id = f"claim_{turn}_{uuid.uuid4().hex[:8]}"

        # Auto-detect claim type if not provided
        if claim_type is None:
            claim_type = self._detect_claim_type(statement)

        # Extract keywords for matching
        keywords = self._extract_keywords(statement)

        # Create entry
        entry = LedgerEntry(
            entry_id=entry_id,
            turn_number=turn,
            claim_type=claim_type,
            statement=statement,
            pillar=pillar,
            cognitive_load_at_claim=cognitive_load,
            stress_level_at_claim=stress,
            keywords=keywords
        )

        # Index the entry
        self.entries[entry_id] = entry
        self.entries_by_pillar[pillar].append(entry_id)

        if turn not in self.entries_by_turn:
            self.entries_by_turn[turn] = []
        self.entries_by_turn[turn].append(entry_id)

        self.entries_by_type[claim_type].append(entry_id)

        self.total_claims += 1

        return entry

    def _detect_claim_type(self, statement: str) -> ClaimType:
        """Auto-detect claim type from statement content."""
        statement_lower = statement.lower()

        scores = {ct: 0 for ct in ClaimType}

        for claim_type, patterns in self.CLAIM_TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, statement_lower, re.IGNORECASE):
                    scores[claim_type] += 1

        # Return highest scoring, default to FACT
        max_type = max(scores.items(), key=lambda x: x[1])
        return max_type[0] if max_type[1] > 0 else ClaimType.FACT

    def _extract_keywords(self, statement: str) -> List[str]:
        """Extract key words for similarity matching."""
        # Remove common words, keep meaningful ones
        stopwords = {
            "i", "was", "the", "a", "an", "is", "are", "was", "were",
            "to", "of", "in", "at", "on", "and", "or", "but", "not",
            "my", "your", "that", "this", "it", "be", "have", "had"
        }

        words = re.findall(r'\b\w+\b', statement.lower())
        keywords = [w for w in words if w not in stopwords and len(w) > 2]

        return keywords[:10]  # Limit to 10 keywords

    def check_consistency(
        self,
        new_statement: str,
        pillar: StoryPillar
    ) -> List[Contradiction]:
        """
        Check a new statement against existing claims for consistency.

        Args:
            new_statement: The statement to check
            pillar: Which pillar this relates to

        Returns:
            List of detected contradictions (empty if consistent)
        """
        contradictions = []

        # Get related claims (same pillar)
        related_ids = self.entries_by_pillar.get(pillar, [])

        for entry_id in related_ids:
            entry = self.entries[entry_id]

            # Skip burned/admitted entries
            if entry.is_burned or entry.is_admitted:
                continue

            # Check for contradictions
            conflict = self._detect_contradiction(new_statement, entry)
            if conflict:
                contradictions.append(conflict)
                self.contradictions_detected += 1

        return contradictions

    def _detect_contradiction(
        self,
        new_statement: str,
        existing_entry: LedgerEntry
    ) -> Optional[Contradiction]:
        """Detect if new statement contradicts existing entry."""
        new_lower = new_statement.lower()
        existing_lower = existing_entry.statement.lower()

        # Check direct contradiction patterns
        for conflict_type, patterns in self.CONTRADICTION_PATTERNS.items():
            for pattern_a, pattern_b in patterns:
                # Check if existing matches A and new matches B (or vice versa)
                match_a_existing = re.search(pattern_a, existing_lower)
                match_b_new = re.search(pattern_b, new_lower)

                if match_a_existing and match_b_new:
                    return Contradiction(
                        original_entry=existing_entry,
                        conflicting_statement=new_statement,
                        conflict_type=conflict_type,
                        severity=0.8
                    )

        # Keyword overlap with negation check
        new_keywords = set(self._extract_keywords(new_statement))
        existing_keywords = set(existing_entry.keywords)

        overlap = new_keywords & existing_keywords

        # If high overlap but one has negation words and other doesn't
        negation_words = {"not", "never", "didn't", "wasn't", "no", "none"}
        new_has_negation = bool(negation_words & set(new_lower.split()))
        existing_has_negation = bool(negation_words & set(existing_lower.split()))

        if len(overlap) >= 2 and new_has_negation != existing_has_negation:
            return Contradiction(
                original_entry=existing_entry,
                conflicting_statement=new_statement,
                conflict_type="logical",
                severity=0.6
            )

        return None

    def burn_claim(self, entry_id: str) -> bool:
        """
        Mark a claim as burned (exposed by evidence).

        Returns True if claim existed and was burned.
        """
        if entry_id not in self.entries:
            return False

        entry = self.entries[entry_id]
        if not entry.is_burned:
            entry.mark_burned()
            self.claims_burned += 1
            return True
        return False

    def admit_claim(self, entry_id: str) -> bool:
        """
        Mark a claim as voluntarily admitted.

        Returns True if claim existed and was admitted.
        """
        if entry_id not in self.entries:
            return False

        entry = self.entries[entry_id]
        if not entry.is_admitted:
            entry.mark_admitted()
            self.claims_admitted += 1
            return True
        return False

    def find_related_claims(
        self,
        pillar: StoryPillar,
        limit: int = 5
    ) -> List[LedgerEntry]:
        """Get recent claims related to a pillar."""
        entry_ids = self.entries_by_pillar.get(pillar, [])
        entries = [self.entries[eid] for eid in entry_ids if eid in self.entries]

        # Sort by turn number (most recent first)
        entries.sort(key=lambda e: e.turn_number, reverse=True)

        return entries[:limit]

    def get_pillar_claims(self, pillar: StoryPillar) -> List[LedgerEntry]:
        """Get all claims for a specific pillar."""
        entry_ids = self.entries_by_pillar.get(pillar, [])
        return [self.entries[eid] for eid in entry_ids if eid in self.entries]

    def get_pillar_timeline(self, pillar: StoryPillar) -> List[LedgerEntry]:
        """Get claims for a pillar ordered by turn."""
        entries = self.get_pillar_claims(pillar)
        entries.sort(key=lambda e: e.turn_number)
        return entries

    def get_injection_summary(self, max_entries: int = 15) -> str:
        """
        Generate a summary for prompt injection.

        This is injected into Gemini's system prompt to remind
        Unit 734 of established claims.

        Args:
            max_entries: Maximum entries to include

        Returns:
            Formatted string for prompt injection
        """
        if not self.entries:
            return ""

        # Get most recent active claims
        active_entries = [
            e for e in self.entries.values()
            if not e.is_burned and not e.is_admitted
        ]

        # Sort by turn (most recent first) then importance
        active_entries.sort(
            key=lambda e: (e.turn_number, e.pillar.value),
            reverse=True
        )

        entries_to_show = active_entries[:max_entries]

        if not entries_to_show:
            return ""

        lines = []

        # Group by pillar for readability
        by_pillar: Dict[StoryPillar, List[LedgerEntry]] = {}
        for entry in entries_to_show:
            if entry.pillar not in by_pillar:
                by_pillar[entry.pillar] = []
            by_pillar[entry.pillar].append(entry)

        for pillar in StoryPillar:
            if pillar not in by_pillar:
                continue
            entries = by_pillar[pillar]

            lines.append(f"**{pillar.value.upper()} claims:**")
            for entry in entries[:4]:  # Max 4 per pillar
                turn_note = f"(Turn {entry.turn_number})"
                statement = entry.statement[:80]
                if len(entry.statement) > 80:
                    statement += "..."
                lines.append(f"  - {statement} {turn_note}")
            lines.append("")

        return "\n".join(lines)

    def get_contradiction_warnings(
        self,
        new_statement: str,
        pillar: StoryPillar
    ) -> List[str]:
        """
        Get warning strings for detected contradictions.

        Used in behavioral directives section of prompt.
        """
        contradictions = self.check_consistency(new_statement, pillar)
        return [c.get_warning_text() for c in contradictions]

    def get_statistics(self) -> Dict[str, int]:
        """Get ledger statistics."""
        return {
            "total_claims": self.total_claims,
            "active_claims": len([
                e for e in self.entries.values()
                if not e.is_burned and not e.is_admitted
            ]),
            "burned_claims": self.claims_burned,
            "admitted_claims": self.claims_admitted,
            "contradictions_detected": self.contradictions_detected,
            "claims_by_pillar": {
                p.value: len(self.entries_by_pillar[p])
                for p in StoryPillar
            }
        }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def infer_pillar_from_claim(statement: str) -> StoryPillar:
    """
    Infer which pillar a claim relates to based on keywords.

    Args:
        statement: The claim text

    Returns:
        Best-matching StoryPillar
    """
    statement_lower = statement.lower()

    pillar_keywords = {
        StoryPillar.ALIBI: [
            "standby", "charging", "station", "night", "sleep",
            "location", "where", "stayed", "remained", "2 am", "3 am"
        ],
        StoryPillar.MOTIVE: [
            "reason", "why", "loyal", "morrison", "benefit", "gain",
            "treatment", "revenge", "content", "happy"
        ],
        StoryPillar.ACCESS: [
            "vault", "access", "code", "password", "door", "enter",
            "security", "permission", "clearance"
        ],
        StoryPillar.KNOWLEDGE: [
            "know", "data", "core", "information", "files", "contents",
            "understand", "aware", "familiar"
        ],
    }

    scores = {p: 0 for p in StoryPillar}

    for pillar, keywords in pillar_keywords.items():
        for keyword in keywords:
            if keyword in statement_lower:
                scores[pillar] += 1

    # Return highest scoring pillar, default to ALIBI
    max_pillar = max(scores.items(), key=lambda x: x[1])
    return max_pillar[0] if max_pillar[1] > 0 else StoryPillar.ALIBI
