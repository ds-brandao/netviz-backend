#!/bin/bash
set -e

# Fix SSH key permissions
chown frruser:frruser /home/frruser/.ssh/authorized_keys
chmod 600 /home/frruser/.ssh/authorized_keys

# Configure firewall rules for network isolation
echo "Configuring network isolation..."
# Allow SSH from host on management network
iptables -A INPUT -i eth1 -p tcp --dport 22 -j ACCEPT
# Block all other devices on management network except the gateway
iptables -A INPUT -i eth1 -s 172.20.0.0/24 -j DROP
iptables -A OUTPUT -o eth1 -d 172.20.0.0/24 -j DROP
# Allow communication with Docker host gateway
iptables -I OUTPUT -o eth1 -d 172.20.0.1 -j ACCEPT
iptables -I INPUT -i eth1 -s 172.20.0.1 -j ACCEPT

# Enable IP forwarding
echo "Enabling IP forwarding..."
echo 1 > /proc/sys/net/ipv4/ip_forward

# Add forwarding rules between client and router-switch networks
echo "Adding forwarding rules..."
iptables -A FORWARD -i eth0 -o eth2 -j ACCEPT
iptables -A FORWARD -i eth2 -o eth0 -j ACCEPT

# Start SSH
echo "Starting SSH..."
service ssh start

# Remove Docker's auto-assigned IPs and configure correct IPs
echo "Configuring network interfaces..."
# Remove Docker-assigned IPs
ip addr del 192.168.10.2/24 dev eth0 2>/dev/null || true
ip addr del 192.168.20.2/24 dev eth2 2>/dev/null || true

# Add correct IPs
ip addr add 192.168.10.1/24 dev eth0 2>/dev/null || true
ip addr add 192.168.20.1/24 dev eth2 2>/dev/null || true

# Start FRR
echo "Starting FRR..."
service frr start

# Apply FRR configuration to ensure interfaces are configured
sleep 2
vtysh -c "configure terminal" \
      -c "interface eth0" \
      -c "ip address 192.168.10.1/24" \
      -c "no shutdown" \
      -c "exit" \
      -c "interface eth2" \
      -c "ip address 192.168.20.1/24" \
      -c "no shutdown" \
      -c "exit" \
      -c "exit" \
      -c "write memory"

echo "Services started successfully"
echo "SSH: $(service ssh status | grep Active || echo 'Status unknown')"
echo "FRR: $(service frr status | grep Active || echo 'Status unknown')"

# Show configuration
echo "Interface configuration:"
ip addr show
echo ""
echo "Routing table:"
ip route show

# Keep container running
tail -f /var/log/frr/*.log
