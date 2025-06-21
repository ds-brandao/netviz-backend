#!/bin/bash

echo "=== FRR Router Test Script ==="
echo

# Test SSH connectivity
echo "1. Testing SSH connectivity..."
if ssh -i ../ssh-keys/id_rsa -p 7777 frruser@localhost -o StrictHostKeyChecking=no 'echo "SSH OK"' 2>/dev/null; then
    echo "✅ SSH connection successful"
else
    echo "❌ SSH connection failed"
    exit 1
fi
echo

# Test FRR version
echo "2. Testing FRR installation..."
FRR_VERSION=$(ssh -i ../ssh-keys/id_rsa -p 7777 frruser@localhost -o StrictHostKeyChecking=no 'sudo vtysh -c "show version"' 2>/dev/null | head -1)
if [[ $FRR_VERSION == *"FRRouting"* ]]; then
    echo "✅ FRR installed: $FRR_VERSION"
else
    echo "❌ FRR not responding"
    exit 1
fi
echo

# Test daemons
echo "3. Testing FRR daemons..."
DAEMONS=$(ssh -i ../ssh-keys/id_rsa -p 7777 frruser@localhost -o StrictHostKeyChecking=no 'sudo vtysh -c "show daemons"' 2>/dev/null)
if [[ $DAEMONS == *"bgpd"* ]] && [[ $DAEMONS == *"ospfd"* ]]; then
    echo "✅ FRR daemons running: $DAEMONS"
else
    echo "❌ FRR daemons not running properly"
    exit 1
fi

# Test configuration
echo "3b. Testing FRR configuration..."
CONFIG_TEST=$(ssh -i ../ssh-keys/id_rsa -p 7777 frruser@localhost -o StrictHostKeyChecking=no 'sudo vtysh -c "show running-config"' 2>/dev/null | grep "hostname frr-router")
if [[ -n "$CONFIG_TEST" ]]; then
    echo "✅ FRR configuration loaded"
else
    echo "⚠️  FRR configuration may not be loaded (this is OK for first run)"
fi
echo

# Test interfaces
echo "4. Testing network interfaces..."
INTERFACES=$(ssh -i ../ssh-keys/id_rsa -p 7777 frruser@localhost -o StrictHostKeyChecking=no 'sudo vtysh -c "show interface brief"' 2>/dev/null | grep "eth0.*up")
if [[ -n "$INTERFACES" ]]; then
    echo "✅ Network interfaces active"
    echo "$INTERFACES"
else
    echo "❌ Network interfaces not active"
    exit 1
fi
echo

# Test routing table
echo "5. Testing routing table..."
ROUTES=$(ssh -i ../ssh-keys/id_rsa -p 7777 frruser@localhost -o StrictHostKeyChecking=no 'sudo vtysh -c "show ip route"' 2>/dev/null | grep "K>.*0.0.0.0/0")
if [[ -n "$ROUTES" ]]; then
    echo "✅ Default route present"
else
    echo "❌ No default route found"
    exit 1
fi
echo

# Test network connectivity
echo "6. Testing network connectivity..."
if ssh -i ../ssh-keys/id_rsa -p 7777 frruser@localhost -o StrictHostKeyChecking=no 'ping -c 1 8.8.8.8' >/dev/null 2>&1; then
    echo "✅ Internet connectivity working"
else
    echo "❌ Internet connectivity failed"
    exit 1
fi
echo

# Test Ansible
echo "7. Testing Ansible..."
ANSIBLE_VERSION=$(ssh -i ../ssh-keys/id_rsa -p 7777 frruser@localhost -o StrictHostKeyChecking=no 'ansible --version' 2>/dev/null | head -1)
if [[ $ANSIBLE_VERSION == *"ansible"* ]]; then
    echo "✅ Ansible available: $ANSIBLE_VERSION"
else
    echo "❌ Ansible not available"
    exit 1
fi
echo

echo "🎉 All tests passed! Your FRR router is ready to use."
echo
echo "Quick access commands:"
echo "  SSH into router: ssh -i ../ssh-keys/id_rsa -p 7777 frruser@localhost"
echo "  FRR CLI: ssh -i ../ssh-keys/id_rsa -p 7777 frruser@localhost -t 'sudo vtysh'"
echo "  View logs: docker logs frr-router" 