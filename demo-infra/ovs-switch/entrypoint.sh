#!/bin/bash
set -e

# Copy SSH keys from mounted volume to both root and ovsuser
if [ -d /root/.ssh ]; then
    # Copy authorized_keys to ovsuser home
    if [ -f /root/.ssh/authorized_keys ]; then
        cp /root/.ssh/authorized_keys /home/ovsuser/.ssh/
        chown ovsuser:ovsuser /home/ovsuser/.ssh/authorized_keys
        chmod 600 /home/ovsuser/.ssh/authorized_keys
    fi
    # Note: /root/.ssh is mounted read-only, so we can't change permissions there
fi

echo "Setting up Layer 2 Linux bridge..."

# Docker assigns interfaces in order: eth0 (management), eth1 (data network)
MGMT_IF="eth0"
DATA_IF="eth1"

echo "Management interface: $MGMT_IF"
echo "Data interface: $DATA_IF"

# Verify interfaces exist
if [ ! -d "/sys/class/net/$DATA_IF" ]; then
    echo "ERROR: Data interface not found"
    echo "Available interfaces:"
    ls /sys/class/net/
    exit 1
fi

# Configure firewall rules for network isolation on management interface only
echo "Configuring network isolation..."
# Allow SSH from host on management network
iptables -A INPUT -i $MGMT_IF -p tcp --dport 22 -j ACCEPT
# Block all other devices on management network except the gateway
iptables -A INPUT -i $MGMT_IF -s 172.25.0.0/24 -j DROP
iptables -A OUTPUT -o $MGMT_IF -d 172.25.0.0/24 -j DROP
# Allow communication with Docker host gateway
iptables -I OUTPUT -o $MGMT_IF -d 172.25.0.1 -j ACCEPT
iptables -I INPUT -i $MGMT_IF -s 172.25.0.1 -j ACCEPT

# Since this is a Layer 2 switch with only one data interface,
# we don't need a bridge - just ensure the interface is up and forwarding
echo "Configuring Layer 2 switch behavior..."
echo "Processing interface $DATA_IF..."
# Bring interface down first
ip link set $DATA_IF down
# Remove any IP addresses Docker might have assigned (switches work at Layer 2)
ip addr flush dev $DATA_IF 2>/dev/null || true
# Bring interface up
ip link set $DATA_IF up

# Enable forwarding for Layer 2 switching
echo "Enabling forwarding..."
echo 1 > /proc/sys/net/ipv4/ip_forward

# Start SSH  
echo "Starting SSH..."
service ssh start

echo "Services started successfully"
echo "SSH: $(service ssh status | grep Active || echo 'Status unknown')"

# Wait for interface to come up
sleep 2

# Show configuration
echo ""
echo "Interface configuration:"
ip addr show

# Keep container running efficiently
exec sleep infinity 