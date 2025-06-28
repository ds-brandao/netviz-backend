"""
Pytest tests for external device updates simulation.
"""

import pytest
import aiohttp
import asyncio
import random
from datetime import datetime


@pytest.fixture
def device_ids():
    """Sample device IDs for testing."""
    return ["router-001", "switch-002", "server-003", "firewall-004", "endpoint-005"]


@pytest.fixture
def sample_statuses():
    """Sample device statuses."""
    return ["online", "offline", "warning", "maintenance"]


@pytest.fixture
def sample_device_types():
    """Sample device types."""
    return ["router", "switch", "server", "firewall", "endpoint"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_single_device_update(api_base_url, device_ids, sample_statuses, sample_device_types):
    """Test updating a single device."""
    
    device_id = device_ids[0]
    
    update_data = {
        "name": f"Test {device_id}",
        "type": random.choice(sample_device_types),
        "ip_address": f"192.168.1.{random.randint(10, 100)}",
        "status": random.choice(sample_statuses),
        "layer": "network",
        "metadata": {
            "cpu_usage": round(random.uniform(10, 90), 1),
            "memory_usage": round(random.uniform(20, 80), 1),
            "last_seen": datetime.now().isoformat(),
            "uptime": random.randint(3600, 86400)
        }
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{api_base_url}/network/device-update/{device_id}",
            json=update_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            assert response.status == 200
            data = await response.json()
            
            # Verify response
            assert data["success"] is True
            assert data["action"] in ["created", "updated"]
            assert "node" in data
            
            # Verify node data
            node = data["node"]
            assert node["name"] == update_data["name"]
            assert node["type"] == update_data["type"]
            assert node["ip_address"] == update_data["ip_address"]
            assert node["status"] == update_data["status"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bulk_device_updates(api_base_url, device_ids, sample_statuses, sample_device_types):
    """Test bulk device updates."""
    
    nodes_data = []
    for device_id in device_ids[:3]:  # Test with first 3 devices
        node_data = {
            "name": f"Bulk {device_id}",
            "type": random.choice(sample_device_types),
            "ip_address": f"192.168.2.{random.randint(10, 100)}",
            "status": random.choice(sample_statuses),
            "layer": "network",
            "metadata": {
                "device_id": device_id,
                "cpu_usage": round(random.uniform(10, 90), 1),
                "memory_usage": round(random.uniform(20, 80), 1),
                "bulk_update": True
            }
        }
        nodes_data.append(node_data)
    
    bulk_update_data = {
        "nodes": nodes_data,
        "source": "pytest_bulk_test"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{api_base_url}/network/bulk-update",
            json=bulk_update_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            assert response.status == 200
            data = await response.json()
            
            # Verify response
            assert data["success"] is True
            assert "results" in data
            assert len(data["results"]["nodes"]) == len(nodes_data)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_concurrent_device_updates(api_base_url, device_ids, sample_statuses, sample_device_types):
    """Test concurrent device updates to simulate multiple devices updating simultaneously."""
    
    async def update_device(session, device_id):
        """Update a single device."""
        update_data = {
            "name": f"Concurrent {device_id}",
            "type": random.choice(sample_device_types),
            "ip_address": f"192.168.3.{random.randint(10, 100)}",
            "status": random.choice(sample_statuses),
            "metadata": {
                "concurrent_test": True,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        async with session.post(
            f"{api_base_url}/network/device-update/{device_id}",
            json=update_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            return response.status == 200
    
    async with aiohttp.ClientSession() as session:
        # Create concurrent tasks for all devices
        tasks = [update_device(session, device_id) for device_id in device_ids]
        
        # Wait for all updates to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check that most updates succeeded
        successful_updates = sum(1 for result in results if result is True)
        assert successful_updates >= len(device_ids) * 0.8  # At least 80% success rate


@pytest.mark.asyncio
@pytest.mark.integration
async def test_device_status_changes(api_base_url, device_ids):
    """Test simulating device status changes over time."""
    
    device_id = device_ids[0]
    statuses = ["online", "warning", "offline", "maintenance", "online"]
    
    for i, status in enumerate(statuses):
        update_data = {
            "name": f"Status Test Device",
            "type": "router",
            "ip_address": "192.168.4.10",
            "status": status,
            "metadata": {
                "status_change_test": True,
                "sequence": i + 1,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{api_base_url}/network/device-update/{device_id}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert data["success"] is True
                
                # Verify the status was updated
                node = data["node"]
                assert node["status"] == status
        
        # Small delay between status changes
        await asyncio.sleep(0.1)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_device_metadata_updates(api_base_url, device_ids):
    """Test updating device metadata."""
    
    device_id = device_ids[1]
    
    # Initial device creation
    initial_data = {
        "name": "Metadata Test Device",
        "type": "server",
        "ip_address": "192.168.5.50",
        "status": "online",
        "metadata": {
            "initial_setup": True,
            "version": "1.0"
        }
    }
    
    async with aiohttp.ClientSession() as session:
        # Create device
        async with session.post(
            f"{api_base_url}/network/device-update/{device_id}",
            json=initial_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            assert response.status == 200
        
        # Update metadata
        metadata_update = {
            "name": "Metadata Test Device",
            "type": "server", 
            "ip_address": "192.168.5.50",
            "status": "online",
            "metadata": {
                "initial_setup": True,
                "version": "2.0",
                "cpu_usage": 45.2,
                "memory_usage": 62.8,
                "disk_usage": 33.1,
                "network_interfaces": ["eth0", "eth1"],
                "last_updated": datetime.now().isoformat()
            }
        }
        
        async with session.post(
            f"{api_base_url}/network/device-update/{device_id}",
            json=metadata_update,
            headers={"Content-Type": "application/json"}
        ) as response:
            assert response.status == 200
            data = await response.json()
            
            # Verify metadata was updated
            node = data["node"]
            assert node["metadata"]["version"] == "2.0"
            assert "cpu_usage" in node["metadata"]
            assert "network_interfaces" in node["metadata"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_invalid_device_update(api_base_url):
    """Test handling of invalid device update data."""
    
    device_id = "invalid-test-device"
    
    # Test with missing required fields
    invalid_data = {
        "invalid_field": "invalid_value"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{api_base_url}/network/device-update/{device_id}",
            json=invalid_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            # Should still work as endpoint provides defaults
            assert response.status == 200


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_updated_devices(api_base_url, device_ids):
    """Test retrieving devices after updates."""
    
    # First, update a few devices
    for device_id in device_ids[:2]:
        update_data = {
            "name": f"Retrieved {device_id}",
            "type": "switch",
            "status": "online",
            "metadata": {"test_retrieval": True}
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{api_base_url}/network/device-update/{device_id}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                assert response.status == 200
    
    # Then retrieve the network graph to verify updates
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{api_base_url}/network/graph") as response:
            assert response.status == 200
            data = await response.json()
            
            # Verify we have nodes
            assert "nodes" in data
            nodes = data["nodes"]
            
            # Look for our test devices
            test_devices = [node for node in nodes if node.get("metadata", {}).get("test_retrieval")]
            assert len(test_devices) >= 2