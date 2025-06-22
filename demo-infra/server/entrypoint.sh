#!/bin/bash
set -e

# Copy SSH keys from mounted volume to both root and serveruser
if [ -d /root/.ssh ]; then
    echo "SSH keys directory found at /root/.ssh"
    ls -la /root/.ssh/
    
    # Copy authorized_keys to serveruser home
    if [ -f /root/.ssh/authorized_keys ]; then
        echo "Copying authorized_keys to serveruser"
        cp /root/.ssh/authorized_keys /home/serveruser/.ssh/
        chown serveruser:serveruser /home/serveruser/.ssh/authorized_keys
        chmod 600 /home/serveruser/.ssh/authorized_keys
        
        # Copy to a writable location for root and link it
        echo "Setting up authorized_keys for root"
        mkdir -p /tmp/.ssh
        cp /root/.ssh/authorized_keys /tmp/.ssh/
        chmod 600 /tmp/.ssh/authorized_keys
        
        # Update SSH config to look in /tmp/.ssh for root
        echo "AuthorizedKeysFile /tmp/.ssh/authorized_keys" >> /etc/ssh/sshd_config
    else
        echo "No authorized_keys file found in /root/.ssh/"
    fi
else
    echo "No SSH keys directory found at /root/.ssh"
fi

# Find interfaces
SERVER_IF=$(ip -o addr show | grep "192.168.30.10" | awk '{print $2}')
MGMT_IF=$(ip -o addr show | grep "172.25.0.20" | awk '{print $2}')

echo "Server interface: $SERVER_IF"
echo "Management interface: $MGMT_IF"

# Configure firewall rules for network isolation
echo "Configuring network isolation..."
# Allow SSH from host on management network
iptables -A INPUT -i $MGMT_IF -p tcp --dport 22 -j ACCEPT
# Block all other devices on management network except the gateway
iptables -A INPUT -i $MGMT_IF -s 172.25.0.0/24 -j DROP
iptables -A OUTPUT -o $MGMT_IF -d 172.25.0.0/24 -j DROP
# Allow communication with Docker host gateway
iptables -I OUTPUT -o $MGMT_IF -d 172.25.0.1 -j ACCEPT
iptables -I INPUT -i $MGMT_IF -s 172.25.0.1 -j ACCEPT

# Start SSH
echo "Starting SSH..."
service ssh start

# Configure routing
echo "Configuring routing..."
# Remove all existing default routes
while ip route del default 2>/dev/null; do :; done
# Add default route via router on server network
ip route add default via 192.168.30.254 dev $SERVER_IF || true
# Add specific route to client network via router  
ip route add 192.168.10.0/24 via 192.168.30.254 dev $SERVER_IF || true

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
echo ""
echo "Interface configuration:"
ip addr show
echo ""
echo "Routing table:"
ip route show

# Keep container running efficiently
exec sleep infinity 