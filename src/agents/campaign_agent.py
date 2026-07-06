# Campaign Detection Agent. Clusters messages semantically and tracks burst events.
# Consumes AnalysisResult-annotated evidence records and identifies coordinated harassment
# campaigns through message deduplication, cross-user repetition, and temporal burst analysis.

import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field, field_validator

from src.agents.evidence_agent import EvidenceRecord
from src.core.state import InvestigationState
from src.skills.campaign_clustering import cluster_similar_comments

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration Model
# ---------------------------------------------------------------------------

class CampaignConfig(BaseModel):
    """
    Configurable parameters controlling the sensitivity of campaign detection.

    Attributes:
        similarity_threshold:    Levenshtein similarity score (0.0–1.0) above which two
                                 comments are considered effectively identical. Default 0.80
                                 catches duplicates and near-duplicates but avoids false
                                 positives on merely similar comments.
        min_cluster_size:        Minimum number of comments in a similarity cluster
                                 required before it is promoted to a campaign signal.
        min_unique_accounts:     Minimum number of *distinct* usernames that must be
                                 involved for the cluster to qualify as a coordinated campaign
                                 (guards against a single user spamming).
        burst_window_minutes:    Time window (in minutes) used to measure temporal bursts.
        burst_threshold:         Minimum number of matching messages that must occur within
                                 the burst window to trigger a burst signal.
        high_confidence_cutoff:  If all three signals (cluster, cross-user, burst) fire,
                                 confidence is capped at this value (0.0–1.0).
    """
    similarity_threshold: float = Field(default=0.80, ge=0.0, le=1.0)
    min_cluster_size: int = Field(default=2, ge=2)
    min_unique_accounts: int = Field(default=2, ge=2)
    burst_window_minutes: int = Field(default=60, ge=1)
    burst_threshold: int = Field(default=3, ge=2)
    high_confidence_cutoff: float = Field(default=0.97, ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Output Model
# ---------------------------------------------------------------------------

class CampaignResult(BaseModel):
    """
    Structured output model for the Campaign Detection Agent.

    This result is decision-support data only and does NOT constitute legal advice
    or a determination of legal guilt.  It characterises observable statistical
    patterns in the evidence dataset.

    Attributes:
        campaign_detected:   True when at least one coordinated-campaign signal fires.
        confidence_score:    Aggregate evidence weight (0.0 = no signal, 1.0 = maximum).
        repeated_message:    The canonical repeated message text, or None if no cluster
                             was large enough to qualify.
        affected_accounts:   Deduplicated list of usernames associated with the dominant
                             campaign cluster.
        explanation:         Plain-language summary of which signals fired and why.
                             Uses objective, clinical language per workspace policy.
        cluster_map:         Full mapping of cluster_id → list of comment indices for
                             downstream audit trail use (may be empty dict).
        burst_count:         Number of qualifying messages observed inside the burst window
                             for the dominant cluster (0 if burst signal did not fire).
        total_comments_analyzed: Total number of comments passed into the detector.
    """
    campaign_detected: bool = Field(
        description="True when coordinated campaign patterns are statistically present."
    )
    confidence_score: float = Field(
        description="Aggregated signal weight ranging from 0.0 (none) to 1.0 (maximum).",
        ge=0.0,
        le=1.0,
    )
    repeated_message: Optional[str] = Field(
        default=None,
        description="The canonical repeated message text identified as the campaign anchor."
    )
    affected_accounts: List[str] = Field(
        default_factory=list,
        description="Deduplicated list of usernames associated with the dominant cluster."
    )
    explanation: str = Field(
        description="Objective, clinical summary of which detection signals were observed."
    )
    cluster_map: dict = Field(
        default_factory=dict,
        description="Full cluster_id → [comment_indices] mapping for audit purposes."
    )
    burst_count: int = Field(
        default=0,
        ge=0,
        description="Number of messages in the burst window for the dominant cluster."
    )
    total_comments_analyzed: int = Field(
        default=0,
        ge=0,
        description="Total number of comments that were evaluated."
    )

    @field_validator("confidence_score")
    @classmethod
    def clamp_confidence(cls, value: float) -> float:
        """Ensure confidence remains within the valid [0.0, 1.0] range."""
        return max(0.0, min(1.0, round(value, 4)))


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _dominant_cluster(
    cluster_map: dict[int, List[int]],
    min_size: int,
) -> Optional[Tuple[int, List[int]]]:
    """
    Return the (cluster_id, indices) pair with the most members that meets the
    minimum size threshold, or None if no such cluster exists.

    Args:
        cluster_map:  Output from ``cluster_similar_comments`` mapping cluster_id
                      to a list of comment-index integers.
        min_size:     Minimum cluster membership required to qualify.

    Returns:
        A (cluster_id, member_indices) tuple for the largest qualifying cluster,
        or None if no cluster qualifies.
    """
    qualifying = {
        cid: members
        for cid, members in cluster_map.items()
        if len(members) >= min_size
    }
    if not qualifying:
        return None
    # Pick the cluster with the most members
    best_id = max(qualifying, key=lambda cid: len(qualifying[cid]))
    return best_id, qualifying[best_id]


def _extract_unique_accounts(
    member_indices: List[int],
    records: List[EvidenceRecord],
) -> List[str]:
    """
    Collect and deduplicate usernames for the comments at the given indices.

    Args:
        member_indices: List of integer indices into *records*.
        records:        Full list of EvidenceRecord objects.

    Returns:
        Sorted list of unique usernames.
    """
    usernames: set[str] = set()
    for idx in member_indices:
        if 0 <= idx < len(records):
            usernames.add(records[idx].username)
    return sorted(usernames)


def _canonical_message(
    member_indices: List[int],
    records: List[EvidenceRecord],
) -> str:
    """
    Identify the most frequently occurring comment text within a cluster as the
    canonical repeated message.

    Args:
        member_indices: Comment indices belonging to the cluster.
        records:        Full list of EvidenceRecord objects.

    Returns:
        The most common comment text string (stripped and lowercased for comparison,
        but returned in its original casing).
    """
    texts: List[str] = []
    for idx in member_indices:
        if 0 <= idx < len(records):
            texts.append(records[idx].comment.strip())

    if not texts:
        return ""

    # Use the most-common text as the canonical message
    counter = Counter(texts)
    return counter.most_common(1)[0][0]


def _detect_burst(
    member_indices: List[int],
    records: List[EvidenceRecord],
    window_minutes: int,
    burst_threshold: int,
) -> Tuple[bool, int]:
    """
    Detect whether the cluster messages exhibit a temporal burst — i.e., whether
    *burst_threshold* or more messages occur within a rolling *window_minutes* window.

    This uses a sliding-window scan over the sorted timestamp sequence.

    Args:
        member_indices:  Comment indices belonging to the cluster.
        records:         Full list of EvidenceRecord objects.
        window_minutes:  Rolling time window size in minutes.
        burst_threshold: Number of messages required within the window to fire.

    Returns:
        A (burst_detected: bool, max_count_in_window: int) tuple.
    """
    # Collect sorted timestamps for the cluster members
    timestamps: List[datetime] = []
    for idx in member_indices:
        if 0 <= idx < len(records):
            ts = records[idx].timestamp
            # Ensure timezone-naive for uniform comparison
            if hasattr(ts, "tzinfo") and ts.tzinfo is not None:
                ts = ts.replace(tzinfo=None)
            timestamps.append(ts)

    if not timestamps:
        return False, 0

    timestamps.sort()
    window = timedelta(minutes=window_minutes)
    max_count = 1

    # Two-pointer sliding window
    left = 0
    for right in range(len(timestamps)):
        while timestamps[right] - timestamps[left] > window:
            left += 1
        count = right - left + 1
        if count > max_count:
            max_count = count

    return max_count >= burst_threshold, max_count


def _compute_confidence(
    cluster_signal: bool,
    cross_user_signal: bool,
    burst_signal: bool,
    cluster_size: int,
    unique_account_count: int,
    burst_count: int,
    config: CampaignConfig,
) -> float:
    """
    Aggregate the three independent detection signals into a single confidence score.

    Scoring strategy (additive with caps):
      - Base cluster signal:         +0.40 (qualifies on size alone)
      - Cross-user signal:           +0.30 (multiple distinct accounts posting same text)
      - Burst signal:                +0.20 (temporal concentration)
      - Proportional cluster bonus:  up to +0.07 (scales with cluster_size beyond minimum)
      - Proportional account bonus:  up to +0.03 (scales with unique account count)

    Each signal is independent; total is clamped to [0.0, high_confidence_cutoff].

    Args:
        cluster_signal:       Whether a large enough similarity cluster was detected.
        cross_user_signal:    Whether multiple distinct accounts are in the cluster.
        burst_signal:         Whether a temporal burst was detected.
        cluster_size:         Total members in the dominant cluster.
        unique_account_count: Number of distinct usernames in the cluster.
        burst_count:          Messages observed within the burst window.
        config:               CampaignConfig governing thresholds.

    Returns:
        Float confidence score clamped to [0.0, config.high_confidence_cutoff].
    """
    score = 0.0

    if cluster_signal:
        score += 0.40
        # Proportional bonus: each extra comment above minimum adds a small increment,
        # capped so that a very large cluster doesn't inflate beyond 0.07 extra.
        extra_comments = max(0, cluster_size - config.min_cluster_size)
        score += min(0.07, extra_comments * 0.01)

    if cross_user_signal:
        score += 0.30
        # Additional bonus per extra unique account above the minimum required
        extra_accounts = max(0, unique_account_count - config.min_unique_accounts)
        score += min(0.03, extra_accounts * 0.005)

    if burst_signal:
        score += 0.20
        # Small scaling bonus for larger bursts
        extra_burst = max(0, burst_count - config.burst_threshold)
        score += min(0.05, extra_burst * 0.005)

    return min(score, config.high_confidence_cutoff)


def _build_explanation(
    cluster_signal: bool,
    cross_user_signal: bool,
    burst_signal: bool,
    cluster_size: int,
    unique_account_count: int,
    burst_count: int,
    window_minutes: int,
    total_comments: int,
) -> str:
    """
    Compose a clinical, objective plain-language explanation of detected signals.
    Adheres to workspace policy: no legal conclusions, no guilt determinations.

    Returns:
        Multi-sentence explanation string.
    """
    parts: List[str] = []

    parts.append(
        f"Analysis was conducted across {total_comments} comments."
    )

    if cluster_signal:
        parts.append(
            f"A similarity cluster containing {cluster_size} comments was identified "
            f"using text-similarity scoring. This cluster exhibits characteristics "
            f"consistent with repeated or near-identical message patterns as defined "
            f"by platform safety policy."
        )
    else:
        parts.append(
            "No similarity cluster of sufficient size was detected."
        )

    if cross_user_signal:
        parts.append(
            f"The cluster was associated with {unique_account_count} distinct account "
            f"identifiers, exhibiting characteristics consistent with coordinated "
            f"multi-account activity as defined by platform safety policy."
        )
    else:
        parts.append(
            "Insufficient distinct account identifiers were present in the cluster "
            "to satisfy the cross-user coordination threshold."
        )

    if burst_signal:
        parts.append(
            f"A temporal burst of {burst_count} messages was observed within a "
            f"{window_minutes}-minute window, exhibiting characteristics consistent "
            f"with a concentrated activity event as defined by platform safety policy."
        )
    else:
        parts.append(
            f"No temporal burst exceeding the {window_minutes}-minute window threshold "
            "was detected."
        )

    if not (cluster_signal or cross_user_signal or burst_signal):
        parts.append(
            "No coordinated campaign indicators were detected in the submitted dataset."
        )

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class CampaignAgent:
    """
    Campaign Detection Agent for Apex Legal AI.

    Accepts a list of ``EvidenceRecord`` objects (optionally pre-classified by the
    Analysis Agent) and applies three orthogonal detection signals:

    1. **Similarity clustering** — delegates to ``cluster_similar_comments`` from
       ``src.skills.campaign_clustering`` to group lexically/semantically near-identical
       comments using TF-IDF cosine similarity or edit distance.

    2. **Cross-user repetition** — verifies that the cluster involves multiple *distinct*
       account identifiers, distinguishing coordinated multi-account behaviour from a
       single-user spam burst.

    3. **Temporal burst detection** — uses a sliding-window scan over sorted timestamps
       to detect concentrated activity surges within a configurable rolling window.

    The agent is stateless; call ``detect()`` to run analysis directly on evidence records
    or ``run()`` for ADK pipeline integration through ``InvestigationState``.

    All output language is objective and clinical. This agent does NOT make legal
    determinations. Results are decision-support data only.
    """

    def __init__(self, config: Optional[CampaignConfig] = None) -> None:
        """
        Initialise the CampaignAgent.

        Args:
            config: Optional ``CampaignConfig`` to override detection sensitivity.
                    Defaults to ``CampaignConfig()`` with balanced thresholds.
        """
        self.config: CampaignConfig = config or CampaignConfig()
        logger.debug(
            "CampaignAgent initialised with config: %s", self.config.model_dump()
        )

    def detect(self, records: List[EvidenceRecord]) -> CampaignResult:
        """
        Run campaign detection on a list of evidence records.

        This is the primary analysis entry point.  It orchestrates the three detection
        signals, aggregates a confidence score, and returns a fully populated
        ``CampaignResult`` model.

        Args:
            records: List of ``EvidenceRecord`` objects, each containing at minimum
                     a ``username``, ``comment``, and ``timestamp``.  These are typically
                     produced by ``EvidenceAgent.process_dataframe()`` and may have been
                     pre-classified by ``AnalysisAgent``.

        Returns:
            A ``CampaignResult`` Pydantic model capturing all detected signals, the
            dominant repeated message, affected accounts, and an objective explanation.
        """
        total = len(records)

        # Guard: nothing to analyse
        if total == 0:
            logger.info("CampaignAgent received an empty records list.")
            return CampaignResult(
                campaign_detected=False,
                confidence_score=0.0,
                repeated_message=None,
                affected_accounts=[],
                explanation="No comments were provided for campaign analysis.",
                cluster_map={},
                burst_count=0,
                total_comments_analyzed=0,
            )

        # ------------------------------------------------------------------ #
        # Step 1: Extract raw comment texts for clustering
        # ------------------------------------------------------------------ #
        texts: List[str] = [r.comment.strip() for r in records]

        # ------------------------------------------------------------------ #
        # Step 2: Similarity clustering via the shared skill
        #         cluster_similar_comments returns Dict[int, List[int]] where
        #         key = cluster_id, value = list of indices into *texts*.
        # ------------------------------------------------------------------ #
        logger.debug("Running cluster_similar_comments on %d comments …", total)
        try:
            cluster_map: dict[int, List[int]] = cluster_similar_comments(
                texts, threshold=self.config.similarity_threshold
            )
        except Exception as exc:
            # Defensive: clustering failure should not hard-crash the pipeline.
            logger.warning("cluster_similar_comments raised an exception: %s", exc)
            cluster_map = {}

        # ------------------------------------------------------------------ #
        # Step 3: Identify the dominant cluster (largest above min_cluster_size)
        # ------------------------------------------------------------------ #
        dominant = _dominant_cluster(cluster_map, self.config.min_cluster_size)

        cluster_signal = dominant is not None
        cluster_size = 0
        member_indices: List[int] = []
        canonical_text: Optional[str] = None

        if dominant is not None:
            _, member_indices = dominant
            cluster_size = len(member_indices)
            canonical_text = _canonical_message(member_indices, records)
            logger.debug(
                "Dominant cluster: %d members, canonical text: %.60s …",
                cluster_size,
                canonical_text,
            )

        # ------------------------------------------------------------------ #
        # Step 4: Cross-user signal — require ≥ min_unique_accounts distinct
        #         usernames within the dominant cluster.
        # ------------------------------------------------------------------ #
        affected_accounts: List[str] = []
        cross_user_signal = False

        if cluster_signal:
            affected_accounts = _extract_unique_accounts(member_indices, records)
            cross_user_signal = len(affected_accounts) >= self.config.min_unique_accounts
            logger.debug(
                "Cross-user signal: %s (%d unique accounts)",
                cross_user_signal,
                len(affected_accounts),
            )

        # ------------------------------------------------------------------ #
        # Step 5: Temporal burst detection within the dominant cluster
        # ------------------------------------------------------------------ #
        burst_signal = False
        burst_count = 0

        if cluster_signal:
            burst_signal, burst_count = _detect_burst(
                member_indices,
                records,
                window_minutes=self.config.burst_window_minutes,
                burst_threshold=self.config.burst_threshold,
            )
            logger.debug(
                "Burst signal: %s (count=%d in %d-min window)",
                burst_signal,
                burst_count,
                self.config.burst_window_minutes,
            )

        # ------------------------------------------------------------------ #
        # Step 6: Aggregate confidence score
        # ------------------------------------------------------------------ #
        confidence = _compute_confidence(
            cluster_signal=cluster_signal,
            cross_user_signal=cross_user_signal,
            burst_signal=burst_signal,
            cluster_size=cluster_size,
            unique_account_count=len(affected_accounts),
            burst_count=burst_count,
            config=self.config,
        )

        # Campaign is detected when at least one signal fires (cluster alone
        # is sufficient to flag; cross-user or burst further confirm).
        campaign_detected = cluster_signal

        # ------------------------------------------------------------------ #
        # Step 7: Compose explanation
        # ------------------------------------------------------------------ #
        explanation = _build_explanation(
            cluster_signal=cluster_signal,
            cross_user_signal=cross_user_signal,
            burst_signal=burst_signal,
            cluster_size=cluster_size,
            unique_account_count=len(affected_accounts),
            burst_count=burst_count,
            window_minutes=self.config.burst_window_minutes,
            total_comments=total,
        )

        logger.info(
            "CampaignAgent result — detected=%s, confidence=%.4f, accounts=%d",
            campaign_detected,
            confidence,
            len(affected_accounts),
        )

        return CampaignResult(
            campaign_detected=campaign_detected,
            confidence_score=confidence,
            repeated_message=canonical_text,
            affected_accounts=affected_accounts,
            explanation=explanation,
            cluster_map={str(k): v for k, v in cluster_map.items()},
            burst_count=burst_count,
            total_comments_analyzed=total,
        )

    async def run(self, state: InvestigationState) -> InvestigationState:
        """
        ADK-compliant pipeline execution interface.

        Reads sanitized comments from ``InvestigationState``, converts them to
        lightweight ``EvidenceRecord`` proxies, runs campaign detection, and
        writes the resulting cluster mapping back to
        ``state.campaign_clusters`` for downstream consumption by the Report Agent.

        Args:
            state: The shared ``InvestigationState`` pipeline context object.

        Returns:
            The updated ``InvestigationState`` with ``campaign_clusters`` populated.
        """
        if not state.sanitized_comments:
            logger.info(
                "CampaignAgent.run(): state has no sanitized_comments — skipping."
            )
            return state

        # ------------------------------------------------------------------ #
        # Convert InvestigationState CommentData → lightweight EvidenceRecord
        # proxies so that detect() can operate on a uniform input type.
        # Filter out 'Safe' comments — only analyze flagged content.
        # ------------------------------------------------------------------ #
        records: List[EvidenceRecord] = []
        for idx, comment in enumerate(state.sanitized_comments):
            try:
                # Skip 'Safe' comments — only process flagged/problematic content
                if comment.severity == "Safe":
                    logger.debug("Skipping Safe comment at index %d", idx)
                    continue
                
                record = EvidenceRecord(
                    row_number=idx,
                    username=comment.username,
                    comment=comment.comment_text,
                    timestamp=comment.timestamp,
                    platform=comment.platform,
                )
                records.append(record)
            except Exception as exc:
                # Log conversion failures but continue processing the rest
                logger.warning(
                    "Failed to convert CommentData at index %d to EvidenceRecord: %s",
                    idx,
                    exc,
                )

        if not records:
            logger.warning(
                "CampaignAgent.run(): all CommentData conversions failed — "
                "returning state unchanged."
            )
            return state

        # ------------------------------------------------------------------ #
        # Run campaign detection
        # ------------------------------------------------------------------ #
        result: CampaignResult = self.detect(records)

        # ------------------------------------------------------------------ #
        # Persist cluster mapping to the shared state for the Report Agent.
        # cluster_map keys are cluster_id strings; values are lists of comment
        # index strings (converted for JSON/state serialisation safety).
        # ------------------------------------------------------------------ #
        state.campaign_clusters = {
            cluster_id: [str(i) for i in indices]
            for cluster_id, indices in result.cluster_map.items()
        }

        logger.info(
            "CampaignAgent.run() completed for case '%s': "
            "campaign_detected=%s, confidence=%.4f, clusters=%d",
            state.case_id,
            result.campaign_detected,
            result.confidence_score,
            len(result.cluster_map),
        )

        return state
