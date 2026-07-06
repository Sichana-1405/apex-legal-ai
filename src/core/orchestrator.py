# Google ADK Pipeline Orchestrator — Apex Legal AI
#
# Executes the five-agent investigation pipeline sequentially, propagating
# InvestigationState through each stage.  Each stage is wrapped in a
# structured error boundary: recoverable errors are logged and allow the
# pipeline to continue; unrecoverable exceptions are caught, recorded in
# state, and cause an early return so the caller always receives a valid
# InvestigationState rather than an unhandled exception.

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, List, Optional

import yaml

from src.agents.analysis_agent import AnalysisAgent
from src.agents.campaign_agent import CampaignAgent, CampaignConfig
from src.agents.evidence_agent import EvidenceAgent
from src.agents.report_agent import ReportAgent
from src.agents.security_agent import SecurityAgent
from src.core.state import InvestigationState

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pipeline stage status — used in the execution log returned to callers
# ---------------------------------------------------------------------------

class StageStatus(str, Enum):
    """Outcome of a single pipeline stage execution."""
    COMPLETED = "COMPLETED"
    SKIPPED   = "SKIPPED"    # stage disabled in config
    FAILED    = "FAILED"     # exception caught; pipeline may continue or halt


@dataclass
class StageRecord:
    """
    Immutable audit record for one pipeline stage.

    Attributes:
        agent_name:    Human-readable name of the agent that ran.
        status:        One of the StageStatus enum values.
        elapsed_ms:    Wall-clock duration of the stage in milliseconds.
        error_message: Populated only when status == FAILED.
        completed_at:  UTC timestamp at the moment the stage finished.
    """
    agent_name: str
    status: StageStatus
    elapsed_ms: float
    error_message: Optional[str] = None
    completed_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __str__(self) -> str:
        base = (
            f"[{self.status.value}] {self.agent_name} "
            f"({self.elapsed_ms:.1f} ms) @ {self.completed_at.isoformat()}"
        )
        if self.error_message:
            base += f" | error: {self.error_message}"
        return base


@dataclass
class PipelineResult:
    """
    Container returned by ``ApexLegalOrchestrator.execute_investigation()``.

    Attributes:
        state:          Final ``InvestigationState`` after all stages complete.
        stages:         Ordered list of ``StageRecord`` audit entries.
        pipeline_ok:    True when every enabled stage completed without error.
        total_elapsed_ms: Total wall-clock time for the full pipeline in ms.
    """
    state: InvestigationState
    stages: List[StageRecord]
    pipeline_ok: bool
    total_elapsed_ms: float

    @property
    def failed_stages(self) -> List[StageRecord]:
        """Convenience accessor — returns only FAILED stage records."""
        return [s for s in self.stages if s.status == StageStatus.FAILED]

    def summary(self) -> str:
        """One-line human-readable summary suitable for logging."""
        status_word = "OK" if self.pipeline_ok else "DEGRADED"
        return (
            f"Pipeline {status_word} | "
            f"case={self.state.case_id} | "
            f"stages={len(self.stages)} | "
            f"failed={len(self.failed_stages)} | "
            f"total={self.total_elapsed_ms:.1f} ms"
        )


# ---------------------------------------------------------------------------
# YAML config loader helper
# ---------------------------------------------------------------------------

def _load_yaml_config(path: str) -> dict:
    """
    Load a YAML configuration file and return its contents as a plain dict.
    Returns an empty dict if the file is missing or malformed so the
    orchestrator can fall back to sane defaults gracefully.

    Args:
        path: Absolute or relative filesystem path to the YAML file.

    Returns:
        Parsed YAML contents as a dict, or ``{}`` on any error.
    """
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        logger.debug("Loaded ADK config from '%s': %s", path, data)
        return data
    except FileNotFoundError:
        logger.warning("Config file not found at '%s'; using defaults.", path)
        return {}
    except yaml.YAMLError as exc:
        logger.warning(
            "Failed to parse YAML config at '%s': %s; using defaults.", path, exc
        )
        return {}


def _agent_enabled(config: dict, agent_key: str) -> bool:
    """
    Check whether an agent is enabled in the loaded YAML config.

    Falls back to True (enabled) if the key is absent, so the pipeline runs
    in full with a missing or partial config file.

    Args:
        config:    Parsed YAML config dict (may be empty).
        agent_key: Key under config['agents'] (e.g. 'security', 'campaign').

    Returns:
        bool: True if the agent should be executed; False to skip it.
    """
    agents_block = config.get("agents", {})
    agent_cfg = agents_block.get(agent_key, {})
    # Treat missing key as enabled=True
    return agent_cfg.get("enabled", True)


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class ApexLegalOrchestrator:
    """
    Google ADK-style sequential pipeline orchestrator for Apex Legal AI.

    Instantiates each of the five specialist agents once during ``__init__``,
    then executes them in a fixed order during ``execute_investigation()``.
    The shared ``InvestigationState`` object is threaded through every agent;
    each agent mutates a copy of the state and returns the updated version.

    Pipeline order
    --------------
    1. SecurityAgent   — sanitise raw input CSV; scrub PII
    2. EvidenceAgent   — structure sanitised data into EvidenceRecord objects
    3. AnalysisAgent   — classify toxicity category, severity, and confidence
    4. CampaignAgent   — detect coordinated campaigns, bursts, and repetition
    5. ReportAgent     — draft a structured markdown case report

    Error handling
    --------------
    Each stage is executed inside an isolated try/except block.  If an agent
    raises an unhandled exception:
      - The error is logged at ERROR level with full traceback.
      - A human-readable error message is stored in ``state.report_draft_markdown``
        (prefixed with ``[PIPELINE ERROR]``) so the caller always receives
        actionable output rather than a raw exception.
      - The ``StageRecord`` for that stage is marked ``FAILED``.
      - Pipeline execution **halts immediately** — subsequent stages are skipped
        rather than operating on potentially corrupt state.

    Usage
    -----
    ::

        orchestrator = ApexLegalOrchestrator(config_path="config/adk_config.yaml")
        result = await orchestrator.execute_investigation(initial_state)
        print(result.summary())
        final_state = result.state
    """

    def __init__(self, config_path: str = "config/adk_config.yaml") -> None:
        """
        Initialise the orchestrator and all five pipeline agents.

        Args:
            config_path: Path to the YAML configuration file.  Defaults to the
                         standard project location.  Agents respect the
                         ``agents.<name>.enabled`` flag from this file.
        """
        self.config_path = config_path
        self._config: dict = _load_yaml_config(config_path)

        logger.info(
            "ApexLegalOrchestrator initialising — config='%s'", config_path
        )

        # ------------------------------------------------------------------
        # Instantiate all five agents.
        # Each agent is created unconditionally; the enabled flag only controls
        # whether its run() method is called during pipeline execution.
        # ------------------------------------------------------------------

        # Stage 1: SecurityAgent — raw CSV validation and PII scrubbing.
        self.security_agent = SecurityAgent()

        # Stage 2: EvidenceAgent — converts sanitised rows into typed
        #          EvidenceRecord objects and attaches them to state.
        self.evidence_agent = EvidenceAgent()

        # Stage 3: AnalysisAgent — Gemini-backed toxicity classification.
        #          Reads GEMINI_API_KEY from environment / .env automatically.
        self.analysis_agent = AnalysisAgent()

        # Stage 4: CampaignAgent — similarity clustering, cross-user repetition,
        #          and temporal burst detection.  Uses default CampaignConfig
        #          thresholds unless overridden via config.
        self.campaign_agent = CampaignAgent(config=self._build_campaign_config())

        # Stage 5: ReportAgent — consolidates all state artefacts into a
        #          structured markdown case report draft.
        self.report_agent = ReportAgent()

        logger.info("All five pipeline agents instantiated successfully.")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def execute_investigation(
        self, initial_state: InvestigationState
    ) -> PipelineResult:
        """
        Execute the full five-agent investigation pipeline sequentially.

        The pipeline threads a single ``InvestigationState`` object through
        each agent in order.  After every stage the returned state is
        validated to be a non-None ``InvestigationState`` instance before
        passing it on.

        Args:
            initial_state: A pre-populated ``InvestigationState`` containing at
                           minimum a ``case_id``, ``case_name``, and
                           ``raw_comments`` list.

        Returns:
            A ``PipelineResult`` dataclass holding:
            - the final state object
            - an ordered list of ``StageRecord`` audit entries
            - a boolean indicating overall pipeline health
            - total elapsed wall-clock time in milliseconds
        """
        pipeline_start = time.perf_counter()
        stage_records: List[StageRecord] = []
        state = initial_state
        pipeline_ok = True

        logger.info(
            "Pipeline START — case_id='%s', case_name='%s', raw_comments=%d",
            state.case_id,
            state.case_name,
            len(state.raw_comments),
        )

        # ------------------------------------------------------------------
        # Define the ordered stage list as (agent_key, display_name, coroutine_factory).
        # Using a list of tuples keeps the execution loop DRY and makes it
        # trivial to add, remove, or reorder stages in future.
        # ------------------------------------------------------------------
        pipeline_stages: List[tuple] = [
            ("security",  "SecurityAgent",  self.security_agent),
            ("evidence",  "EvidenceAgent",  self.evidence_agent),
            ("analysis",  "AnalysisAgent",  self.analysis_agent),
            ("campaign",  "CampaignAgent",  self.campaign_agent),
            ("report",    "ReportAgent",    self.report_agent),
        ]

        for agent_key, agent_name, agent in pipeline_stages:
            # ----------------------------------------------------------------
            # Check whether this agent is enabled in the YAML config.
            # Disabled agents are recorded as SKIPPED and do not mutate state.
            # ----------------------------------------------------------------
            if not _agent_enabled(self._config, agent_key):
                logger.info("Stage SKIPPED (disabled in config): %s", agent_name)
                stage_records.append(
                    StageRecord(
                        agent_name=agent_name,
                        status=StageStatus.SKIPPED,
                        elapsed_ms=0.0,
                    )
                )
                continue

            # ----------------------------------------------------------------
            # Execute the stage inside a structured error boundary.
            # ----------------------------------------------------------------
            record, state, fatal = await self._run_stage(
                agent_name=agent_name,
                agent=agent,
                state=state,
            )
            stage_records.append(record)

            if fatal:
                # A fatal exception was caught inside _run_stage.
                # The error has already been recorded in state.report_draft_markdown
                # and logged at ERROR level.  Stop the pipeline here to avoid
                # passing corrupt state to downstream agents.
                pipeline_ok = False
                logger.error(
                    "Pipeline HALTED after unrecoverable failure in '%s'. "
                    "Skipping remaining stages.",
                    agent_name,
                )
                # Mark all remaining stages as SKIPPED in the audit log
                remaining_idx = pipeline_stages.index(
                    (agent_key, agent_name, agent)
                ) + 1
                for _, remaining_name, _ in pipeline_stages[remaining_idx:]:
                    stage_records.append(
                        StageRecord(
                            agent_name=remaining_name,
                            status=StageStatus.SKIPPED,
                            elapsed_ms=0.0,
                            error_message="Skipped due to upstream failure.",
                        )
                    )
                break

            if record.status == StageStatus.FAILED:
                # Non-fatal failure (shouldn't be reached given current logic, but
                # kept for forward-compatibility if _run_stage semantics change).
                pipeline_ok = False

        # ------------------------------------------------------------------
        # Compute total wall-clock duration and emit a summary log line.
        # ------------------------------------------------------------------
        total_ms = (time.perf_counter() - pipeline_start) * 1000.0

        result = PipelineResult(
            state=state,
            stages=stage_records,
            pipeline_ok=pipeline_ok,
            total_elapsed_ms=total_ms,
        )

        log_fn = logger.info if pipeline_ok else logger.warning
        log_fn("Pipeline END — %s", result.summary())

        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _run_stage(
        self,
        agent_name: str,
        agent: object,
        state: InvestigationState,
    ) -> tuple[StageRecord, InvestigationState, bool]:
        """
        Execute a single pipeline stage with timing, validation, and error handling.

        This method is the core execution unit for every agent in the pipeline.
        It guarantees that:
          - The agent's ``run()`` coroutine is awaited correctly.
          - Wall-clock elapsed time is measured with high precision.
          - The returned value is validated to be a non-None InvestigationState.
          - Any exception is caught, logged with full traceback, and stored in
            state so callers always receive a usable object.

        Args:
            agent_name: Human-readable agent name for logging.
            agent:      Agent instance exposing an ``async run(state)`` method.
            state:      Current ``InvestigationState`` to pass into the agent.

        Returns:
            A 3-tuple of:
              - ``StageRecord`` — audit record for this stage
              - ``InvestigationState`` — updated state (or original on failure)
              - ``bool`` — True if the failure is fatal and the pipeline should halt
        """
        logger.info("Stage START: %s", agent_name)
        stage_start = time.perf_counter()

        try:
            # Await the agent's ADK-compliant run() coroutine
            updated_state = await agent.run(state)

            # ----------------------------------------------------------
            # Post-stage validation: the returned value must be a valid
            # InvestigationState.  A None return or wrong type indicates
            # a programming error in the agent and is treated as fatal.
            # ----------------------------------------------------------
            if updated_state is None:
                raise RuntimeError(
                    f"{agent_name}.run() returned None instead of InvestigationState."
                )
            if not isinstance(updated_state, InvestigationState):
                raise TypeError(
                    f"{agent_name}.run() returned {type(updated_state).__name__!r} "
                    f"instead of InvestigationState."
                )

            elapsed_ms = (time.perf_counter() - stage_start) * 1000.0
            record = StageRecord(
                agent_name=agent_name,
                status=StageStatus.COMPLETED,
                elapsed_ms=elapsed_ms,
            )
            logger.info(
                "Stage COMPLETED: %s in %.1f ms | "
                "sanitized=%d, clusters=%d, report_ready=%s",
                agent_name,
                elapsed_ms,
                len(updated_state.sanitized_comments),
                len(updated_state.campaign_clusters),
                updated_state.report_draft_markdown is not None,
            )
            return record, updated_state, False

        except Exception as exc:  # noqa: BLE001 — intentional broad catch
            elapsed_ms = (time.perf_counter() - stage_start) * 1000.0

            # Log the full traceback at ERROR level for observability
            logger.error(
                "Stage FAILED: %s after %.1f ms — %s: %s",
                agent_name,
                elapsed_ms,
                type(exc).__name__,
                exc,
                exc_info=True,   # include full traceback in log record
            )

            # Embed a structured error annotation in state so the caller has
            # actionable information regardless of whether it catches exceptions.
            error_msg = (
                f"[PIPELINE ERROR] Stage '{agent_name}' failed after "
                f"{elapsed_ms:.1f} ms.\n"
                f"Error type: {type(exc).__name__}\n"
                f"Details: {exc}\n\n"
                f"Pipeline execution halted at this stage.  "
                f"Stages that ran before this point may have partially updated state."
            )
            # Preserve any existing report draft content that was produced before
            # the error; prepend the error notice rather than overwriting it.
            if state.report_draft_markdown:
                state.report_draft_markdown = (
                    error_msg + "\n\n---\n\n" + state.report_draft_markdown
                )
            else:
                state.report_draft_markdown = error_msg

            record = StageRecord(
                agent_name=agent_name,
                status=StageStatus.FAILED,
                elapsed_ms=elapsed_ms,
                error_message=f"{type(exc).__name__}: {exc}",
            )
            # Return the original (pre-failure) state so downstream code that
            # might inspect it still gets the last known-good values.
            return record, state, True  # fatal=True → halt pipeline

    def _build_campaign_config(self) -> CampaignConfig:
        """
        Construct a ``CampaignConfig`` from the loaded YAML configuration.

        Reads optional overrides from the ``agents.campaign`` block in the
        YAML file.  Any missing keys fall back to ``CampaignConfig`` defaults,
        so the pipeline is fully operational with a minimal or absent config.

        Returns:
            A validated ``CampaignConfig`` instance.
        """
        campaign_cfg = self._config.get("agents", {}).get("campaign", {})

        # Extract optional overrides, defaulting to None so CampaignConfig
        # uses its own Pydantic defaults when the key is absent.
        kwargs = {}
        key_map = {
            "similarity_threshold":  "similarity_threshold",
            "min_cluster_size":      "min_cluster_size",
            "min_unique_accounts":   "min_unique_accounts",
            "burst_window_minutes":  "burst_window_minutes",
            "burst_threshold":       "burst_threshold",
            "high_confidence_cutoff": "high_confidence_cutoff",
        }
        for yaml_key, config_attr in key_map.items():
            if yaml_key in campaign_cfg:
                kwargs[config_attr] = campaign_cfg[yaml_key]

        try:
            return CampaignConfig(**kwargs)
        except Exception as exc:
            logger.warning(
                "Invalid CampaignConfig overrides in YAML (%s); "
                "falling back to defaults.", exc
            )
            return CampaignConfig()
