import pytest
import tempfile
import os
from unittest.mock import Mock, patch, mock_open
import subprocess

from src.utils.playbook_validator import PlaybookValidator

class TestPlaybookValidator:
    
    @patch('src.utils.playbook_validator.config_manager')
    def test_init(self, mock_config_manager):
        mock_config_manager.get_playbook_config.return_value = {
            'validation_enabled': True,
            'lint_enabled': True,
            'temp_dir': '/tmp/test-playbook-agent'
        }
        
        with patch('os.makedirs') as mock_makedirs:
            with patch('os.path.exists', return_value=False):
                validator = PlaybookValidator()
        
        assert validator.config['validation_enabled'] is True
        assert validator.config['lint_enabled'] is True
        assert validator.temp_dir == '/tmp/test-playbook-agent'
        mock_makedirs.assert_called_once_with('/tmp/test-playbook-agent', exist_ok=True)
    
    @patch('src.utils.playbook_validator.config_manager')
    def test_validate_yaml_syntax_success(self, mock_config_manager, sample_playbook):
        mock_config_manager.get_playbook_config.return_value = {
            'validation_enabled': True,
            'lint_enabled': True,
            'temp_dir': '/tmp/test'
        }
        
        validator = PlaybookValidator()
        
        is_valid, errors = validator.validate_yaml_syntax(sample_playbook)
        
        assert is_valid is True
        assert len(errors) == 0
    
    @patch('src.utils.playbook_validator.config_manager')
    def test_validate_yaml_syntax_invalid(self, mock_config_manager):
        mock_config_manager.get_playbook_config.return_value = {
            'validation_enabled': True,
            'lint_enabled': True,
            'temp_dir': '/tmp/test'
        }
        
        validator = PlaybookValidator()
        
        invalid_yaml = "---\n- name: Test\n  invalid_indentation"
        
        is_valid, errors = validator.validate_yaml_syntax(invalid_yaml)
        
        assert is_valid is False
        assert len(errors) > 0
        assert "YAML syntax error" in errors[0]
    
    @patch('src.utils.playbook_validator.config_manager')
    def test_validate_yaml_syntax_disabled(self, mock_config_manager, sample_playbook):
        mock_config_manager.get_playbook_config.return_value = {
            'validation_enabled': False,
            'lint_enabled': True,
            'temp_dir': '/tmp/test'
        }
        
        validator = PlaybookValidator()
        
        is_valid, errors = validator.validate_yaml_syntax(sample_playbook)
        
        assert is_valid is True
        assert len(errors) == 0
    
    @patch('src.utils.playbook_validator.config_manager')
    @patch('subprocess.run')
    def test_lint_playbook_success(self, mock_subprocess, mock_config_manager, sample_playbook):
        mock_config_manager.get_playbook_config.return_value = {
            'validation_enabled': True,
            'lint_enabled': True,
            'temp_dir': '/tmp/test'
        }
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        validator = PlaybookValidator()
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('os.path.exists', return_value=True):
                with patch('os.remove'):
                    is_valid, errors = validator.lint_playbook(sample_playbook)
        
        assert is_valid is True
        assert len(errors) == 0
        mock_subprocess.assert_called_once()
        
        # Verify ansible-lint was called
        call_args = mock_subprocess.call_args[0][0]
        assert call_args[0] == "ansible-lint"
    
    @patch('src.utils.playbook_validator.config_manager')
    @patch('subprocess.run')
    def test_lint_playbook_failure(self, mock_subprocess, mock_config_manager, sample_playbook):
        mock_config_manager.get_playbook_config.return_value = {
            'validation_enabled': True,
            'lint_enabled': True,
            'temp_dir': '/tmp/test'
        }
        
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = "Lint error output"
        mock_result.stderr = "Lint error stderr"
        mock_subprocess.return_value = mock_result
        
        validator = PlaybookValidator()
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('os.path.exists', return_value=True):
                with patch('os.remove'):
                    is_valid, errors = validator.lint_playbook(sample_playbook)
        
        assert is_valid is False
        assert len(errors) > 0
        assert "Ansible lint errors" in errors[0]
        assert "Lint error output" in errors[0]
    
    @patch('src.utils.playbook_validator.config_manager')
    def test_lint_playbook_disabled(self, mock_config_manager, sample_playbook):
        mock_config_manager.get_playbook_config.return_value = {
            'validation_enabled': True,
            'lint_enabled': False,
            'temp_dir': '/tmp/test'
        }
        
        validator = PlaybookValidator()
        
        is_valid, errors = validator.lint_playbook(sample_playbook)
        
        assert is_valid is True
        assert len(errors) == 0
    
    @patch('src.utils.playbook_validator.config_manager')
    @patch('subprocess.run')
    def test_lint_playbook_timeout(self, mock_subprocess, mock_config_manager, sample_playbook):
        mock_config_manager.get_playbook_config.return_value = {
            'validation_enabled': True,
            'lint_enabled': True,
            'temp_dir': '/tmp/test'
        }
        
        mock_subprocess.side_effect = subprocess.TimeoutExpired("ansible-lint", 60)
        
        validator = PlaybookValidator()
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('os.path.exists', return_value=True):
                with patch('os.remove'):
                    is_valid, errors = validator.lint_playbook(sample_playbook)
        
        assert is_valid is False
        assert len(errors) > 0
        assert "Ansible lint timed out" in errors[0]
    
    @patch('src.utils.playbook_validator.config_manager')
    def test_validate_playbook_structure_success(self, mock_config_manager, sample_playbook):
        mock_config_manager.get_playbook_config.return_value = {
            'validation_enabled': True,
            'lint_enabled': True,
            'temp_dir': '/tmp/test'
        }
        
        validator = PlaybookValidator()
        
        is_valid, errors = validator.validate_playbook_structure(sample_playbook)
        
        assert is_valid is True
        assert len(errors) == 0
    
    @patch('src.utils.playbook_validator.config_manager')
    def test_validate_playbook_structure_not_list(self, mock_config_manager):
        mock_config_manager.get_playbook_config.return_value = {
            'validation_enabled': True,
            'lint_enabled': True,
            'temp_dir': '/tmp/test'
        }
        
        validator = PlaybookValidator()
        
        invalid_playbook = "name: Not a list"
        
        is_valid, errors = validator.validate_playbook_structure(invalid_playbook)
        
        assert is_valid is False
        assert len(errors) > 0
        assert "Playbook must be a list of plays" in errors[0]
    
    @patch('src.utils.playbook_validator.config_manager')
    def test_validate_playbook_structure_missing_hosts(self, mock_config_manager):
        mock_config_manager.get_playbook_config.return_value = {
            'validation_enabled': True,
            'lint_enabled': True,
            'temp_dir': '/tmp/test'
        }
        
        validator = PlaybookValidator()
        
        playbook_missing_hosts = """---
- name: Test play
  tasks:
    - name: Test task
      debug:
        msg: "test"
"""
        
        is_valid, errors = validator.validate_playbook_structure(playbook_missing_hosts)
        
        assert is_valid is False
        assert len(errors) > 0
        assert "missing required 'hosts' field" in errors[0]
    
    @patch('src.utils.playbook_validator.config_manager')
    def test_validate_playbook_structure_missing_tasks_and_roles(self, mock_config_manager):
        mock_config_manager.get_playbook_config.return_value = {
            'validation_enabled': True,
            'lint_enabled': True,
            'temp_dir': '/tmp/test'
        }
        
        validator = PlaybookValidator()
        
        playbook_missing_tasks = """---
- name: Test play
  hosts: all
"""
        
        is_valid, errors = validator.validate_playbook_structure(playbook_missing_tasks)
        
        assert is_valid is False
        assert len(errors) > 0
        assert "must have either 'tasks' or 'roles'" in errors[0]
    
    @patch('src.utils.playbook_validator.config_manager')
    def test_validate_playbook_structure_task_missing_name(self, mock_config_manager):
        mock_config_manager.get_playbook_config.return_value = {
            'validation_enabled': True,
            'lint_enabled': True,
            'temp_dir': '/tmp/test'
        }
        
        validator = PlaybookValidator()
        
        playbook_task_no_name = """---
- name: Test play
  hosts: all
  tasks:
    - debug:
        msg: "test"
"""
        
        is_valid, errors = validator.validate_playbook_structure(playbook_task_no_name)
        
        assert is_valid is False
        assert len(errors) > 0
        assert "missing 'name' field" in errors[0]
    
    @patch('src.utils.playbook_validator.config_manager')
    def test_validate_playbook_structure_disabled(self, mock_config_manager):
        mock_config_manager.get_playbook_config.return_value = {
            'validation_enabled': False,
            'lint_enabled': True,
            'temp_dir': '/tmp/test'
        }
        
        validator = PlaybookValidator()
        
        invalid_playbook = "invalid structure"
        
        is_valid, errors = validator.validate_playbook_structure(invalid_playbook)
        
        assert is_valid is True
        assert len(errors) == 0
    
    @patch('src.utils.playbook_validator.config_manager')
    @patch('subprocess.run')
    def test_validate_all_success(self, mock_subprocess, mock_config_manager, sample_playbook):
        mock_config_manager.get_playbook_config.return_value = {
            'validation_enabled': True,
            'lint_enabled': True,
            'temp_dir': '/tmp/test'
        }
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        validator = PlaybookValidator()
        
        with patch('builtins.open', mock_open()):
            with patch('os.path.exists', return_value=True):
                with patch('os.remove'):
                    is_valid, errors = validator.validate_all(sample_playbook)
        
        assert is_valid is True
        assert len(errors) == 0
    
    @patch('src.utils.playbook_validator.config_manager')
    def test_validate_all_yaml_failure_stops_validation(self, mock_config_manager):
        mock_config_manager.get_playbook_config.return_value = {
            'validation_enabled': True,
            'lint_enabled': True,
            'temp_dir': '/tmp/test'
        }
        
        validator = PlaybookValidator()
        
        invalid_yaml = "---\n- name: Test\n  invalid_indentation"
        
        is_valid, errors = validator.validate_all(invalid_yaml)
        
        assert is_valid is False
        assert len(errors) > 0
        assert "YAML syntax error" in errors[0]
    
    @patch('src.utils.playbook_validator.config_manager')
    @patch('subprocess.run')
    def test_validate_all_multiple_errors(self, mock_subprocess, mock_config_manager):
        mock_config_manager.get_playbook_config.return_value = {
            'validation_enabled': True,
            'lint_enabled': True,
            'temp_dir': '/tmp/test'
        }
        
        # Mock lint failure
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = "Lint error"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        validator = PlaybookValidator()
        
        # Invalid structure but valid YAML
        invalid_structure_playbook = """---
- name: Test play missing hosts
  tasks:
    - debug:
        msg: "test"
"""
        
        with patch('builtins.open', mock_open()):
            with patch('os.path.exists', return_value=True):
                with patch('os.remove'):
                    is_valid, errors = validator.validate_all(invalid_structure_playbook)
        
        assert is_valid is False
        assert len(errors) >= 2  # Structure error + lint error
    
    @patch('src.utils.playbook_validator.config_manager')
    def test_cleanup(self, mock_config_manager):
        mock_config_manager.get_playbook_config.return_value = {
            'validation_enabled': True,
            'lint_enabled': True,
            'temp_dir': '/custom/temp/dir'
        }
        
        validator = PlaybookValidator()
        
        with patch('os.path.exists', return_value=True) as mock_exists:
            with patch('shutil.rmtree') as mock_rmtree:
                validator.cleanup()
        
        mock_exists.assert_called_once_with('/custom/temp/dir')
        mock_rmtree.assert_called_once_with('/custom/temp/dir')
    
    @patch('src.utils.playbook_validator.config_manager')
    def test_cleanup_temp_dir_is_system_temp(self, mock_config_manager):
        mock_config_manager.get_playbook_config.return_value = {
            'validation_enabled': True,
            'lint_enabled': True,
            'temp_dir': '/tmp'  # System temp directory
        }
        
        validator = PlaybookValidator()
        
        with patch('tempfile.gettempdir', return_value='/tmp'):
            with patch('os.path.exists', return_value=True):
                with patch('shutil.rmtree') as mock_rmtree:
                    validator.cleanup()
        
        # Should not remove system temp directory
        mock_rmtree.assert_not_called()