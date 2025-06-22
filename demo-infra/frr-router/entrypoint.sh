#!/bin/bash
set -e

# Copy SSH keys from mounted volume to both root and frruser
if [ -d /root/.ssh ]; then
    # Copy authorized_keys to frruser home
    if [ -f /root/.ssh/authorized_keys ]; then
        cp /root/.ssh/authorized_keys /home/frruser/.ssh/
        chown frruser:frruser /home/frruser/.ssh/authorized_keys
        chmod 600 /home/frruser/.ssh/authorized_keys
    fi
    # Note: /root/.ssh is mounted read-only, so we can't change permissions there
fi

# Find network interfaces
MGMT_IF=$(ip -o addr show | grep "172.25.0.10" | awk '{print $2}')
CLIENT_IF=$(ip -o addr show | grep "192.168.10.254" | awk '{print $2}')
SERVER_IF=$(ip -o addr show | grep "192.168.30.254" | awk '{print $2}')

echo "Management interface: $MGMT_IF"
echo "Client interface: $CLIENT_IF"
echo "Server interface: $SERVER_IF"

# Validate critical interfaces exist
if [ -z "$CLIENT_IF" ] || [ -z "$SERVER_IF" ]; then
    echo "ERROR: Could not find required interfaces"
    echo "Available interfaces:"
    ip addr show
    sleep 5
    exit 1
fi

# Configure firewall rules for network isolation
echo "Configuring network isolation..."
# Allow SSH from host on management network
iptables -A INPUT -i "$MGMT_IF" -p tcp --dport 22 -j ACCEPT
# Block all other devices on management network except the gateway
iptables -A INPUT -i "$MGMT_IF" -s 172.25.0.0/24 -j DROP
iptables -A OUTPUT -o "$MGMT_IF" -d 172.25.0.0/24 -j DROP
# Allow communication with Docker host gateway
iptables -I OUTPUT -o "$MGMT_IF" -d 172.25.0.1 -j ACCEPT
iptables -I INPUT -i "$MGMT_IF" -s 172.25.0.1 -j ACCEPT

# Enable IP forwarding
echo "Enabling IP forwarding..."
echo 1 > /proc/sys/net/ipv4/ip_forward

# Add forwarding rules between networks  
echo "Adding forwarding rules..."
iptables -A FORWARD -i "$CLIENT_IF" -o "$SERVER_IF" -j ACCEPT
iptables -A FORWARD -i "$SERVER_IF" -o "$CLIENT_IF" -j ACCEPT

# Start SSH
echo "Starting SSH..."
service ssh start

# Gateway IPs already assigned by Docker - no need to add them manually
echo "Using Docker-assigned gateway IPs..."

# Start FRR
echo "Starting FRR..."
service frr start

# Apply FRR configuration
sleep 2
vtysh -c "configure terminal" \
      -c "interface $CLIENT_IF" \
      -c "no shutdown" \
      -c "exit" \
      -c "interface $SERVER_IF" \
      -c "no shutdown" \
      -c "exit" \
      -c "exit" \
      -c "write memory"

echo "Services started successfully"
echo "SSH: $(service ssh status | grep Active || echo 'Status unknown')"
echo "FRR: $(service frr status | grep Active || echo 'Status unknown')"

# Show configuration
echo ""
echo "Interface configuration:"
ip addr show
echo ""
echo "Routing table:"
ip route show
echo ""
echo "IP forwarding status:"
cat /proc/sys/net/ipv4/ip_forward

# Keep container running efficiently
exec sleep infinity
