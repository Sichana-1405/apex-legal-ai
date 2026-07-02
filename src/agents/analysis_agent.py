# Analysis Agent implementation. Evaluates toxicity types and risk severity.

from src.core.state import InvestigationState

class AnalysisAgent:
    def __init__(self):
        pass

    async def run(self, state: InvestigationState) -> InvestigationState:
        """Classifies comment types (e.g. violent threats, doxxing) and computes threat severity."""
        return state
