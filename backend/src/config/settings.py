"""
Configuration settings for the NetViz backend application.
Centralizes all configuration in one place for easy management.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings"""
    
    # Application
    APP_NAME = "NetViz Backend"
    APP_VERSION = "1.0.0"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Server
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 3001))
    
    # Database
    DATABASE_URL = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://postgres:postgres@localhost:5432/netviz"
    )
    
    # OpenSearch configuration
    OPENSEARCH_BASE_URL = os.getenv("OPENSEARCH_BASE_URL", "https://192.168.0.132:9200")
    OPENSEARCH_USERNAME = os.getenv("OPENSEARCH_USERNAME", "admin")
    OPENSEARCH_PASSWORD = os.getenv("OPENSEARCH_PASSWORD")
    if not OPENSEARCH_PASSWORD:
        raise ValueError("Environment variable 'OPENSEARCH_PASSWORD' must be set and cannot be empty.")
    OPENSEARCH_VERIFY_SSL = os.getenv("OPENSEARCH_VERIFY_SSL", "False").lower() == "true"
    
    # OpenSearch indexes
    OPENSEARCH_LOG_INDEXES = [
        "client-logs",
        "frr-router-logs", 
        "server-logs",
        "switch1-logs",
        "switch2-logs"
    ]
    OPENSEARCH_METRICS_INDEX_PATTERN = "system-metrics-*"
    
    # Cache settings
    METRICS_CACHE_TTL_SECONDS = int(os.getenv("METRICS_CACHE_TTL", 60))
    
    # Background task intervals
    METRICS_SYNC_INTERVAL = int(os.getenv("METRICS_SYNC_INTERVAL", 30))
    METRICS_SYNC_ERROR_INTERVAL = int(os.getenv("METRICS_SYNC_ERROR_INTERVAL", 60))
    
    # WebSocket settings
    WEBSOCKET_PING_INTERVAL = int(os.getenv("WEBSOCKET_PING_INTERVAL", 30))
    
    # CORS settings
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    CORS_ALLOW_CREDENTIALS = True
    CORS_ALLOW_METHODS = ["*"]
    CORS_ALLOW_HEADERS = ["*"]
    
    # API settings
    API_PREFIX = os.getenv("API_PREFIX", "")
    
    # Device topology mappings
    DEVICE_TYPE_MAPPINGS = {
        "frr-router": "router",
        "switch1": "switch",
        "switch2": "switch",
        "server": "server",
        "client": "client"
    }
    
    # Network topology
    DEMO_NETWORK_TOPOLOGY = [
        ("client", "switch1", "ethernet"),
        ("switch1", "frr-router", "ethernet"), 
        ("frr-router", "switch2", "ethernet"),
        ("switch2", "server", "ethernet"),
    ]
    
    # IP address mappings
    DEVICE_IP_MAPPINGS = {
        "client": "192.168.10.10",
        "frr-router": "192.168.10.254",
        "server": "192.168.30.10"
    }
    
    # Subnet information
    SUBNET_INFO = {
        ("client", "switch1"): "192.168.10.0/24 (1Gbps)",
        ("switch1", "frr-router"): "192.168.10.0/24 (1Gbps)",
        ("frr-router", "switch2"): "192.168.30.0/24 (1Gbps)",
        ("switch2", "server"): "192.168.30.0/24 (1Gbps)"
    }

# Create a global settings instance
settings = Settings()