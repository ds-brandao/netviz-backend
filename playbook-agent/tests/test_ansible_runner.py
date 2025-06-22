import pytest
import tempfile
import os
from unittest.mock import Mock, patch, mock_open
import subprocess
from datetime import datetime

from src.mcp_server.ansible_runner import AnsibleRunner

class TestAnsibleRunner:
    
    @patch('src.mcp_server.ansible_runner.config_manager')
    def test_init(self, mock_config_manager):
        mock_config_manager.get_mcp_server_config.return_value = {
            'timeout': 300
        }
        
        with patch('tempfile.mkdtemp', return_value='/tmp/test-ansible'):
            runner = AnsibleRunner()
        
        assert runner.config['timeout'] == 300
        assert runner.temp_dir == '/tmp/test-ansible'
    
    @patch('src.mcp_server.ansible_runner.config_manager')
    @patch('subprocess.run')
    async def test_run_playbook_success(self, mock_subprocess, mock_config_manager, sample_playbook):
        mock_config_manager.get_mcp_server_config.return_value = {
            'timeout': 300
        }
        
        # Mock successful subprocess run
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "PLAY [Test] ****\nTASK [Test task] ****\nok: [device]\n"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        runner = AnsibleRunner()
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('os.path.exists', return_value=True):
                with patch('os.remove'):
                    result = await runner.run_playbook(
                        playbook_content=sample_playbook,
                        device_host="192.168.1.1",
                        device_user="admin",
                        device_password="password"
                    )
        
        assert result["success"] is True
        assert result["return_code"] == 0
        assert "PLAY [Test]" in result["stdout"]
        assert result["stderr"] == ""
        assert "start_time" in result
        assert "end_time" in result
        
        # Verify subprocess was called with correct arguments
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        assert call_args[0] == "ansible-playbook"
        assert "-i" in call_args
        assert "-v" in call_args
    
    @patch('src.mcp_server.ansible_runner.config_manager')
    @patch('subprocess.run')
    async def test_run_playbook_failure(self, mock_subprocess, mock_config_manager, sample_playbook):
        mock_config_manager.get_mcp_server_config.return_value = {
            'timeout': 300
        }
        
        # Mock failed subprocess run
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = "PLAY [Test] ****\n"
        mock_result.stderr = "TASK [Test task] **** FAILED!"
        mock_subprocess.return_value = mock_result
        
        runner = AnsibleRunner()
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('os.path.exists', return_value=True):
                with patch('os.remove'):
                    result = await runner.run_playbook(
                        playbook_content=sample_playbook,
                        device_host="192.168.1.1",
                        device_user="admin",
                        device_password="password"
                    )
        
        assert result["success"] is False
        assert result["return_code"] == 1
        assert len(result["errors"]) >= 2
        assert "failed with return code 1" in result["errors"][0]
        assert "STDERR:" in result["errors"][1]
        assert "FAILED!" in result["stderr"]
    
    @patch('src.mcp_server.ansible_runner.config_manager')
    @patch('subprocess.run')
    async def test_run_playbook_with_private_key(self, mock_subprocess, mock_config_manager, sample_playbook):
        mock_config_manager.get_mcp_server_config.return_value = {
            'timeout': 300
        }
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        runner = AnsibleRunner()
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('os.path.exists', return_value=True):
                with patch('os.remove'):
                    result = await runner.run_playbook(
                        playbook_content=sample_playbook,
                        device_host="192.168.1.1",
                        device_user="admin",
                        private_key_path="/path/to/key"
                    )
        
        assert result["success"] is True
        
        # Verify private key argument was added
        call_args = mock_subprocess.call_args[0][0]
        assert "--private-key" in call_args
        assert "/path/to/key" in call_args
    
    @patch('src.mcp_server.ansible_runner.config_manager')
    @patch('subprocess.run')
    async def test_run_playbook_timeout(self, mock_subprocess, mock_config_manager, sample_playbook):
        mock_config_manager.get_mcp_server_config.return_value = {
            'timeout': 60
        }
        
        # Mock timeout exception
        mock_subprocess.side_effect = subprocess.TimeoutExpired("ansible-playbook", 60)
        
        runner = AnsibleRunner()
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('os.path.exists', return_value=True):
                with patch('os.remove'):
                    result = await runner.run_playbook(
                        playbook_content=sample_playbook,
                        device_host="192.168.1.1",
                        device_user="admin"
                    )
        
        assert result["success"] is False
        assert len(result["errors"]) > 0
        assert "timed out after 60 seconds" in result["errors"][0]
        assert "end_time" in result
    
    @patch('src.mcp_server.ansible_runner.config_manager')
    @patch('subprocess.run')
    async def test_run_playbook_exception(self, mock_subprocess, mock_config_manager, sample_playbook):
        mock_config_manager.get_mcp_server_config.return_value = {
            'timeout': 300
        }
        
        # Mock general exception
        mock_subprocess.side_effect = Exception("Subprocess failed")
        
        runner = AnsibleRunner()
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('os.path.exists', return_value=True):
                with patch('os.remove'):
                    result = await runner.run_playbook(
                        playbook_content=sample_playbook,
                        device_host="192.168.1.1",
                        device_user="admin"
                    )
        
        assert result["success"] is False
        assert len(result["errors"]) > 0
        assert "Subprocess failed" in result["errors"][0]
        assert "end_time" in result
    
    @patch('src.mcp_server.ansible_runner.config_manager')
    def test_create_inventory_with_password(self, mock_config_manager):
        mock_config_manager.get_mcp_server_config.return_value = {
            'timeout': 300
        }
        
        runner = AnsibleRunner()
        
        inventory = runner._create_inventory(
            device_host="192.168.1.1",
            device_user="admin",
            device_password="password"
        )
        
        assert "[network_devices]" in inventory
        assert "192.168.1.1 ansible_user=admin" in inventory
        assert "ansible_password=password" in inventory
        assert "ansible_connection=network_cli" in inventory
        assert "ansible_network_os=ios" in inventory
        assert "StrictHostKeyChecking=no" in inventory
    
    @patch('src.mcp_server.ansible_runner.config_manager')
    def test_create_inventory_with_private_key(self, mock_config_manager):
        mock_config_manager.get_mcp_server_config.return_value = {
            'timeout': 300
        }
        
        runner = AnsibleRunner()
        
        inventory = runner._create_inventory(
            device_host="192.168.1.1",
            device_user="admin",
            private_key_path="/path/to/key"
        )
        
        assert "[network_devices]" in inventory
        assert "192.168.1.1 ansible_user=admin" in inventory
        assert "ansible_ssh_private_key_file=/path/to/key" in inventory
        assert "ansible_connection=network_cli" in inventory
        assert "ansible_network_os=ios" in inventory
        assert "ansible_password" not in inventory
    
    @patch('src.mcp_server.ansible_runner.config_manager')
    def test_create_inventory_minimal(self, mock_config_manager):
        mock_config_manager.get_mcp_server_config.return_value = {
            'timeout': 300
        }
        
        runner = AnsibleRunner()
        
        inventory = runner._create_inventory(
            device_host="10.0.0.1",
            device_user="netadmin"
        )
        
        assert "[network_devices]" in inventory
        assert "10.0.0.1 ansible_user=netadmin" in inventory
        assert "ansible_connection=network_cli" in inventory
        assert "ansible_network_os=ios" in inventory
        assert "StrictHostKeyChecking=no" in inventory
        assert "ansible_password" not in inventory
        assert "ansible_ssh_private_key_file" not in inventory
    
    @patch('src.mcp_server.ansible_runner.config_manager')
    @patch('subprocess.run')
    def test_health_check_success(self, mock_subprocess, mock_config_manager):
        mock_config_manager.get_mcp_server_config.return_value = {
            'timeout': 300
        }
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "ansible 2.14.0"
        mock_subprocess.return_value = mock_result
        
        runner = AnsibleRunner()
        
        result = runner.health_check()
        
        assert result is True
        
        # Verify ansible --version was called
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        assert call_args == ["ansible", "--version"]
    
    @patch('src.mcp_server.ansible_runner.config_manager')
    @patch('subprocess.run')
    def test_health_check_failure_return_code(self, mock_subprocess, mock_config_manager):
        mock_config_manager.get_mcp_server_config.return_value = {
            'timeout': 300
        }
        
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Command not found"
        mock_subprocess.return_value = mock_result
        
        runner = AnsibleRunner()
        
        result = runner.health_check()
        
        assert result is False
    
    @patch('src.mcp_server.ansible_runner.config_manager')
    @patch('subprocess.run')
    def test_health_check_exception(self, mock_subprocess, mock_config_manager):
        mock_config_manager.get_mcp_server_config.return_value = {
            'timeout': 300
        }
        
        mock_subprocess.side_effect = Exception("Ansible not found")
        
        runner = AnsibleRunner()
        
        result = runner.health_check()
        
        assert result is False
    
    @patch('src.mcp_server.ansible_runner.config_manager')
    @patch('subprocess.run')
    def test_health_check_timeout(self, mock_subprocess, mock_config_manager):
        mock_config_manager.get_mcp_server_config.return_value = {
            'timeout': 300
        }
        
        mock_subprocess.side_effect = subprocess.TimeoutExpired("ansible", 10)
        
        runner = AnsibleRunner()
        
        result = runner.health_check()
        
        assert result is False
    
    @patch('src.mcp_server.ansible_runner.config_manager')
    def test_cleanup(self, mock_config_manager):
        mock_config_manager.get_mcp_server_config.return_value = {
            'timeout': 300
        }
        
        runner = AnsibleRunner()
        
        with patch('os.path.exists', return_value=True) as mock_exists:
            with patch('shutil.rmtree') as mock_rmtree:
                runner.cleanup()
        
        mock_exists.assert_called_once_with(runner.temp_dir)
        mock_rmtree.assert_called_once_with(runner.temp_dir)
    
    @patch('src.mcp_server.ansible_runner.config_manager')
    def test_cleanup_directory_not_exists(self, mock_config_manager):
        mock_config_manager.get_mcp_server_config.return_value = {
            'timeout': 300
        }
        
        runner = AnsibleRunner()
        
        with patch('os.path.exists', return_value=False) as mock_exists:
            with patch('shutil.rmtree') as mock_rmtree:
                runner.cleanup()
        
        mock_exists.assert_called_once_with(runner.temp_dir)
        mock_rmtree.assert_not_called()
    
    @patch('src.mcp_server.ansible_runner.config_manager')
    @patch('subprocess.run')
    async def test_file_cleanup_on_success(self, mock_subprocess, mock_config_manager, sample_playbook):
        mock_config_manager.get_mcp_server_config.return_value = {
            'timeout': 300
        }
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        runner = AnsibleRunner()
        
        mock_remove = Mock()
        with patch('builtins.open', mock_open()):
            with patch('os.path.exists', return_value=True):
                with patch('os.remove', mock_remove):
                    result = await runner.run_playbook(
                        playbook_content=sample_playbook,
                        device_host="192.168.1.1",
                        device_user="admin"
                    )
        
        # Verify files were cleaned up
        assert mock_remove.call_count == 2  # playbook and inventory files
    
    @patch('src.mcp_server.ansible_runner.config_manager')
    @patch('subprocess.run')
    async def test_file_cleanup_on_exception(self, mock_subprocess, mock_config_manager, sample_playbook):
        mock_config_manager.get_mcp_server_config.return_value = {
            'timeout': 300
        }
        
        mock_subprocess.side_effect = Exception("Test exception")
        
        runner = AnsibleRunner()
        
        mock_remove = Mock()
        with patch('builtins.open', mock_open()):
            with patch('os.path.exists', return_value=True):
                with patch('os.remove', mock_remove):
                    result = await runner.run_playbook(
                        playbook_content=sample_playbook,
                        device_host="192.168.1.1",
                        device_user="admin"
                    )
        
        # Verify files were cleaned up even on exception
        assert mock_remove.call_count == 2
        assert result["success"] is False