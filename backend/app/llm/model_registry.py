from app.llm.provider import PROVIDER_CONFIG


MODEL_DISPLAY_NAMES = {
    "llama-3.3-70b-versatile": "Llama 3.3 70B",
    "llama-3.1-8b-instant": "Llama 3.1 8B",
    "llama3.1-8b": "Llama 3.1 8B",
    "qwen/qwen3-next-80b-a3b-instruct:free": "Qwen 3 Next 80B",
    "nvidia/nemotron-3-super-120b-a12b:free": "Nemotron 3 Super 120B",
    "meta-llama/llama-3.3-70b-instruct:free": "Llama 3.3 70B (OR)",
}

PROVIDER_DISPLAY_NAMES = {
    "groq": "Groq",
    "cerebras": "Cerebras",
    "openrouter": "OpenRouter",
}

PROVIDER_COLORS = {
    "groq": "#F55036",
    "cerebras": "#6366F1",
    "openrouter": "#10B981",
}


def get_model_display_name(model_id: str) -> str:
    return MODEL_DISPLAY_NAMES.get(model_id, model_id)


def get_provider_display_name(provider: str) -> str:
    return PROVIDER_DISPLAY_NAMES.get(provider, provider)


def get_all_models_info() -> list[dict]:
    """Get all available models with display info."""
    from app.config import settings
    models = []
    for provider, config in PROVIDER_CONFIG.items():
        api_key = config["api_key"]()
        for model_id, limits in config["models"].items():
            models.append({
                "provider": provider,
                "provider_display": get_provider_display_name(provider),
                "model_id": model_id,
                "model_display": get_model_display_name(model_id),
                "rate_limits": limits,
                "color": PROVIDER_COLORS.get(provider, "#6B7280"),
                "available": bool(api_key),
            })
    return models
