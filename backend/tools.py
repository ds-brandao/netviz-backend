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