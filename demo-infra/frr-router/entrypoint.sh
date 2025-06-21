#!/bin/bash
set -e

# Ensure proper ownership of authorized_keys (mounted at runtime)
chown frruser:frruser /home/frruser/.ssh/authorized_keys
chmod 600 /home/frruser/.ssh/authorized_keys

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
