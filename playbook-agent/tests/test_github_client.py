import pytest
import base64
import json
from unittest.mock import Mock, patch, AsyncMock
import aiohttp

from src.mcp_server.github_client import GitHubClient

class TestGitHubClient:
    
    @patch('src.mcp_server.github_client.config_manager')
    def test_init_success(self, mock_config_manager):
        mock_config_manager.get_github_config.return_value = {
            'token': 'test-token',
            'username': 'test-user',
            'repository': 'test-repo',
            'branch': 'main',
            'commit_message_template': 'Generated playbook for {device_id} - iteration {iteration}'
        }
        
        client = GitHubClient()
        
        assert client.base_url == "https://api.github.com"
        assert client.headers["Authorization"] == "Bearer test-token"
        assert client.config['username'] == 'test-user'
        assert client.config['repository'] == 'test-repo'
    
    @patch('src.mcp_server.github_client.config_manager')
    def test_init_no_token_raises_error(self, mock_config_manager):
        mock_config_manager.get_github_config.return_value = {
            'token': None,
            'username': 'test-user',
            'repository': 'test-repo',
            'branch': 'main',
            'commit_message_template': 'Generated playbook for {device_id} - iteration {iteration}'
        }
        
        with pytest.raises(ValueError, match="GitHub token is required"):
            GitHubClient()
    
    @patch('src.mcp_server.github_client.config_manager')
    @patch('aiohttp.ClientSession')
    async def test_store_playbook_new_file(self, mock_session_class, mock_config_manager):
        mock_config_manager.get_github_config.return_value = {
            'token': 'test-token',
            'username': 'test-user',
            'repository': 'test-repo',
            'branch': 'main',
            'commit_message_template': 'Generated playbook for {device_id} - iteration {iteration}'
        }
        
        # Mock _get_file to return None (file doesn't exist)
        client = GitHubClient()
        client._get_file = AsyncMock(return_value=None)
        
        # Mock the PUT response
        mock_response = AsyncMock()
        mock_response.status = 201
        mock_response.json.return_value = {
            "content": {"sha": "new-sha", "html_url": "http://github.com/test"},
            "commit": {"sha": "commit-sha"}
        }
        
        mock_session = AsyncMock()
        mock_session.put.return_value.__aenter__.return_value = mock_response
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        result = await client.store_playbook(
            name="test-playbook.yml",
            content="---\n- name: test",
            iteration=1
        )
        
        assert result["sha"] == "new-sha"
        assert result["url"] == "http://github.com/test"
        assert result["commit_sha"] == "commit-sha"
        
        # Verify the PUT call
        call_args = mock_session.put.call_args
        assert "playbooks/test-playbook.yml" in call_args[0][0]
        
        json_payload = call_args[1]["json"]
        assert json_payload["message"] == "Generated playbook for test-playbook - iteration 1"
        assert json_payload["branch"] == "main"
        
        # Verify content is base64 encoded
        decoded_content = base64.b64decode(json_payload["content"]).decode()
        assert decoded_content == "---\n- name: test"
    
    @patch('src.mcp_server.github_client.config_manager')
    @patch('aiohttp.ClientSession')
    async def test_store_playbook_update_existing(self, mock_session_class, mock_config_manager):
        mock_config_manager.get_github_config.return_value = {
            'token': 'test-token',
            'username': 'test-user',
            'repository': 'test-repo',
            'branch': 'main',
            'commit_message_template': 'Generated playbook for {device_id} - iteration {iteration}'
        }
        
        client = GitHubClient()
        
        # Mock _get_file to return existing file
        client._get_file = AsyncMock(return_value={"sha": "existing-sha"})
        
        # Mock the PUT response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "content": {"sha": "updated-sha", "html_url": "http://github.com/test"},
            "commit": {"sha": "new-commit-sha"}
        }
        
        mock_session = AsyncMock()
        mock_session.put.return_value.__aenter__.return_value = mock_response
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        result = await client.store_playbook(
            name="existing-playbook.yml",
            content="---\n- name: updated test",
            iteration=2
        )
        
        assert result["sha"] == "updated-sha"
        
        # Verify the PUT call includes the existing SHA
        call_args = mock_session.put.call_args
        json_payload = call_args[1]["json"]
        assert json_payload["sha"] == "existing-sha"
        assert json_payload["message"] == "Generated playbook for existing-playbook - iteration 2"
    
    @patch('src.mcp_server.github_client.config_manager')
    @patch('aiohttp.ClientSession')
    async def test_store_playbook_api_error(self, mock_session_class, mock_config_manager):
        mock_config_manager.get_github_config.return_value = {
            'token': 'test-token',
            'username': 'test-user',
            'repository': 'test-repo',
            'branch': 'main',
            'commit_message_template': 'Generated playbook for {device_id} - iteration {iteration}'
        }
        
        client = GitHubClient()
        client._get_file = AsyncMock(return_value=None)
        
        # Mock API error response
        mock_response = AsyncMock()
        mock_response.status = 422
        mock_response.text.return_value = "Validation failed"
        
        mock_session = AsyncMock()
        mock_session.put.return_value.__aenter__.return_value = mock_response
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        with pytest.raises(Exception, match="GitHub API error 422"):
            await client.store_playbook(
                name="test-playbook.yml",
                content="---\n- name: test"
            )
    
    @patch('src.mcp_server.github_client.config_manager')
    @patch('aiohttp.ClientSession')
    async def test_get_playbook_success(self, mock_session_class, mock_config_manager):
        mock_config_manager.get_github_config.return_value = {
            'token': 'test-token',
            'username': 'test-user',
            'repository': 'test-repo',
            'branch': 'main',
            'commit_message_template': 'Generated playbook for {device_id} - iteration {iteration}'
        }
        
        client = GitHubClient()
        
        # Mock _get_file to return file content
        playbook_content = "---\n- name: test playbook"
        encoded_content = base64.b64encode(playbook_content.encode()).decode()
        
        client._get_file = AsyncMock(return_value={
            "content": encoded_content,
            "sha": "file-sha"
        })
        
        result = await client.get_playbook("test-playbook.yml")
        
        assert result == playbook_content
        client._get_file.assert_called_once_with("playbooks/test-playbook.yml")
    
    @patch('src.mcp_server.github_client.config_manager')
    async def test_get_playbook_not_found(self, mock_config_manager):
        mock_config_manager.get_github_config.return_value = {
            'token': 'test-token',
            'username': 'test-user',
            'repository': 'test-repo',
            'branch': 'main',
            'commit_message_template': 'Generated playbook for {device_id} - iteration {iteration}'
        }
        
        client = GitHubClient()
        client._get_file = AsyncMock(return_value=None)
        
        with pytest.raises(Exception, match="Playbook test-playbook.yml not found"):
            await client.get_playbook("test-playbook.yml")
    
    @patch('src.mcp_server.github_client.config_manager')
    @patch('aiohttp.ClientSession')
    async def test_get_playbook_history_success(self, mock_session_class, mock_config_manager):
        mock_config_manager.get_github_config.return_value = {
            'token': 'test-token',
            'username': 'test-user',
            'repository': 'test-repo',
            'branch': 'main',
            'commit_message_template': 'Generated playbook for {device_id} - iteration {iteration}'
        }
        
        client = GitHubClient()
        
        # Mock the directory listing response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = [
            {
                "name": "test-device_v1.yml",
                "path": "playbooks/test-device_v1.yml",
                "size": 100,
                "html_url": "http://github.com/file1"
            },
            {
                "name": "test-device_v2.yml",
                "path": "playbooks/test-device_v2.yml",
                "size": 120,
                "html_url": "http://github.com/file2"
            },
            {
                "name": "other-playbook.yml",
                "path": "playbooks/other-playbook.yml",
                "size": 80,
                "html_url": "http://github.com/file3"
            }
        ]
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        # Mock _get_file_commits
        client._get_file_commits = AsyncMock(return_value=[
            {"commit": {"author": {"date": "2023-01-01T00:00:00Z"}}}
        ])
        
        result = await client.get_playbook_history("test-device")
        
        assert result["base_name"] == "test-device"
        assert result["total_versions"] == 2
        assert len(result["files"]) == 2
        
        # Should only include files that start with "test-device"
        file_names = [f["name"] for f in result["files"]]
        assert "test-device_v1.yml" in file_names
        assert "test-device_v2.yml" in file_names
        assert "other-playbook.yml" not in file_names
    
    @patch('src.mcp_server.github_client.config_manager')
    @patch('aiohttp.ClientSession')
    async def test_get_file_success(self, mock_session_class, mock_config_manager):
        mock_config_manager.get_github_config.return_value = {
            'token': 'test-token',
            'username': 'test-user',
            'repository': 'test-repo',
            'branch': 'main',
            'commit_message_template': 'Generated playbook for {device_id} - iteration {iteration}'
        }
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "content": "dGVzdCBjb250ZW50",  # base64 encoded "test content"
            "sha": "file-sha"
        }
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        client = GitHubClient()
        
        result = await client._get_file("test/path.yml")
        
        assert result["content"] == "dGVzdCBjb250ZW50"
        assert result["sha"] == "file-sha"
        
        call_args = mock_session.get.call_args
        assert "test-user/test-repo/contents/test/path.yml" in call_args[0][0]
    
    @patch('src.mcp_server.github_client.config_manager')
    @patch('aiohttp.ClientSession')
    async def test_get_file_not_found(self, mock_session_class, mock_config_manager):
        mock_config_manager.get_github_config.return_value = {
            'token': 'test-token',
            'username': 'test-user',
            'repository': 'test-repo',
            'branch': 'main',
            'commit_message_template': 'Generated playbook for {device_id} - iteration {iteration}'
        }
        
        mock_response = AsyncMock()
        mock_response.status = 404
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        client = GitHubClient()
        
        result = await client._get_file("nonexistent/path.yml")
        
        assert result is None
    
    @patch('src.mcp_server.github_client.config_manager')
    @patch('aiohttp.ClientSession')
    async def test_get_file_api_error(self, mock_session_class, mock_config_manager):
        mock_config_manager.get_github_config.return_value = {
            'token': 'test-token',
            'username': 'test-user',
            'repository': 'test-repo',
            'branch': 'main',
            'commit_message_template': 'Generated playbook for {device_id} - iteration {iteration}'
        }
        
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text.return_value = "Internal server error"
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        client = GitHubClient()
        
        with pytest.raises(Exception, match="GitHub API error 500"):
            await client._get_file("test/path.yml")
    
    @patch('src.mcp_server.github_client.config_manager')
    @patch('aiohttp.ClientSession')
    async def test_get_file_commits_success(self, mock_session_class, mock_config_manager):
        mock_config_manager.get_github_config.return_value = {
            'token': 'test-token',
            'username': 'test-user',
            'repository': 'test-repo',
            'branch': 'main',
            'commit_message_template': 'Generated playbook for {device_id} - iteration {iteration}'
        }
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = [
            {"sha": "commit1", "commit": {"author": {"date": "2023-01-01"}}},
            {"sha": "commit2", "commit": {"author": {"date": "2023-01-02"}}}
        ]
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        client = GitHubClient()
        
        result = await client._get_file_commits("test/path.yml")
        
        assert len(result) == 2
        assert result[0]["sha"] == "commit1"
        assert result[1]["sha"] == "commit2"
        
        call_args = mock_session.get.call_args
        assert "commits" in call_args[0][0]
        assert call_args[1]["params"]["path"] == "test/path.yml"
    
    @patch('src.mcp_server.github_client.config_manager')
    @patch('aiohttp.ClientSession')
    async def test_health_check_success(self, mock_session_class, mock_config_manager):
        mock_config_manager.get_github_config.return_value = {
            'token': 'test-token',
            'username': 'test-user',
            'repository': 'test-repo',
            'branch': 'main',
            'commit_message_template': 'Generated playbook for {device_id} - iteration {iteration}'
        }
        
        mock_response = AsyncMock()
        mock_response.status = 200
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        client = GitHubClient()
        
        result = await client.health_check()
        
        assert result is True
        
        call_args = mock_session.get.call_args
        assert "test-user/test-repo" in call_args[0][0]
    
    @patch('src.mcp_server.github_client.config_manager')
    @patch('aiohttp.ClientSession')
    async def test_health_check_failure(self, mock_session_class, mock_config_manager):
        mock_config_manager.get_github_config.return_value = {
            'token': 'test-token',
            'username': 'test-user',
            'repository': 'test-repo',
            'branch': 'main',
            'commit_message_template': 'Generated playbook for {device_id} - iteration {iteration}'
        }
        
        mock_response = AsyncMock()
        mock_response.status = 404
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        client = GitHubClient()
        
        result = await client.health_check()
        
        assert result is False
    
    @patch('src.mcp_server.github_client.config_manager')
    @patch('aiohttp.ClientSession')
    async def test_health_check_exception(self, mock_session_class, mock_config_manager):
        mock_config_manager.get_github_config.return_value = {
            'token': 'test-token',
            'username': 'test-user',
            'repository': 'test-repo',
            'branch': 'main',
            'commit_message_template': 'Generated playbook for {device_id} - iteration {iteration}'
        }
        
        mock_session = AsyncMock()
        mock_session.get.side_effect = aiohttp.ClientError("Connection failed")
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        client = GitHubClient()
        
        result = await client.health_check()
        
        assert result is False