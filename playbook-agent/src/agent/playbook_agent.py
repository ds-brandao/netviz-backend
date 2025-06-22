import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from config.ingestion_config import config_manager
from src.utils.llm_client import LLMClient
from src.utils.playbook_validator import PlaybookValidator
from src.utils.mcp_client import MCPClient

logger = logging.getLogger(__name__)

class PlaybookAgent:
    def __init__(self):
        self.config = config_manager.get_agent_config()
        self.max_iterations = self.config.get('max_iterations', 3)
        
        self.llm_client = LLMClient()
        self.mcp_client = MCPClient()
        self.validator = PlaybookValidator()
        
        logging.basicConfig(level=getattr(logging, self.config.get('log_level', 'INFO')))

    async def generate_playbook(self, device_id: str, intentions: str) -> str:
        """Generate initial playbook based on device_id and intentions"""
        try:
            logger.info(f"Generating playbook for device {device_id}")
            
            playbook_content = self.llm_client.generate_playbook(
                device_id=device_id,
                intentions=intentions,
                device_config=None,
                previous_errors=[],
                iteration=1
            )
            
            is_valid, validation_errors = self.validator.validate_all(playbook_content)
            if not is_valid:
                logger.warning(f"Generated playbook has validation errors: {validation_errors}")
            
            return playbook_content
            
        except Exception as e:
            logger.error(f"Failed to generate playbook: {str(e)}")
            raise
    
    async def iterate_playbook(self, device_id: str, intentions: str, 
                             previous_playbook: str, iteration: int) -> str:
        """Iterate on existing playbook to fix issues"""
        try:
            logger.info(f"Iterating playbook for device {device_id}, iteration {iteration}")
            
            playbook_content = self.llm_client.generate_playbook(
                device_id=device_id,
                intentions=intentions,
                device_config=None,
                previous_errors=[f"Previous playbook failed: {previous_playbook}"],
                iteration=iteration
            )
            
            is_valid, validation_errors = self.validator.validate_all(playbook_content)
            if not is_valid:
                logger.warning(f"Iterated playbook has validation errors: {validation_errors}")
            
            return playbook_content
            
        except Exception as e:
            logger.error(f"Failed to iterate playbook: {str(e)}")
            raise
    
    async def generate_and_test_playbook(self, device_id: str, device_host: str, 
                                       device_user: str, intentions: str,
                                       device_password: Optional[str] = None,
                                       private_key_path: Optional[str] = None) -> Dict[str, Any]:
        
        logger.info(f"Starting playbook generation for device {device_id}")
        
        results = {
            "device_id": device_id,
            "intentions": intentions,
            "success": False,
            "iterations": [],
            "final_playbook": None,
            "errors": []
        }
        
        try:
            previous_errors = []
            
            for iteration in range(1, self.max_iterations + 1):
                logger.info(f"Starting iteration {iteration}/{self.max_iterations}")
                
                iteration_result = await self._execute_iteration(
                    device_id=device_id,
                    device_host=device_host,
                    device_user=device_user,
                    device_password=device_password,
                    private_key_path=private_key_path,
                    intentions=intentions,
                    previous_errors=previous_errors,
                    iteration=iteration
                )
                
                results["iterations"].append(iteration_result)
                
                if iteration_result["success"]:
                    results["success"] = True
                    results["final_playbook"] = iteration_result["playbook"]
                    logger.info(f"Playbook generation successful on iteration {iteration}")
                    break
                else:
                    previous_errors.extend(iteration_result["errors"])
                    logger.warning(f"Iteration {iteration} failed, continuing...")
            
            if not results["success"]:
                results["errors"].append(f"Failed to generate working playbook after {self.max_iterations} iterations")
                logger.error(f"All {self.max_iterations} iterations failed for device {device_id}")
            
        except Exception as e:
            error_msg = f"Critical error in playbook generation: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
        
        finally:
            self.validator.cleanup()
        
        return results

    async def _execute_iteration(self, device_id: str, device_host: str, device_user: str,
                               device_password: Optional[str], private_key_path: Optional[str],
                               intentions: str, previous_errors: List[str],
                               iteration: int) -> Dict[str, Any]:
        
        iteration_result = {
            "iteration": iteration,
            "timestamp": datetime.utcnow().isoformat(),
            "success": False,
            "playbook": None,
            "validation_errors": [],
            "execution_errors": [],
            "errors": []
        }
        
        try:
            playbook_content = self.llm_client.generate_playbook(
                device_id=device_id,
                intentions=intentions,
                device_config=None,
                previous_errors=previous_errors,
                iteration=iteration
            )
            
            iteration_result["playbook"] = playbook_content
            
            is_valid, validation_errors = self.validator.validate_all(playbook_content)
            iteration_result["validation_errors"] = validation_errors
            
            if not is_valid:
                iteration_result["errors"].extend(validation_errors)
                logger.warning(f"Iteration {iteration}: Playbook validation failed")
                return iteration_result
            
            playbook_name = f"{device_id}_{intentions.replace(' ', '_')[:20]}"
            
            try:
                await self.mcp_client.store_playbook(
                    playbook_name=playbook_name,
                    playbook_content=playbook_content,
                    iteration=iteration
                )
            except Exception as e:
                logger.warning(f"Failed to store playbook in GitHub: {str(e)}")
            
            execution_result = await self.mcp_client.run_playbook(
                playbook_name=f"{playbook_name}_v{iteration}.yml",
                device_id=device_id,
                device_host=device_host,
                device_user=device_user,
                device_password=device_password,
                private_key_path=private_key_path
            )
            
            if execution_result.get("success", False):
                iteration_result["success"] = True
                logger.info(f"Iteration {iteration}: Playbook executed successfully")
            else:
                execution_errors = execution_result.get("data", {}).get("errors", [])
                iteration_result["execution_errors"] = execution_errors
                iteration_result["errors"].extend(execution_errors)
                
                logger.warning(f"Iteration {iteration}: Playbook execution failed")
        
        except Exception as e:
            error_msg = f"Iteration {iteration} error: {str(e)}"
            logger.error(error_msg)
            iteration_result["errors"].append(error_msg)
        
        return iteration_result

    async def health_check(self) -> Dict[str, Any]:
        health_status = {
            "agent": True,
            "mcp_server": False,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            health_status["mcp_server"] = await self.mcp_client.health_check()
        except Exception as e:
            logger.error(f"MCP server health check failed: {str(e)}")
        
        return health_status