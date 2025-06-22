import yaml
import tempfile
import subprocess
import os
from typing import List, Tuple, Dict, Any
import logging
from config.ingestion_config import config_manager

logger = logging.getLogger(__name__)

class PlaybookValidator:
    def __init__(self):
        self.config = config_manager.get_playbook_config()
        self.temp_dir = self.config.get('temp_dir', tempfile.mkdtemp())
        
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir, exist_ok=True)

    def validate_yaml_syntax(self, playbook_content: str) -> Tuple[bool, List[str]]:
        if not self.config['validation_enabled']:
            return True, []
            
        errors = []
        try:
            yaml.safe_load(playbook_content)
            logger.info("YAML syntax validation passed")
            return True, []
        except yaml.YAMLError as e:
            error_msg = f"YAML syntax error: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            return False, errors

    def lint_playbook(self, playbook_content: str) -> Tuple[bool, List[str]]:
        if not self.config['lint_enabled']:
            return True, []
            
        errors = []
        
        temp_playbook_path = os.path.join(self.temp_dir, "playbook.yml")
        try:
            with open(temp_playbook_path, 'w') as f:
                f.write(playbook_content)
            
            result = subprocess.run(
                ["ansible-lint", temp_playbook_path],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                logger.info("Ansible lint validation passed")
                return True, []
            else:
                error_msg = f"Ansible lint errors: {result.stdout}\n{result.stderr}"
                logger.warning(error_msg)
                errors.append(error_msg)
                return False, errors
                
        except subprocess.TimeoutExpired:
            error_msg = "Ansible lint timed out"
            logger.error(error_msg)
            errors.append(error_msg)
            return False, errors
        except Exception as e:
            error_msg = f"Ansible lint execution error: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            return False, errors
        finally:
            if os.path.exists(temp_playbook_path):
                os.remove(temp_playbook_path)

    def validate_playbook_structure(self, playbook_content: str) -> Tuple[bool, List[str]]:
        if not self.config['validation_enabled']:
            return True, []
            
        errors = []
        
        try:
            playbook_data = yaml.safe_load(playbook_content)
            
            if not isinstance(playbook_data, list):
                errors.append("Playbook must be a list of plays")
                return False, errors
            
            for i, play in enumerate(playbook_data):
                if not isinstance(play, dict):
                    errors.append(f"Play {i+1} must be a dictionary")
                    continue
                
                if 'hosts' not in play:
                    errors.append(f"Play {i+1} missing required 'hosts' field")
                
                if 'tasks' not in play and 'roles' not in play:
                    errors.append(f"Play {i+1} must have either 'tasks' or 'roles'")
                
                if 'tasks' in play:
                    if not isinstance(play['tasks'], list):
                        errors.append(f"Play {i+1} 'tasks' must be a list")
                    else:
                        for j, task in enumerate(play['tasks']):
                            if not isinstance(task, dict):
                                errors.append(f"Play {i+1}, task {j+1} must be a dictionary")
                                continue
                            
                            if 'name' not in task:
                                errors.append(f"Play {i+1}, task {j+1} missing 'name' field")
            
            if errors:
                return False, errors
            
            logger.info("Playbook structure validation passed")
            return True, []
            
        except Exception as e:
            error_msg = f"Structure validation error: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            return False, errors

    def validate_all(self, playbook_content: str) -> Tuple[bool, List[str]]:
        all_errors = []
        
        yaml_valid, yaml_errors = self.validate_yaml_syntax(playbook_content)
        all_errors.extend(yaml_errors)
        
        if not yaml_valid:
            return False, all_errors
        
        structure_valid, structure_errors = self.validate_playbook_structure(playbook_content)
        all_errors.extend(structure_errors)
        
        lint_valid, lint_errors = self.lint_playbook(playbook_content)
        all_errors.extend(lint_errors)
        
        is_valid = yaml_valid and structure_valid and lint_valid
        
        if is_valid:
            logger.info("All playbook validations passed")
        else:
            logger.warning(f"Playbook validation failed with {len(all_errors)} errors")
        
        return is_valid, all_errors

    def cleanup(self):
        if os.path.exists(self.temp_dir) and self.temp_dir != tempfile.gettempdir():
            import shutil
            shutil.rmtree(self.temp_dir)