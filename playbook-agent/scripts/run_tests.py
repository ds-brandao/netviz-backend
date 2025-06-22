#!/usr/bin/env python3

import os
import sys
import subprocess
from pathlib import Path

def main():
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print("🧪 Running Playbook Agent Test Suite")
    print("=" * 50)
    
    # Check if pytest is installed
    try:
        subprocess.run(["pytest", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ pytest not found. Please install requirements:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    
    # Run tests with different configurations
    test_commands = [
        {
            "name": "🔧 Configuration Tests",
            "command": ["pytest", "tests/test_config.py", "-v"]
        },
        {
            "name": "🔌 Device Manager Tests", 
            "command": ["pytest", "tests/test_device_manager.py", "-v"]
        },
        {
            "name": "🤖 LLM Client Tests",
            "command": ["pytest", "tests/test_llm_client.py", "-v"]
        },
        {
            "name": "✅ Playbook Validator Tests",
            "command": ["pytest", "tests/test_playbook_validator.py", "-v"]
        },
        {
            "name": "🌐 MCP Client Tests",
            "command": ["pytest", "tests/test_mcp_client.py", "-v"]
        },
        {
            "name": "📚 GitHub Client Tests",
            "command": ["pytest", "tests/test_github_client.py", "-v"]
        },
        {
            "name": "⚙️ Ansible Runner Tests",
            "command": ["pytest", "tests/test_ansible_runner.py", "-v"]
        },
        {
            "name": "🎯 Playbook Agent Tests",
            "command": ["pytest", "tests/test_playbook_agent.py", "-v"]
        },
        {
            "name": "🌍 Agent API Tests",
            "command": ["pytest", "tests/test_agent_api.py", "-v"]
        }
    ]
    
    failed_tests = []
    
    for test_config in test_commands:
        print(f"\n{test_config['name']}")
        print("-" * len(test_config['name']))
        
        try:
            result = subprocess.run(
                test_config['command'],
                check=True,
                capture_output=True,
                text=True
            )
            print("✅ PASSED")
            if result.stdout:
                # Show summary line
                lines = result.stdout.strip().split('\n')
                summary_line = [line for line in lines if 'passed' in line and ('failed' in line or 'error' in line or line.endswith('passed'))]
                if summary_line:
                    print(f"   {summary_line[-1]}")
        
        except subprocess.CalledProcessError as e:
            print("❌ FAILED")
            failed_tests.append(test_config['name'])
            if e.stdout:
                print("STDOUT:")
                print(e.stdout)
            if e.stderr:
                print("STDERR:")
                print(e.stderr)
    
    # Run all tests together for coverage
    print("\n🎯 Running Full Test Suite")
    print("-" * 30)
    
    try:
        result = subprocess.run([
            "pytest", 
            "tests/",
            "-v",
            "--tb=short",
            "--durations=10"
        ], check=True, capture_output=True, text=True)
        
        print("✅ ALL TESTS PASSED")
        
        # Extract and display summary
        lines = result.stdout.strip().split('\n')
        summary_lines = [line for line in lines if 'passed' in line or 'failed' in line or 'error' in line]
        if summary_lines:
            print("\n📊 Test Summary:")
            for line in summary_lines[-3:]:  # Last few lines usually contain summary
                if '=====' in line or 'passed' in line:
                    print(f"   {line}")
        
        # Show slowest tests
        print("\n⏱️  Slowest Tests:")
        duration_lines = [line for line in lines if 'slowest' in line.lower() or ('PASSED' in line and 's' in line)]
        for line in duration_lines[-5:]:  # Show last 5 duration lines
            if 'PASSED' in line and '::' in line:
                print(f"   {line}")
    
    except subprocess.CalledProcessError as e:
        print("❌ SOME TESTS FAILED")
        failed_tests.append("Full Test Suite")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
    
    # Final summary
    print("\n" + "=" * 50)
    if failed_tests:
        print(f"❌ {len(failed_tests)} test suite(s) failed:")
        for test in failed_tests:
            print(f"   - {test}")
        sys.exit(1)
    else:
        print("🎉 All test suites passed successfully!")
        print("\n💡 To run specific tests:")
        print("   pytest tests/test_config.py::TestConfigManager::test_init")
        print("   pytest tests/ -k 'test_health_check'")
        print("   pytest tests/ --tb=long")

if __name__ == "__main__":
    main()