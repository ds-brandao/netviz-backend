"""
Pytest configuration and shared fixtures for NetViz backend tests.
"""

import os
import sys
import pytest
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add the parent directory to the Python path so we can import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def api_base_url():
    """Base URL for API tests."""
    return "http://localhost:3001"


@pytest.fixture(scope="session")
def test_session_id():
    """Test session ID for chat tests."""
    return "pytest_test_session"


@pytest.fixture(scope="session")
def llama_api_key():
    """Llama API key for agent tests."""
    api_key = os.getenv("LLAMA_API_KEY")
    if not api_key:
        pytest.skip("LLAMA_API_KEY environment variable not set")
    return api_key


@pytest.fixture
def sample_network_context():
    """Sample network context for testing."""
    return {
        "focused_node": {
            "id": "test-node-1",
            "label": "Test Router",
            "type": "router",
            "status": "online"
        },
        "network_stats": {
            "total_nodes": 5,
            "active": 4,
            "issues": 1
        }
    }


@pytest.fixture
def sample_conversation_history():
    """Sample conversation history for testing."""
    return [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi! How can I help you with your network infrastructure?"},
        {"role": "user", "content": "What's the network status?"},
        {"role": "assistant", "content": "Let me check the current network status for you."}
    ]


@pytest.fixture
def sample_device_update():
    """Sample device update data for testing."""
    return {
        "name": "Test Device",
        "type": "router",
        "ip_address": "192.168.1.1",
        "status": "online",
        "layer": "network",
        "metadata": {
            "cpu_usage": 45.2,
            "memory_usage": 62.1,
            "uptime": 3600
        }
    }


@pytest.fixture
def sample_log_query():
    """Sample log query for testing."""
    return {
        "level": ["ERROR", "WARN"],
        "node_id": "test-router",
        "time_range": "1h",
        "size": 50
    }