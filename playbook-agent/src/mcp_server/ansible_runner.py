import tempfile
import subprocess
import os
import yaml
import json
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from config.ingestion_config import config_manager

logger = logging.getLogger(__name__)

class AnsibleRunner:
    def __init__(self):
        self.config = config_manager.get_mcp_server_config()
        self.temp_dir = tempfile.mkdtemp()

    async def run_playbook(self, playbook_content: str, device_host: str, 
                          device_user: str, device_password: Optional[str] = None,
                          private_key_path: Optional[str] = None) -> Dict[str, Any]:
        
        result = {
            "success": False,
            "stdout": "",
            "stderr": "",
            "return_code": -1,
            "errors": [],
            "start_time": datetime.utcnow().isoformat(),
            "end_time": None
        }
        
        playbook_path = None
        inventory_path = None
        
        try:
            playbook_path = os.path.join(self.temp_dir, f"playbook_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yml")
            inventory_path = os.path.join(self.temp_dir, f"inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ini")
            
            with open(playbook_path, 'w') as f:
                f.write(playbook_content)
            
            inventory_content = self._create_inventory(device_host, device_user, device_password, private_key_path)
            with open(inventory_path, 'w') as f:
                f.write(inventory_content)
            
            cmd = [
                "ansible-playbook",
                "-i", inventory_path,
                playbook_path,
                "-v"
            ]
            
            if private_key_path:
                cmd.extend(["--private-key", private_key_path])
            
            if device_password:
                cmd.extend(["--ask-pass"])
                env = os.environ.copy()
                env["ANSIBLE_HOST_KEY_CHECKING"] = "False"
            else:
                env = os.environ.copy()
                env["ANSIBLE_HOST_KEY_CHECKING"] = "False"
            
            logger.info(f"Running ansible-playbook command: {' '.join(cmd)}")
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config['timeout'],
                env=env,
                cwd=self.temp_dir
            )
            
            result["return_code"] = process.returncode
            result["stdout"] = process.stdout
            result["stderr"] = process.stderr
            result["end_time"] = datetime.utcnow().isoformat()
            
            if process.returncode == 0:
                result["success"] = True
                logger.info("Ansible playbook executed successfully")
            else:
                result["errors"].append(f"Ansible playbook failed with return code {process.returncode}")
                result["errors"].append(f"STDERR: {process.stderr}")
                logger.error(f"Ansible playbook failed: {process.stderr}")
            
        except subprocess.TimeoutExpired:
            error_msg = f"Ansible playbook execution timed out after {self.config['timeout']} seconds"
            result["errors"].append(error_msg)
            result["end_time"] = datetime.utcnow().isoformat()
            logger.error(error_msg)
            
        except Exception as e:
            error_msg = f"Ansible playbook execution failed: {str(e)}"
            result["errors"].append(error_msg)
            result["end_time"] = datetime.utcnow().isoformat()
            logger.error(error_msg)
            
        finally:
            if playbook_path and os.path.exists(playbook_path):
                os.remove(playbook_path)
            if inventory_path and os.path.exists(inventory_path):
                os.remove(inventory_path)
        
        return result

    def _create_inventory(self, device_host: str, device_user: str, 
                         device_password: Optional[str] = None,
                         private_key_path: Optional[str] = None) -> str:
        
        inventory_lines = [
            "[network_devices]",
            f"{device_host} ansible_user={device_user}"
        ]
        
        if device_password:
            inventory_lines.append(f"ansible_password={device_password}")
        
        if private_key_path:
            inventory_lines.append(f"ansible_ssh_private_key_file={private_key_path}")
        
        inventory_lines.extend([
            "ansible_connection=network_cli",
            "ansible_network_os=ios",  # Default to Cisco IOS, can be made configurable
            "ansible_ssh_common_args='-o StrictHostKeyChecking=no'"
        ])
        
        return "\n".join(inventory_lines)

    def health_check(self) -> bool:
        try:
            result = subprocess.run(
                ["ansible", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logger.info("Ansible health check passed")
                return True
            else:
                logger.error(f"Ansible health check failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Ansible health check failed: {str(e)}")
            return False

    def cleanup(self):
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)