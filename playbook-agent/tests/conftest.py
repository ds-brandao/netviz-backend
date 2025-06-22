import pytest
import tempfile
import os
import yaml
from pathlib import Path
from unittest.mock import Mock, patch
import asyncio

@pytest.fixture
def temp_config_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir()
        
        agent_config = {
            "agent": {
                "max_iterations": 3,
                "timeout_seconds": 120,
                "log_level": "INFO"
            },
            "llm": {
                "model": "llama-3.1-405b",
                "temperature": 0.1,
                "max_tokens": 2000
            },
            "device": {
                "connection_timeout": 15,
                "command_timeout": 30,
                "config_backup_enabled": True
            },
            "github": {
                "repository": "test-playbooks",
                "branch": "main"
            },
            "mcp_server": {
                "host": "localhost",
                "port": 8080,
                "timeout": 120
            },
            "api": {
                "host": "localhost",
                "port": 8000,
                "reload": False
            }
        }
        
        secrets_config = {
            "llm": {
                "api_key": "test-llama-key"
            },
            "github": {
                "token": "test-github-token",
                "username": "test-user"
            }
        }
        
        with open(config_dir / "agent_config.yaml", 'w') as f:
            yaml.dump(agent_config, f)
        
        with open(config_dir / "secrets.yaml", 'w') as f:
            yaml.dump(secrets_config, f)
        
        yield config_dir

@pytest.fixture
def mock_ssh_client():
    with patch('paramiko.SSHClient') as mock_client:
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        
        mock_instance.connect.return_value = None
        mock_instance.set_missing_host_key_policy.return_value = None
        
        mock_stdin = Mock()
        mock_stdout = Mock()
        mock_stderr = Mock()
        
        mock_stdout.read.return_value = b"test output"
        mock_stderr.read.return_value = b""
        
        mock_instance.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)
        
        yield mock_instance

@pytest.fixture
def sample_playbook():
    return """---
- name: Configure network device
  hosts: all
  tasks:
    - name: Configure interface
      ios_config:
        lines:
          - description Test Interface
          - ip address 192.168.1.1 255.255.255.0
        parents: interface GigabitEthernet0/0
"""

@pytest.fixture
def sample_device_config():
    return {
        "show_running-config": "version 15.1\nhostname Router1\n!",
        "show_interfaces": "GigabitEthernet0/0 is up, line protocol is up",
        "show_version": "Cisco IOS Software, Version 15.1",
        "show_ip_route": "Gateway of last resort is not set"
    }

@pytest.fixture
def mock_llm_response():
    return {
        "choices": [{
            "message": {
                "content": """---
- name: Test playbook
  hosts: all
  tasks:
    - name: Test task
      debug:
        msg: "Hello World"
"""
            }
        }]
    }

@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_aiohttp_session():
    with patch('aiohttp.ClientSession') as mock_session:
        mock_instance = Mock()
        mock_session.return_value.__aenter__ = Mock(return_value=mock_instance)
        mock_session.return_value.__aexit__ = Mock(return_value=None)
        
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = Mock(return_value={"success": True})
        mock_response.text = Mock(return_value="OK")
        mock_response.raise_for_status = Mock()
        
        mock_instance.get.return_value.__aenter__ = Mock(return_value=mock_response)
        mock_instance.get.return_value.__aexit__ = Mock(return_value=None)
        mock_instance.post.return_value.__aenter__ = Mock(return_value=mock_response)
        mock_instance.post.return_value.__aexit__ = Mock(return_value=None)
        mock_instance.put.return_value.__aenter__ = Mock(return_value=mock_response)
        mock_instance.put.return_value.__aexit__ = Mock(return_value=None)
        
        yield mock_instance