#!/bin/bash
set -e

# Ensure proper ownership of authorized_keys (mounted at runtime)
chown frruser:frruser /home/frruser/.ssh/authorized_keys
chmod 600 /home/frruser/.ssh/authorized_keys

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

# Start services
echo "Starting SSH..."
service ssh start

echo "Starting FRR..."
# Create FRR log directory if it doesn't exist
mkdir -p /var/log/frr
chown frr:frr /var/log/frr

# Start FRR service
service frr start

# Wait a moment for services to initialize
sleep 2

echo "Services started successfully"
echo "SSH: $(service ssh status | grep Active || echo 'Status unknown')"
echo "FRR: $(service frr status | grep Active || echo 'Status unknown')"

# Keep container running and show logs
echo "Tailing FRR logs..."
touch /var/log/frr/frr.log
tail -f /var/log/frr/frr.log
