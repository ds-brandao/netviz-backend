#!/bin/bash
set -e

# Setup logging
LOG_DIR="/var/log/client"
mkdir -p "$LOG_DIR"
exec 1> >(tee -a "$LOG_DIR/client.log")
exec 2> >(tee -a "$LOG_DIR/client-error.log")

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

# Start continuous logging process
echo "$(date): Client container startup completed" >> "$LOG_DIR/system.log"

# Log connectivity tests and network status
(
  while true; do
    echo "$(date): Network connectivity test:" >> "$LOG_DIR/connectivity.log"
    ping -c 1 192.168.30.10 >> "$LOG_DIR/connectivity.log" 2>&1 || echo "$(date): Ping to server failed" >> "$LOG_DIR/connectivity.log"
    echo "$(date): HTTP test:" >> "$LOG_DIR/connectivity.log"
    curl -s --max-time 5 http://192.168.30.10:8080 >> "$LOG_DIR/connectivity.log" 2>&1 || echo "$(date): HTTP request failed" >> "$LOG_DIR/connectivity.log"
    echo "$(date): Interface stats:" >> "$LOG_DIR/system.log"
    ip -s link show >> "$LOG_DIR/system.log" 2>&1
    echo "$(date): Routing table:" >> "$LOG_DIR/system.log"
    ip route show >> "$LOG_DIR/system.log" 2>&1
    echo "$(date): Memory usage: $(free -h | grep Mem)" >> "$LOG_DIR/system.log"
    sleep 60
  done
) &

# Keep container running efficiently
exec sleep infinity 