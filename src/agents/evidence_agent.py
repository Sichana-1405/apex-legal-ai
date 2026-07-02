# Evidence Agent implementation. Extracts structured metadata (handles, platforms, target/abuser).

from src.core.state import InvestigationState

class EvidenceAgent:
    def __init__(self):
        pass

    async def run(self, state: InvestigationState) -> InvestigationState:
        """Extracts actors, timestamps, platforms and structures raw comments into records."""
        return state
