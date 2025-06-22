import asyncio
import json
from typing import Dict, Any, Optional, AsyncGenerator
from langchain_core.tools import tool
import paramiko
import tempfile
import os
from database import get_db_session, NetworkNode
from sqlalchemy import select
from datetime import datetime
import requests

# Backend API configuration for AI tools
BACKEND_API_BASE = "http://localhost:3001"

@tool
async def get_network_status(node_name: str = None) -> dict:
    """Get the status of network infrastructure nodes."""
    async with get_db_session() as session:
        if node_name:
            result = await session.execute(
                select(NetworkNode).where(NetworkNode.name == node_name)
            )
            node = result.scalar_one_or_none()
            if node:
                return {
                    "node": node.name,
                    "status": node.status,
                    "type": node.type,
                    "ip_address": node.ip_address,
                    "last_seen": node.last_updated.isoformat() if node.last_updated else None,
                    "metadata": node.node_metadata
                }
            else:
                return {"error": f"Node '{node_name}' not found"}
        else:
            # Get all nodes
            result = await session.execute(select(NetworkNode))
            nodes = result.scalars().all()
            
            active_count = sum(1 for n in nodes if n.status == "active")
            inactive_count = sum(1 for n in nodes if n.status == "inactive")
            
            return {
                "total_nodes": len(nodes),
                "active": active_count,
                "inactive": inactive_count,
                "nodes": [
                    {
                        "name": node.name,
                        "status": node.status,
                        "type": node.type,
                        "ip_address": node.ip_address
                    }
                    for node in nodes
                ]
            }

@tool
async def get_node_details(node_name: str) -> dict:
    """Get detailed information about a specific network node."""
    async with get_db_session() as session:
        result = await session.execute(
            select(NetworkNode).where(NetworkNode.name == node_name)
        )
        node = result.scalar_one_or_none()
        
        if not node:
            return {"error": f"Node '{node_name}' not found"}
        
        return {
            "id": node.id,
            "name": node.name,
            "type": node.type,
            "ip_address": node.ip_address,
            "status": node.status,
            "metadata": node.node_metadata,
            "last_updated": node.last_updated.isoformat() if node.last_updated else None
        }

@tool
async def update_node_status(node_name: str, status: str, metadata: Optional[Dict[str, Any]] = None) -> dict:
    """Update the status and metadata of a network node."""
    valid_statuses = ["active", "inactive", "warning", "error", "maintenance"]
    if status not in valid_statuses:
        return {"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}
    
    async with get_db_session() as session:
        result = await session.execute(
            select(NetworkNode).where(NetworkNode.name == node_name)
        )
        node = result.scalar_one_or_none()
        
        if not node:
            return {"error": f"Node '{node_name}' not found"}
        
        node.status = status
        node.last_updated = datetime.now()
        
        if metadata:
            node.node_metadata = {**node.node_metadata, **metadata}
        
        await session.commit()
        
        return {
            "success": True,
            "message": f"Node '{node_name}' status updated to '{status}'",
            "node": {
                "name": node.name,
                "status": node.status,
                "metadata": node.node_metadata
            }
        }

@tool
def create_ansible_playbook(task_description: str, target_hosts: str = "all") -> str:
    """Create an Ansible playbook based on natural language description."""
    playbook = f"""---
- name: Generated Ansible Playbook
  hosts: {target_hosts}
  become: yes
  tasks:
    - name: Execute task - {task_description}
      debug:
        msg: "Task: {task_description}"
"""
    
    # Enhanced pattern matching for common tasks
    task_lower = task_description.lower()
    
    if "update" in task_lower and "packages" in task_lower:
        playbook += """
    - name: Update package cache
      apt:
        update_cache: yes
      when: ansible_os_family == "Debian"
    
    - name: Update all packages
      apt:
        upgrade: dist
      when: ansible_os_family == "Debian"
      
    - name: Update package cache (RedHat)
      yum:
        update_cache: yes
      when: ansible_os_family == "RedHat"
"""
    elif "install" in task_lower:
        # Extract package names if mentioned
        packages = ["vim", "htop", "curl"]  # Default packages
        playbook += f"""
    - name: Install packages
      package:
        name: "{{{{ item }}}}"
        state: present
      loop:
        {chr(10).join(f'        - {pkg}' for pkg in packages)}
"""
    elif "restart" in task_lower and "service" in task_lower:
        # Try to extract service name
        service_name = "nginx"  # Default
        if "apache" in task_lower:
            service_name = "apache2"
        elif "mysql" in task_lower:
            service_name = "mysql"
        elif "docker" in task_lower:
            service_name = "docker"
            
        playbook += f"""
    - name: Restart {service_name} service
      systemd:
        name: {service_name}
        state: restarted
        daemon_reload: yes
"""
    elif "check" in task_lower and "disk" in task_lower:
        playbook += """
    - name: Check disk usage
      shell: df -h
      register: disk_usage
    
    - name: Display disk usage
      debug:
        var: disk_usage.stdout_lines
"""
    elif "backup" in task_lower:
        playbook += """
    - name: Create backup directory
      file:
        path: /backup/{{ ansible_date_time.date }}
        state: directory
        mode: '0755'
    
    - name: Backup configuration files
      archive:
        path:
          - /etc/
          - /opt/
        dest: /backup/{{ ansible_date_time.date }}/config_backup.tar.gz
        format: gz
"""
    
    return playbook

@tool
async def execute_ssh_command(host: str, command: str, username: str = "admin", password: Optional[str] = None, key_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Execute SSH command on a remote host with streaming output support.
    Returns a dictionary with status and output.
    """
    try:
        # Create SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect using password or key
        connect_params = {
            "hostname": host,
            "username": username,
            "timeout": 30
        }
        
        if key_file:
            connect_params["key_filename"] = key_file
        elif password:
            connect_params["password"] = password
        else:
            # Try to use default SSH key
            connect_params["key_filename"] = os.path.expanduser("~/.ssh/id_rsa")
        
        ssh.connect(**connect_params)
        
        # Execute command
        stdin, stdout, stderr = ssh.exec_command(command)
        
        # Collect output
        output_lines = []
        error_lines = []
        
        for line in stdout:
            output_lines.append(line.strip())
        
        for line in stderr:
            error_lines.append(line.strip())
        
        # Get exit status
        exit_status = stdout.channel.recv_exit_status()
        
        ssh.close()
        
        return {
            "success": exit_status == 0,
            "exit_code": exit_status,
            "output": "\n".join(output_lines),
            "error": "\n".join(error_lines) if error_lines else None,
            "host": host,
            "command": command
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "host": host,
            "command": command
        }

@tool
async def run_ansible_playbook(playbook_content: str, inventory: str = "localhost,", extra_vars: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Execute an Ansible playbook with streaming output support.
    The inventory can be a comma-separated list of hosts or a path to an inventory file.
    """
    try:
        # Create temporary files for playbook and inventory
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as playbook_file:
            playbook_file.write(playbook_content)
            playbook_path = playbook_file.name
        
        # Prepare ansible command
        cmd = [
            "ansible-playbook",
            "-i", inventory,
            playbook_path
        ]
        
        # Add extra vars if provided
        if extra_vars:
            cmd.extend(["-e", json.dumps(extra_vars)])
        
        # Execute ansible playbook
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Collect output
        stdout, stderr = await process.communicate()
        
        # Clean up temporary file
        os.unlink(playbook_path)
        
        return {
            "success": process.returncode == 0,
            "exit_code": process.returncode,
            "output": stdout.decode() if stdout else "",
            "error": stderr.decode() if stderr else None,
            "playbook_summary": "Playbook execution completed"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "playbook_summary": "Failed to execute playbook"
        } 

@tool
async def get_recent_logs(device_name: Optional[str] = None, time_range: int = 2, log_level: Optional[str] = None) -> str:
    """Get recent logs from OpenSearch directly"""
    print(f"=== GET_RECENT_LOGS FUNCTION DEBUG ===")
    print(f"Received parameters: device_name='{device_name}', time_range={time_range}, log_level='{log_level}'")
    try:
        # Import OpenSearch functionality from app.py
        from app import get_opensearch_session, OPENSEARCH_BASE_URL
        
        # Device name to index mapping
        device_to_index = {
            "frr-router": "frr-router-logs",
            "switch1": "switch1-logs", 
            "switch2": "switch2-logs",
            "server": "server-logs",
            "client": "client-logs"
        }
        
        # Default to searching all log indexes if no specific device
        target_indexes = "*-logs"
        
        if device_name:
            # Map device name to specific index
            if device_name in device_to_index:
                target_indexes = device_to_index[device_name]
                print(f"Mapping device '{device_name}' to index '{target_indexes}'")
            else:
                # Fallback to wildcard search
                target_indexes = f"*{device_name}*-logs"
                print(f"Using fallback mapping for device '{device_name}': {target_indexes}")
        
        # Build OpenSearch query
        opensearch_query = {
            "size": 20,
            "sort": [{"@timestamp": {"order": "desc"}}],
            "query": {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "@timestamp": {
                                    "gte": f"now-{time_range}h"
                                }
                            }
                        }
                    ]
                }
            }
        }
        
        if log_level:
            opensearch_query["query"]["bool"]["must"].append({
                "term": {"level": log_level.upper()}
            })
        
        session = get_opensearch_session()
        url = f"{OPENSEARCH_BASE_URL}/{target_indexes}/_search"
        
        print(f"Querying OpenSearch directly: {url}")
        print(f"Query: {opensearch_query}")
        
        response = session.post(url, json=opensearch_query, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        
        data = response.json()
        logs = []
        
        print(f"OpenSearch returned {data.get('hits', {}).get('total', {}).get('value', 0)} total hits")
        
        for hit in data.get("hits", {}).get("hits", []):
            source = hit["_source"]
            log_message = source.get("log", source.get("message", ""))
            
            # Infer log level from content
            level = "INFO"
            if any(keyword in log_message.lower() for keyword in ["error", "fail", "exception"]):
                level = "ERROR"
            elif any(keyword in log_message.lower() for keyword in ["warn", "warning"]):
                level = "WARN"
            
            logs.append({
                "id": hit["_id"],
                "timestamp": source.get("@timestamp"),
                "level": level,
                "service": hit.get("_index", "").replace("-logs", ""),
                "message": log_message,
            })
        
        print(f"Processed {len(logs)} logs")
        
        if not logs:
            filter_desc = f"last {time_range} hours"
            if device_name:
                filter_desc += f" for device {device_name}"
            if log_level:
                filter_desc += f" with level {log_level}"
            result = f"No logs found for {filter_desc}"
            print(f"Returning: {result}")
            return result
        
        # Format logs for display
        log_summary = f"**Recent Logs** ({len(logs)} entries"
        if device_name:
            log_summary += f" for **{device_name}**"
        log_summary += f", last {time_range} hours):\n\n"
        
        for log in logs[:15]:  # Show first 15 logs
            timestamp = log.get('timestamp', 'Unknown time')
            level = log.get('level', 'INFO')
            message = log.get('message', 'No message')
            service = log.get('service', 'unknown')
            
            # Format timestamp more readable
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime('%H:%M:%S')
            except:
                time_str = timestamp
            
            log_summary += f"`{time_str}` **{level}** [{service}]: {message}\n"
            
        
        if len(logs) > 10:
            log_summary += f"... and {len(logs) - 10} more entries\n"
        
        return log_summary
        
    except Exception as e:
        return f"Error fetching logs: {str(e)}"

@tool  
async def get_device_info(device_id: str) -> str:
    """Get comprehensive device information including recent logs and metrics"""
    try:
        url = f"{BACKEND_API_BASE}/ai/device-info/{device_id}"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return f"Failed to get device info: {response.status_code} - {response.text}"
        
        data = response.json()
        device = data.get("device", {})
        metrics = data.get("metrics", {})
        recent_logs = data.get("recent_logs", [])
        
        # Format comprehensive device report
        report = f"# **{device.get('name', device_id)} Device Report**\n\n"
        
        # Device Status
        report += f"**Status**: {device.get('status', 'Unknown')}\n"
        report += f"**Type**: {device.get('type', 'Unknown')}\n"
        report += f"**Layer**: {device.get('layer', 'Unknown')}\n"
        if device.get('ip_address'):
            report += f"**IP Address**: {device['ip_address']}\n"
        if device.get('last_updated'):
            report += f"**Last Updated**: {device['last_updated']}\n"
        
        report += "\n"
        
        # Metrics
        if metrics:
            report += "## **Current Metrics**\n"
            for host, data in metrics.items():
                if data.get('system'):
                    sys = data['system']
                    if sys.get('cpu', {}).get('usage_percent'):
                        report += f"- **CPU Usage**: {sys['cpu']['usage_percent']:.1f}%\n"
                    if sys.get('memory', {}).get('usage_percent'):
                        report += f"- **Memory Usage**: {sys['memory']['usage_percent']:.1f}%\n"
                    if sys.get('load', {}).get('1m'):
                        report += f"- **Load Average**: {sys['load']['1m']}\n"
        
        # Recent Activity
        if recent_logs:
            report += f"\n## **Recent Activity** ({len(recent_logs)} logs)\n"
            for log in recent_logs[:5]:
                timestamp = log.get('timestamp', '')
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime('%H:%M:%S')
                except:
                    time_str = timestamp
                
                level = log.get('level', 'INFO')
                message = log.get('message', 'No message')
                report += f"- `{time_str}` **{level}**: {message[:100]}{'...' if len(message) > 100 else ''}\n"
        
        return report
        
    except Exception as e:
        return f"Error getting device info: {str(e)}"

@tool
async def get_error_logs(hours: int = 24) -> str:
    """Get error and warning logs from the last N hours"""
    try:
        url = f"{OPENSEARCH_BASE_URL.replace('http://localhost:9200', 'http://localhost:3001')}/logs/errors?hours={hours}&size=50"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return f"Failed to fetch error logs: {response.status_code}"
        
        logs = response.json()
        
        if not logs:
            return f"No error or warning logs found in the last {hours} hours"
        
        # Group by level
        errors = [log for log in logs if log.get('level') == 'ERROR']
        warnings = [log for log in logs if log.get('level') == 'WARN']
        
        summary = f"Error and Warning Logs (last {hours} hours):\n\n"
        summary += f"Found {len(errors)} errors and {len(warnings)} warnings\n\n"
        
        if errors:
            summary += "ERRORS:\n"
            for log in errors[:5]:  # Show first 5 errors
                timestamp = log.get('timestamp', 'Unknown time')
                message = log.get('message', 'No message')
                node = log.get('node_id', 'unknown')
                event_type = log.get('event_type', 'unknown')
                
                summary += f"  [{timestamp}] {node} - {event_type}\n"
                summary += f"    {message}\n"
                
                # Add error details
                metadata = log.get('metadata', {})
                if 'error_code' in metadata:
                    summary += f"    Error Code: {metadata['error_code']}\n"
                if 'retry_count' in metadata:
                    summary += f"    Retry Count: {metadata['retry_count']}\n"
                summary += "\n"
        
        if warnings:
            summary += "WARNINGS:\n"
            for log in warnings[:5]:  # Show first 5 warnings
                timestamp = log.get('timestamp', 'Unknown time')
                message = log.get('message', 'No message')
                node = log.get('node_id', 'unknown')
                event_type = log.get('event_type', 'unknown')
                
                summary += f"  [{timestamp}] {node} - {event_type}\n"
                summary += f"    {message}\n"
                
                # Add warning details
                metadata = log.get('metadata', {})
                if 'cpu_usage' in metadata:
                    summary += f"    CPU Usage: {metadata['cpu_usage']}%\n"
                if 'memory_usage' in metadata:
                    summary += f"    Memory Usage: {metadata['memory_usage']}%\n"
                if 'alert_level' in metadata:
                    summary += f"    Alert Level: {metadata['alert_level']}\n"
                summary += "\n"
        
        return summary
        
    except Exception as e:
        return f"Error fetching error logs: {str(e)}"

@tool
async def search_logs(search_term: str, size: int = 20) -> str:
    """Search logs for specific terms or patterns"""
    try:
        url = f"{OPENSEARCH_BASE_URL.replace('http://localhost:9200', 'http://localhost:3001')}/logs"
        params = {"search": search_term, "size": size}
        
        search_params = "&".join([f"{k}={v}" for k, v in params.items()])
        response = requests.get(f"{url}?{search_params}", timeout=10)
        
        if response.status_code != 200:
            return f"Failed to search logs: {response.status_code}"
        
        logs = response.json()
        
        if not logs:
            return f"No logs found matching '{search_term}'"
        
        summary = f"Search Results for '{search_term}' ({len(logs)} matches):\n\n"
        
        for log in logs[:10]:  # Show first 10 results
            timestamp = log.get('timestamp', 'Unknown time')
            level = log.get('level', 'INFO')
            message = log.get('message', 'No message')
            node = log.get('node_id', 'unknown')
            event_type = log.get('event_type', 'unknown')
            
            summary += f"[{timestamp}] {level} - {node}\n"
            summary += f"  Event: {event_type}\n"
            summary += f"  Message: {message}\n\n"
        
        if len(logs) > 10:
            summary += f"... and {len(logs) - 10} more matches\n"
        
        return summary
        
    except Exception as e:
        return f"Error searching logs: {str(e)}" 