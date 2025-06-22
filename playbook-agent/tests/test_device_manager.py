import pytest
from unittest.mock import Mock, patch, MagicMock
import paramiko

from src.utils.device_manager import DeviceManager

class TestDeviceManager:
    
    def test_init(self):
        dm = DeviceManager(
            device_id="test-device",
            host="192.168.1.1",
            username="admin",
            password="password"
        )
        
        assert dm.device_id == "test-device"
        assert dm.host == "192.168.1.1"
        assert dm.username == "admin"
        assert dm.password == "password"
        assert dm.client is None
        assert dm.original_config is None
    
    def test_init_with_key(self):
        dm = DeviceManager(
            device_id="test-device",
            host="192.168.1.1",
            username="admin",
            private_key_path="/path/to/key"
        )
        
        assert dm.private_key_path == "/path/to/key"
        assert dm.password is None
    
    @patch('src.utils.device_manager.config_manager')
    def test_connect_with_password_success(self, mock_config_manager, mock_ssh_client):
        mock_config_manager.get_device_config.return_value = {
            'connection_timeout': 30,
            'command_timeout': 60,
            'config_backup_enabled': True
        }
        
        dm = DeviceManager("test-device", "192.168.1.1", "admin", password="password")
        
        with patch('src.utils.device_manager.paramiko.SSHClient') as mock_ssh_class:
            mock_ssh_class.return_value = mock_ssh_client
            
            result = dm.connect()
            
            assert result is True
            assert dm.client == mock_ssh_client
            mock_ssh_client.set_missing_host_key_policy.assert_called_once()
            mock_ssh_client.connect.assert_called_once_with(
                hostname="192.168.1.1",
                username="admin",
                password="password",
                timeout=30
            )
    
    @patch('src.utils.device_manager.config_manager')
    @patch('src.utils.device_manager.paramiko.RSAKey')
    def test_connect_with_private_key_success(self, mock_rsa_key, mock_config_manager, mock_ssh_client):
        mock_config_manager.get_device_config.return_value = {
            'connection_timeout': 30,
            'command_timeout': 60,
            'config_backup_enabled': True
        }
        
        mock_key = Mock()
        mock_rsa_key.from_private_key_file.return_value = mock_key
        
        dm = DeviceManager("test-device", "192.168.1.1", "admin", private_key_path="/path/to/key")
        
        with patch('src.utils.device_manager.paramiko.SSHClient') as mock_ssh_class:
            mock_ssh_class.return_value = mock_ssh_client
            
            result = dm.connect()
            
            assert result is True
            mock_rsa_key.from_private_key_file.assert_called_once_with("/path/to/key")
            mock_ssh_client.connect.assert_called_once_with(
                hostname="192.168.1.1",
                username="admin",
                pkey=mock_key,
                timeout=30
            )
    
    @patch('src.utils.device_manager.config_manager')
    def test_connect_failure(self, mock_config_manager):
        mock_config_manager.get_device_config.return_value = {
            'connection_timeout': 30,
            'command_timeout': 60,
            'config_backup_enabled': True
        }
        
        dm = DeviceManager("test-device", "192.168.1.1", "admin", password="password")
        
        with patch('src.utils.device_manager.paramiko.SSHClient') as mock_ssh_class:
            mock_client = Mock()
            mock_ssh_class.return_value = mock_client
            mock_client.connect.side_effect = paramiko.AuthenticationException("Auth failed")
            
            result = dm.connect()
            
            assert result is False
            assert dm.client is not None  # Client is still assigned before connection attempt
    
    @patch('src.utils.device_manager.config_manager')
    def test_capture_configuration_success(self, mock_config_manager, mock_ssh_client, sample_device_config):
        mock_config_manager.get_device_config.return_value = {
            'connection_timeout': 30,
            'command_timeout': 60,
            'config_backup_enabled': True
        }
        
        dm = DeviceManager("test-device", "192.168.1.1", "admin")
        dm.client = mock_ssh_client
        
        def mock_exec_command(command, timeout=None):
            mock_stdin = Mock()
            mock_stdout = Mock()
            mock_stderr = Mock()
            
            if "running-config" in command:
                mock_stdout.read.return_value = b"version 15.1\nhostname Router1\n!"
            elif "interfaces" in command:
                mock_stdout.read.return_value = b"GigabitEthernet0/0 is up, line protocol is up"
            else:
                mock_stdout.read.return_value = b"test output"
            
            mock_stderr.read.return_value = b""
            return mock_stdin, mock_stdout, mock_stderr
        
        mock_ssh_client.exec_command.side_effect = mock_exec_command
        
        result = dm.capture_configuration()
        
        assert isinstance(result, dict)
        assert "show_running-config" in result
        assert "show_interfaces" in result
        assert dm.original_config is not None
        assert mock_ssh_client.exec_command.call_count == 5  # 5 commands configured
    
    @patch('src.utils.device_manager.config_manager')
    def test_capture_configuration_not_connected(self, mock_config_manager):
        mock_config_manager.get_device_config.return_value = {
            'connection_timeout': 30,
            'command_timeout': 60,
            'config_backup_enabled': True
        }
        
        dm = DeviceManager("test-device", "192.168.1.1", "admin")
        dm.client = None
        
        with pytest.raises(RuntimeError, match="Not connected to device"):
            dm.capture_configuration()
    
    @patch('src.utils.device_manager.config_manager')
    def test_capture_configuration_command_error(self, mock_config_manager, mock_ssh_client):
        mock_config_manager.get_device_config.return_value = {
            'connection_timeout': 30,
            'command_timeout': 60,
            'config_backup_enabled': True
        }
        
        dm = DeviceManager("test-device", "192.168.1.1", "admin")
        dm.client = mock_ssh_client
        
        mock_ssh_client.exec_command.side_effect = Exception("Command failed")
        
        result = dm.capture_configuration()
        
        assert isinstance(result, dict)
        for key, value in result.items():
            assert value.startswith("Error:")
    
    @patch('src.utils.device_manager.config_manager')
    def test_restore_configuration_success(self, mock_config_manager, mock_ssh_client):
        mock_config_manager.get_device_config.return_value = {
            'connection_timeout': 30,
            'command_timeout': 60,
            'config_backup_enabled': True
        }
        
        dm = DeviceManager("test-device", "192.168.1.1", "admin")
        dm.client = mock_ssh_client
        dm.original_config = {
            "show_running-config": "version 15.1\nhostname Router1\n!"
        }
        
        mock_stdin = Mock()
        mock_stdout = Mock()
        mock_stderr = Mock()
        mock_ssh_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)
        
        result = dm.restore_configuration()
        
        assert result is True
        mock_ssh_client.exec_command.assert_called()
        mock_stdin.write.assert_called()
        mock_stdin.flush.assert_called()
    
    @patch('src.utils.device_manager.config_manager')
    def test_restore_configuration_not_connected(self, mock_config_manager):
        mock_config_manager.get_device_config.return_value = {
            'connection_timeout': 30,
            'command_timeout': 60,
            'config_backup_enabled': True
        }
        
        dm = DeviceManager("test-device", "192.168.1.1", "admin")
        dm.client = None
        
        with pytest.raises(RuntimeError, match="Not connected to device"):
            dm.restore_configuration()
    
    @patch('src.utils.device_manager.config_manager')
    def test_restore_configuration_no_original_config(self, mock_config_manager, mock_ssh_client):
        mock_config_manager.get_device_config.return_value = {
            'connection_timeout': 30,
            'command_timeout': 60,
            'config_backup_enabled': True
        }
        
        dm = DeviceManager("test-device", "192.168.1.1", "admin")
        dm.client = mock_ssh_client
        dm.original_config = None
        
        result = dm.restore_configuration()
        
        assert result is False
    
    @patch('src.utils.device_manager.config_manager')
    def test_restore_configuration_failure(self, mock_config_manager, mock_ssh_client):
        mock_config_manager.get_device_config.return_value = {
            'connection_timeout': 30,
            'command_timeout': 60,
            'config_backup_enabled': True
        }
        
        dm = DeviceManager("test-device", "192.168.1.1", "admin")
        dm.client = mock_ssh_client
        dm.original_config = {
            "show_running-config": "version 15.1\nhostname Router1\n!"
        }
        
        mock_ssh_client.exec_command.side_effect = Exception("Restore failed")
        
        result = dm.restore_configuration()
        
        assert result is False
    
    def test_disconnect(self, mock_ssh_client):
        dm = DeviceManager("test-device", "192.168.1.1", "admin")
        dm.client = mock_ssh_client
        
        dm.disconnect()
        
        mock_ssh_client.close.assert_called_once()
    
    def test_disconnect_no_client(self):
        dm = DeviceManager("test-device", "192.168.1.1", "admin")
        dm.client = None
        
        dm.disconnect()  # Should not raise an exception