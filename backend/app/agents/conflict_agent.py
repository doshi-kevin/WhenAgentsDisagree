"""Conflict agent - an agent assigned a position with specific briefing."""
from app.agents.base_agent import BaseAgent
from app.agents.prompts import (
    SYSTEM_BASE,
    VOTING_PROMPT,
    DEBATE_ARGUE_PROMPT,
    SUBORDINATE_BRIEF_PROMPT,
    SUBORDINATE_RESPOND_PROMPT,
    SOURCE_RANKING_PROMPT,
    WEIGHTED_ARGUMENT_PROMPT,
)


class ConflictAgent(BaseAgent):
    """Agent that holds a position based on its assigned briefing."""

    async def vote(self, question: str) -> dict:
        """Cast a vote (Majority Voting strategy)."""
        system = SYSTEM_BASE.format(agent_name=self.name)
        user = VOTING_PROMPT.format(
            agent_name=self.name,
            briefing=self.briefing,
            source_type=self.source_type,
            question=question,
        )
        return await self.invoke(system, user)

    async def argue(
        self,
        question: str,
        conversation_history: str,
        round_number: int,
        max_rounds: int,
    ) -> dict:
        """Make an argument (Structured Debate strategy)."""
        system = SYSTEM_BASE.format(agent_name=self.name)
        user = DEBATE_ARGUE_PROMPT.format(
            agent_name=self.name,
            briefing=self.briefing,
            source_type=self.source_type,
            question=question,
            conversation_history=conversation_history or "No previous discussion yet.",
            round_number=round_number,
            max_rounds=max_rounds,
        )
        return await self.invoke(system, user)

    async def brief_subordinate(self, question: str) -> dict:
        """Provide a subordinate brief (Hierarchical strategy)."""
        system = SYSTEM_BASE.format(agent_name=self.name)
        user = SUBORDINATE_BRIEF_PROMPT.format(
            agent_name=self.name,
            briefing=self.briefing,
            source_type=self.source_type,
            question=question,
        )
        return await self.invoke(system, user)

    async def respond_to_lead(self, question_from_lead: str) -> dict:
        """Respond to lead agent's question (Hierarchical strategy)."""
        system = SYSTEM_BASE.format(agent_name=self.name)
        user = SUBORDINATE_RESPOND_PROMPT.format(
            agent_name=self.name,
            briefing=self.briefing,
            question_from_lead=question_from_lead,
        )
        return await self.invoke(system, user)

    async def rank_sources(self, question: str, all_sources: str) -> dict:
        """Rank evidence sources (Evidence-Weighted strategy)."""
        system = SYSTEM_BASE.format(agent_name=self.name)
        user = SOURCE_RANKING_PROMPT.format(
            agent_name=self.name,
            all_sources=all_sources,
            question=question,
        )
        return await self.invoke(system, user)

    async def weighted_argue(
        self,
        question: str,
        source_rankings: str,
        conversation_history: str,
    ) -> dict:
        """Make an evidence-weighted argument (Evidence-Weighted strategy)."""
        system = SYSTEM_BASE.format(agent_name=self.name)
        user = WEIGHTED_ARGUMENT_PROMPT.format(
            agent_name=self.name,
            briefing=self.briefing,
            source_rankings=source_rankings,
            question=question,
            conversation_history=conversation_history or "No previous arguments yet.",
        )
        return await self.invoke(system, user)
