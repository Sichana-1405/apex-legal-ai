import uuid
from datetime import datetime
from typing import List

from pydantic import BaseModel, Field

from src.core.state import InvestigationState


class EvidenceRecord(BaseModel):
    """
    Structured representation of one comment/evidence.
    """

    evidence_id: uuid.UUID = Field(default_factory=uuid.uuid4)

    row_number: int
    username: str
    comment: str
    timestamp: datetime
    platform: str

    # Filled by Analysis Agent
    category: str | None = None
    severity: int | None = None
    confidence: float | None = None
    explanation: str | None = None


class EvidenceAgent:

    def __init__(self):
        pass

    async def run(
        self,
        state: InvestigationState
    ) -> InvestigationState:

        print("\n========== Evidence Agent ==========")

        records: List[EvidenceRecord] = []

        for index, comment in enumerate(state.sanitized_comments):

            record = EvidenceRecord(

                row_number=index,

                username=comment.username,

                comment=comment.comment_text,

                timestamp=comment.timestamp,

                platform=comment.platform

            )

            records.append(record)

            print(
                f"{index+1}. {record.username} | "
                f"{record.platform} | "
                f"{record.comment}"
            )

        # Attach evidence records to the state
        state.evidence_records = records

        print(f"\nCreated {len(records)} evidence records.")

        return state