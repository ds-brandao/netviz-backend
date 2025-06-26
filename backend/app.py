"""
Refactored NetViz Backend FastAPI Application.
Main application entry point with modular router structure.
"""

import asyncio
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.database import init_db
from src.config.settings import Settings
settings = Settings()
from src.services.metrics_sync_service import metrics_sync_service
from websocket_manager import periodic_ping

# Import routers
from src.api.routers import agent, network, logs, metrics, websocket, test


# Background task for metrics hydration and topology sync
async def periodic_metrics_fetch():
    """Periodically fetch metrics from OpenSearch and sync topology"""
    # First run: clear bad data
    await metrics_sync_service.clear_bad_data()
    
    while True:
        try:
            # Sync topology from metrics
            await metrics_sync_service.sync_network_topology()
            await asyncio.sleep(settings.METRICS_SYNC_INTERVAL)
        except Exception as e:
            print(f"Error in periodic metrics fetch: {e}")
            await asyncio.sleep(settings.METRICS_SYNC_ERROR_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    await init_db()
    # Start periodic ping task
    asyncio.create_task(periodic_ping())
    # Start periodic metrics fetch
    asyncio.create_task(periodic_metrics_fetch())
    yield
    # Shutdown (if needed)
    pass


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )
    
    # Include routers
    app.include_router(agent.router)
    app.include_router(network.router)
    app.include_router(logs.router)
    app.include_router(metrics.router)
    app.include_router(websocket.router)
    app.include_router(test.router)
    
    return app


# Create the app instance
app = create_app()




if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )