#!/bin/bash

echo "Testing connection chain: Client → Switch1 → Router → Switch2 → Server"
echo "======================================================================="

# Test from client to router
echo "1. Testing Client → Router..."
docker exec client ping -c 3 192.168.10.254 || echo "❌ Client cannot reach Router"

# Test from router to server  
echo "2. Testing Router → Server..."
docker exec frr-router ping -c 3 192.168.30.10 || echo "❌ Router cannot reach Server"

# Test from client to server via router
echo "3. Testing Client → Switch1 → Router → Switch2 → Server..."
docker exec client ping -c 3 192.168.30.10 || echo "❌ Client cannot reach Server via Router"

# Test HTTP connection from client to server
echo "4. Testing HTTP connection Client → Server..."
docker exec client curl -s --connect-timeout 5 http://192.168.30.10:8080 | head -5 || echo "❌ Client cannot access HTTP server"

# Test return path from server to client
echo "5. Testing Server → Switch2 → Router → Switch1 → Client (return path)..."
docker exec server ping -c 3 192.168.10.10 || echo "❌ Server cannot reach Client via Router"

# Show routing tables
echo ""
echo "=== Routing Tables ==="
echo "Client routing table:"
docker exec client ip route

echo ""
echo "Router routing table:"
docker exec frr-router ip route

echo ""
echo "Server routing table:"
docker exec server ip route

echo ""
echo "=== Switch Configuration ==="
echo "Switch1 interfaces:"
docker exec switch1 ip link show | grep -E "eth[0-9]|state"
echo ""
echo "Switch2 interfaces:"
docker exec switch2 ip link show | grep -E "eth[0-9]|state" 