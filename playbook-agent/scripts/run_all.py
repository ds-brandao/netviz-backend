#!/usr/bin/env python3

import os
import sys
import subprocess
import signal
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

sys.path.append(str(Path(__file__).parent.parent))

from config.ingestion_config import config_manager

def run_mcp_server():
    config = config_manager.get_mcp_server_config()
    
    print(f"Starting MCP Server on {config['host']}:{config['port']}")
    
    process = subprocess.Popen([
        "uvicorn", 
        "src.mcp_server.server:app",
        "--host", config['host'],
        "--port", str(config['port']),
        "--reload"
    ])
    
    return process

def run_agent():
    time.sleep(5)  # Wait for MCP server to start
    
    config = config_manager.get_api_config()
    
    print(f"Starting Playbook Agent on {config['host']}:{config['port']}")
    
    process = subprocess.Popen([
        "uvicorn", 
        "src.agent.api:app",
        "--host", config['host'],
        "--port", str(config['port']),
        "--reload"
    ])
    
    return process

def main():
    required_vars = [
        "llm.api_key",
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
    
    print("Starting Playbook Agent System...")
    print("This will start both the MCP Server and the Agent API")
    
    mcp_process = None
    agent_process = None
    
    try:
        mcp_process = run_mcp_server()
        agent_process = run_agent()
        
        print("\nBoth services are running. Press Ctrl+C to stop.")
        
        while True:
            if mcp_process.poll() is not None:
                print("MCP Server has stopped unexpectedly")
                break
            if agent_process.poll() is not None:
                print("Agent has stopped unexpectedly")
                break
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\nShutting down services...")
    
    finally:
        if mcp_process:
            mcp_process.terminate()
            mcp_process.wait()
        if agent_process:
            agent_process.terminate()
            agent_process.wait()
        
        print("All services stopped.")

if __name__ == "__main__":
    main()