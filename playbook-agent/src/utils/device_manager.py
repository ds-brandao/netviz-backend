import paramiko
import json
import yaml
from typing import Dict, Any, Optional
import logging
from config.ingestion_config import config_manager

logger = logging.getLogger(__name__)

class DeviceManager:
    def __init__(self, device_id: str, host: str, username: str, password: Optional[str] = None, 
                 private_key_path: Optional[str] = None):
        self.device_id = device_id
        self.host = host
        self.username = username
        self.password = password
        self.private_key_path = private_key_path
        self.client = None
        self.original_config = None
        
        self.config = config_manager.get_device_config()

    def connect(self) -> bool:
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if self.private_key_path:
                private_key = paramiko.RSAKey.from_private_key_file(self.private_key_path)
                self.client.connect(
                    hostname=self.host,
                    username=self.username,
                    pkey=private_key,
                    timeout=self.config['connection_timeout']
                )
            else:
                self.client.connect(
                    hostname=self.host,
                    username=self.username,
                    password=self.password,
                    timeout=self.config['connection_timeout']
                )
            
            logger.info(f"Successfully connected to device {self.device_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to device {self.device_id}: {str(e)}")
            return False

    def capture_configuration(self) -> Dict[str, Any]:
        if not self.client:
            raise RuntimeError("Not connected to device")
        
        config_commands = [
            "show running-config",
            "show interfaces", 
            "show ip route",
            "show version",
            "show inventory"
        ]
        
        captured_config = {}
        
        for command in config_commands:
            try:
                stdin, stdout, stderr = self.client.exec_command(
                    command, 
                    timeout=self.config['command_timeout']
                )
                output = stdout.read().decode('utf-8')
                error = stderr.read().decode('utf-8')
                
                if error:
                    logger.warning(f"Warning executing {command}: {error}")
                
                captured_config[command.replace(" ", "_")] = output
            except Exception as e:
                logger.error(f"Failed to execute {command}: {str(e)}")
                captured_config[command.replace(" ", "_")] = f"Error: {str(e)}"
        
        if self.config['config_backup_enabled']:
            self.original_config = captured_config
            logger.info(f"Configuration captured for device {self.device_id}")
        
        return captured_config

    def restore_configuration(self) -> bool:
        if not self.client:
            raise RuntimeError("Not connected to device")
        
        if not self.original_config:
            logger.warning("No original configuration to restore")
            return False
        
        try:
            running_config = self.original_config.get("show_running-config", "")
            if running_config and not running_config.startswith("Error:"):
                stdin, stdout, stderr = self.client.exec_command(
                    "configure terminal",
                    timeout=self.config['command_timeout']
                )
                stdin.write("no startup-config\n")
                stdin.write("copy running-config startup-config\n")
                stdin.flush()
                
                config_lines = running_config.split('\n')
                for line in config_lines:
                    if line.strip() and not line.startswith('!'):
                        stdin.write(f"{line}\n")
                
                stdin.write("end\n")
                stdin.write("copy running-config startup-config\n")
                stdin.flush()
                
                logger.info(f"Configuration restored for device {self.device_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to restore configuration for device {self.device_id}: {str(e)}")
            return False
        
        return False

    def disconnect(self):
        if self.client:
            self.client.close()
            logger.info(f"Disconnected from device {self.device_id}")