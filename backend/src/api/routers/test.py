"""
Test API endpoints.
Handles testing and health check endpoints.
"""

import json
import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/test", tags=["Test"])


@router.get("/stream")
async def test_stream():
    """Test SSE streaming"""
    async def generate():
        for i in range(5):
            yield f"data: {json.dumps({'count': i, 'message': f'Test message {i}'})}\n\n"
            await asyncio.sleep(1)
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}