#!/bin/bash
set -e

# Fix SSH key permissions
chown ovsuser:ovsuser /home/ovsuser/.ssh/authorized_keys
chmod 600 /home/ovsuser/.ssh/authorized_keys

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

# Start Open vSwitch in userspace mode
echo "Starting Open vSwitch..."
mkdir -p /var/run/openvswitch
ovsdb-tool create /etc/openvswitch/conf.db /usr/share/openvswitch/vswitch.ovsschema || true
ovsdb-server --remote=punix:/var/run/openvswitch/db.sock \
             --remote=db:Open_vSwitch,Open_vSwitch,manager_options \
             --pidfile --detach --log-file

# Initialize OVS
ovs-vsctl --no-wait init
ovs-vswitchd --pidfile --detach --log-file

# Wait for OVS to initialize
sleep 2

# Create main bridge
echo "Creating OVS bridge..."
ovs-vsctl add-br br0 || true

# Add prodnet interface to bridge
if ip link show eth1 &>/dev/null; then
    echo "Adding eth1 to bridge..."
    # Remove IP from eth1 first
    ip addr flush dev eth1
    ovs-vsctl add-port br0 eth1 || true
    # Assign IP to bridge only
    ip addr add 192.168.100.11/24 dev br0
    ip link set br0 up
fi

echo "Services started successfully"
echo "SSH: $(service ssh status | grep Active || echo 'Status unknown')"

# Show OVS configuration
echo "OVS Configuration:"
ovs-vsctl show

# Keep container running
tail -f /var/log/openvswitch/*.log 