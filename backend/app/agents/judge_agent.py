"""Judge agent - evaluates debates and resolves deadlocks."""
from app.agents.base_agent import BaseAgent
from app.agents.prompts import (
    SYSTEM_BASE,
    LEAD_DECISION_PROMPT,
    LEAD_QUESTION_PROMPT,
    JUDGE_PROMPT,
    DEADLOCK_RESOLUTION_PROMPT,
)


class JudgeAgent(BaseAgent):
    """Agent that evaluates arguments and makes final decisions."""

    def __init__(self, **kwargs):
        kwargs.setdefault("role", "judge")
        kwargs.setdefault("name", "Judge")
        super().__init__(**kwargs)

    async def judge_debate(self, question: str, transcript: str) -> dict:
        """Judge a debate and determine the winner."""
        system = SYSTEM_BASE.format(agent_name=self.name)
        user = JUDGE_PROMPT.format(
            question=question,
            transcript=transcript,
        )
        return await self.invoke(system, user, temperature=0.3)

    async def lead_decision(self, question: str, subordinate_briefs: str) -> dict:
        """Make a lead decision based on subordinate briefs."""
        system = SYSTEM_BASE.format(agent_name=self.name)
        user = LEAD_DECISION_PROMPT.format(
            agent_name=self.name,
            question=question,
            subordinate_briefs=subordinate_briefs,
        )
        return await self.invoke(system, user, temperature=0.3)

    async def lead_ask_questions(self, question: str, subordinate_briefs: str) -> dict:
        """Ask follow-up questions as lead agent."""
        system = SYSTEM_BASE.format(agent_name=self.name)
        user = LEAD_QUESTION_PROMPT.format(
            agent_name=self.name,
            question=question,
            subordinate_briefs=subordinate_briefs,
        )
        return await self.invoke(system, user, temperature=0.5)

    async def resolve_deadlock(
        self, question: str, transcript: str, deadlock_details: str
    ) -> dict:
        """Resolve a deadlocked debate."""
        system = SYSTEM_BASE.format(agent_name=self.name)
        user = DEADLOCK_RESOLUTION_PROMPT.format(
            question=question,
            transcript=transcript,
            deadlock_details=deadlock_details,
        )
        return await self.invoke(system, user, temperature=0.3)
