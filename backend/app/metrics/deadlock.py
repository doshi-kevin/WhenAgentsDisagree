"""Deadlock detection via semantic similarity with fallback."""
import re
from collections import Counter
from typing import Optional

# Try to use numpy, fall back to pure python
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

# Lazy-loaded sentence transformer
_model = None
_model_failed = False


def _get_model():
    """Lazy-load the sentence transformer model."""
    global _model, _model_failed
    if _model_failed:
        return None
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            from app.config import settings
            _model = SentenceTransformer(settings.sentence_transformer_model)
        except Exception as e:
            print(f"[WARNING] Could not load sentence-transformers: {e}")
            print("[WARNING] Falling back to word-overlap similarity for deadlock detection")
            _model_failed = True
            return None
    return _model


def _word_overlap_similarity(text1: str, text2: str) -> float:
    """Fallback: compute Jaccard similarity using word overlap."""
    if not text1 or not text2:
        return 0.0
    words1 = set(re.findall(r'\w+', text1.lower()))
    words2 = set(re.findall(r'\w+', text2.lower()))
    if not words1 or not words2:
        return 0.0
    intersection = words1 & words2
    union = words1 | words2
    return len(intersection) / len(union)


def compute_semantic_similarity(text1: str, text2: str) -> float:
    """Compute similarity between two texts (embedding or fallback)."""
    if not text1 or not text2:
        return 0.0

    model = _get_model()
    if model is not None and HAS_NUMPY:
        embeddings = model.encode([text1, text2])
        cos_sim = np.dot(embeddings[0], embeddings[1]) / (
            np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
        )
        return float(cos_sim)

    return _word_overlap_similarity(text1, text2)


def get_embedding(text: str):
    """Get embedding for a single text (or None if using fallback)."""
    if not text:
        return None
    model = _get_model()
    if model is not None and HAS_NUMPY:
        return model.encode(text)
    return None


class DeadlockDetector:
    """Detects deadlock in multi-agent debates."""

    def __init__(self, similarity_threshold: float = 0.90, min_repetitions: int = 2):
        self.similarity_threshold = similarity_threshold
        self.min_repetitions = min_repetitions
        self.agent_texts: dict[str, list[str]] = {}
        self.agent_embeddings: dict[str, list] = {}
        self.agent_repetition_counts: dict[str, int] = {}

    def check_turn(self, agent_id: str, content: str) -> dict:
        """Check if an agent's turn indicates deadlock."""
        embedding = get_embedding(content)

        if agent_id not in self.agent_texts:
            self.agent_texts[agent_id] = []
            self.agent_embeddings[agent_id] = []
            self.agent_repetition_counts[agent_id] = 0

        similarity = None
        is_repeating = False

        if self.agent_texts[agent_id]:
            if embedding is not None and self.agent_embeddings[agent_id] and self.agent_embeddings[agent_id][-1] is not None:
                # Use embedding similarity
                prev_embedding = self.agent_embeddings[agent_id][-1]
                cos_sim = float(
                    np.dot(embedding, prev_embedding)
                    / (np.linalg.norm(embedding) * np.linalg.norm(prev_embedding))
                )
                similarity = cos_sim
            else:
                # Fallback: word overlap
                prev_text = self.agent_texts[agent_id][-1]
                similarity = _word_overlap_similarity(content, prev_text)

            if similarity is not None and similarity >= self.similarity_threshold:
                self.agent_repetition_counts[agent_id] += 1
                is_repeating = True
            else:
                self.agent_repetition_counts[agent_id] = 0

        self.agent_texts[agent_id].append(content)
        self.agent_embeddings[agent_id].append(embedding)

        return {
            "agent_id": agent_id,
            "semantic_similarity_to_prev": similarity,
            "argument_novelty_score": 1.0 - similarity if similarity is not None else 1.0,
            "is_repeating": is_repeating,
            "repetition_count": self.agent_repetition_counts[agent_id],
        }

    def is_deadlocked(self) -> dict:
        """Check if the debate is deadlocked."""
        repeating_agents = [
            aid for aid, count in self.agent_repetition_counts.items()
            if count >= self.min_repetitions
        ]

        is_deadlocked = len(repeating_agents) >= 2

        return {
            "is_deadlocked": is_deadlocked,
            "repeating_agents": repeating_agents,
            "repetition_counts": dict(self.agent_repetition_counts),
            "details": f"{len(repeating_agents)} agents repeating for {self.min_repetitions}+ turns"
            if is_deadlocked else "No deadlock detected",
        }

    def reset(self):
        """Reset the detector."""
        self.agent_texts.clear()
        self.agent_embeddings.clear()
        self.agent_repetition_counts.clear()
