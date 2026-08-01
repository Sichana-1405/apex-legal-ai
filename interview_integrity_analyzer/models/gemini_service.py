"""
models/gemini_service.py
─────────────────────────
Google Gemini 2.5 Flash integration for interview integrity analysis.

Sends resume + interview Q&A to Gemini and receives a structured JSON assessment
covering skill match, technical depth, unverified claims, and recruiter explanation.

All outputs are decision-support signals only — not hiring verdicts.
"""

from __future__ import annotations
import json
import re
import os
from typing import Optional

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

from utils.resume_parser import truncate_for_api


# ─────────────────────────────────────────────────────────────────────────────
# Default / Fallback Response
# ─────────────────────────────────────────────────────────────────────────────
FALLBACK_RESPONSE: dict = {
    "skill_match_percentage":   60,
    "technical_depth":          "Moderate",
    "missing_skills":           ["Unable to determine — API unavailable"],
    "resume_claims_verified":   ["Unable to verify — API unavailable"],
    "resume_claims_unverified": ["Unable to verify — API unavailable"],
    "confidence_score":         50,
    "key_observations": [
        "Gemini API was not available for this analysis.",
        "Risk score is based on behavioral observations only.",
        "Please configure a valid GEMINI_API_KEY to enable AI analysis.",
    ],
    "ai_explanation": (
        "AI-powered analysis could not be completed because the Gemini API key "
        "is missing or invalid. The risk score shown reflects behavioral observations "
        "only. Please add your GEMINI_API_KEY to the sidebar or .env file and re-run "
        "the analysis for a complete AI assessment."
    ),
    "_api_used": False,
}


# ─────────────────────────────────────────────────────────────────────────────
# Prompt Template
# ─────────────────────────────────────────────────────────────────────────────
ANALYSIS_PROMPT_TEMPLATE = """
You are a senior HR analyst and interview integrity specialist at a professional recruitment firm.

Your task is to objectively assess whether a candidate's interview performance is consistent
with the skills and experience they claim in their resume.

─────────────────────────────────────────
CANDIDATE RESUME:
─────────────────────────────────────────
{resume_text}

─────────────────────────────────────────
INTERVIEW QUESTION ASKED:
─────────────────────────────────────────
{question}

─────────────────────────────────────────
CANDIDATE'S INTERVIEW ANSWER:
─────────────────────────────────────────
{answer}

─────────────────────────────────────────
ADDITIONAL TRANSCRIPT NOTES (if any):
─────────────────────────────────────────
{notes}

─────────────────────────────────────────
INSTRUCTIONS:
─────────────────────────────────────────
Analyze the candidate objectively and respond with ONLY valid JSON.
Do NOT include any markdown code blocks, backticks, or extra text.
Your response must start with {{ and end with }}.

Use the following scoring guidelines:
- skill_match_percentage: How well does the answer demonstrate the skills claimed in the resume?
  0 = No alignment at all, 100 = Perfect demonstration of all claimed skills
- technical_depth: "Weak" = cannot explain basics; "Moderate" = explains basics but lacks depth;
  "Strong" = demonstrates comprehensive, nuanced understanding
- confidence_score: Your overall confidence that the candidate genuinely possesses the claimed
  skills based ONLY on the interview answer (0 = no confidence, 100 = fully confident)
- missing_skills: Skills listed in the resume that the answer failed to demonstrate
- resume_claims_verified: Resume claims that the interview answer successfully validated
- resume_claims_unverified: Resume claims that the interview answer failed to support
- key_observations: 3 specific, factual observations (not judgements) about the answer quality
- ai_explanation: A 2–3 sentence, recruiter-friendly explanation of the assessment.
  Write in a neutral, professional tone. Do not use words like "liar" or "fraud".
  Use phrasing like "exhibits characteristics of..." or "answer was inconsistent with..."

RESPOND WITH THIS EXACT JSON STRUCTURE:
{{
    "skill_match_percentage": <integer 0-100>,
    "technical_depth": "<Weak|Moderate|Strong>",
    "missing_skills": ["<skill1>", "<skill2>"],
    "resume_claims_verified": ["<claim1>", "<claim2>"],
    "resume_claims_unverified": ["<claim1>", "<claim2>"],
    "confidence_score": <integer 0-100>,
    "key_observations": ["<observation1>", "<observation2>", "<observation3>"],
    "ai_explanation": "<2-3 sentence recruiter-friendly explanation>"
}}
"""


# ─────────────────────────────────────────────────────────────────────────────
# Gemini Service Class
# ─────────────────────────────────────────────────────────────────────────────
class GeminiService:
    """
    Wraps Google Gemini API for interview analysis.
    Falls back gracefully if API key is missing or call fails.
    """

    MODEL_NAME = "gemini-2.5-flash"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize with an API key.
        Falls back to GEMINI_API_KEY environment variable if not provided.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.is_configured = bool(self.api_key and GENAI_AVAILABLE)

    def analyze_interview(
        self,
        resume_text:       str,
        question:          str,
        answer:            str,
        transcript_notes:  str = "",
    ) -> dict:
        """
        Send resume + interview data to Gemini for structured analysis.

        Returns a dict with the analysis result.
        Falls back to FALLBACK_RESPONSE on any error.
        """
        if not self.is_configured:
            result = FALLBACK_RESPONSE.copy()
            if not GENAI_AVAILABLE:
                result["ai_explanation"] = (
                    "The 'google-generativeai' package is not installed. "
                    "Run: pip install google-generativeai"
                )
            return result

        # Prepare truncated resume text for API
        truncated_resume = truncate_for_api(resume_text, max_chars=5000)
        notes_str = transcript_notes.strip() if transcript_notes else "None provided."

        prompt = ANALYSIS_PROMPT_TEMPLATE.format(
            resume_text=truncated_resume,
            question=question.strip(),
            answer=answer.strip(),
            notes=notes_str,
        )

        try:
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.MODEL_NAME)

            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=1500,
                ),
            )

            raw_text = response.text.strip()
            parsed   = self._parse_json_response(raw_text)
            parsed["_api_used"] = True
            return parsed

        except Exception as e:
            error_msg = str(e)
            result = FALLBACK_RESPONSE.copy()
            result["ai_explanation"] = (
                f"Gemini API call failed: {error_msg[:200]}. "
                "Risk score is based on behavioral observations only. "
                "Verify your API key and try again."
            )
            result["_api_used"] = False
            return result

    def _parse_json_response(self, raw: str) -> dict:
        """
        Robustly extract and parse JSON from Gemini's response.
        Handles markdown code fences and leading/trailing text.
        """
        # Strip markdown code fences if present
        raw = re.sub(r"```(?:json)?", "", raw).strip()
        raw = raw.strip("`").strip()

        # Find the JSON object boundaries
        start = raw.find("{")
        end   = raw.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON object found in Gemini response.")

        json_str = raw[start:end]
        parsed   = json.loads(json_str)

        # Validate and coerce required fields
        return self._validate_response(parsed)

    def _validate_response(self, data: dict) -> dict:
        """
        Validate and coerce Gemini response fields to expected types.
        Fills in defaults for any missing or malformed fields.
        """
        defaults = FALLBACK_RESPONSE.copy()
        validated = {}

        # skill_match_percentage: clamp 0-100
        smp = data.get("skill_match_percentage", defaults["skill_match_percentage"])
        validated["skill_match_percentage"] = max(0, min(100, int(smp)))

        # technical_depth: must be one of three values
        depth = data.get("technical_depth", defaults["technical_depth"])
        validated["technical_depth"] = depth if depth in ("Weak", "Moderate", "Strong") else "Moderate"

        # confidence_score: clamp 0-100
        cs = data.get("confidence_score", defaults["confidence_score"])
        validated["confidence_score"] = max(0, min(100, int(cs)))

        # List fields
        for key in ("missing_skills", "resume_claims_verified",
                    "resume_claims_unverified", "key_observations"):
            val = data.get(key, defaults[key])
            validated[key] = val if isinstance(val, list) else [str(val)]

        # ai_explanation
        validated["ai_explanation"] = str(
            data.get("ai_explanation", defaults["ai_explanation"])
        )

        return validated


# ─────────────────────────────────────────────────────────────────────────────
# Module-level convenience function
# ─────────────────────────────────────────────────────────────────────────────
def analyze_interview(
    resume_text:      str,
    question:         str,
    answer:           str,
    transcript_notes: str = "",
    api_key:          Optional[str] = None,
) -> dict:
    """
    Convenience wrapper around GeminiService for use in Streamlit pages.
    """
    service = GeminiService(api_key=api_key)
    return service.analyze_interview(resume_text, question, answer, transcript_notes)
