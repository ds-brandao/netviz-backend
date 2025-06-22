#!/bin/bash

# Lightweight Monitoring Script for Ubuntu Server and Docker Containers
# Sends metrics directly to OpenSearch without Metricbeat

# Configuration
OS_HOST="192.168.0.132"
OS_USER="admin"
OS_PASS="xuwzuc-rExzo3-hotjed"
MONITORING_INTERVAL=30  # seconds
INDEX_PREFIX="system-metrics"

# Function to get current timestamp
get_timestamp() {
    date -u +"%Y-%m-%dT%H:%M:%S.%3NZ"
}

# Function to get system metrics
get_system_metrics() {
    local timestamp=$(get_timestamp)
    local hostname=$(hostname)
    
    # CPU usage (simplified)
    local cpu_usage=$(grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$3+$4+$5)} END {print usage}')
    
    # Memory usage
    local mem_info=$(free -m)
    local mem_total=$(echo "$mem_info" | grep "^Mem:" | awk '{print $2}')
    local mem_used=$(echo "$mem_info" | grep "^Mem:" | awk '{print $3}')
    local mem_percent=$(awk "BEGIN {if($mem_total>0) printf \"%.2f\", ($mem_used/$mem_total)*100; else print 0}")
    
    # Disk usage
    local disk_info=$(df -h / | tail -1)
    local disk_used=$(echo $disk_info | awk '{print $5}' | sed 's/%//')
    
    # Load average
    local load_avg=$(cat /proc/loadavg | awk '{print $1}')
    
    # System uptime
    local uptime_seconds=$(cat /proc/uptime | awk '{print int($1)}')
    
    # Create JSON document
    local json=$(cat <<EOF
{
    "@timestamp": "${timestamp}",
    "host": {
        "name": "${hostname}"
    },
    "metric_type": "system",
    "system": {
        "cpu": {
            "usage_percent": ${cpu_usage:-0}
        },
        "memory": {
            "total_mb": ${mem_total:-0},
            "used_mb": ${mem_used:-0},
            "usage_percent": ${mem_percent:-0}
        },
        "disk": {
            "usage_percent": ${disk_used:-0}
        },
        "load": {
            "1m": ${load_avg:-0}
        },
        "uptime": {
            "seconds": ${uptime_seconds:-0}
        }
    }
}
EOF
)
    
    # Send to OpenSearch
    curl -sk -u "${OS_USER}:${OS_PASS}" \
        -X POST "https://${OS_HOST}:9200/${INDEX_PREFIX}-$(date +%Y.%m.%d)/_doc" \
        -H "Content-Type: application/json" \
        -d "${json}" > /dev/null 2>&1
}

# Function to get Docker container metrics
get_docker_metrics() {
    local timestamp=$(get_timestamp)
    local hostname=$(hostname)
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        return
    fi
    
    # Get list of running containers
    docker ps --format "{{.ID}},{{.Names}},{{.Status}}" | while IFS=',' read container_id container_name container_status; do
        # Get container stats (without streaming)
        local stats=$(timeout 5 docker stats --no-stream --format "{{.CPUPerc}},{{.MemPerc}}" $container_id 2>/dev/null)
        
        if [ -n "$stats" ]; then
            local cpu_percent=$(echo $stats | cut -d',' -f1 | sed 's/%//')
            local mem_percent=$(echo $stats | cut -d',' -f2 | sed 's/%//')
            
            # Create JSON document
            local json=$(cat <<EOF
{
    "@timestamp": "${timestamp}",
    "host": {
        "name": "${hostname}"
    },
    "metric_type": "docker",
    "container": {
        "id": "${container_id:0:12}",
        "name": "${container_name}",
        "status": "${container_status}"
    },
    "docker": {
        "cpu": {
            "usage_percent": ${cpu_percent:-0}
        },
        "memory": {
            "usage_percent": ${mem_percent:-0}
        }
    }
}
EOF
)
            
            # Send to OpenSearch
            curl -sk -u "${OS_USER}:${OS_PASS}" \
                -X POST "https://${OS_HOST}:9200/${INDEX_PREFIX}-$(date +%Y.%m.%d)/_doc" \
                -H "Content-Type: application/json" \
                -d "${json}" > /dev/null 2>&1
        fi
    done
}

# Function to check service health
check_service_health() {
    local timestamp=$(get_timestamp)
    local hostname=$(hostname)
    
    # Check key services
    local services=("ssh:22" "docker:none")
    
    for service_port in "${services[@]}"; do
        local service=$(echo $service_port | cut -d':' -f1)
        local port=$(echo $service_port | cut -d':' -f2)
        local status="down"
        
        # Check service status
        if [ "$service" == "docker" ]; then
            if docker info > /dev/null 2>&1; then
                status="up"
            fi
        elif [ "$port" != "none" ]; then
            if netstat -tuln 2>/dev/null | grep -q ":${port}\s"; then
                status="up"
            fi
        fi
        
        # Create JSON document
        local json=$(cat <<EOF
{
    "@timestamp": "${timestamp}",
    "host": {
        "name": "${hostname}"
    },
    "metric_type": "service_health",
    "service": {
        "name": "${service}",
        "status": "${status}"
    }
}
EOF
)
        
        # Send to OpenSearch
        curl -sk -u "${OS_USER}:${OS_PASS}" \
            -X POST "https://${OS_HOST}:9200/${INDEX_PREFIX}-$(date +%Y.%m.%d)/_doc" \
            -H "Content-Type: application/json" \
            -d "${json}" > /dev/null 2>&1
    done
}

# Main monitoring loop
main() {
    echo "Starting lightweight monitoring..."
    echo "Sending metrics to OpenSearch at ${OS_HOST}"
    echo "Index prefix: ${INDEX_PREFIX}"
    echo "Monitoring interval: ${MONITORING_INTERVAL} seconds"
    echo ""
    
    while true; do
        echo -n "$(date '+%Y-%m-%d %H:%M:%S') - Collecting metrics... "
        
        # Collect and send metrics
        get_system_metrics
        get_docker_metrics
        check_service_health
        
        echo "done"
        
        # Wait for next interval
        sleep $MONITORING_INTERVAL
    done
}

# Handle script termination
trap 'echo -e "\nMonitoring stopped"; exit 0' INT TERM

# Check dependencies
check_dependencies() {
    local missing_deps=()
    
    command -v curl >/dev/null 2>&1 || missing_deps+=("curl")
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        echo "Error: Missing dependencies: ${missing_deps[*]}"
        echo "Install with: sudo apt-get install ${missing_deps[*]}"
        exit 1
    fi
}

# Run checks and start monitoring
check_dependencies
main 