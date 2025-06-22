import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

class ConfigManager:
    def __init__(self, config_dir: Optional[str] = None):
        if config_dir is None:
            config_dir = Path(__file__).parent
        
        self.config_dir = Path(config_dir)
        load_dotenv()
        
        self._agent_config = None
        self._secrets_config = None
        
    def _load_yaml_file(self, filename: str) -> Dict[str, Any]:
        file_path = self.config_dir / filename
        if not file_path.exists():
            return {}
        
        with open(file_path, 'r') as f:
            return yaml.safe_load(f) or {}
    
    @property
    def agent_config(self) -> Dict[str, Any]:
        if self._agent_config is None:
            self._agent_config = self._load_yaml_file("agent_config.yaml")
        return self._agent_config
    
    @property
    def secrets_config(self) -> Dict[str, Any]:
        if self._secrets_config is None:
            self._secrets_config = self._load_yaml_file("secrets.yaml")
        return self._secrets_config
    
    def get(self, key_path: str, default: Any = None) -> Any:
        keys = key_path.split('.')
        
        value = os.getenv(key_path.upper().replace('.', '_'))
        if value is not None:
            return value
        
        for config in [self.secrets_config, self.agent_config]:
            current = config
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    current = None
                    break
            
            if current is not None:
                return current
        
        return default
    
    def get_llm_config(self) -> Dict[str, Any]:
        return {
            'api_key': self.get('llm.api_key'),
            'model': self.get('llm.model'),
            'temperature': self.get('llm.temperature'),
            'max_tokens': self.get('llm.max_tokens'),
            'timeout': self.get('llm.api_timeout')
        }
    
    def get_agent_config(self) -> Dict[str, Any]:
        return {
            'max_iterations': int(self.get('agent.max_iterations')),
            'timeout_seconds': int(self.get('agent.timeout_seconds')),
            'log_level': self.get('agent.log_level')
        }
    
    def get_device_config(self) -> Dict[str, Any]:
        return {
            'connection_timeout': int(self.get('device.connection_timeout', 30)),
            'command_timeout': int(self.get('device.command_timeout', 60)),
            'config_backup_enabled': bool(self.get('device.config_backup_enabled', True))
        }
    
    def get_github_config(self) -> Dict[str, Any]:
        return {
            'token': self.get('github.token'),
            'username': self.get('github.username'),
            'repository': self.get('github.repository', 'playbooks'),
            'branch': self.get('github.branch', 'main'),
            'commit_message_template': self.get('github.commit_message_template', 
                                             'Generated playbook for {device_id} - iteration {iteration}')
        }
    
    def get_mcp_server_config(self) -> Dict[str, Any]:
        return {
            'url': self.get('mcp_server.url', 'http://localhost:8080'),
            'host': self.get('mcp_server.host', '0.0.0.0'),
            'port': int(self.get('mcp_server.port', 8080)),
            'timeout': int(self.get('mcp_server.timeout', 300))
        }
    
    def get_api_config(self) -> Dict[str, Any]:
        return {
            'host': self.get('api.host', '0.0.0.0'),
            'port': int(self.get('api.port', 8000)),
            'reload': bool(self.get('api.reload', True)),
            'workers': int(self.get('api.workers', 1))
        }
    
    def get_playbook_config(self) -> Dict[str, Any]:
        return {
            'validation_enabled': bool(self.get('playbook.validation_enabled', True)),
            'lint_enabled': bool(self.get('playbook.lint_enabled', True)),
            'temp_dir': self.get('playbook.temp_dir', '/tmp/playbook-agent')
        }
    
    def get_device_info(self, device_name: str) -> Dict[str, Any]:
        devices = self.agent_config.get('devices', {})
        if device_name not in devices:
            raise ValueError(f"Device '{device_name}' not found in configuration")
        return devices[device_name]
    
    def get_backend_url(self) -> str:
        return self.get('backend.url', 'http://localhost:8080')

config_manager = ConfigManager()