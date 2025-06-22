#!/usr/bin/env python3

import os
import sys
import subprocess
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from config.ingestion_config import config_manager

def main():
    required_vars = [
        "github.token",
        "github.username"
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
    
    config = config_manager.get_mcp_server_config()
    
    print("Starting MCP Server...")
    print(f"Server will run on {config['host']}:{config['port']}")
    print(f"GitHub Repository: {config_manager.get('github.username')}/{config_manager.get('github.repository')}")
    
    try:
        subprocess.run([
            "uvicorn", 
            "src.mcp_server.server:app",
            "--host", config['host'],
            "--port", str(config['port']),
            "--reload"
        ], check=True)
    except KeyboardInterrupt:
        print("\nShutting down MCP Server...")
    except subprocess.CalledProcessError as e:
        print(f"Error starting MCP server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()