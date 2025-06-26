"""
Metrics API endpoints.
Handles system metrics retrieval and caching.
"""

from fastapi import APIRouter
from datetime import datetime

from src.services.metrics_sync_service import metrics_sync_service
from src.services.opensearch_service import opensearch_service

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/")
async def get_current_metrics():
    """Get current network metrics from cache"""
    # Fetch fresh metrics if cache should be refreshed
    if metrics_sync_service.should_refresh_cache():
        await opensearch_service.fetch_metrics()
    
    return metrics_sync_service.get_cached_metrics()