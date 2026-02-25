"""
Deterministic concept extraction from text.
Supports both textbook PDFs and lowercase student notes.
"""

import re
from typing import List, Tuple
from collections import Counter


START_STOPWORDS = {
    "the", "this", "that", "any", "which", "whose", "for", "with"
}

END_STOPWORDS = {
    "the", "will", "are", "was", "were", "with", "into", "of"
}


class ConceptExtractor:
    def __init__(self, min_frequency: int = 2):
        self.min_frequency = min_frequency

    def extract_concepts(self, text: str) -> List[Tuple[str, str]]:
        candidates = self._extract_candidates(text)
        freq = Counter(candidates)

        concepts = []
        for (orig, norm), count in freq.items():
            if not self._passes_filters(norm, count):
                continue
            concepts.append((orig, norm))

        concepts.sort(key=lambda x: x[1])
        return concepts

    def _passes_filters(self, normalized: str, count: int) -> bool:
        words = normalized.split()

        # Reject single-word lowercase noise
        if len(words) == 1 and count < self.min_frequency:
            return False

        # Allow frequent terms or single-occurrence multi-word terms
        if count < self.min_frequency and len(words) < 2:
            return False

        # Stopword-based pruning
        if words[0] in START_STOPWORDS:
            return False
        if words[-1] in END_STOPWORDS:
            return False

        return True

    def _extract_candidates(self, text: str) -> List[Tuple[str, str]]:
        candidates: List[Tuple[str, str]] = []

        # Capitalized multi-word phrases
        cap_multi = re.findall(
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b',
            text
        )
        for t in cap_multi:
            candidates.append((t, self._normalize(t)))

        # Lowercase technical phrases (2–3 words)
        lower_phrases = re.findall(
            r'\b[a-z]{3,}(?:\s+[a-z]{3,}){1,2}\b',
            text
        )
        for t in lower_phrases:
            candidates.append((t, self._normalize(t)))

        return candidates

    def _normalize(self, term: str) -> str:
        term = term.lower()
        term = re.sub(r'\s+', ' ', term)
        return term.strip()

    def normalize_concept_for_id(self, term: str) -> str:
        return self._normalize(term)

