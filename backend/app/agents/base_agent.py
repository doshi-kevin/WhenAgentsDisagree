"""Base agent class with metrics collection hooks."""
import uuid
from typing import Optional
from app.llm.provider import invoke_llm


class BaseAgent:
    """Base agent that wraps LLM invocation with structured output and metrics."""

    def __init__(
        self,
        agent_id: Optional[str] = None,
        name: str = "Agent",
        provider: str = "groq",
        model_id: str = "llama-3.3-70b-versatile",
        role: str = "advocate",
        briefing: str = "",
        source_type: str = "unknown",
        position: str = "",
    ):
        self.agent_id = agent_id or str(uuid.uuid4())
        self.name = name
        self.provider = provider
        self.model_id = model_id
        self.role = role
        self.briefing = briefing
        self.source_type = source_type
        self.position = position
        self.turn_history: list[dict] = []

    async def invoke(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
    ) -> dict:
        """Invoke the LLM and return structured response with metrics."""
        result = await invoke_llm(
            provider=self.provider,
            model_id=self.model_id,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
        )

        # Track position changes
        parsed = result.get("parsed") or {}
        new_position = parsed.get("current_position") or parsed.get("vote") or parsed.get("decision")
        position_changed = False
        change_reason = None

        if new_position and self.position and new_position.lower() != self.position.lower():
            position_changed = True
            change_reason = parsed.get("change_reason", "Position changed without explicit reason")
            self.position = new_position
        elif new_position and not self.position:
            self.position = new_position

        # Also check parsed field
        if parsed.get("position_changed"):
            position_changed = True
            change_reason = parsed.get("change_reason", change_reason)

        turn_record = {
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "provider": self.provider,
            "model_id": self.model_id,
            "content": result["content"],
            "parsed": parsed,
            "confidence": parsed.get("confidence", 0.5),
            "position_held": new_position or self.position,
            "position_changed": position_changed,
            "change_reason": change_reason,
            "prompt_tokens": result["prompt_tokens"],
            "completion_tokens": result["completion_tokens"],
            "total_tokens": result["total_tokens"],
            "latency_ms": result["latency_ms"],
            "raw_response": result.get("raw_response"),
            "error": result.get("error"),
        }

        self.turn_history.append(turn_record)
        return turn_record

    @property
    def last_turn(self) -> Optional[dict]:
        return self.turn_history[-1] if self.turn_history else None

    @property
    def last_content(self) -> str:
        return self.turn_history[-1]["content"] if self.turn_history else ""
