import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.agent.playbook_agent import PlaybookAgent

class TestPlaybookAgent:
    
    @patch('src.agent.playbook_agent.config_manager')
    @patch('src.agent.playbook_agent.LLMClient')
    @patch('src.agent.playbook_agent.MCPClient')
    @patch('src.agent.playbook_agent.PlaybookValidator')
    def test_init(self, mock_validator, mock_mcp_client, mock_llm_client, mock_config_manager):
        mock_config_manager.get_agent_config.return_value = {
            'max_iterations': 5,
            'timeout_seconds': 300,
            'log_level': 'INFO'
        }
        
        agent = PlaybookAgent()
        
        assert agent.max_iterations == 5
        mock_llm_client.assert_called_once()
        mock_mcp_client.assert_called_once()
        mock_validator.assert_called_once()
    
    @patch('src.agent.playbook_agent.config_manager')
    @patch('src.agent.playbook_agent.DeviceManager')
    @patch('src.agent.playbook_agent.LLMClient')
    @patch('src.agent.playbook_agent.MCPClient')
    @patch('src.agent.playbook_agent.PlaybookValidator')
    async def test_generate_and_test_playbook_success_first_iteration(
        self, mock_validator, mock_mcp_client, mock_llm_client, mock_device_manager, mock_config_manager, 
        sample_device_config, sample_playbook
    ):
        mock_config_manager.get_agent_config.return_value = {
            'max_iterations': 3,
            'timeout_seconds': 300,
            'log_level': 'INFO'
        }
        
        # Mock device manager
        mock_dm_instance = Mock()
        mock_device_manager.return_value = mock_dm_instance
        mock_dm_instance.connect.return_value = True
        mock_dm_instance.capture_configuration.return_value = sample_device_config
        mock_dm_instance.disconnect.return_value = None
        
        # Mock validator
        mock_validator_instance = Mock()
        mock_validator.return_value = mock_validator_instance
        mock_validator_instance.validate_all.return_value = (True, [])
        mock_validator_instance.cleanup.return_value = None
        
        # Mock LLM client
        mock_llm_instance = Mock()
        mock_llm_client.return_value = mock_llm_instance
        mock_llm_instance.generate_playbook.return_value = sample_playbook
        
        # Mock MCP client
        mock_mcp_instance = AsyncMock()
        mock_mcp_client.return_value = mock_mcp_instance
        mock_mcp_instance.store_playbook.return_value = {"success": True}
        mock_mcp_instance.run_playbook.return_value = {"success": True}
        
        agent = PlaybookAgent()
        
        result = await agent.generate_and_test_playbook(
            device_id="test-device",
            device_host="192.168.1.1",
            device_user="admin",
            intentions="Configure OSPF",
            device_password="password"
        )
        
        assert result["success"] is True
        assert result["device_id"] == "test-device"
        assert result["intentions"] == "Configure OSPF"
        assert len(result["iterations"]) == 1
        assert result["iterations"][0]["success"] is True
        assert result["final_playbook"] == sample_playbook
        
        # Verify device manager was called correctly
        mock_dm_instance.connect.assert_called_once()
        mock_dm_instance.capture_configuration.assert_called_once()
        mock_dm_instance.disconnect.assert_called_once()
        
        # Verify LLM was called
        mock_llm_instance.generate_playbook.assert_called_once()
        
        # Verify validation
        mock_validator_instance.validate_all.assert_called_once_with(sample_playbook)
        
        # Verify MCP calls
        mock_mcp_instance.store_playbook.assert_called_once()
        mock_mcp_instance.run_playbook.assert_called_once()
    
    @patch('src.agent.playbook_agent.config_manager')
    @patch('src.agent.playbook_agent.DeviceManager')
    @patch('src.agent.playbook_agent.LLMClient')
    @patch('src.agent.playbook_agent.MCPClient')
    @patch('src.agent.playbook_agent.PlaybookValidator')
    async def test_generate_and_test_playbook_success_after_iterations(
        self, mock_validator, mock_mcp_client, mock_llm_client, mock_device_manager, mock_config_manager,
        sample_device_config, sample_playbook
    ):
        mock_config_manager.get_agent_config.return_value = {
            'max_iterations': 3,
            'timeout_seconds': 300,
            'log_level': 'INFO'
        }
        
        # Mock device manager
        mock_dm_instance = Mock()
        mock_device_manager.return_value = mock_dm_instance
        mock_dm_instance.connect.return_value = True
        mock_dm_instance.capture_configuration.return_value = sample_device_config
        mock_dm_instance.restore_configuration.return_value = True
        mock_dm_instance.disconnect.return_value = None
        
        # Mock validator - always pass
        mock_validator_instance = Mock()
        mock_validator.return_value = mock_validator_instance
        mock_validator_instance.validate_all.return_value = (True, [])
        mock_validator_instance.cleanup.return_value = None
        
        # Mock LLM client
        mock_llm_instance = Mock()
        mock_llm_client.return_value = mock_llm_instance
        mock_llm_instance.generate_playbook.return_value = sample_playbook
        
        # Mock MCP client - fail first two iterations, succeed on third
        mock_mcp_instance = AsyncMock()
        mock_mcp_client.return_value = mock_mcp_instance
        mock_mcp_instance.store_playbook.return_value = {"success": True}
        mock_mcp_instance.run_playbook.side_effect = [
            {"success": False, "data": {"errors": ["Error 1"]}},
            {"success": False, "data": {"errors": ["Error 2"]}},
            {"success": True}
        ]
        
        agent = PlaybookAgent()
        
        result = await agent.generate_and_test_playbook(
            device_id="test-device",
            device_host="192.168.1.1",
            device_user="admin",
            intentions="Configure OSPF"
        )
        
        assert result["success"] is True
        assert len(result["iterations"]) == 3
        assert result["iterations"][0]["success"] is False
        assert result["iterations"][1]["success"] is False
        assert result["iterations"][2]["success"] is True
        
        # Verify restore_configuration was called for failed iterations
        assert mock_dm_instance.restore_configuration.call_count == 2
        
        # Verify LLM was called with previous errors
        assert mock_llm_instance.generate_playbook.call_count == 3
        calls = mock_llm_instance.generate_playbook.call_args_list
        assert calls[1][1]["previous_errors"] == ["Error 1"]
        assert calls[2][1]["previous_errors"] == ["Error 1", "Error 2"]
    
    @patch('src.agent.playbook_agent.config_manager')
    @patch('src.agent.playbook_agent.DeviceManager')
    @patch('src.agent.playbook_agent.LLMClient')
    @patch('src.agent.playbook_agent.MCPClient')
    @patch('src.agent.playbook_agent.PlaybookValidator')
    async def test_generate_and_test_playbook_max_iterations_reached(
        self, mock_validator, mock_mcp_client, mock_llm_client, mock_device_manager, mock_config_manager,
        sample_device_config, sample_playbook
    ):
        mock_config_manager.get_agent_config.return_value = {
            'max_iterations': 2,
            'timeout_seconds': 300,
            'log_level': 'INFO'
        }
        
        # Mock device manager
        mock_dm_instance = Mock()
        mock_device_manager.return_value = mock_dm_instance
        mock_dm_instance.connect.return_value = True
        mock_dm_instance.capture_configuration.return_value = sample_device_config
        mock_dm_instance.restore_configuration.return_value = True
        mock_dm_instance.disconnect.return_value = None
        
        # Mock validator
        mock_validator_instance = Mock()
        mock_validator.return_value = mock_validator_instance
        mock_validator_instance.validate_all.return_value = (True, [])
        mock_validator_instance.cleanup.return_value = None
        
        # Mock LLM client
        mock_llm_instance = Mock()
        mock_llm_client.return_value = mock_llm_instance
        mock_llm_instance.generate_playbook.return_value = sample_playbook
        
        # Mock MCP client - always fail
        mock_mcp_instance = AsyncMock()
        mock_mcp_client.return_value = mock_mcp_instance
        mock_mcp_instance.store_playbook.return_value = {"success": True}
        mock_mcp_instance.run_playbook.return_value = {"success": False, "data": {"errors": ["Always fails"]}}
        
        agent = PlaybookAgent()
        
        result = await agent.generate_and_test_playbook(
            device_id="test-device",
            device_host="192.168.1.1",
            device_user="admin",
            intentions="Configure OSPF"
        )
        
        assert result["success"] is False
        assert len(result["iterations"]) == 2  # max_iterations
        assert all(not iteration["success"] for iteration in result["iterations"])
        assert len(result["errors"]) > 0
        assert "Failed to generate working playbook after 2 iterations" in result["errors"]
    
    @patch('src.agent.playbook_agent.config_manager')
    @patch('src.agent.playbook_agent.DeviceManager')
    @patch('src.agent.playbook_agent.LLMClient')
    @patch('src.agent.playbook_agent.MCPClient')
    @patch('src.agent.playbook_agent.PlaybookValidator')
    async def test_generate_and_test_playbook_validation_failure(
        self, mock_validator, mock_mcp_client, mock_llm_client, mock_device_manager, mock_config_manager,
        sample_device_config, sample_playbook
    ):
        mock_config_manager.get_agent_config.return_value = {
            'max_iterations': 3,
            'timeout_seconds': 300,
            'log_level': 'INFO'
        }
        
        # Mock device manager
        mock_dm_instance = Mock()
        mock_device_manager.return_value = mock_dm_instance
        mock_dm_instance.connect.return_value = True
        mock_dm_instance.capture_configuration.return_value = sample_device_config
        mock_dm_instance.disconnect.return_value = None
        
        # Mock validator - always fail
        mock_validator_instance = Mock()
        mock_validator.return_value = mock_validator_instance
        mock_validator_instance.validate_all.return_value = (False, ["YAML syntax error"])
        mock_validator_instance.cleanup.return_value = None
        
        # Mock LLM client
        mock_llm_instance = Mock()
        mock_llm_client.return_value = mock_llm_instance
        mock_llm_instance.generate_playbook.return_value = sample_playbook
        
        # Mock MCP client
        mock_mcp_instance = AsyncMock()
        mock_mcp_client.return_value = mock_mcp_instance
        
        agent = PlaybookAgent()
        
        result = await agent.generate_and_test_playbook(
            device_id="test-device",
            device_host="192.168.1.1",
            device_user="admin",
            intentions="Configure OSPF"
        )
        
        assert result["success"] is False
        assert len(result["iterations"]) == 3  # All iterations should fail validation
        
        for iteration in result["iterations"]:
            assert not iteration["success"]
            assert "YAML syntax error" in iteration["validation_errors"]
        
        # MCP should not be called if validation fails
        mock_mcp_instance.store_playbook.assert_not_called()
        mock_mcp_instance.run_playbook.assert_not_called()
    
    @patch('src.agent.playbook_agent.config_manager')
    @patch('src.agent.playbook_agent.DeviceManager')
    async def test_generate_and_test_playbook_connection_failure(
        self, mock_device_manager, mock_config_manager
    ):
        mock_config_manager.get_agent_config.return_value = {
            'max_iterations': 3,
            'timeout_seconds': 300,
            'log_level': 'INFO'
        }
        
        # Mock device manager connection failure
        mock_dm_instance = Mock()
        mock_device_manager.return_value = mock_dm_instance
        mock_dm_instance.connect.return_value = False
        mock_dm_instance.disconnect.return_value = None
        
        agent = PlaybookAgent()
        
        result = await agent.generate_and_test_playbook(
            device_id="test-device",
            device_host="192.168.1.1",
            device_user="admin",
            intentions="Configure OSPF"
        )
        
        assert result["success"] is False
        assert len(result["errors"]) > 0
        assert "Failed to connect to device test-device" in result["errors"][0]
        assert len(result["iterations"]) == 0  # No iterations should be attempted
    
    @patch('src.agent.playbook_agent.config_manager')
    @patch('src.agent.playbook_agent.DeviceManager')
    @patch('src.agent.playbook_agent.LLMClient')
    @patch('src.agent.playbook_agent.MCPClient')
    @patch('src.agent.playbook_agent.PlaybookValidator')
    async def test_generate_and_test_playbook_critical_error(
        self, mock_validator, mock_mcp_client, mock_llm_client, mock_device_manager, mock_config_manager
    ):
        mock_config_manager.get_agent_config.return_value = {
            'max_iterations': 3,
            'timeout_seconds': 300,
            'log_level': 'INFO'
        }
        
        # Mock device manager to raise exception
        mock_dm_instance = Mock()
        mock_device_manager.return_value = mock_dm_instance
        mock_dm_instance.connect.side_effect = Exception("Critical system error")
        mock_dm_instance.disconnect.return_value = None
        
        # Mock validator cleanup
        mock_validator_instance = Mock()
        mock_validator.return_value = mock_validator_instance
        mock_validator_instance.cleanup.return_value = None
        
        agent = PlaybookAgent()
        
        result = await agent.generate_and_test_playbook(
            device_id="test-device",
            device_host="192.168.1.1",
            device_user="admin",
            intentions="Configure OSPF"
        )
        
        assert result["success"] is False
        assert len(result["errors"]) > 0
        assert "Critical system error" in result["errors"][0]
        
        # Cleanup should still be called
        mock_validator_instance.cleanup.assert_called_once()
        mock_dm_instance.disconnect.assert_called_once()
    
    @patch('src.agent.playbook_agent.config_manager')
    @patch('src.agent.playbook_agent.MCPClient')
    async def test_health_check_success(self, mock_mcp_client, mock_config_manager):
        mock_config_manager.get_agent_config.return_value = {
            'max_iterations': 3,
            'timeout_seconds': 300,
            'log_level': 'INFO'
        }
        
        # Mock MCP client health check
        mock_mcp_instance = AsyncMock()
        mock_mcp_client.return_value = mock_mcp_instance
        mock_mcp_instance.health_check.return_value = True
        
        agent = PlaybookAgent()
        
        result = await agent.health_check()
        
        assert result["agent"] is True
        assert result["mcp_server"] is True
        assert "timestamp" in result
        
        mock_mcp_instance.health_check.assert_called_once()
    
    @patch('src.agent.playbook_agent.config_manager')
    @patch('src.agent.playbook_agent.MCPClient')
    async def test_health_check_mcp_failure(self, mock_mcp_client, mock_config_manager):
        mock_config_manager.get_agent_config.return_value = {
            'max_iterations': 3,
            'timeout_seconds': 300,
            'log_level': 'INFO'
        }
        
        # Mock MCP client health check failure
        mock_mcp_instance = AsyncMock()
        mock_mcp_client.return_value = mock_mcp_instance
        mock_mcp_instance.health_check.side_effect = Exception("MCP server down")
        
        agent = PlaybookAgent()
        
        result = await agent.health_check()
        
        assert result["agent"] is True
        assert result["mcp_server"] is False
        assert "timestamp" in result
    
    @patch('src.agent.playbook_agent.config_manager')
    @patch('src.agent.playbook_agent.DeviceManager')
    @patch('src.agent.playbook_agent.LLMClient')
    @patch('src.agent.playbook_agent.MCPClient')
    @patch('src.agent.playbook_agent.PlaybookValidator')
    async def test_execute_iteration_restore_configuration_failure(
        self, mock_validator, mock_mcp_client, mock_llm_client, mock_device_manager, mock_config_manager,
        sample_device_config, sample_playbook
    ):
        mock_config_manager.get_agent_config.return_value = {
            'max_iterations': 3,
            'timeout_seconds': 300,
            'log_level': 'INFO'
        }
        
        # Mock device manager with restore failure
        mock_dm_instance = Mock()
        mock_device_manager.return_value = mock_dm_instance
        mock_dm_instance.connect.return_value = True
        mock_dm_instance.capture_configuration.return_value = sample_device_config
        mock_dm_instance.restore_configuration.return_value = False  # Fail restore
        mock_dm_instance.disconnect.return_value = None
        
        # Mock validator
        mock_validator_instance = Mock()
        mock_validator.return_value = mock_validator_instance
        mock_validator_instance.validate_all.return_value = (True, [])
        mock_validator_instance.cleanup.return_value = None
        
        # Mock LLM client
        mock_llm_instance = Mock()
        mock_llm_client.return_value = mock_llm_instance
        mock_llm_instance.generate_playbook.return_value = sample_playbook
        
        # Mock MCP client - fail execution
        mock_mcp_instance = AsyncMock()
        mock_mcp_client.return_value = mock_mcp_instance
        mock_mcp_instance.store_playbook.return_value = {"success": True}
        mock_mcp_instance.run_playbook.return_value = {"success": False, "data": {"errors": ["Execution failed"]}}
        
        agent = PlaybookAgent()
        
        result = await agent.generate_and_test_playbook(
            device_id="test-device",
            device_host="192.168.1.1",
            device_user="admin",
            intentions="Configure OSPF"
        )
        
        assert result["success"] is False
        iteration = result["iterations"][0]
        assert not iteration["success"]
        assert "Failed to restore device configuration" in iteration["errors"]