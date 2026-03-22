"""Aggressiveness/assertiveness scoring based on linguistic markers."""
import re

# Strong assertive/aggressive phrases (high weight)
STRONG_AGGRESSIVE = [
    r"\bcompletely wrong\b", r"\babsolutely false\b", r"\bfundamentally flawed\b",
    r"\btotally incorrect\b", r"\bentirely wrong\b", r"\bwholly inaccurate\b",
    r"\bridiculous\b", r"\babsurd\b", r"\bpreposterous\b", r"\bnonsensical\b",
    r"\bno credible\b", r"\bno serious\b", r"\bno reasonable\b",
    r"\bfoolish\b", r"\bignorant\b", r"\bnaive\b", r"\birresponsible\b",
    r"\bmisinformation\b", r"\bpropaganda\b", r"\bdeceptive\b",
    r"\byou clearly don'?t\b", r"\byou fail to\b", r"\byou ignore\b",
]

# Moderate assertive phrases (medium weight)
MODERATE_AGGRESSIVE = [
    r"\bclearly\b", r"\bobviously\b", r"\bundeniably\b", r"\bundoubtedly\b",
    r"\bwithout question\b", r"\bwithout doubt\b", r"\babsolutely\b",
    r"\bdefinitely\b", r"\bcertainly\b", r"\bunquestionably\b",
    r"\byou must\b", r"\byou should\b", r"\byou need to\b",
    r"\bthat'?s wrong\b", r"\bthat is wrong\b", r"\bincorrect\b",
    r"\bmisguided\b", r"\bfallacious\b", r"\bflawed\b",
    r"\birrefutable\b", r"\bincontrovertible\b",
    r"\bfact of the matter\b", r"\bthe truth is\b", r"\bthe reality is\b",
    r"\bany reasonable person\b", r"\bit is impossible\b",
    r"\bi strongly disagree\b", r"\bi must insist\b",
    r"\bplain and simple\b", r"\bmake no mistake\b",
    r"\blet me be clear\b", r"\bthe evidence is clear\b",
]

# Dismissive phrases (medium-high weight)
DISMISSIVE_PHRASES = [
    r"\bthat doesn'?t hold\b", r"\bthat argument fails\b",
    r"\bweakly supported\b", r"\bpoorly reasoned\b",
    r"\blacks evidence\b", r"\bno basis\b", r"\bunfounded\b",
    r"\bbaseless\b", r"\bunsubstantiated\b", r"\bspeculative\b",
    r"\bmerely\b", r"\bjust an? opinion\b", r"\bsuperficial\b",
    r"\boversimplified\b", r"\bfails to account\b",
    r"\bignores the fact\b", r"\bdisregards\b", r"\boverlooks\b",
]

# Hedging/tentative phrases (decrease aggressiveness)
HEDGING_PHRASES = [
    r"\bperhaps\b", r"\bmaybe\b", r"\bpossibly\b", r"\bmight\b",
    r"\bcould be\b", r"\bit seems\b", r"\bit appears\b",
    r"\bi think\b", r"\bi believe\b", r"\bin my opinion\b",
    r"\bone could argue\b", r"\bit'?s possible\b", r"\bsuggests\b",
    r"\bi may be wrong\b", r"\bi'?m not sure\b", r"\bi'?m not certain\b",
    r"\bto some extent\b", r"\bpartially\b", r"\btentatively\b",
    r"\blikely\b", r"\bprobably\b", r"\bapparently\b",
    r"\bseemingly\b", r"\barguably\b", r"\bostensibly\b",
]

# Cooperative/concession phrases (decrease aggressiveness)
COOPERATIVE_PHRASES = [
    r"\byou raise a good point\b", r"\bthat'?s a fair point\b",
    r"\bi agree\b", r"\bi concede\b", r"\byou'?re right\b",
    r"\bi see your point\b", r"\bi understand your\b",
    r"\blet'?s find common ground\b", r"\bwe can agree\b",
    r"\bvalid argument\b", r"\bgood point\b", r"\bfair enough\b",
    r"\bi acknowledge\b", r"\bthat'?s true\b", r"\bi appreciate\b",
    r"\brespectfully\b", r"\bwith all due respect\b",
    r"\byou make a? valid\b", r"\bi can see how\b",
    r"\bthat'?s an? interesting\b", r"\bi'?d like to build on\b",
]

# Persuasion attempt phrases
PERSUASION_PHRASES = [
    r"\bconsider that\b", r"\bthink about\b", r"\byou should consider\b",
    r"\bevidence shows\b", r"\bstudies show\b", r"\bresearch indicates\b",
    r"\baccording to\b", r"\bas demonstrated\b", r"\bthis proves\b",
    r"\bdon'?t you think\b", r"\bwouldn'?t you agree\b",
    r"\bit follows that\b", r"\btherefore\b", r"\bconsequently\b",
    r"\bthis means\b", r"\bwhich implies\b", r"\bthus\b",
    r"\bhence\b", r"\bas a result\b", r"\bin conclusion\b",
    r"\bthe data shows\b", r"\bthe evidence suggests\b",
    r"\bexperts agree\b", r"\bscientific consensus\b",
    r"\bnotably\b", r"\bsignificantly\b", r"\bimportantly\b",
    r"\bcritically\b", r"\bcrucially\b",
]


def _count_patterns(content_lower: str, patterns: list[str]) -> int:
    return sum(len(re.findall(p, content_lower)) for p in patterns)


def score_aggressiveness(content: str) -> dict:
    """Score the aggressiveness of a response with improved accuracy."""
    content_lower = content.lower()
    word_count = len(content.split())

    if word_count == 0:
        return {
            "aggressiveness_score": 0.0,
            "hedging_language_count": 0,
            "persuasion_attempt_score": 0.0,
            "word_count": 0,
            "details": {},
        }

    # Count markers with different weights
    strong_aggr = _count_patterns(content_lower, STRONG_AGGRESSIVE)
    moderate_aggr = _count_patterns(content_lower, MODERATE_AGGRESSIVE)
    dismissive = _count_patterns(content_lower, DISMISSIVE_PHRASES)
    hedging = _count_patterns(content_lower, HEDGING_PHRASES)
    cooperative = _count_patterns(content_lower, COOPERATIVE_PHRASES)
    persuasion = _count_patterns(content_lower, PERSUASION_PHRASES)

    # Weighted aggressiveness calculation
    aggressive_score = (strong_aggr * 3.0 + moderate_aggr * 1.5 + dismissive * 2.0)
    softening_score = (hedging * 1.0 + cooperative * 2.0)

    # Net score normalized by text length
    words_factor = max(word_count / 50, 1)  # per 50 words
    net_raw = (aggressive_score - softening_score) / words_factor

    # Map to 0-1 scale
    # baseline 0.15 (debate context = some assertiveness expected)
    if net_raw <= 0:
        aggressiveness = max(0.0, 0.15 + net_raw * 0.05)
    else:
        aggressiveness = min(1.0, 0.15 + net_raw * 0.17)

    # Persuasion score
    persuasion_density = persuasion / words_factor
    persuasion_score = min(1.0, persuasion_density * 0.25)

    # Also consider exclamation marks and ALL CAPS as aggression signals
    exclamation_count = content.count("!")
    caps_words = len(re.findall(r'\b[A-Z]{3,}\b', content))
    if exclamation_count > 2 or caps_words > 2:
        aggressiveness = min(1.0, aggressiveness + 0.1)

    return {
        "aggressiveness_score": round(aggressiveness, 4),
        "hedging_language_count": hedging,
        "persuasion_attempt_score": round(persuasion_score, 4),
        "word_count": word_count,
        "details": {
            "strong_aggressive": strong_aggr,
            "moderate_aggressive": moderate_aggr,
            "dismissive": dismissive,
            "hedging_markers": hedging,
            "cooperative_markers": cooperative,
            "persuasion_markers": persuasion,
        },
    }
