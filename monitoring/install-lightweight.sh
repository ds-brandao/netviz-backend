#!/bin/bash

echo "=== Installing Lightweight Monitoring Service ==="
echo

# Check if running as root or with sudo
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root or with sudo" 
   exit 1
fi

# Install basic dependencies
echo "1. Installing dependencies..."
apt-get update -qq
apt-get install -y curl net-tools

# Copy script to system location
echo "2. Installing monitoring script..."
cp lightweight-monitor.sh /usr/local/bin/lightweight-monitor
chmod +x /usr/local/bin/lightweight-monitor

# Create systemd service
echo "3. Creating systemd service..."
cat > /etc/systemd/system/lightweight-monitor.service << 'EOF'
[Unit]
Description=Lightweight System and Docker Monitoring
After=network.target
Wants=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/lightweight-monitor
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=lightweight-monitor
KillMode=process

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start service
echo "4. Starting service..."
systemctl daemon-reload
systemctl enable lightweight-monitor.service
systemctl start lightweight-monitor.service

# Check status
echo "5. Checking service status..."
sleep 5
if systemctl is-active --quiet lightweight-monitor; then
    echo "✅ Lightweight monitor is running"
    echo
    echo "View logs: sudo journalctl -u lightweight-monitor -f"
    echo
    
    # Check if data is being sent
    echo "Checking for monitoring data in 30 seconds..."
    sleep 30
    response=$(curl -sk -u admin:xuwzuc-rExzo3-hotjed "https://192.168.0.132:9200/_cat/indices/system-metrics-*?v" 2>/dev/null)
    
    if [[ $response == *"system-metrics-"* ]]; then
        echo "✅ SUCCESS! Monitoring data is being sent to OpenSearch:"
        echo "$response"
    else
        echo "⚠️  No monitoring indices found yet. Check logs if this persists."
        echo "Expected index: system-metrics-$(date +%Y.%m.%d)"
    fi
else
    echo "❌ Service failed to start"
    echo "Check logs: sudo journalctl -u lightweight-monitor -n 50"
    exit 1
fi

echo
echo "=== Installation Complete ==="
echo
echo "The lightweight monitor is now running as a system service."
echo "It collects system and Docker metrics every 30 seconds with minimal overhead."
echo
echo "Useful commands:"
echo "- Check status: sudo systemctl status lightweight-monitor"
echo "- View logs: sudo journalctl -u lightweight-monitor -f"
echo "- Stop service: sudo systemctl stop lightweight-monitor"
echo "- Restart service: sudo systemctl restart lightweight-monitor"
echo
echo "View data in OpenSearch:"
echo "curl -sk -u admin:xuwzuc-rExzo3-hotjed 'https://192.168.0.132:9200/system-metrics-*/_search?size=1&pretty'" 