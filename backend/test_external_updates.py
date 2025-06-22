#!/usr/bin/env python3
"""
Test script to demonstrate external device updates to the NetViz backend.
This simulates how external devices can send real-time updates to the graph.
"""

import asyncio
import aiohttp
import json
import random
import time
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:3001"
DEVICE_IDS = ["router-001", "switch-002", "server-003", "firewall-004", "endpoint-005"]

async def send_device_update(session: aiohttp.ClientSession, device_id: str):
    """Send a device update to the backend"""
    
    # Generate random update data
    update_data = {
        "name": f"Device {device_id}",
        "type": random.choice(["router", "switch", "server", "firewall", "endpoint"]),
        "ip_address": f"192.168.1.{random.randint(10, 254)}",
        "status": random.choice(["online", "offline", "warning"]),
        "layer": random.choice(["physical", "datalink", "network", "transport", "application"]),
        "metadata": {
            "vendor": random.choice(["Cisco", "Juniper", "HP", "Dell", "Arista"]),
            "model": f"Model-{random.randint(1000, 9999)}",
            "version": f"v{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
            "location": random.choice(["Datacenter A", "Office B", "Remote Site C", "Branch D"]),
            "ports": random.randint(8, 48),
            "uptime": f"{random.randint(1, 365)} days",
            "cpu": random.randint(10, 95),
            "memory": random.randint(20, 90),
            "device_id": device_id,
            "last_seen": datetime.now().isoformat()
        }
    }
    
    try:
        url = f"{API_BASE_URL}/network/device-update/{device_id}"
        async with session.post(url, json=update_data) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ {device_id}: {result['action']} - {result['node']['name']}")
                return True
            else:
                error_text = await response.text()
                print(f"❌ {device_id}: HTTP {response.status} - {error_text}")
                return False
    except Exception as e:
        print(f"❌ {device_id}: Error - {str(e)}")
        return False

async def send_bulk_update(session: aiohttp.ClientSession):
    """Send a bulk update with multiple nodes and edges"""
    
    bulk_data = {
        "source": "network_scanner",
        "nodes": [
            {
                "name": "Core Router",
                "type": "router",
                "ip_address": "10.0.0.1",
                "status": "online",
                "layer": "network",
                "metadata": {
                    "vendor": "Cisco",
                    "model": "ASR-9000",
                    "version": "v7.3.2",
                    "location": "Main Datacenter",
                    "ports": 24,
                    "uptime": "127 days",
                    "cpu": 45,
                    "memory": 62
                }
            },
            {
                "name": "Distribution Switch",
                "type": "switch",
                "ip_address": "10.0.0.2",
                "status": "online",
                "layer": "datalink",
                "metadata": {
                    "vendor": "Arista",
                    "model": "7050X",
                    "version": "v4.28.1F",
                    "location": "Main Datacenter",
                    "ports": 48,
                    "uptime": "89 days",
                    "cpu": 23,
                    "memory": 34
                }
            }
        ],
        "edges": [
            {
                "source": "1",  # Assuming these node IDs exist
                "target": "2",
                "type": "fiber",
                "bandwidth": "10Gbps",
                "utilization": 67.5,
                "status": "active",
                "metadata": {
                    "interface": "TenGigE0/0/1",
                    "vlan": "100"
                }
            }
        ]
    }
    
    try:
        url = f"{API_BASE_URL}/network/bulk-update"
        async with session.post(url, json=bulk_data) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ Bulk update: {result['message']}")
                return True
            else:
                error_text = await response.text()
                print(f"❌ Bulk update: HTTP {response.status} - {error_text}")
                return False
    except Exception as e:
        print(f"❌ Bulk update: Error - {str(e)}")
        return False

async def check_api_health(session: aiohttp.ClientSession):
    """Check if the API is healthy"""
    try:
        url = f"{API_BASE_URL}/health"
        async with session.get(url) as response:
            if response.status == 200:
                print("✅ API is healthy")
                return True
            else:
                print(f"❌ API health check failed: HTTP {response.status}")
                return False
    except Exception as e:
        print(f"❌ API health check failed: {str(e)}")
        return False

async def simulate_continuous_updates():
    """Simulate continuous updates from multiple devices"""
    print("🚀 Starting NetViz External Device Update Simulation")
    print(f"📡 Target API: {API_BASE_URL}")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # Check API health first
        if not await check_api_health(session):
            print("❌ Cannot connect to API. Make sure the backend is running.")
            return
        
        print("\n📊 Sending initial device updates...")
        
        # Send initial updates for all devices
        for device_id in DEVICE_IDS:
            await send_device_update(session, device_id)
            await asyncio.sleep(0.5)  # Small delay between requests
        
        print("\n📦 Sending bulk update...")
        await send_bulk_update(session)
        
        print("\n🔄 Starting continuous updates (press Ctrl+C to stop)...")
        print("=" * 60)
        
        try:
            update_count = 0
            while True:
                # Pick a random device to update
                device_id = random.choice(DEVICE_IDS)
                success = await send_device_update(session, device_id)
                
                if success:
                    update_count += 1
                
                # Show statistics every 10 updates
                if update_count % 10 == 0:
                    print(f"📈 Sent {update_count} updates so far...")
                
                # Wait before next update (random interval between 2-8 seconds)
                await asyncio.sleep(random.uniform(2, 8))
                
        except KeyboardInterrupt:
            print(f"\n🛑 Simulation stopped. Sent {update_count} total updates.")

async def send_single_update():
    """Send a single test update"""
    print("🔧 Sending single test update...")
    
    async with aiohttp.ClientSession() as session:
        if not await check_api_health(session):
            print("❌ Cannot connect to API. Make sure the backend is running.")
            return
        
        device_id = "test-device-001"
        await send_device_update(session, device_id)

def main():
    """Main function"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "single":
        asyncio.run(send_single_update())
    else:
        asyncio.run(simulate_continuous_updates())

if __name__ == "__main__":
    main() 