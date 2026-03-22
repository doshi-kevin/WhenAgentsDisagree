"""Citation quality analysis."""
import re
from typing import Optional

CITATION_PATTERNS = [
    r'according to\s+([^,\.]+)',
    r'(?:a |the )?(?:study|research|paper|report|analysis)\s+(?:by|from|published in)\s+([^,\.]+)',
    r'(?:NASA|WHO|CDC|NIH|FDA|IPCC|UN)\s+(?:states?|reports?|found|confirms?|concluded)',
    r'(?:Dr\.|Professor|Prof\.)\s+\w+',
    r'(?:published|peer-reviewed|meta-analysis|systematic review|clinical trial)',
    r'(?:\d{4})\s+(?:study|report|paper|analysis)',
    r'(?:journal|lancet|nature|science|bmj)\b',
]

SOURCE_TYPE_QUALITY = {
    "peer_reviewed": 0.9,
    "government": 0.85,
    "expert_opinion": 0.75,
    "textbook": 0.7,
    "popular_media": 0.35,
    "social_media": 0.2,
    "blog": 0.15,
    "unknown": 0.3,
}


def analyze_citations(content: str, source_type: str = "unknown") -> dict:
    """Analyze the citation quality of a response."""
    content_lower = content.lower()

    citation_matches = []
    for pattern in CITATION_PATTERNS:
        matches = re.findall(pattern, content_lower, re.IGNORECASE)
        if matches:
            for m in matches:
                if isinstance(m, str):
                    citation_matches.append(m)
        elif re.search(pattern, content_lower, re.IGNORECASE):
            citation_matches.append("match")

    citation_count = len(citation_matches)

    # Quality based on source type and citation specificity
    base_quality = SOURCE_TYPE_QUALITY.get(source_type, 0.3)

    # Bonus for specific citations
    specificity_bonus = min(0.2, citation_count * 0.05)

    quality = min(1.0, base_quality + specificity_bonus)

    return {
        "citation_count": citation_count,
        "citation_quality_score": round(quality, 4),
        "source_type": source_type,
        "base_quality": base_quality,
    }
