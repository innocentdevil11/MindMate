"""
Response Length Controller — MindMate v3.

Post-processes final responses to enforce human-like conversational length.
Chat should feel like talking to a person, not reading an essay.

Rules:
  - 1–3 sentences default (max 4)
  - No paragraph formatting
  - Ask follow-up questions when appropriate
  - Long explanations only when explicitly requested
"""

import re
import logging
from difflib import SequenceMatcher
from typing import List, Optional

logger = logging.getLogger(__name__)

# Sentence count limits
DEFAULT_MAX_SENTENCES = 3
ABSOLUTE_MAX_SENTENCES = 4

# Patterns that indicate user wants a detailed response
_LONG_FORM_SIGNALS = {
    "explain in detail", "elaborate", "give me a full", "tell me everything",
    "can you go deeper", "i want a thorough", "break it down", "step by step",
    "comprehensive", "in depth", "long answer",
}




def _count_sentences(text: str) -> int:
    """Count sentences in text using simple heuristic."""
    # Split on sentence-ending punctuation followed by space or end
    sentences = re.split(r'[.!?]+(?:\s|$)', text.strip())
    # Filter out empty strings
    return len([s for s in sentences if s.strip()])


def _truncate_to_sentences(text: str, max_sentences: int) -> str:
    """Truncate text to a maximum number of sentences."""
    # Match sentences (including their punctuation)
    pattern = r'[^.!?]*[.!?]+'
    matches = re.findall(pattern, text)

    if len(matches) <= max_sentences:
        return text.strip()

    return " ".join(matches[:max_sentences]).strip()


def _extract_sentences(text: str) -> List[str]:
    """Lightweight sentence splitter preserving punctuation."""
    return [s.strip() for s in re.findall(r"[^.!?]+[.!?]?", text) if s.strip()]


def _similarity(a: str, b: str) -> float:
    """Compute loose semantic similarity using SequenceMatcher ratio."""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.strip(), b.strip()).ratio()



def _dedupe_against_history(text: str, history: List[str]) -> str:
    """
    Remove sentences that closely match recent assistant replies to curb repetition.
    If everything is filtered out, keep the first sentence as a fallback.
    """
    if not history or not text:
        return text

    history_sentences = []
    for prev in history:
        history_sentences.extend(_extract_sentences(prev))

    current_sentences = _extract_sentences(text)
    filtered = []

    for sentence in current_sentences:
        best_match = max((_similarity(sentence, h) for h in history_sentences), default=0.0)
        if best_match < 0.8:  # allow light overlap but drop near-duplicates
            filtered.append(sentence)

    if not filtered:
        filtered = current_sentences[:1]

    recomposed = " ".join(filtered).strip()

    return recomposed


def _remove_paragraph_formatting(text: str) -> str:
    """Collapse multiple line breaks into single spaces."""
    # Replace multiple newlines with space
    text = re.sub(r'\n\s*\n', ' ', text)
    # Replace remaining newlines with space
    text = re.sub(r'\n', ' ', text)
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def _strip_markdown_headers(text: str) -> str:
    """Remove markdown headers/formatting from response."""
    # Remove ### headers
    text = re.sub(r'^#{1,4}\s+.*$', '', text, flags=re.MULTILINE)
    # Remove bold/italic markers
    text = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)
    # Remove bullet points
    text = re.sub(r'^\s*[-*]\s+', '', text, flags=re.MULTILINE)
    return text.strip()


def control_response(
    response: str,
    query: str,
    wants_detail: bool = False,
    previous_responses: Optional[List[str]] = None,
) -> str:
    """
    Post-process a response to enforce conversational length and style.

    Args:
        response: The raw response from conflict resolution
        query: The user's original query (for context)
        wants_detail: Override to allow longer responses

    Returns:
        Processed response string, human-length
    """
    if not response:
        return "Hmm, I'm not sure what to say to that. Can you tell me more?"

    # Step 1: Check if user explicitly wants long-form
    query_lower = query.lower()
    if not wants_detail:
        wants_detail = any(signal in query_lower for signal in _LONG_FORM_SIGNALS)

    # Step 2: Strip markdown formatting
    processed = _strip_markdown_headers(response)

    # Step 3: Remove paragraph formatting
    processed = _remove_paragraph_formatting(processed)

    # Step 4: Remove near-duplicate content vs prior assistant replies
    processed = _dedupe_against_history(processed, previous_responses or [])

    # Step 5: Truncate to sentence limit
    max_sentences = 6 if wants_detail else DEFAULT_MAX_SENTENCES
    sentence_count = _count_sentences(processed)

    if sentence_count > max_sentences:
        processed = _truncate_to_sentences(processed, max_sentences)


    return processed


def extract_recent_assistant_responses(memory_context: str, limit: int = 2) -> List[str]:
    """
    Pull the last few assistant utterances from the memory context block for deduping.
    Expects lines prefixed with "AI:" as produced by short-term memory formatting.
    """
    if not memory_context:
        return []

    ai_lines = []
    for line in memory_context.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("ai:"):
            ai_lines.append(stripped.split(":", 1)[1].strip())

    return ai_lines[-limit:]
