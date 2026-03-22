import asyncio
import time
import json
import re
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import settings
from app.llm.rate_limiter import RateLimiter


PROVIDER_CONFIG = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "api_key": lambda: settings.groq_api_key,
        "models": {
            "llama-3.3-70b-versatile": {"rpm": 30, "rpd": 1000, "tpm": 131072},
            "llama-3.1-8b-instant": {"rpm": 30, "rpd": 14400, "tpm": 131072},
        },
    },
    "cerebras": {
        "base_url": "https://api.cerebras.ai/v1",
        "api_key": lambda: settings.cerebras_api_key,
        "models": {
            "llama3.1-8b": {"rpm": 30, "rpd": None, "tpd": 1000000},
        },
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": lambda: settings.openrouter_api_key,
        "models": {
            "nvidia/nemotron-3-super-120b-a12b:free": {"rpm": 20, "rpd": 200},
            "meta-llama/llama-3.3-70b-instruct:free": {"rpm": 20, "rpd": 200},
        },
    },
}

# Global rate limiter instance
rate_limiter = RateLimiter()


def get_llm(provider: str, model_id: str, temperature: float = 0.7) -> ChatOpenAI:
    """Create a ChatOpenAI instance for the given provider and model."""
    config = PROVIDER_CONFIG.get(provider)
    if not config:
        raise ValueError(f"Unknown provider: {provider}. Choose from: {list(PROVIDER_CONFIG.keys())}")

    api_key = config["api_key"]()
    if not api_key:
        raise ValueError(f"API key not set for provider: {provider}")

    extra_kwargs = {}
    if provider == "openrouter":
        extra_kwargs["default_headers"] = {
            "HTTP-Referer": "https://github.com/when-agents-disagree",
            "X-Title": "When Agents Disagree",
        }

    return ChatOpenAI(
        base_url=config["base_url"],
        api_key=api_key,
        model=model_id,
        temperature=temperature,
        **extra_kwargs,
    )


async def invoke_llm(
    provider: str,
    model_id: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.7,
) -> dict:
    """Invoke an LLM and return structured response with metrics."""
    await rate_limiter.acquire(provider, model_id)

    llm = get_llm(provider, model_id, temperature)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    max_retries = 3
    start_time = time.time()

    for attempt in range(max_retries):
        try:
            response = await llm.ainvoke(messages)
            latency_ms = int((time.time() - start_time) * 1000)

            # Extract token usage from response metadata
            usage = response.response_metadata.get("token_usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

            # Parse JSON from response
            content = response.content
            parsed = parse_json_response(content)

            return {
                "content": content,
                "parsed": parsed,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "latency_ms": latency_ms,
                "raw_response": {
                    "content": content,
                    "metadata": response.response_metadata,
                },
            }
        except Exception as e:
            error_str = str(e)
            # Retry on rate limit (429) with exponential backoff
            if "429" in error_str and attempt < max_retries - 1:
                wait = (attempt + 1) * 5  # 5s, 10s
                print(f"[RATE LIMIT] {provider}:{model_id} - retrying in {wait}s (attempt {attempt + 1})")
                await asyncio.sleep(wait)
                continue

            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "content": f"Error: {error_str}",
                "parsed": None,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "latency_ms": latency_ms,
                "raw_response": {"error": error_str},
                "error": error_str,
            }


def parse_json_response(content: str) -> Optional[dict]:
    """Parse JSON from LLM response with multiple fallback strategies."""
    # Strategy 1: Direct JSON parse
    try:
        return json.loads(content)
    except (json.JSONDecodeError, TypeError):
        pass

    # Strategy 2: Extract JSON from markdown code blocks
    json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except (json.JSONDecodeError, TypeError):
            pass

    # Strategy 3: Find JSON object in text
    brace_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except (json.JSONDecodeError, TypeError):
            pass

    # Strategy 4: Manual extraction of key fields
    result = {}
    confidence_match = re.search(r'confidence["\s:]+([0-9.]+)', content, re.IGNORECASE)
    if confidence_match:
        result["confidence"] = float(confidence_match.group(1))

    position_match = re.search(r'(?:position|vote|answer)["\s:]+["\']?([^"\'}\n,]+)', content, re.IGNORECASE)
    if position_match:
        result["vote"] = position_match.group(1).strip()
        result["current_position"] = position_match.group(1).strip()

    return result if result else None


def get_available_models() -> list[dict]:
    """Return all available models with their metadata."""
    models = []
    for provider, config in PROVIDER_CONFIG.items():
        api_key = config["api_key"]()
        for model_id, limits in config["models"].items():
            models.append({
                "provider": provider,
                "model_id": model_id,
                "base_url": config["base_url"],
                "rate_limits": limits,
                "available": bool(api_key),
            })
    return models
