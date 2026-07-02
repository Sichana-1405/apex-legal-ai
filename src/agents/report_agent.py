# Report Agent implementation. Generates structured case file markdown from evidence data.

from src.core.state import InvestigationState

class ReportAgent:
    def __init__(self):
        pass

    async def run(self, state: InvestigationState) -> InvestigationState:
        """Consolidates timelines and campaign details into a structured markdown report draft."""
        return state
