"""
models/risk_engine.py
──────────────────────
Rule-based interview integrity risk scoring engine.

Calculates a 0–100 risk score from:
  • AI analysis results (skill match, technical depth)
  • Behavioral observations (eye contact, lip sync, voice, prompting)

Returns risk level (LOW / MEDIUM / HIGH) and a breakdown of contributing factors.

NOTE: This is a prototype decision-support tool.
      The output must NOT be used as a standalone hiring decision.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal


# ─────────────────────────────────────────────────────────────────────────────
# Type Aliases
# ─────────────────────────────────────────────────────────────────────────────
RiskLevel = Literal["LOW", "MEDIUM", "HIGH"]


# ─────────────────────────────────────────────────────────────────────────────
# Data Classes
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class RiskFactor:
    """Represents a single contributing risk factor."""
    name:        str
    score:       int           # Points added to the risk total
    description: str
    category:    str           # "AI Analysis" | "Behavioral" | "Content"
    severity:    str           # "high" | "medium" | "low"


@dataclass
class RiskResult:
    """Complete risk assessment result."""
    risk_score:    int
    risk_level:    RiskLevel
    risk_color:    str                    # CSS color string
    risk_emoji:    str
    factors:       list[RiskFactor]       = field(default_factory=list)
    recommendation: str                  = ""
    summary_line:   str                  = ""


# ─────────────────────────────────────────────────────────────────────────────
# Scoring Weights
# ─────────────────────────────────────────────────────────────────────────────
# Maximum theoretical score before cap = 35+15+15+20+10+15 = 110 → capped at 100

SKILL_MATCH_WEIGHTS = {
    "very_low":  (0,  30,  35, "Very Low Skill Match",
                  "Answer demonstrates almost none of the skills claimed in the resume.",
                  "high"),
    "low":       (30, 50,  25, "Low Skill Match",
                  "Answer demonstrates below-average alignment with resume skill claims.",
                  "high"),
    "moderate":  (50, 70,  12, "Moderate Skill Match",
                  "Answer shows partial alignment — some claims unverified by response.",
                  "medium"),
    "good":      (70, 100,  0, None, None, None),
}

TECHNICAL_DEPTH_WEIGHTS = {
    "Weak":     (15, "Weak Technical Depth",
                 "Candidate could not articulate technical concepts claimed in the resume.",
                 "high"),
    "Moderate": (8,  "Moderate Technical Depth",
                 "Candidate demonstrated surface-level understanding without depth.",
                 "medium"),
    "Strong":   (0,  None, None, None),
}

EYE_CONTACT_WEIGHTS = {
    "Poor":    (15, "Poor Eye Contact",
                "Candidate consistently avoided camera / eye contact during interview.",
                "medium"),
    "Average": (7,  "Inconsistent Eye Contact",
                "Candidate showed inconsistent eye contact; may indicate distraction.",
                "low"),
    "Good":    (0,  None, None, None),
}

LIP_SYNC_WEIGHTS = {
    "Large Delay": (20, "Large Lip Sync Delay",
                    "Significant audio-visual mismatch detected — possible deepfake indicator.",
                    "high"),
    "Slight Delay":(10, "Slight Lip Sync Delay",
                    "Minor audio-visual inconsistency observed during the session.",
                    "medium"),
    "Matched":     (0,  None, None, None),
}

VOICE_WEIGHTS = {
    "Robotic": (10, "Robotic Voice Pattern",
                "Voice lacked natural variation and human inflection patterns.",
                "medium"),
    "Delayed": (5,  "Delayed Voice Response",
                "Noticeable pauses before answers; may indicate scripted responses.",
                "low"),
    "Natural": (0,  None, None, None),
}

PROMPTING_WEIGHTS = {
    "Yes": (15, "External Prompting Suspected",
            "Behavioral cues suggest the candidate may be receiving real-time assistance.",
            "high"),
    "No":  (0,  None, None, None),
}


# ─────────────────────────────────────────────────────────────────────────────
# Recommendation Templates
# ─────────────────────────────────────────────────────────────────────────────
RECOMMENDATIONS = {
    "LOW": (
        "✅ Proceed to next stage with standard verification. "
        "The candidate's interview responses are broadly consistent with their resume claims. "
        "Routine background check and reference verification is recommended as per standard policy."
    ),
    "MEDIUM": (
        "⚠️ Manual review recommended before proceeding. "
        "Several factors suggest partial inconsistencies between the resume profile and interview "
        "performance. A follow-up technical round with targeted skill verification questions is advised. "
        "Do not make a hiring decision based solely on this automated assessment."
    ),
    "HIGH": (
        "🚨 Strong manual review required. "
        "Multiple risk indicators suggest significant inconsistencies between the candidate's claimed "
        "profile and their demonstrated interview performance. Behavioral anomalies have also been flagged. "
        "Escalate to senior recruiter for in-person verification. "
        "This tool does NOT make a hiring decision — human judgment is mandatory."
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# Main Scoring Function
# ─────────────────────────────────────────────────────────────────────────────
def calculate_risk(
    analysis_result: dict,
    behavioral_obs:  dict,
) -> RiskResult:
    """
    Calculate the interview integrity risk score.

    Parameters
    ----------
    analysis_result : dict
        Output from gemini_service.analyze_interview().
        Expected keys: skill_match_percentage, technical_depth
    behavioral_obs : dict
        Recruiter-recorded behavioral observations.
        Expected keys: eye_contact, lip_sync, voice_behaviour, prompting_detected

    Returns
    -------
    RiskResult
        Complete risk assessment with score, level, factors, and recommendation.
    """
    total_score = 0
    factors: list[RiskFactor] = []

    # ── 1. Skill Match Score ──────────────────────────────────────────────────
    skill_match = int(analysis_result.get("skill_match_percentage", 70))
    for tier, (lo, hi, pts, name, desc, sev) in SKILL_MATCH_WEIGHTS.items():
        if lo <= skill_match < hi and pts > 0:
            total_score += pts
            factors.append(RiskFactor(
                name=name, score=pts, description=desc,
                category="AI Analysis", severity=sev
            ))
            break

    # ── 2. Technical Depth ───────────────────────────────────────────────────
    depth = analysis_result.get("technical_depth", "Strong")
    pts, name, desc, sev = TECHNICAL_DEPTH_WEIGHTS.get(depth, (0, None, None, None))
    if pts > 0:
        total_score += pts
        factors.append(RiskFactor(
            name=name, score=pts, description=desc,
            category="AI Analysis", severity=sev
        ))

    # ── 3. Eye Contact ───────────────────────────────────────────────────────
    eye = behavioral_obs.get("eye_contact", "Good")
    pts, name, desc, sev = EYE_CONTACT_WEIGHTS.get(eye, (0, None, None, None))
    if pts > 0:
        total_score += pts
        factors.append(RiskFactor(
            name=name, score=pts, description=desc,
            category="Behavioral", severity=sev
        ))

    # ── 4. Lip Sync ──────────────────────────────────────────────────────────
    lip = behavioral_obs.get("lip_sync", "Matched")
    pts, name, desc, sev = LIP_SYNC_WEIGHTS.get(lip, (0, None, None, None))
    if pts > 0:
        total_score += pts
        factors.append(RiskFactor(
            name=name, score=pts, description=desc,
            category="Behavioral", severity=sev
        ))

    # ── 5. Voice Behaviour ───────────────────────────────────────────────────
    voice = behavioral_obs.get("voice_behaviour", "Natural")
    pts, name, desc, sev = VOICE_WEIGHTS.get(voice, (0, None, None, None))
    if pts > 0:
        total_score += pts
        factors.append(RiskFactor(
            name=name, score=pts, description=desc,
            category="Behavioral", severity=sev
        ))

    # ── 6. Prompting Detected ────────────────────────────────────────────────
    prompting = behavioral_obs.get("prompting_detected", "No")
    pts, name, desc, sev = PROMPTING_WEIGHTS.get(prompting, (0, None, None, None))
    if pts > 0:
        total_score += pts
        factors.append(RiskFactor(
            name=name, score=pts, description=desc,
            category="Behavioral", severity=sev
        ))

    # ── Cap score at 100 ─────────────────────────────────────────────────────
    final_score = min(total_score, 100)

    # ── Determine risk level ─────────────────────────────────────────────────
    if final_score <= 30:
        level  = "LOW"
        color  = "#10b981"
        emoji  = "🟢"
    elif final_score <= 70:
        level  = "MEDIUM"
        color  = "#f59e0b"
        emoji  = "🟡"
    else:
        level  = "HIGH"
        color  = "#ef4444"
        emoji  = "🔴"

    recommendation = RECOMMENDATIONS[level]
    summary_line   = _build_summary(final_score, level, factors)

    return RiskResult(
        risk_score     = final_score,
        risk_level     = level,
        risk_color     = color,
        risk_emoji     = emoji,
        factors        = factors,
        recommendation = recommendation,
        summary_line   = summary_line,
    )


def _build_summary(score: int, level: str, factors: list[RiskFactor]) -> str:
    """Build a one-line risk summary string for display."""
    n = len(factors)
    if n == 0:
        return f"No significant risk indicators detected. Risk Score: {score}/100."
    top = sorted(factors, key=lambda f: f.score, reverse=True)[:2]
    top_names = " and ".join(f.name for f in top)
    return (
        f"Risk Score {score}/100 — {level} RISK. "
        f"Primary contributors: {top_names}."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Chart Data Helper
# ─────────────────────────────────────────────────────────────────────────────
def get_factor_chart_data(result: RiskResult) -> tuple[list[str], list[int], list[str]]:
    """
    Returns (names, scores, colors) for Plotly bar chart rendering.
    Colors are based on severity: high=red, medium=amber, low=blue.
    """
    color_map = {"high": "#ef4444", "medium": "#f59e0b", "low": "#3b82f6"}
    names  = [f.name for f in result.factors]
    scores = [f.score for f in result.factors]
    colors = [color_map.get(f.severity, "#3b82f6") for f in result.factors]
    return names, scores, colors
