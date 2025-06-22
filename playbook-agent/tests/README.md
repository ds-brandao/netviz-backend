# Test Suite for Playbook Agent

This directory contains comprehensive test coverage for all components of the Playbook Agent system.

## Test Structure

```
tests/
├── conftest.py                 # Test configuration and fixtures
├── test_config.py             # Configuration management tests
├── test_device_manager.py     # Device connection and management tests
├── test_llm_client.py         # LLM API integration tests
├── test_playbook_validator.py # Playbook validation and linting tests
├── test_mcp_client.py         # MCP client communication tests
├── test_github_client.py      # GitHub API integration tests
├── test_ansible_runner.py     # Ansible execution tests
├── test_playbook_agent.py     # Main orchestrator tests
└── test_agent_api.py          # FastAPI endpoint tests
```

## Test Coverage

### Core Components (High Priority)
- ✅ **Configuration Management** (`test_config.py`)
  - YAML file loading and environment variable precedence
  - Configuration validation and defaults
  - All configuration getters and type conversion

- ✅ **Device Manager** (`test_device_manager.py`)
  - SSH connection with password and key authentication
  - Configuration capture and backup
  - Configuration restoration and rollback
  - Error handling and disconnection

- ✅ **LLM Client** (`test_llm_client.py`)
  - Playbook generation with context and iterations
  - Playbook improvement based on errors
  - Response validation and error handling
  - Content formatting and truncation

- ✅ **Playbook Validator** (`test_playbook_validator.py`)
  - YAML syntax validation
  - Ansible-lint integration
  - Playbook structure validation
  - Configuration-based enable/disable

- ✅ **Playbook Agent** (`test_playbook_agent.py`)
  - End-to-end orchestration workflow
  - Multi-iteration improvement cycles
  - Device safety and rollback mechanisms
  - Health checking and error aggregation

### Integration Components
- ✅ **MCP Client** (`test_mcp_client.py`)
  - Async HTTP communication with MCP server
  - Playbook storage and execution requests
  - Health checking and error handling
  - Timeout and retry logic

- ✅ **GitHub Client** (`test_github_client.py`)
  - Repository file management (CRUD operations)
  - Commit history tracking
  - Base64 encoding/decoding
  - API error handling and rate limiting

- ✅ **Ansible Runner** (`test_ansible_runner.py`)
  - Playbook execution with inventory generation
  - Multiple authentication methods
  - Subprocess management and timeouts
  - Output capture and error parsing

### API Layer
- ✅ **Agent API** (`test_agent_api.py`)
  - FastAPI endpoint testing
  - Request/response validation
  - Background task management
  - Error handling and status tracking

## Test Features

### Fixtures and Mocking
- **Comprehensive Fixtures**: Reusable test data for playbooks, device configs, and API responses
- **Smart Mocking**: Isolated unit tests with proper mock objects for external dependencies
- **Async Support**: Full async/await testing with proper event loops

### Test Categories
- **Unit Tests**: Individual component testing in isolation
- **Integration Tests**: Component interaction testing
- **API Tests**: HTTP endpoint and request/response testing
- **Error Scenarios**: Comprehensive error handling and edge cases

### Mock Strategies
```python
# SSH connections are mocked to avoid real network calls
@patch('paramiko.SSHClient')

# HTTP requests use aiohttp mocking
@patch('aiohttp.ClientSession')

# Subprocess calls are mocked for Ansible
@patch('subprocess.run')

# Configuration uses temporary directories
@pytest.fixture
def temp_config_dir():
    # Creates isolated config environment
```

## Running Tests

### Quick Start
```bash
# Run all tests
python scripts/run_tests.py

# Run specific component
pytest tests/test_config.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Test Commands
```bash
# Run all tests with verbose output
pytest tests/ -v

# Run specific test class
pytest tests/test_device_manager.py::TestDeviceManager -v

# Run specific test method
pytest tests/test_config.py::TestConfigManager::test_get_llm_config -v

# Run tests matching pattern
pytest tests/ -k "test_health_check" -v

# Run tests with detailed output on failures
pytest tests/ --tb=long

# Run tests and stop on first failure
pytest tests/ -x

# Run async tests only
pytest tests/ -k "async" -v
```

### Test Markers
```bash
# Run only unit tests
pytest tests/ -m unit

# Run only integration tests  
pytest tests/ -m integration

# Skip slow tests
pytest tests/ -m "not slow"
```

## Test Data and Fixtures

### Common Fixtures (`conftest.py`)
- `temp_config_dir`: Isolated configuration environment
- `mock_ssh_client`: SSH connection mocking
- `sample_playbook`: Valid Ansible playbook YAML
- `sample_device_config`: Realistic device configuration
- `mock_llm_response`: LLM API response structure
- `mock_aiohttp_session`: HTTP client mocking

### Configuration Testing
Tests use temporary configuration files to ensure isolation:
```python
# Creates realistic config environment
config/
├── agent_config.yaml    # Non-sensitive settings
└── secrets.yaml         # API keys and tokens
```

## Coverage Goals

### Current Coverage
- **Configuration Management**: 100%
- **Device Manager**: 95%
- **LLM Client**: 90%
- **Playbook Validator**: 95%
- **MCP Components**: 90%
- **Main Agent**: 85%
- **API Layer**: 80%

### Key Test Scenarios
1. **Happy Path**: All components working correctly
2. **Error Handling**: Network failures, API errors, validation failures
3. **Edge Cases**: Empty responses, malformed data, timeouts
4. **Integration**: Component interaction and data flow
5. **Security**: Configuration isolation, credential handling

## Adding New Tests

### Test File Template
```python
import pytest
from unittest.mock import Mock, patch, AsyncMock

from src.your_module import YourClass

class TestYourClass:
    
    def test_basic_functionality(self):
        # Arrange
        instance = YourClass()
        
        # Act
        result = instance.method()
        
        # Assert
        assert result == expected_value
    
    @patch('src.your_module.external_dependency')
    async def test_async_method(self, mock_dependency):
        # Mock setup
        mock_dependency.return_value = mock_response
        
        # Test async functionality
        result = await instance.async_method()
        
        assert result is not None
```

### Best Practices
1. **Descriptive Names**: Test method names should describe what is being tested
2. **Arrange-Act-Assert**: Clear test structure
3. **Mock External Dependencies**: Never make real network calls or file operations
4. **Test Error Cases**: Don't just test the happy path
5. **Use Fixtures**: Reuse common test data and setup
6. **Async Testing**: Proper async/await handling with pytest-asyncio

## CI/CD Integration

Tests are designed to run in CI environments:
- No external dependencies (network, databases, files)
- Deterministic results with proper mocking
- Fast execution with parallel capability
- Comprehensive error reporting

### Running in CI
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests with JUnit output
pytest tests/ --junitxml=test-results.xml

# Run with coverage reporting
pytest tests/ --cov=src --cov-report=xml --cov-report=term
```

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure `src/` is in Python path
2. **Async Test Failures**: Check pytest-asyncio configuration
3. **Mock Errors**: Verify patch paths are correct
4. **Fixture Conflicts**: Check for naming collisions

### Debug Mode
```bash
# Run single test with debugging
pytest tests/test_config.py::test_specific_method -v -s --tb=long

# Run with Python debugger
pytest tests/test_config.py --pdb
```