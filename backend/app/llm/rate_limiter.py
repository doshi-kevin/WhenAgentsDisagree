import asyncio
import time
from collections import defaultdict, deque


class RateLimiter:
    """Token bucket rate limiter with per-provider, per-model tracking."""

    def __init__(self):
        self._request_times: dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self._locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._daily_counts: dict[str, int] = defaultdict(int)
        self._daily_reset: dict[str, float] = {}

        # Default limits per provider
        self._limits = {
            "groq": {"rpm": 30, "rpd": 1000},
            "cerebras": {"rpm": 30, "rpd": 10000},
            "openrouter": {"rpm": 20, "rpd": 200},
        }

    async def acquire(self, provider: str, model_id: str):
        """Wait until a request slot is available."""
        key = f"{provider}:{model_id}"
        async with self._locks[key]:
            limits = self._limits.get(provider, {"rpm": 10, "rpd": 100})

            # Check and reset daily counter
            now = time.time()
            if key not in self._daily_reset or now - self._daily_reset[key] > 86400:
                self._daily_counts[key] = 0
                self._daily_reset[key] = now

            # Wait if we've hit the per-minute limit
            while True:
                now = time.time()
                minute_ago = now - 60

                # Remove old entries
                while self._request_times[key] and self._request_times[key][0] < minute_ago:
                    self._request_times[key].popleft()

                rpm = limits.get("rpm", 30)
                if len(self._request_times[key]) < rpm:
                    break

                # Wait until oldest request exits the window
                wait_time = self._request_times[key][0] - minute_ago + 0.1
                await asyncio.sleep(wait_time)

            # Check daily limit
            rpd = limits.get("rpd")
            if rpd and self._daily_counts[key] >= rpd:
                raise RuntimeError(
                    f"Daily rate limit exhausted for {provider}:{model_id}. "
                    f"Limit: {rpd} requests/day"
                )

            # Record this request
            self._request_times[key].append(time.time())
            self._daily_counts[key] += 1

    def get_usage(self, provider: str, model_id: str) -> dict:
        """Get current usage stats for a provider/model."""
        key = f"{provider}:{model_id}"
        now = time.time()
        minute_ago = now - 60

        # Count requests in last minute
        recent = sum(1 for t in self._request_times[key] if t > minute_ago)

        return {
            "provider": provider,
            "model_id": model_id,
            "requests_last_minute": recent,
            "requests_today": self._daily_counts[key],
            "rpm_limit": self._limits.get(provider, {}).get("rpm", 30),
            "rpd_limit": self._limits.get(provider, {}).get("rpd"),
        }
