#!/bin/bash
set -e

# Setup logging
LOG_DIR="/var/log/frr-router"
mkdir -p "$LOG_DIR"
exec 1> >(tee -a "$LOG_DIR/router.log")
exec 2> >(tee -a "$LOG_DIR/router-error.log")

# Copy SSH keys from mounted volume to both root and frruser
if [ -d /root/.ssh ]; then
    echo "SSH keys directory found at /root/.ssh"
    ls -la /root/.ssh/
    
    # Copy authorized_keys to frruser home
    if [ -f /root/.ssh/authorized_keys ]; then
        echo "Copying authorized_keys to frruser"
        cp /root/.ssh/authorized_keys /home/frruser/.ssh/
        chown frruser:frruser /home/frruser/.ssh/authorized_keys
        chmod 600 /home/frruser/.ssh/authorized_keys
        
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

# Set passwords for SSH access
echo "Setting up passwords..."
echo 'root:ansible123' | chpasswd
echo 'frruser:ansible123' | chpasswd

# Configure SSH logging
echo "Configuring SSH logging..."
echo "SyslogFacility LOCAL0" >> /etc/ssh/sshd_config
echo "LogLevel INFO" >> /etc/ssh/sshd_config

# Start SSH
echo "Starting SSH..."
service ssh start

# Gateway IPs already assigned by Docker - no need to add them manually
echo "Using Docker-assigned gateway IPs..."

# Configure FRR logging
echo "Configuring FRR logging..."
mkdir -p /etc/frr
echo "log file $LOG_DIR/frr.log" >> /etc/frr/vtysh.conf
echo "log commands" >> /etc/frr/vtysh.conf

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

# Start continuous logging process
echo "$(date): Router container startup completed" >> "$LOG_DIR/system.log"

# Log routing table changes and system metrics
(
  while true; do
    echo "$(date): Routing table:" >> "$LOG_DIR/system.log"
    ip route show >> "$LOG_DIR/system.log" 2>&1
    echo "$(date): Interface stats:" >> "$LOG_DIR/system.log"
    ip -s link show >> "$LOG_DIR/system.log" 2>&1
    echo "$(date): FRR status:" >> "$LOG_DIR/system.log"
    vtysh -c "show ip route" >> "$LOG_DIR/system.log" 2>&1 || true
    echo "$(date): Memory usage: $(free -h | grep Mem)" >> "$LOG_DIR/system.log"
    sleep 60
  done
) &

# Keep container running efficiently
exec sleep infinity
