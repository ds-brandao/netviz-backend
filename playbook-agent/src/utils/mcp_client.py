import aiohttp
import asyncio
import json
from typing import Dict, Any, Optional
import logging
from config.ingestion_config import config_manager

logger = logging.getLogger(__name__)

class MCPClient:
    def __init__(self):
        self.config = config_manager.get_mcp_server_config()
        self.base_url = self.config['url'].rstrip('/')
        self.timeout = self.config['timeout']

    async def store_playbook(self, playbook_name: str, playbook_content: str, 
                           iteration: int = 1) -> Dict[str, Any]:
        
        versioned_name = f"{playbook_name}_v{iteration}.yml"
        
        payload = {
            "playbook_name": versioned_name,
            "playbook_content": playbook_content,
            "iteration": iteration,
            "timestamp": self._get_timestamp()
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/store-playbook",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    
                    logger.info(f"Successfully stored playbook {versioned_name} in GitHub")
                    return result
                    
        except Exception as e:
            logger.error(f"Failed to store playbook {versioned_name}: {str(e)}")
            raise

    async def run_playbook(self, playbook_name: str, device_id: str, 
                          device_host: str, device_user: str,
                          device_password: Optional[str] = None,
                          private_key_path: Optional[str] = None) -> Dict[str, Any]:
        
        payload = {
            "playbook_name": playbook_name,
            "device_id": device_id,
            "device_host": device_host,
            "device_user": device_user,
        }
        
        if device_password:
            payload["device_password"] = device_password
        if private_key_path:
            payload["private_key_path"] = private_key_path
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/run-playbook",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    
                    logger.info(f"Playbook {playbook_name} execution completed on device {device_id}")
                    return result
                    
        except Exception as e:
            logger.error(f"Failed to run playbook {playbook_name} on device {device_id}: {str(e)}")
            raise

    async def get_playbook_history(self, playbook_base_name: str) -> Dict[str, Any]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/playbook-history/{playbook_base_name}",
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    
                    logger.info(f"Retrieved history for playbook {playbook_base_name}")
                    return result
                    
        except Exception as e:
            logger.error(f"Failed to get playbook history for {playbook_base_name}: {str(e)}")
            raise

    async def health_check(self) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/health",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info("MCP server health check passed")
                        return True
                    else:
                        logger.error(f"MCP server health check failed with status {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"MCP server health check failed: {str(e)}")
            return False

    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"