#!/bin/bash

echo "=== Metricbeat Setup Script for Ubuntu ==="
echo

# Check if running as root or with sudo
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root or with sudo" 
   exit 1
fi

# Function to check command success
check_status() {
    if [ $? -eq 0 ]; then
        echo "✅ $1"
    else
        echo "❌ $1 failed"
        exit 1
    fi
}

# Option 1: Install Metricbeat directly on host
install_host_metricbeat() {
    echo "Installing Metricbeat on host system..."
    
    # Add Elastic repository
    wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | apt-key add -
    check_status "Added Elastic GPG key"
    
    apt-get install -y apt-transport-https
    check_status "Installed apt-transport-https"
    
    echo "deb https://artifacts.elastic.co/packages/7.x/apt stable main" | tee /etc/apt/sources.list.d/elastic-7.x.list
    check_status "Added Elastic repository"
    
    # Update and install
    apt-get update
    apt-get install -y metricbeat
    check_status "Installed Metricbeat"
    
    # Copy configuration
    cp metricbeat.yml /etc/metricbeat/metricbeat.yml
    check_status "Copied configuration"
    
    # Set permissions
    chmod 600 /etc/metricbeat/metricbeat.yml
    chown root:root /etc/metricbeat/metricbeat.yml
    
    # Create log directory
    mkdir -p /var/log/metricbeat
    
    # Enable and start service
    systemctl enable metricbeat
    systemctl start metricbeat
    check_status "Started Metricbeat service"
    
    echo ""
    echo "Metricbeat installed and running on host"
    echo "Check status: sudo systemctl status metricbeat"
    echo "View logs: sudo journalctl -u metricbeat -f"
}

# Option 2: Run Metricbeat in Docker
run_docker_metricbeat() {
    echo "Running Metricbeat in Docker container..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        echo "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Create log directory
    mkdir -p /var/log/metricbeat
    chmod 755 /var/log/metricbeat
    
    # Start Metricbeat container
    docker-compose -f docker-compose.metricbeat.yml up -d
    check_status "Started Metricbeat container"
    
    echo ""
    echo "Metricbeat running in Docker container"
    echo "Check status: docker ps | grep metricbeat"
    echo "View logs: docker logs -f metricbeat"
}

# Test connection to OpenSearch
test_opensearch_connection() {
    echo ""
    echo "Testing OpenSearch connection..."
    
    # Wait for Metricbeat to start
    sleep 10
    
    # Check if indices are created
    response=$(curl -sk -u admin:xuwzuc-rExzo3-hotjed "https://192.168.0.132:9200/_cat/indices/metricbeat-*?v" 2>/dev/null)
    
    if [[ $response == *"metricbeat-"* ]]; then
        echo "✅ Metricbeat is successfully sending data to OpenSearch"
        echo "$response"
    else
        echo "⚠️  No Metricbeat indices found yet. This may take a minute..."
        echo "Check manually: curl -sk -u admin:xuwzuc-rExzo3-hotjed 'https://192.168.0.132:9200/_cat/indices/metricbeat-*?v'"
    fi
}

# Main menu
echo "Choose installation method:"
echo "1) Install Metricbeat on host (recommended for production)"
echo "2) Run Metricbeat in Docker container (easier setup)"
echo "3) Exit"
echo

read -p "Enter choice [1-3]: " choice

case $choice in
    1)
        install_host_metricbeat
        test_opensearch_connection
        ;;
    2)
        run_docker_metricbeat
        test_opensearch_connection
        ;;
    3)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Verify data in OpenSearch:"
echo "   curl -sk -u admin:xuwzuc-rExzo3-hotjed 'https://192.168.0.132:9200/metricbeat-*/_search?size=1&pretty'"
echo ""
echo "2. Create visualizations in OpenSearch Dashboards:"
echo "   https://192.168.0.132:5601"
echo ""
echo "3. Set up alerts using the provided monitor configurations" 