#!/bin/bash

echo "====================================="
echo "Network Isolation Test"
echo "====================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "1. Testing connectivity on PRODNET (192.168.100.0/24)"
echo "-------------------------------------"

echo -n "Router -> Switch on prodnet: "
if docker exec frr-router ping -c 2 -W 1 192.168.100.11 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ SUCCESS${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
fi

echo -n "Switch -> Router on prodnet: "
if docker exec ovs-switch ping -c 2 -W 1 192.168.100.10 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ SUCCESS${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
fi

echo ""
echo "2. Testing connectivity on MANAGEMENT network (172.20.0.0/24)"
echo "-------------------------------------"

echo -n "Router -> Switch on management: "
if docker exec frr-router ping -c 2 -W 1 172.20.0.11 > /dev/null 2>&1; then
    echo -e "${RED}✗ FAILED - Devices should NOT communicate on management network${NC}"
else
    echo -e "${GREEN}✓ SUCCESS - No connectivity (as expected)${NC}"
fi

echo -n "Switch -> Router on management: "
if docker exec ovs-switch ping -c 2 -W 1 172.20.0.10 > /dev/null 2>&1; then
    echo -e "${RED}✗ FAILED - Devices should NOT communicate on management network${NC}"
else
    echo -e "${GREEN}✓ SUCCESS - No connectivity (as expected)${NC}"
fi

echo ""
echo "3. Verifying SSH access via management network"
echo "-------------------------------------"

# Clean up known hosts for these ports (suppress output)
ssh-keygen -R "[localhost]:7777" >/dev/null 2>&1
ssh-keygen -R "[localhost]:7778" >/dev/null 2>&1

echo -n "SSH to Router (port 7777): "
if ssh -i test-ssh-keys/id_rsa -o StrictHostKeyChecking=no -o ConnectTimeout=2 -o UserKnownHostsFile=/dev/null frruser@localhost -p 7777 'exit' 2>/dev/null; then
    echo -e "${GREEN}✓ SUCCESS${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
fi

echo -n "SSH to Switch (port 7778): "
if ssh -i test-ssh-keys/id_rsa -o StrictHostKeyChecking=no -o ConnectTimeout=2 -o UserKnownHostsFile=/dev/null ovsuser@localhost -p 7778 'exit' 2>/dev/null; then
    echo -e "${GREEN}✓ SUCCESS${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
fi

echo ""
echo "====================================="
echo "Test Summary:"
echo "- Prodnet: Devices SHOULD communicate"
echo "- Management: Devices should NOT communicate"
echo "- SSH: Should work via management network only"
echo "=====================================" 