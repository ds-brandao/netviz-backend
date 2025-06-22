import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import asyncio
import uuid

from src.agent.api import app

class TestAgentAPI:
    
    def setup_method(self):
        self.client = TestClient(app)
    
    def test_root_endpoint(self):
        response = self.client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Playbook Agent API"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
    
    @patch('src.agent.api.agent')
    async def test_health_check_success(self, mock_agent):
        mock_agent.health_check.return_value = {
            "agent": True,
            "mcp_server": True,
            "timestamp": "2023-01-01T00:00:00Z"
        }
        
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["agent"] is True
        assert data["mcp_server"] is True
        assert "timestamp" in data
    
    @patch('src.agent.api.agent')
    async def test_health_check_failure(self, mock_agent):
        mock_agent.health_check.side_effect = Exception("Health check failed")
        
        response = self.client.get("/health")
        
        assert response.status_code == 500
        assert "Health check failed" in response.json()["detail"]
    
    @patch('uuid.uuid4')
    @patch('src.agent.api.task_results', {})
    def test_generate_playbook_success(self, mock_uuid):
        mock_task_id = "test-task-id-123"
        mock_uuid.return_value = mock_task_id
        
        request_data = {
            "device_id": "router-01",
            "device_host": "192.168.1.1", 
            "device_user": "admin",
            "intentions": "Configure OSPF routing",
            "device_password": "password"
        }
        
        response = self.client.post("/generate-playbook", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == mock_task_id
        assert data["status"] == "running"
        assert data["message"] == "Playbook generation started"
        
        # Verify task was added to task_results
        from src.agent.api import task_results
        assert mock_task_id in task_results
        assert task_results[mock_task_id]["status"] == "running"
    
    def test_generate_playbook_missing_required_fields(self):
        request_data = {
            "device_id": "router-01",
            # Missing device_host, device_user, intentions
        }
        
        response = self.client.post("/generate-playbook", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_generate_playbook_invalid_json(self):
        response = self.client.post("/generate-playbook", data="invalid json")
        
        assert response.status_code == 422
    
    @patch('src.agent.api.task_results')
    def test_get_task_status_success(self, mock_task_results):
        task_id = "test-task-123"
        mock_task_results.__getitem__.return_value = {
            "status": "completed",
            "started_at": "2023-01-01T00:00:00Z",
            "completed_at": "2023-01-01T00:05:00Z",
            "result": {
                "success": True,
                "device_id": "router-01",
                "final_playbook": "---\n- name: test"
            }
        }
        mock_task_results.__contains__.return_value = True
        
        response = self.client.get(f"/task/{task_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["result"]["success"] is True
        assert "final_playbook" in data["result"]
    
    @patch('src.agent.api.task_results')
    def test_get_task_status_not_found(self, mock_task_results):
        task_id = "nonexistent-task"
        mock_task_results.__contains__.return_value = False
        
        response = self.client.get(f"/task/{task_id}")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"
    
    @patch('src.agent.api.task_results')
    def test_get_task_status_running(self, mock_task_results):
        task_id = "running-task-123"
        mock_task_results.__getitem__.return_value = {
            "status": "running",
            "started_at": "2023-01-01T00:00:00Z",
            "result": None
        }
        mock_task_results.__contains__.return_value = True
        
        response = self.client.get(f"/task/{task_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert data["result"] is None
    
    @patch('src.agent.api.task_results')
    def test_get_task_status_failed(self, mock_task_results):
        task_id = "failed-task-123"
        mock_task_results.__getitem__.return_value = {
            "status": "failed",
            "started_at": "2023-01-01T00:00:00Z",
            "completed_at": "2023-01-01T00:03:00Z",
            "result": {
                "success": False,
                "errors": ["Connection failed", "Max iterations reached"]
            }
        }
        mock_task_results.__contains__.return_value = True
        
        response = self.client.get(f"/task/{task_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert data["result"]["success"] is False
        assert len(data["result"]["errors"]) == 2

class TestPlaybookRequest:
    
    def test_playbook_request_validation_success(self):
        from src.agent.api import PlaybookRequest
        
        valid_data = {
            "device_id": "router-01",
            "device_host": "192.168.1.1",
            "device_user": "admin", 
            "intentions": "Configure OSPF routing",
            "device_password": "password"
        }
        
        request = PlaybookRequest(**valid_data)
        
        assert request.device_id == "router-01"
        assert request.device_host == "192.168.1.1"
        assert request.device_user == "admin"
        assert request.intentions == "Configure OSPF routing"
        assert request.device_password == "password"
        assert request.private_key_path is None
    
    def test_playbook_request_validation_with_private_key(self):
        from src.agent.api import PlaybookRequest
        
        valid_data = {
            "device_id": "router-01",
            "device_host": "192.168.1.1",
            "device_user": "admin",
            "intentions": "Configure OSPF routing",
            "private_key_path": "/path/to/key.pem"
        }
        
        request = PlaybookRequest(**valid_data)
        
        assert request.device_password is None
        assert request.private_key_path == "/path/to/key.pem"
    
    def test_playbook_request_validation_missing_required(self):
        from src.agent.api import PlaybookRequest
        from pydantic import ValidationError
        
        invalid_data = {
            "device_id": "router-01",
            # Missing device_host, device_user, intentions
        }
        
        with pytest.raises(ValidationError):
            PlaybookRequest(**invalid_data)

class TestPlaybookResponse:
    
    def test_playbook_response_validation(self):
        from src.agent.api import PlaybookResponse
        
        valid_data = {
            "task_id": "test-task-123",
            "status": "running",
            "message": "Playbook generation started"
        }
        
        response = PlaybookResponse(**valid_data)
        
        assert response.task_id == "test-task-123"
        assert response.status == "running"
        assert response.message == "Playbook generation started"

class TestBackgroundTask:
    
    @patch('src.agent.api.task_results', {})
    @patch('src.agent.api.agent')
    async def test_run_playbook_generation_success(self, mock_agent):
        from src.agent.api import run_playbook_generation, PlaybookRequest, task_results
        
        mock_agent.generate_and_test_playbook.return_value = {
            "success": True,
            "device_id": "router-01",
            "intentions": "Configure OSPF",
            "final_playbook": "---\n- name: test",
            "iterations": [{"success": True}]
        }
        
        task_id = "test-task-123"
        task_results[task_id] = {"status": "running", "started_at": "now"}
        
        request = PlaybookRequest(
            device_id="router-01",
            device_host="192.168.1.1",
            device_user="admin",
            intentions="Configure OSPF",
            device_password="password"
        )
        
        await run_playbook_generation(task_id, request)
        
        assert task_results[task_id]["status"] == "completed"
        assert task_results[task_id]["result"]["success"] is True
        
        mock_agent.generate_and_test_playbook.assert_called_once_with(
            device_id="router-01",
            device_host="192.168.1.1",
            device_user="admin",
            intentions="Configure OSPF",
            device_password="password",
            private_key_path=None
        )
    
    @patch('src.agent.api.task_results', {})
    @patch('src.agent.api.agent')
    async def test_run_playbook_generation_failure(self, mock_agent):
        from src.agent.api import run_playbook_generation, PlaybookRequest, task_results
        
        mock_agent.generate_and_test_playbook.return_value = {
            "success": False,
            "device_id": "router-01",
            "intentions": "Configure OSPF",
            "errors": ["Connection failed", "Max iterations reached"],
            "iterations": [{"success": False}]
        }
        
        task_id = "test-task-123"
        task_results[task_id] = {"status": "running", "started_at": "now"}
        
        request = PlaybookRequest(
            device_id="router-01",
            device_host="192.168.1.1",
            device_user="admin",
            intentions="Configure OSPF"
        )
        
        await run_playbook_generation(task_id, request)
        
        assert task_results[task_id]["status"] == "failed"
        assert task_results[task_id]["result"]["success"] is False
        assert len(task_results[task_id]["result"]["errors"]) == 2
    
    @patch('src.agent.api.task_results', {})
    @patch('src.agent.api.agent')
    async def test_run_playbook_generation_exception(self, mock_agent):
        from src.agent.api import run_playbook_generation, PlaybookRequest, task_results
        
        mock_agent.generate_and_test_playbook.side_effect = Exception("Critical error")
        
        task_id = "test-task-123"
        task_results[task_id] = {"status": "running", "started_at": "now"}
        
        request = PlaybookRequest(
            device_id="router-01",
            device_host="192.168.1.1",
            device_user="admin",
            intentions="Configure OSPF"
        )
        
        await run_playbook_generation(task_id, request)
        
        assert task_results[task_id]["status"] == "error"
        assert "Critical error" in task_results[task_id]["error"]
    
    @patch('src.agent.api.task_results', {})
    @patch('src.agent.api.agent')
    async def test_run_playbook_generation_with_private_key(self, mock_agent):
        from src.agent.api import run_playbook_generation, PlaybookRequest, task_results
        
        mock_agent.generate_and_test_playbook.return_value = {
            "success": True,
            "device_id": "router-01"
        }
        
        task_id = "test-task-123"
        task_results[task_id] = {"status": "running", "started_at": "now"}
        
        request = PlaybookRequest(
            device_id="router-01",
            device_host="192.168.1.1",
            device_user="admin",
            intentions="Configure OSPF",
            private_key_path="/path/to/key.pem"
        )
        
        await run_playbook_generation(task_id, request)
        
        mock_agent.generate_and_test_playbook.assert_called_once_with(
            device_id="router-01",
            device_host="192.168.1.1",
            device_user="admin",
            intentions="Configure OSPF",
            device_password=None,
            private_key_path="/path/to/key.pem"
        )