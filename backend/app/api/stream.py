"""SSE streaming endpoint for live debate events."""
import asyncio
import json
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.services.debate_service import subscribe, unsubscribe

router = APIRouter(prefix="/stream", tags=["streaming"])


@router.get("/debate/{debate_id}")
async def stream_debate(debate_id: str, request: Request):
    """Stream debate events via Server-Sent Events."""

    async def event_generator():
        queue = subscribe(debate_id)
        try:
            # Send initial connection event
            yield f"event: connected\ndata: {json.dumps({'debate_id': debate_id})}\n\n"

            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break

                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30)
                    event_type = event.get("type", "message")
                    event_data = json.dumps(event.get("data", event), default=str)
                    yield f"event: {event_type}\ndata: {event_data}\n\n"

                    # End stream on debate completion
                    if event_type in ("debate_end", "error"):
                        break

                except asyncio.TimeoutError:
                    # Send keepalive
                    yield f"event: keepalive\ndata: {json.dumps({'status': 'waiting'})}\n\n"

        finally:
            unsubscribe(debate_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
