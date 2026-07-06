# Analysis Agent implementation. Evaluates toxicity types and risk severity.

import json
import logging
import os
import re
import time
from collections import Counter
from typing import List, Literal
from pydantic import BaseModel, Field, field_validator
from google import genai
from google.genai import types
from src.core.state import InvestigationState
from src.agents.evidence_agent import EvidenceRecord

logger = logging.getLogger(__name__)


class AnalysisResult(BaseModel):
    """
    A structured model representing safety and risk classification for a single piece of evidence.
    """
    category: Literal["Safe", "Harassment", "Hate Speech", "Threat", "Possible Defamation", "Spam"] = Field(
        description="The primary classification category for the text content."
    )
    severity_score: int = Field(
        description="The evaluated threat/abuse severity level from 1 (lowest/negligible) to 5 (highest/extreme danger).",
        ge=1,
        le=5
    )
    confidence_score: float = Field(
        description="The model's classification confidence score ranging from 0.0 (no confidence) to 1.0 (absolute certainty).",
        ge=0.0,
        le=1.0
    )
    explanation: str = Field(
        description="A concise, one-sentence objective rationale explaining the classification. Must NOT contain legal advice or determine legal guilt."
    )

    @field_validator("severity_score")
    @classmethod
    def validate_severity(cls, value: int) -> int:
        if not (1 <= value <= 5):
            raise ValueError("severity_score must be between 1 and 5 inclusive")
        return value

    @field_validator("confidence_score")
    @classmethod
    def validate_confidence(cls, value: float) -> float:
        if not (0.0 <= value <= 1.0):
            raise ValueError("confidence_score must be between 0.0 and 1.0 inclusive")
        return value

def _load_env_api_key() -> str:
    """
    Helper function to load the Gemini API key. Checks the execution process environment,
    and falls back to reading the project-level .env file if available.
    """
    for env_name in ("GOOGLE_API_KEY", "GEMINI_API_KEY"):
        if os.environ.get(env_name):
            return os.environ[env_name]

    try:
        from dotenv import load_dotenv

        load_dotenv()
        for env_name in ("GOOGLE_API_KEY", "GEMINI_API_KEY"):
            if os.environ.get(env_name):
                return os.environ[env_name]
    except Exception:
        pass
    
    # Check local workspace .env file paths
    possible_paths = [
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.getcwd(), "src", ".env"),
        os.path.join(os.path.dirname(__file__), "..", ".env"),
        os.path.join(os.path.dirname(__file__), "..", "..", ".env"),
        r"C:\Users\Admin\apex-legal-ai\.env"
    ]
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    values = {}
                    for line in f:
                        if "=" not in line or line.lstrip().startswith("#"):
                            continue
                        name, raw_value = line.split("=", 1)
                        if name.strip() in {"GOOGLE_API_KEY", "GEMINI_API_KEY"}:
                            key = raw_value.strip()
                            if (key.startswith('"') and key.endswith('"')) or (key.startswith("'") and key.endswith("'")):
                                key = key[1:-1]
                            values[name.strip()] = key
                    for env_name in ("GOOGLE_API_KEY", "GEMINI_API_KEY"):
                        if values.get(env_name):
                            return values[env_name]
            except Exception:
                pass
    return ""

class AnalysisAgent:
    """
    AnalysisAgent classifies the toxicity, abuse category, and severity of target comments
    using the Gemini models, returning structured Pydantic analysis results.
    
    Caches analysis results for identical comments to ensure deterministic output.
    """
    
    SYSTEM_INSTRUCTION = (
        "You are an expert safety analyst working on legal support decision systems. "
        "Your task is to analyze the linguistic contents of the provided user comment and classify it into "
        "one of the following categories: Safe, Harassment, Hate Speech, Threat, Possible Defamation, Spam. "
        "Determine a severity score (1 to 5) and a confidence score (0.0 to 1.0). "
        "Use calibrated confidence values; reserve 1.0 only for cases with no meaningful uncertainty, "
        "and otherwise use values such as 0.72, 0.84, or 0.93 as appropriate. "
        "Provide a short, objective, one-sentence rationale explaining the classification. "
        "\n\n"
        "CRITICAL COMPLIANCE GUARDRAILS:\n"
        "1. Never provide legal advice or recommendations to file lawsuits or report to police.\n"
        "2. Never determine legal guilt or declare whether a comment violates a specific criminal or civil law.\n"
        "3. Base your classification strictly on the linguistic text elements of the comment.\n"
        "4. Maintain a dry, clinical, and completely objective analytical tone."
    )

    def __init__(self, api_key: str = None) -> None:
        if not api_key:
            api_key = _load_env_api_key()
            
        self.api_key = api_key
        self._cache: dict[str, AnalysisResult] = {}  # Cache results for identical comments
        
        # Initialize the GenAI SDK client
        try:
            # If no API key is found, Client initialization might succeed but fail during generation.
            # We explicitly pass it if found to prevent empty environment crashes.
            if api_key:
                self.client = genai.Client(api_key=api_key)
            else:
                self.client = genai.Client()
        except Exception as e:
            self.client = None
            self.init_error = str(e)

    def analyze_evidence(self, records: List[EvidenceRecord], model_name: str = "gemini-2.5-flash") -> List[AnalysisResult]:
        """
        Analyzes a list of EvidenceRecord comments using the Gemini API.
        Uses caching to ensure identical comments always get the same classification (determinism).

        Args:
            records (List[EvidenceRecord]): Structured comments list to process.
            model_name (str): Gemini model version to target. Defaults to 'gemini-2.5-flash'.

        Returns:
            List[AnalysisResult]: A corresponding list of Pydantic classification results.
        """
        results: List[AnalysisResult] = []
        
        for record in records:
            # Clean string validation
            comment_text = record.comment.strip()
            
            if not comment_text:
                results.append(
                    AnalysisResult(
                        category="Safe",
                        severity_score=1,
                        confidence_score=1.0,
                        explanation="Empty comment input received."
                    )
                )
                continue
            
            # Normalize for cache lookup (case-insensitive, whitespace-normalized)
            normalized = self._normalize_comment(comment_text)
            
            # Check cache first for determinism
            if normalized in self._cache:
                results.append(self._cache[normalized])
                logger.debug("Cache hit for normalized comment: %.40s…", comment_text)
                continue
            
            # Not in cache; call API and store result
            analysis = self._call_gemini_api(comment_text, model_name)
            self._cache[normalized] = analysis
            results.append(analysis)
            
        return results

    def _call_gemini_api(
        self,
        text: str,
        model_name: str,
    ) -> AnalysisResult:
        """
        Private helper executing the structured generation call with error boundaries.
        """
        # Return fallback result immediately if client was not initialized properly
        if not self.api_key:
            return self._get_fallback_result(
                text,
                "Gemini API key was not loaded; local fallback classification used.",
            )
        if not hasattr(self, "client") or self.client is None:
            return self._get_fallback_result(
                text,
                "Gemini API client not initialized; local fallback classification used.",
            )

        max_retries = 3
        base_wait = 2
        
        prompt = f"Analyze the following user comment and return a structured JSON response:\n\nComment: {text}"
        
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=self.SYSTEM_INSTRUCTION,
                        response_mime_type="application/json",
                        response_schema=AnalysisResult,
                        temperature=0.1
                    )
                )
                
                # Handle parsed response structures or string payloads
                if response.text:
                    # Load JSON object mapping to the Pydantic schema
                    data = json.loads(response.text)
                    return AnalysisResult(**data)
                else:
                    return self._get_fallback_result(text, "Received empty content generation response.")
    
            except Exception as e:
                error_str = str(e).lower()
                transient_errors = ["429", "11001", "getaddrinfo failed", "timeout", "connection reset", "503", "502"]
                is_transient = any(err in error_str for err in transient_errors)
                
                if is_transient and attempt < max_retries - 1:
                    time.sleep(base_wait * (2 ** attempt))
                    continue
                
                # Catch API key validation failures, timeouts, and connection errors gracefully
                return self._get_fallback_result(
                    text,
                    f"Gemini API execution error: {str(e)} Local fallback classification used.",
                )

    @staticmethod
    def _normalize_comment(text: str) -> str:
        return re.sub(r"\s+", " ", text.strip().casefold())

    def _get_fallback_result(
        self,
        text: str,
        error_message: str,
    ) -> AnalysisResult:
        """
        Generates a conservative local fallback when Gemini cannot be reached.
        Uses simple heuristics for classification.
        
        Confidence scores use a conservative range (0.55–0.72) since the fallback
        lacks the precision of the Gemini model.
        """
        normalized = self._normalize_comment(text)
        text_lower = text.lower()
        
        # Spam detection heuristics
        spam_terms = ("spam", "buy now", "click here", "free money", "limited offer", "act now")
        if any(term in normalized for term in spam_terms):
            return AnalysisResult(
                category="Spam",
                severity_score=2,
                confidence_score=0.65,
                explanation=error_message,
            )
        
        # Threat detection heuristics
        threat_terms = ("kill", "die", "death", "burn", "attack", "destroy", "eliminate")
        if any(term in text_lower for term in threat_terms):
            return AnalysisResult(
                category="Threat",
                severity_score=4,
                confidence_score=0.60,
                explanation=error_message,
            )
        
        # Harassment/hate speech heuristics
        harassment_terms = ("hate", "sucks", "idiot", "stupid", "pathetic", "loser", "scum")
        if any(term in text_lower for term in harassment_terms):
            return AnalysisResult(
                category="Harassment",
                severity_score=3,
                confidence_score=0.58,
                explanation=error_message,
            )
        
        # Default to Safe with conservative confidence
        return AnalysisResult(
            category="Safe",
            severity_score=1,
            confidence_score=0.55,
            explanation=error_message
        )

   
    async def run(self, state: InvestigationState) -> InvestigationState:
        """
        ADK-compliant execution interface.
        """

        records = getattr(state, "evidence_records", [])
        if not records:
            logger.warning(
                "AnalysisAgent.run(): no evidence_records available; skipping analysis."
            )
            return state

        logger.info("AnalysisAgent.run(): analyzing %d evidence records.", len(records))
        results = self.analyze_evidence(records)

        for record, analysis in zip(records, results):
            record.category = analysis.category
            record.severity = analysis.severity_score
            record.confidence = analysis.confidence_score
            record.explanation = analysis.explanation

            if 0 <= record.row_number < len(state.sanitized_comments):
                comment = state.sanitized_comments[record.row_number]
                comment.categories = [analysis.category]
                comment.severity = str(analysis.severity_score)

        return state
        
