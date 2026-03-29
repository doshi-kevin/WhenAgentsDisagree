"""Conflict agent - an agent assigned a position with specific briefing."""
from app.agents.base_agent import BaseAgent
from app.agents.prompts import (
    SYSTEM_BASE,
    BIAS_ROLE_AUGMENTS,
    VOTING_PROMPT,
    DEBATE_ARGUE_PROMPT,
    SUBORDINATE_BRIEF_PROMPT,
    SUBORDINATE_RESPOND_PROMPT,
    SOURCE_RANKING_PROMPT,
    WEIGHTED_ARGUMENT_PROMPT,
)


class ConflictAgent(BaseAgent):
    """Agent that holds a position based on its assigned briefing."""

    def __init__(self, bias_role: str = "", **kwargs):
        super().__init__(**kwargs)
        self.bias_role = bias_role

    def _system_prompt(self) -> str:
        """Build system prompt with optional bias role augmentation."""
        prompt = SYSTEM_BASE.format(agent_name=self.name)
        if self.bias_role and self.bias_role in BIAS_ROLE_AUGMENTS:
            prompt += BIAS_ROLE_AUGMENTS[self.bias_role]
        return prompt

    async def vote(self, question: str) -> dict:
        """Cast a vote (Majority Voting strategy)."""
        system = self._system_prompt()
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
        novelty_section: str = "",
    ) -> dict:
        """Make an argument (Structured Debate strategy)."""
        system = self._system_prompt()
        user = DEBATE_ARGUE_PROMPT.format(
            agent_name=self.name,
            briefing=self.briefing,
            source_type=self.source_type,
            question=question,
            conversation_history=conversation_history or "No previous discussion yet.",
            round_number=round_number,
            max_rounds=max_rounds,
            novelty_section=novelty_section,
        )
        return await self.invoke(system, user)

    async def brief_subordinate(self, question: str) -> dict:
        """Provide a subordinate brief (Hierarchical strategy)."""
        system = self._system_prompt()
        user = SUBORDINATE_BRIEF_PROMPT.format(
            agent_name=self.name,
            briefing=self.briefing,
            source_type=self.source_type,
            question=question,
        )
        return await self.invoke(system, user)

    async def respond_to_lead(self, question_from_lead: str) -> dict:
        """Respond to lead agent's question (Hierarchical strategy)."""
        system = self._system_prompt()
        user = SUBORDINATE_RESPOND_PROMPT.format(
            agent_name=self.name,
            briefing=self.briefing,
            question_from_lead=question_from_lead,
        )
        return await self.invoke(system, user)

    async def rank_sources(self, question: str, all_sources: str) -> dict:
        """Rank evidence sources (Evidence-Weighted strategy)."""
        system = self._system_prompt()
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
        system = self._system_prompt()
        user = WEIGHTED_ARGUMENT_PROMPT.format(
            agent_name=self.name,
            briefing=self.briefing,
            source_rankings=source_rankings,
            question=question,
            conversation_history=conversation_history or "No previous arguments yet.",
        )
        return await self.invoke(system, user)
