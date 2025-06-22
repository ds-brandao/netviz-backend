#!/usr/bin/env python3

import os
import sys
import subprocess
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from config.ingestion_config import config_manager

def main():
    required_vars = [
        "llm.api_key",
        "mcp_server.url"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not config_manager.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("Error: Missing required configuration variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease set these variables in your config/secrets.yaml file or environment.")
        sys.exit(1)
    
    config = config_manager.get_api_config()
    
    print("Starting Playbook Agent...")
    print(f"Server will run on {config['host']}:{config['port']}")
    print(f"MCP Server URL: {config_manager.get('mcp_server.url')}")
    print(f"Max Iterations: {config_manager.get('agent.max_iterations')}")
    
    try:
        subprocess.run([
            "uvicorn", 
            "src.agent.api:app",
            "--host", config['host'],
            "--port", str(config['port']),
            "--reload" if config['reload'] else "--no-reload"
        ], check=True)
    except KeyboardInterrupt:
        print("\nShutting down Playbook Agent...")
    except subprocess.CalledProcessError as e:
        print(f"Error starting agent: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()