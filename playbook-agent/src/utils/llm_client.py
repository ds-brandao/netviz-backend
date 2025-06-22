import os
from typing import Dict, Any, Optional, List
import logging
from llama_api_client import LlamaAPIClient
from config.ingestion_config import config_manager

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, api_key: Optional[str] = None):
        self.config = config_manager.get_llm_config()
        self.api_key = api_key or self.config['api_key']
        
        if not self.api_key:
            raise ValueError("LLAMA_API_KEY is required in configuration")
        
        self.client = LlamaAPIClient(api_key=self.api_key)

    def generate_playbook(self, device_id: str, intentions: str, 
                         device_config: Optional[Dict[str, Any]] = None,
                         previous_errors: Optional[List[str]] = None,
                         iteration: int = 1) -> str:
        
        system_prompt = """You are an expert Ansible playbook generator. Create well-structured, 
        production-ready Ansible playbooks for network device configuration. Always include:
        - Proper YAML formatting
        - Error handling with rescue blocks
        - Idempotent tasks
        - Descriptive task names
        - Appropriate modules for network devices
        - Validation steps"""

        user_prompt = f"""
        Device ID: {device_id}
        Intentions: {intentions}
        Iteration: {iteration}
        
        """

        if device_config:
            user_prompt += f"\nCurrent Device Configuration:\n{self._format_device_config(device_config)}\n"

        if previous_errors:
            user_prompt += f"\nPrevious Execution Errors (fix these):\n"
            for i, error in enumerate(previous_errors, 1):
                user_prompt += f"{i}. {error}\n"

        user_prompt += """
        Generate an Ansible playbook that:
        1. Accomplishes the stated intentions
        2. Is idempotent and safe to run multiple times
        3. Includes proper error handling
        4. Uses appropriate network modules
        5. Validates changes after applying them
        
        Return only the YAML playbook content, no explanations.
        """

        try:
            response = self.client.run({
                "model": self.config['model'],
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": self.config['temperature'],
                "max_tokens": self.config['max_tokens']
            })
            
            playbook_content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            if not playbook_content:
                raise ValueError("Empty response from LLM")
            
            logger.info(f"Generated playbook for device {device_id}, iteration {iteration}")
            return playbook_content.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate playbook: {str(e)}")
            raise

    def improve_playbook(self, original_playbook: str, errors: List[str], 
                        device_config: Dict[str, Any]) -> str:
        
        system_prompt = """You are an expert Ansible playbook debugger. Analyze the provided 
        playbook and errors, then generate an improved version that fixes the issues."""

        user_prompt = f"""
        Original Playbook:
        ```yaml
        {original_playbook}
        ```
        
        Execution Errors:
        {chr(10).join(f"- {error}" for error in errors)}
        
        Device Configuration Context:
        {self._format_device_config(device_config)}
        
        Generate an improved playbook that fixes these errors while maintaining the original intent.
        Return only the YAML playbook content.
        """

        try:
            response = self.client.run({
                "model": self.config['model'],
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": self.config['temperature'],
                "max_tokens": self.config['max_tokens']
            })
            
            improved_playbook = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            if not improved_playbook:
                raise ValueError("Empty response from LLM")
            
            logger.info("Generated improved playbook")
            return improved_playbook.strip()
            
        except Exception as e:
            logger.error(f"Failed to improve playbook: {str(e)}")
            raise

    def _format_device_config(self, config: Dict[str, Any]) -> str:
        formatted = []
        for key, value in config.items():
            if isinstance(value, str) and not value.startswith("Error:"):
                formatted.append(f"{key}:\n{value[:500]}{'...' if len(value) > 500 else ''}")
        return "\n\n".join(formatted)