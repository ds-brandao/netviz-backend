import pytest
import os
import tempfile
from unittest.mock import patch, Mock
from pathlib import Path

from config.ingestion_config import ConfigManager

class TestConfigManager:
    
    def test_init_with_custom_config_dir(self, temp_config_dir):
        config_manager = ConfigManager(str(temp_config_dir))
        assert config_manager.config_dir == temp_config_dir
    
    def test_init_with_default_config_dir(self):
        config_manager = ConfigManager()
        expected_path = Path(__file__).parent.parent / "config"
        assert config_manager.config_dir.name == "config"
    
    def test_load_agent_config(self, temp_config_dir):
        config_manager = ConfigManager(str(temp_config_dir))
        agent_config = config_manager.agent_config
        
        assert agent_config["agent"]["max_iterations"] == 3
        assert agent_config["llm"]["model"] == "llama-3.1-405b"
        assert agent_config["device"]["connection_timeout"] == 15
    
    def test_load_secrets_config(self, temp_config_dir):
        config_manager = ConfigManager(str(temp_config_dir))
        secrets_config = config_manager.secrets_config
        
        assert secrets_config["llm"]["api_key"] == "test-llama-key"
        assert secrets_config["github"]["token"] == "test-github-token"
    
    def test_get_with_env_variable_priority(self, temp_config_dir):
        with patch.dict(os.environ, {"LLM_API_KEY": "env-api-key"}):
            config_manager = ConfigManager(str(temp_config_dir))
            value = config_manager.get("llm.api_key")
            assert value == "env-api-key"
    
    def test_get_from_secrets_config(self, temp_config_dir):
        config_manager = ConfigManager(str(temp_config_dir))
        value = config_manager.get("github.token")
        assert value == "test-github-token"
    
    def test_get_from_agent_config(self, temp_config_dir):
        config_manager = ConfigManager(str(temp_config_dir))
        value = config_manager.get("agent.max_iterations")
        assert value == 3
    
    def test_get_with_default_value(self, temp_config_dir):
        config_manager = ConfigManager(str(temp_config_dir))
        value = config_manager.get("nonexistent.key", "default_value")
        assert value == "default_value"
    
    def test_get_llm_config(self, temp_config_dir):
        config_manager = ConfigManager(str(temp_config_dir))
        llm_config = config_manager.get_llm_config()
        
        expected = {
            'api_key': 'test-llama-key',
            'model': 'llama-3.1-405b',
            'temperature': 0.1,
            'max_tokens': 2000,
            'timeout': 60
        }
        assert llm_config == expected
    
    def test_get_agent_config(self, temp_config_dir):
        config_manager = ConfigManager(str(temp_config_dir))
        agent_config = config_manager.get_agent_config()
        
        expected = {
            'max_iterations': 3,
            'timeout_seconds': 120,
            'log_level': 'INFO'
        }
        assert agent_config == expected
    
    def test_get_device_config(self, temp_config_dir):
        config_manager = ConfigManager(str(temp_config_dir))
        device_config = config_manager.get_device_config()
        
        expected = {
            'connection_timeout': 15,
            'command_timeout': 30,
            'config_backup_enabled': True
        }
        assert device_config == expected
    
    def test_get_github_config(self, temp_config_dir):
        config_manager = ConfigManager(str(temp_config_dir))
        github_config = config_manager.get_github_config()
        
        expected = {
            'token': 'test-github-token',
            'username': 'test-user',
            'repository': 'test-playbooks',
            'branch': 'main',
            'commit_message_template': 'Generated playbook for {device_id} - iteration {iteration}'
        }
        assert github_config == expected
    
    def test_get_mcp_server_config(self, temp_config_dir):
        config_manager = ConfigManager(str(temp_config_dir))
        mcp_config = config_manager.get_mcp_server_config()
        
        expected = {
            'url': 'http://localhost:8080',
            'host': 'localhost',
            'port': 8080,
            'timeout': 120
        }
        assert mcp_config == expected
    
    def test_get_api_config(self, temp_config_dir):
        config_manager = ConfigManager(str(temp_config_dir))
        api_config = config_manager.get_api_config()
        
        expected = {
            'host': 'localhost',
            'port': 8000,
            'reload': False,
            'workers': 1
        }
        assert api_config == expected
    
    def test_get_playbook_config(self, temp_config_dir):
        config_manager = ConfigManager(str(temp_config_dir))
        playbook_config = config_manager.get_playbook_config()
        
        expected = {
            'validation_enabled': True,
            'lint_enabled': True,
            'temp_dir': '/tmp/playbook-agent'
        }
        assert playbook_config == expected
    
    def test_missing_config_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "empty_config"
            config_dir.mkdir()
            
            config_manager = ConfigManager(str(config_dir))
            
            assert config_manager.agent_config == {}
            assert config_manager.secrets_config == {}
            assert config_manager.get("any.key", "default") == "default"
    
    @patch.dict(os.environ, {
        "AGENT_MAX_ITERATIONS": "10",
        "LLM_MODEL": "custom-model",
        "GITHUB_REPOSITORY": "custom-repo"
    })
    def test_environment_variable_overrides(self, temp_config_dir):
        config_manager = ConfigManager(str(temp_config_dir))
        
        assert config_manager.get("agent.max_iterations") == "10"
        assert config_manager.get("llm.model") == "custom-model"
        assert config_manager.get("github.repository") == "custom-repo"