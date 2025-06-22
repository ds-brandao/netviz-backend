#!/bin/bash
set -e

# Fix SSH key permissions
chown clientuser:clientuser /home/clientuser/.ssh/authorized_keys
chmod 600 /home/clientuser/.ssh/authorized_keys

# Configure firewall rules for network isolation
echo "Configuring network isolation..."
# Allow SSH from host on management network
iptables -A INPUT -i eth0 -p tcp --dport 22 -j ACCEPT
# Block all other devices on management network except the gateway
iptables -A INPUT -i eth0 -s 172.20.0.0/24 -j DROP
iptables -A OUTPUT -o eth0 -d 172.20.0.0/24 -j DROP
# Allow communication with Docker host gateway
iptables -I OUTPUT -o eth0 -d 172.20.0.1 -j ACCEPT
iptables -I INPUT -i eth0 -s 172.20.0.1 -j ACCEPT

# Start SSH
echo "Starting SSH..."
service ssh start

# Configure routing
echo "Configuring routing..."
# Add default route via router
ip route add default via 192.168.10.1 || true
# Add specific routes for server networks via router
ip route add 192.168.30.0/24 via 192.168.10.1 || true
ip route add 192.168.20.0/24 via 192.168.10.1 || true

echo "Services started successfully"
echo "SSH: $(service ssh status | grep Active || echo 'Status unknown')"
echo "Client ready"

# Show configuration
echo "Interface configuration:"
ip addr show
echo ""
echo "Routing table:"
ip route show

# Keep container running
tail -f /dev/null 