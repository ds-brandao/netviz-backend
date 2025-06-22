import base64
import json
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import aiohttp
import asyncio

from config.ingestion_config import config_manager

logger = logging.getLogger(__name__)

class GitHubClient:
    def __init__(self):
        self.config = config_manager.get_github_config()
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {self.config['token']}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        
        if not self.config['token']:
            raise ValueError("GitHub token is required")

    async def store_playbook(self, name: str, content: str, iteration: int = 1, 
                           timestamp: Optional[str] = None) -> Dict[str, Any]:
        
        if not timestamp:
            timestamp = datetime.utcnow().isoformat()
        
        file_path = f"playbooks/{name}"
        
        commit_message = self.config['commit_message_template'].format(
            device_id=name.split('_')[0] if '_' in name else name,
            iteration=iteration
        )
        
        encoded_content = base64.b64encode(content.encode()).decode()
        
        payload = {
            "message": commit_message,
            "content": encoded_content,
            "branch": self.config['branch']
        }
        
        try:
            existing_file = await self._get_file(file_path)
            if existing_file:
                payload["sha"] = existing_file["sha"]
        except Exception:
            pass
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            url = f"{self.base_url}/repos/{self.config['username']}/{self.config['repository']}/contents/{file_path}"
            
            async with session.put(url, json=payload) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    logger.info(f"Successfully stored playbook {name} in GitHub")
                    return {
                        "sha": result["content"]["sha"],
                        "url": result["content"]["html_url"],
                        "commit_sha": result["commit"]["sha"]
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"GitHub API error {response.status}: {error_text}")

    async def get_playbook(self, name: str) -> str:
        file_path = f"playbooks/{name}"
        
        try:
            file_info = await self._get_file(file_path)
            if not file_info:
                raise Exception(f"Playbook {name} not found")
            
            content = base64.b64decode(file_info["content"]).decode()
            logger.info(f"Retrieved playbook {name} from GitHub")
            return content
            
        except Exception as e:
            logger.error(f"Failed to get playbook {name}: {str(e)}")
            raise

    async def get_playbook_history(self, playbook_base_name: str) -> Dict[str, Any]:
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                url = f"{self.base_url}/repos/{self.config['username']}/{self.config['repository']}/contents/playbooks"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        files = await response.json()
                        
                        matching_files = [
                            f for f in files 
                            if f["name"].startswith(playbook_base_name) and f["name"].endswith(".yml")
                        ]
                        
                        history = []
                        for file_info in matching_files:
                            commits = await self._get_file_commits(file_info["path"])
                            history.append({
                                "name": file_info["name"],
                                "path": file_info["path"],
                                "size": file_info["size"],
                                "url": file_info["html_url"],
                                "last_modified": commits[0]["commit"]["author"]["date"] if commits else None,
                                "commits_count": len(commits)
                            })
                        
                        return {
                            "base_name": playbook_base_name,
                            "files": history,
                            "total_versions": len(history)
                        }
                    else:
                        error_text = await response.text()
                        raise Exception(f"GitHub API error {response.status}: {error_text}")
                        
        except Exception as e:
            logger.error(f"Failed to get playbook history for {playbook_base_name}: {str(e)}")
            raise

    async def _get_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        async with aiohttp.ClientSession(headers=self.headers) as session:
            url = f"{self.base_url}/repos/{self.config['username']}/{self.config['repository']}/contents/{file_path}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    return None
                else:
                    error_text = await response.text()
                    raise Exception(f"GitHub API error {response.status}: {error_text}")

    async def _get_file_commits(self, file_path: str) -> List[Dict[str, Any]]:
        async with aiohttp.ClientSession(headers=self.headers) as session:
            url = f"{self.base_url}/repos/{self.config['username']}/{self.config['repository']}/commits"
            params = {"path": file_path}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return []

    async def health_check(self) -> bool:
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                url = f"{self.base_url}/repos/{self.config['username']}/{self.config['repository']}"
                
                async with session.get(url) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"GitHub health check failed: {str(e)}")
            return False