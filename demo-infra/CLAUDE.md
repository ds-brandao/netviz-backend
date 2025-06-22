# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NetViz Backend is a self-healing network system that uses AI and Ansible to detect, roll back, and adjust network configurations. This demo-infra directory contains Docker-based infrastructure for simulating network devices using FRRouting (FRR).

## Common Development Commands

### Infrastructure Management
- **Setup**: `./setup-ssh.sh` - Generate SSH keys for container access
- **Start**: `docker-compose up -d` - Start the FRR router container
- **Test**: `./frr-router/test-frr-w-test-ssh-keys.sh` - Run comprehensive infrastructure tests
- **Cleanup**: `./cleanup.sh` - Remove containers, volumes, and generated SSH keys
- **Access Router**: `ssh -i test-ssh-keys/id_rsa -p 7777 frruser@localhost`

### Docker Commands
- **View Logs**: `docker-compose logs -f frr-router` - Follow container logs
- **Restart**: `docker-compose restart` - Restart services
- **Stop**: `docker-compose down` - Stop services

## Architecture

### Core Components
- **FRR Router Container**: Ubuntu 22.04 with FRRouting, SSH server, and Ansible
- **Docker Compose**: Single-service setup exposing SSH on port 7777
- **SSH Authentication**: Key-based access with generated RSA keys
- **Network Configuration**: FRR with BGP/OSPF capabilities

### Technology Stack
- **Backend**: Python, FastAPI (planned)
- **Automation**: Ansible
- **Monitoring**: OpenSearch (planned)
- **Network Simulation**: FRRouting in Docker
- **Frontend**: React with TypeScript (planned)

### Service Architecture
The broader system includes:
- collective-hackathon: 192.168.0.130
- collective-ansible: 192.168.0.131  
- collective-opensearch: 192.168.0.132

## File Structure

### Key Files
- `docker-compose.yml`: Infrastructure definition
- `frr-router/Dockerfile`: Container build configuration
- `frr-router/frr.conf`: FRR routing configuration
- `frr-router/entrypoint.sh`: Container startup script
- `setup-ssh.sh`: SSH key generation
- `cleanup.sh`: Infrastructure cleanup

### Generated Files (Git Ignored)
- `test-ssh-keys/`: SSH keys for container access
- Container volumes and networks

## Development Workflow

1. Generate SSH keys: `./setup-ssh.sh`
2. Start infrastructure: `docker-compose up -d`
3. Validate setup: `./frr-router/test-frr-w-test-ssh-keys.sh`
4. Access router for configuration: `ssh -i test-ssh-keys/id_rsa -p 7777 frruser@localhost`
5. Clean up when done: `./cleanup.sh`

## Network Configuration

The FRR router is configured with:
- IP forwarding enabled
- BGP AS 65001 (example configuration available)
- OSPF area 0.0.0.0 (example configuration available)
- Container network interface on eth0

## Security

- SSH key-based authentication only
- Non-root user (frruser) with sudo privileges
- Proper file permissions for SSH and FRR configurations
- Test SSH keys excluded from version control