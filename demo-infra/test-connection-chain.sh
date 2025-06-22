#!/bin/bash

echo "Testing connection chain: Client → Router → Switch → Server"
echo "============================================================"

# Test from client to router
echo "1. Testing Client → Router..."
docker exec client ping -c 3 192.168.10.1 || echo "❌ Client cannot reach Router"

# Test from client to switch via router
echo "2. Testing Client → Router → Switch..."
docker exec client ping -c 3 192.168.20.3 || echo "❌ Client cannot reach Switch via Router"

# Test from client to server via router and switch
echo "3. Testing Client → Router → Switch → Server..."
docker exec client ping -c 3 192.168.30.10 || echo "❌ Client cannot reach Server via Router and Switch"

# Test HTTP connection from client to server
echo "4. Testing HTTP connection Client → Server..."
docker exec client curl -s --connect-timeout 5 http://192.168.30.10:8080 | head -5 || echo "❌ Client cannot access HTTP server"

# Show routing tables
echo ""
echo "=== Routing Tables ==="
echo "Client routing table:"
docker exec client ip route

echo ""
echo "Router routing table:"
docker exec frr-router ip route

echo ""
echo "Switch routing table:"
docker exec ovs-switch ip route

echo ""
echo "Server routing table:"
docker exec server ip route

echo ""
echo "=== OVS Switch Configuration ==="
docker exec ovs-switch ovs-vsctl show 