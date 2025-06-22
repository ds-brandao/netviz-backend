import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import aiohttp

from src.utils.mcp_client import MCPClient

class TestMCPClient:
    
    @patch('src.utils.mcp_client.config_manager')
    def test_init(self, mock_config_manager):
        mock_config_manager.get_mcp_server_config.return_value = {
            'url': 'http://localhost:8080',
            'host': 'localhost',
            'port': 8080,
            'timeout': 300
        }
        
        client = MCPClient()
        
        assert client.base_url == 'http://localhost:8080'
        assert client.timeout == 300
    
    @patch('src.utils.mcp_client.config_manager')
    @patch('aiohttp.ClientSession')
    async def test_store_playbook_success(self, mock_session_class, mock_config_manager):
        mock_config_manager.get_mcp_server_config.return_value = {
            'url': 'http://localhost:8080',
            'timeout': 300
        }
        
        # Mock the response
        mock_response = AsyncMock()
        mock_response.json.return_value = {"success": True, "id": "123"}
        mock_response.raise_for_status.return_value = None
        
        # Mock the session
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        client = MCPClient()
        
        result = await client.store_playbook(
            playbook_name="test-playbook",
            playbook_content="---\n- name: test",
            iteration=2
        )
        
        assert result["success"] is True
        assert result["id"] == "123"
        
        # Verify the call was made correctly
        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args
        assert "store-playbook" in call_args[0][0]
        
        json_payload = call_args[1]["json"]
        assert json_payload["playbook_name"] == "test-playbook_v2.yml"
        assert json_payload["playbook_content"] == "---\n- name: test"
        assert json_payload["iteration"] == 2
    
    @patch('src.utils.mcp_client.config_manager')
    @patch('aiohttp.ClientSession')
    async def test_store_playbook_default_iteration(self, mock_session_class, mock_config_manager):
        mock_config_manager.get_mcp_server_config.return_value = {
            'url': 'http://localhost:8080',
            'timeout': 300
        }
        
        mock_response = AsyncMock()
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status.return_value = None
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        client = MCPClient()
        
        await client.store_playbook(
            playbook_name="test-playbook",
            playbook_content="---\n- name: test"
        )
        
        call_args = mock_session.post.call_args
        json_payload = call_args[1]["json"]
        assert json_payload["playbook_name"] == "test-playbook_v1.yml"
        assert json_payload["iteration"] == 1
    
    @patch('src.utils.mcp_client.config_manager')
    @patch('aiohttp.ClientSession')
    async def test_store_playbook_failure(self, mock_session_class, mock_config_manager):
        mock_config_manager.get_mcp_server_config.return_value = {
            'url': 'http://localhost:8080',
            'timeout': 300
        }
        
        mock_session = AsyncMock()
        mock_session.post.side_effect = aiohttp.ClientError("Connection error")
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        client = MCPClient()
        
        with pytest.raises(aiohttp.ClientError):
            await client.store_playbook(
                playbook_name="test-playbook",
                playbook_content="---\n- name: test"
            )
    
    @patch('src.utils.mcp_client.config_manager')
    @patch('aiohttp.ClientSession')
    async def test_run_playbook_success(self, mock_session_class, mock_config_manager):
        mock_config_manager.get_mcp_server_config.return_value = {
            'url': 'http://localhost:8080',
            'timeout': 300
        }
        
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "success": True,
            "message": "Playbook executed successfully"
        }
        mock_response.raise_for_status.return_value = None
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        client = MCPClient()
        
        result = await client.run_playbook(
            playbook_name="test-playbook.yml",
            device_id="device-01",
            device_host="192.168.1.1",
            device_user="admin",
            device_password="password"
        )
        
        assert result["success"] is True
        assert "executed successfully" in result["message"]
        
        call_args = mock_session.post.call_args
        assert "run-playbook" in call_args[0][0]
        
        json_payload = call_args[1]["json"]
        assert json_payload["playbook_name"] == "test-playbook.yml"
        assert json_payload["device_id"] == "device-01"
        assert json_payload["device_host"] == "192.168.1.1"
        assert json_payload["device_user"] == "admin"
        assert json_payload["device_password"] == "password"
    
    @patch('src.utils.mcp_client.config_manager')
    @patch('aiohttp.ClientSession')
    async def test_run_playbook_with_private_key(self, mock_session_class, mock_config_manager):
        mock_config_manager.get_mcp_server_config.return_value = {
            'url': 'http://localhost:8080',
            'timeout': 300
        }
        
        mock_response = AsyncMock()
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status.return_value = None
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        client = MCPClient()
        
        await client.run_playbook(
            playbook_name="test-playbook.yml",
            device_id="device-01",
            device_host="192.168.1.1",
            device_user="admin",
            private_key_path="/path/to/key"
        )
        
        call_args = mock_session.post.call_args
        json_payload = call_args[1]["json"]
        assert json_payload["private_key_path"] == "/path/to/key"
        assert "device_password" not in json_payload
    
    @patch('src.utils.mcp_client.config_manager')
    @patch('aiohttp.ClientSession')
    async def test_run_playbook_failure(self, mock_session_class, mock_config_manager):
        mock_config_manager.get_mcp_server_config.return_value = {
            'url': 'http://localhost:8080',
            'timeout': 300
        }
        
        mock_session = AsyncMock()
        mock_session.post.side_effect = aiohttp.ClientError("Server error")
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        client = MCPClient()
        
        with pytest.raises(aiohttp.ClientError):
            await client.run_playbook(
                playbook_name="test-playbook.yml",
                device_id="device-01",
                device_host="192.168.1.1",
                device_user="admin"
            )
    
    @patch('src.utils.mcp_client.config_manager')
    @patch('aiohttp.ClientSession')
    async def test_get_playbook_history_success(self, mock_session_class, mock_config_manager):
        mock_config_manager.get_mcp_server_config.return_value = {
            'url': 'http://localhost:8080',
            'timeout': 300
        }
        
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "base_name": "test-playbook",
            "files": [
                {"name": "test-playbook_v1.yml", "size": 100},
                {"name": "test-playbook_v2.yml", "size": 120}
            ],
            "total_versions": 2
        }
        mock_response.raise_for_status.return_value = None
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        client = MCPClient()
        
        result = await client.get_playbook_history("test-playbook")
        
        assert result["base_name"] == "test-playbook"
        assert result["total_versions"] == 2
        assert len(result["files"]) == 2
        
        call_args = mock_session.get.call_args
        assert "playbook-history/test-playbook" in call_args[0][0]
    
    @patch('src.utils.mcp_client.config_manager')
    @patch('aiohttp.ClientSession')
    async def test_get_playbook_history_failure(self, mock_session_class, mock_config_manager):
        mock_config_manager.get_mcp_server_config.return_value = {
            'url': 'http://localhost:8080',
            'timeout': 300
        }
        
        mock_session = AsyncMock()
        mock_session.get.side_effect = aiohttp.ClientError("Not found")
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        client = MCPClient()
        
        with pytest.raises(aiohttp.ClientError):
            await client.get_playbook_history("nonexistent-playbook")
    
    @patch('src.utils.mcp_client.config_manager')
    @patch('aiohttp.ClientSession')
    async def test_health_check_success(self, mock_session_class, mock_config_manager):
        mock_config_manager.get_mcp_server_config.return_value = {
            'url': 'http://localhost:8080',
            'timeout': 300
        }
        
        mock_response = AsyncMock()
        mock_response.status = 200
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        client = MCPClient()
        
        result = await client.health_check()
        
        assert result is True
        
        call_args = mock_session.get.call_args
        assert "health" in call_args[0][0]
    
    @patch('src.utils.mcp_client.config_manager')
    @patch('aiohttp.ClientSession')
    async def test_health_check_failure_status(self, mock_session_class, mock_config_manager):
        mock_config_manager.get_mcp_server_config.return_value = {
            'url': 'http://localhost:8080',
            'timeout': 300
        }
        
        mock_response = AsyncMock()
        mock_response.status = 500
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        client = MCPClient()
        
        result = await client.health_check()
        
        assert result is False
    
    @patch('src.utils.mcp_client.config_manager')
    @patch('aiohttp.ClientSession')
    async def test_health_check_exception(self, mock_session_class, mock_config_manager):
        mock_config_manager.get_mcp_server_config.return_value = {
            'url': 'http://localhost:8080',
            'timeout': 300
        }
        
        mock_session = AsyncMock()
        mock_session.get.side_effect = aiohttp.ClientError("Connection failed")
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        client = MCPClient()
        
        result = await client.health_check()
        
        assert result is False
    
    @patch('src.utils.mcp_client.config_manager')
    def test_get_timestamp(self, mock_config_manager):
        mock_config_manager.get_mcp_server_config.return_value = {
            'url': 'http://localhost:8080',
            'timeout': 300
        }
        
        client = MCPClient()
        
        timestamp = client._get_timestamp()
        
        assert isinstance(timestamp, str)
        assert timestamp.endswith('Z')
        assert 'T' in timestamp  # ISO format
    
    @patch('src.utils.mcp_client.config_manager')
    def test_url_stripping(self, mock_config_manager):
        mock_config_manager.get_mcp_server_config.return_value = {
            'url': 'http://localhost:8080/',  # Note trailing slash
            'timeout': 300
        }
        
        client = MCPClient()
        
        assert client.base_url == 'http://localhost:8080'  # Should be stripped