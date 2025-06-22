#!/bin/bash
set -e

# Fix SSH key permissions
chown serveruser:serveruser /home/serveruser/.ssh/authorized_keys
chmod 600 /home/serveruser/.ssh/authorized_keys

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
# Remove default route via management network
ip route del default via 172.20.0.1 2>/dev/null || true
# Add default route via switch
ip route add default via 192.168.30.2 || true
# Add route to client network via switch
ip route add 192.168.10.0/24 via 192.168.30.2 || true
# Add route to router-switch network via switch
ip route add 192.168.20.0/24 via 192.168.30.2 || true

# Wait for network to be ready
sleep 2

# Start simple HTTP server
echo "Starting HTTP server on port 8080..."
cd /var/www
python3 -m http.server 8080 &

echo "Services started successfully"
echo "SSH: $(service ssh status | grep Active || echo 'Status unknown')"
echo "HTTP Server running on port 8080"

# Show configuration
echo "Interface configuration:"
ip addr show
echo ""
echo "Routing table:"
ip route show

# Keep container running
tail -f /dev/null 