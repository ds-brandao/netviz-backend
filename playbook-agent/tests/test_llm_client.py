import pytest
from unittest.mock import Mock, patch, MagicMock

from src.utils.llm_client import LLMClient

class TestLLMClient:
    
    @patch('src.utils.llm_client.config_manager')
    @patch('src.utils.llm_client.LlamaAPI')
    def test_init_with_api_key(self, mock_llama_api, mock_config_manager):
        mock_config_manager.get_llm_config.return_value = {
            'api_key': 'config-key',
            'model': 'llama-3.1-405b',
            'temperature': 0.1,
            'max_tokens': 4000,
            'timeout': 60
        }
        
        client = LLMClient(api_key="test-key")
        
        assert client.api_key == "test-key"
        mock_llama_api.assert_called_once_with(api_key="test-key")
    
    @patch('src.utils.llm_client.config_manager')
    @patch('src.utils.llm_client.LlamaAPI')
    def test_init_with_config_api_key(self, mock_llama_api, mock_config_manager):
        mock_config_manager.get_llm_config.return_value = {
            'api_key': 'config-key',
            'model': 'llama-3.1-405b',
            'temperature': 0.1,
            'max_tokens': 4000,
            'timeout': 60
        }
        
        client = LLMClient()
        
        assert client.api_key == "config-key"
        mock_llama_api.assert_called_once_with(api_key="config-key")
    
    @patch('src.utils.llm_client.config_manager')
    def test_init_no_api_key_raises_error(self, mock_config_manager):
        mock_config_manager.get_llm_config.return_value = {
            'api_key': None,
            'model': 'llama-3.1-405b',
            'temperature': 0.1,
            'max_tokens': 4000,
            'timeout': 60
        }
        
        with pytest.raises(ValueError, match="LLAMA_API_KEY is required"):
            LLMClient()
    
    @patch('src.utils.llm_client.config_manager')
    @patch('src.utils.llm_client.LlamaAPI')
    def test_generate_playbook_success(self, mock_llama_api, mock_config_manager, mock_llm_response, sample_device_config):
        mock_config_manager.get_llm_config.return_value = {
            'api_key': 'test-key',
            'model': 'llama-3.1-405b',
            'temperature': 0.1,
            'max_tokens': 4000,
            'timeout': 60
        }
        
        mock_client = Mock()
        mock_llama_api.return_value = mock_client
        mock_client.run.return_value = mock_llm_response
        
        client = LLMClient()
        
        result = client.generate_playbook(
            device_id="test-device",
            intentions="Configure OSPF",
            device_config=sample_device_config,
            previous_errors=["Previous error"],
            iteration=2
        )
        
        assert "Test playbook" in result
        assert "Test task" in result
        
        mock_client.run.assert_called_once()
        call_args = mock_client.run.call_args[0][0]
        
        assert call_args["model"] == "llama-3.1-405b"
        assert call_args["temperature"] == 0.1
        assert call_args["max_tokens"] == 4000
        assert len(call_args["messages"]) == 2
        assert call_args["messages"][0]["role"] == "system"
        assert call_args["messages"][1]["role"] == "user"
        
        user_message = call_args["messages"][1]["content"]
        assert "test-device" in user_message
        assert "Configure OSPF" in user_message
        assert "Iteration: 2" in user_message
        assert "Previous error" in user_message
    
    @patch('src.utils.llm_client.config_manager')
    @patch('src.utils.llm_client.LlamaAPI')
    def test_generate_playbook_minimal_params(self, mock_llama_api, mock_config_manager, mock_llm_response):
        mock_config_manager.get_llm_config.return_value = {
            'api_key': 'test-key',
            'model': 'llama-3.1-405b',
            'temperature': 0.1,
            'max_tokens': 4000,
            'timeout': 60
        }
        
        mock_client = Mock()
        mock_llama_api.return_value = mock_client
        mock_client.run.return_value = mock_llm_response
        
        client = LLMClient()
        
        result = client.generate_playbook(
            device_id="test-device",
            intentions="Configure OSPF"
        )
        
        assert "Test playbook" in result
        
        call_args = mock_client.run.call_args[0][0]
        user_message = call_args["messages"][1]["content"]
        assert "test-device" in user_message
        assert "Configure OSPF" in user_message
        assert "Iteration: 1" in user_message
    
    @patch('src.utils.llm_client.config_manager')
    @patch('src.utils.llm_client.LlamaAPI')
    def test_generate_playbook_empty_response(self, mock_llama_api, mock_config_manager):
        mock_config_manager.get_llm_config.return_value = {
            'api_key': 'test-key',
            'model': 'llama-3.1-405b',
            'temperature': 0.1,
            'max_tokens': 4000,
            'timeout': 60
        }
        
        mock_client = Mock()
        mock_llama_api.return_value = mock_client
        mock_client.run.return_value = {"choices": [{"message": {"content": ""}}]}
        
        client = LLMClient()
        
        with pytest.raises(ValueError, match="Empty response from LLM"):
            client.generate_playbook(
                device_id="test-device",
                intentions="Configure OSPF"
            )
    
    @patch('src.utils.llm_client.config_manager')
    @patch('src.utils.llm_client.LlamaAPI')
    def test_generate_playbook_api_error(self, mock_llama_api, mock_config_manager):
        mock_config_manager.get_llm_config.return_value = {
            'api_key': 'test-key',
            'model': 'llama-3.1-405b',
            'temperature': 0.1,
            'max_tokens': 4000,
            'timeout': 60
        }
        
        mock_client = Mock()
        mock_llama_api.return_value = mock_client
        mock_client.run.side_effect = Exception("API Error")
        
        client = LLMClient()
        
        with pytest.raises(Exception, match="API Error"):
            client.generate_playbook(
                device_id="test-device",
                intentions="Configure OSPF"
            )
    
    @patch('src.utils.llm_client.config_manager')
    @patch('src.utils.llm_client.LlamaAPI')
    def test_improve_playbook_success(self, mock_llama_api, mock_config_manager, sample_device_config):
        mock_config_manager.get_llm_config.return_value = {
            'api_key': 'test-key',
            'model': 'llama-3.1-405b',
            'temperature': 0.1,
            'max_tokens': 4000,
            'timeout': 60
        }
        
        mock_client = Mock()
        mock_llama_api.return_value = mock_client
        
        improved_response = {
            "choices": [{
                "message": {
                    "content": "---\n- name: Improved playbook\n  hosts: all\n  tasks:\n    - name: Fixed task"
                }
            }]
        }
        mock_client.run.return_value = improved_response
        
        client = LLMClient()
        
        original_playbook = "---\n- name: Original playbook"
        errors = ["Error 1", "Error 2"]
        
        result = client.improve_playbook(
            original_playbook=original_playbook,
            errors=errors,
            device_config=sample_device_config
        )
        
        assert "Improved playbook" in result
        assert "Fixed task" in result
        
        mock_client.run.assert_called_once()
        call_args = mock_client.run.call_args[0][0]
        
        assert call_args["model"] == "llama-3.1-405b"
        assert len(call_args["messages"]) == 2
        assert call_args["messages"][0]["role"] == "system"
        assert call_args["messages"][1]["role"] == "user"
        
        user_message = call_args["messages"][1]["content"]
        assert "Original playbook" in user_message
        assert "Error 1" in user_message
        assert "Error 2" in user_message
    
    @patch('src.utils.llm_client.config_manager')
    @patch('src.utils.llm_client.LlamaAPI')
    def test_improve_playbook_empty_response(self, mock_llama_api, mock_config_manager, sample_device_config):
        mock_config_manager.get_llm_config.return_value = {
            'api_key': 'test-key',
            'model': 'llama-3.1-405b',
            'temperature': 0.1,
            'max_tokens': 4000,
            'timeout': 60
        }
        
        mock_client = Mock()
        mock_llama_api.return_value = mock_client
        mock_client.run.return_value = {"choices": [{"message": {"content": ""}}]}
        
        client = LLMClient()
        
        with pytest.raises(ValueError, match="Empty response from LLM"):
            client.improve_playbook(
                original_playbook="original",
                errors=["error"],
                device_config=sample_device_config
            )
    
    @patch('src.utils.llm_client.config_manager')
    @patch('src.utils.llm_client.LlamaAPI')
    def test_format_device_config(self, mock_llama_api, mock_config_manager, sample_device_config):
        mock_config_manager.get_llm_config.return_value = {
            'api_key': 'test-key',
            'model': 'llama-3.1-405b',
            'temperature': 0.1,
            'max_tokens': 4000,
            'timeout': 60
        }
        
        client = LLMClient()
        
        formatted = client._format_device_config(sample_device_config)
        
        assert "show_running-config:" in formatted
        assert "show_interfaces:" in formatted
        assert "version 15.1" in formatted
        assert "GigabitEthernet0/0 is up" in formatted
    
    @patch('src.utils.llm_client.config_manager')
    @patch('src.utils.llm_client.LlamaAPI')
    def test_format_device_config_with_errors(self, mock_llama_api, mock_config_manager):
        mock_config_manager.get_llm_config.return_value = {
            'api_key': 'test-key',
            'model': 'llama-3.1-405b',
            'temperature': 0.1,
            'max_tokens': 4000,
            'timeout': 60
        }
        
        client = LLMClient()
        
        config_with_errors = {
            "good_command": "Valid output",
            "bad_command": "Error: Command failed",
            "another_good": "More valid output"
        }
        
        formatted = client._format_device_config(config_with_errors)
        
        assert "good_command:" in formatted
        assert "another_good:" in formatted
        assert "bad_command:" not in formatted  # Error entries should be excluded
        assert "Error: Command failed" not in formatted
    
    @patch('src.utils.llm_client.config_manager')
    @patch('src.utils.llm_client.LlamaAPI')
    def test_format_device_config_truncation(self, mock_llama_api, mock_config_manager):
        mock_config_manager.get_llm_config.return_value = {
            'api_key': 'test-key',
            'model': 'llama-3.1-405b',
            'temperature': 0.1,
            'max_tokens': 4000,
            'timeout': 60
        }
        
        client = LLMClient()
        
        long_output = "x" * 1000  # Long output that should be truncated
        config_with_long_output = {
            "long_command": long_output
        }
        
        formatted = client._format_device_config(config_with_long_output)
        
        assert "long_command:" in formatted
        assert "..." in formatted  # Should contain truncation indicator
        assert len(formatted) < len(long_output)  # Should be shorter than original