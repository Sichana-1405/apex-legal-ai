import asyncio
from datetime import datetime

from src.agents.analysis_agent import AnalysisAgent, AnalysisResult, _load_env_api_key
from src.agents.evidence_agent import EvidenceAgent, EvidenceRecord
from src.agents.report_agent import ReportAgent
from src.core.state import CommentData, InvestigationState


def _comment(text: str, username: str = "user") -> CommentData:
    return CommentData(
        comment_id=f"id-{username}-{text[:4]}",
        platform="X",
        username=username,
        timestamp=datetime(2026, 1, 1, 12, 0, 0),
        comment_text=text,
    )


def _state() -> InvestigationState:
    comments = [
        _comment("This is a test comment", "alice"),
        _comment("Spam message repeated", "bob"),
        _comment("Spam message repeated", "carol"),
        _comment("Normal discussion comment", "dana"),
    ]
    return InvestigationState(
        case_id="case-1",
        case_name="Regression Case",
        raw_comments=comments,
        sanitized_comments=comments,
    )


def test_evidence_agent_populates_evidence_records():
    state = asyncio.run(EvidenceAgent().run(_state()))

    assert len(state.evidence_records) == 4
    assert all(isinstance(record, EvidenceRecord) for record in state.evidence_records)
    assert [record.comment for record in state.evidence_records] == [
        "This is a test comment",
        "Spam message repeated",
        "Spam message repeated",
        "Normal discussion comment",
    ]


def test_analysis_run_calls_analyze_evidence_with_non_empty_records(monkeypatch):
    state = asyncio.run(EvidenceAgent().run(_state()))
    agent = AnalysisAgent(api_key="test-key")
    seen = {}

    def fake_analyze(records):
        seen["count"] = len(records)
        return [
            AnalysisResult(
                category="Safe",
                severity_score=1,
                confidence_score=0.99,
                explanation="Benign test content.",
            ),
            AnalysisResult(
                category="Spam",
                severity_score=3,
                confidence_score=0.98,
                explanation="Repeated spam-like content.",
            ),
            AnalysisResult(
                category="Spam",
                severity_score=3,
                confidence_score=0.98,
                explanation="Repeated spam-like content.",
            ),
            AnalysisResult(
                category="Safe",
                severity_score=1,
                confidence_score=0.99,
                explanation="Benign discussion content.",
            ),
        ]

    monkeypatch.setattr(agent, "analyze_evidence", fake_analyze)

    state = asyncio.run(agent.run(state))

    assert seen["count"] == 4
    assert [record.category for record in state.evidence_records] == [
        "Safe",
        "Spam",
        "Spam",
        "Safe",
    ]
    assert [record.severity for record in state.evidence_records] == [1, 3, 3, 1]
    assert [comment.categories[0] for comment in state.sanitized_comments] == [
        "Safe",
        "Spam",
        "Spam",
        "Safe",
    ]


def test_gemini_key_loader_and_generate_content_call(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("GEMINI_API_KEY=loaded-from-env-file\n", encoding="utf-8")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)

    assert _load_env_api_key() == "loaded-from-env-file"

    class FakeResponse:
        text = (
            '{"category":"Spam","severity_score":3,'
            '"confidence_score":0.97,"explanation":"Repeated spam-like content."}'
        )

    class FakeModels:
        def __init__(self):
            self.calls = []

        def generate_content(self, **kwargs):
            self.calls.append(kwargs)
            return FakeResponse()

    class FakeClient:
        def __init__(self):
            self.models = FakeModels()

    agent = AnalysisAgent(api_key="loaded-from-env-file")
    agent.client = FakeClient()

    result = agent.analyze_evidence(
        [
            EvidenceRecord(
                row_number=0,
                username="bob",
                comment="Spam message repeated",
                timestamp=datetime(2026, 1, 1, 12, 0, 0),
                platform="X",
            )
        ]
    )

    assert result[0].category == "Spam"
    assert result[0].severity_score == 3
    assert len(agent.client.models.calls) == 1
    assert agent.client.models.calls[0]["model"] == "gemini-2.5-flash"


def test_report_reads_classifications_from_evidence_records():
    state = asyncio.run(EvidenceAgent().run(_state()))
    classifications = [("Safe", 1, 0.99), ("Spam", 3, 0.98), ("Spam", 3, 0.98), ("Safe", 1, 0.99)]
    for record, (category, severity, confidence) in zip(state.evidence_records, classifications):
        record.category = category
        record.severity = severity
        record.confidence = confidence

    report = ReportAgent().generate_report(state)

    assert "This is a test comment" in report
    assert "Safe" in report
    assert "Spam" in report
    assert "3 / Moderate" in report
    assert "98%" in report
    assert "â“" not in report


def test_missing_gemini_key_fallback_marks_repeated_spam():
    state = asyncio.run(EvidenceAgent().run(_state()))
    agent = AnalysisAgent(api_key="")
    agent.client = None

    state = asyncio.run(agent.run(state))

    assert [record.category for record in state.evidence_records] == [
        "Safe",
        "Spam",
        "Spam",
        "Safe",
    ]
    assert [record.severity for record in state.evidence_records] == [1, 3, 3, 1]
    assert all("fallback classification used" in record.explanation for record in state.evidence_records)


def test_report_counts_spam_as_harmful_and_dominant_category():
    state = asyncio.run(EvidenceAgent().run(_state()))
    classifications = [
        ("Safe", 1, 0.91),
        ("Spam", 1, 0.88),
        ("Spam", 1, 0.86),
        ("Safe", 1, 0.90),
    ]
    for record, (category, severity, confidence) in zip(state.evidence_records, classifications):
        record.category = category
        record.severity = severity
        record.confidence = confidence

    report = ReportAgent().generate_report(state)

    assert "**Harmful Comments Detected** | 2 (50.0%)" in report
    assert "**Safe / Benign Comments** | 2" in report
    assert "Of the total dataset, **2** comment(s) were classified" in report
    assert "**Dominant harmful category:** **Spam** (2)." in report
