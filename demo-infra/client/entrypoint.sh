#!/bin/bash
set -e

# Client doesn't need SSH server - removing SSH configuration

# Find interfaces
CLIENT_IF=$(ip -o addr show | grep "192.168.10.10" | awk '{print $2}')
MGMT_IF=$(ip -o addr show | grep "172.25.0.5" | awk '{print $2}')

echo "Client interface: $CLIENT_IF"
echo "Management interface: $MGMT_IF"

# Configure firewall rules for network isolation
echo "Configuring network isolation..."
# Block all other devices on management network except the gateway
iptables -A INPUT -i $MGMT_IF -s 172.25.0.0/24 -j DROP
iptables -A OUTPUT -o $MGMT_IF -d 172.25.0.0/24 -j DROP
# Allow communication with Docker host gateway
iptables -I OUTPUT -o $MGMT_IF -d 172.25.0.1 -j ACCEPT
iptables -I INPUT -i $MGMT_IF -s 172.25.0.1 -j ACCEPT

# Configure routing
echo "Configuring routing..."
# Remove all existing default routes first
while ip route del default 2>/dev/null; do :; done
# Add default route via router on client network
ip route add default via 192.168.10.254 dev $CLIENT_IF || true
# Add specific route for server network via router
ip route add 192.168.30.0/24 via 192.168.10.254 dev $CLIENT_IF || true

echo "Client ready"

# Show configuration
echo "Interface configuration:"
ip addr show
echo ""
echo "Routing table:"
ip route show

# Keep container running efficiently
exec sleep infinity 