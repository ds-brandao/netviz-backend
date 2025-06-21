# Self-Healing Network

A self-healing network system that uses AI and Ansible to detect, roll back, and adjust network configurations.

## Stack
- Python
- FastAPI
- Ansible
- OpenSearch
- Docker
- React (UI)
- TypeScript

## Devices
- Simulated with frrouting in Docker

## Services
- collective-hackathon: 192.168.0.130
- collective-ansible: 192.168.0.131
- collective-opensearch: 192.168.0.132

## Goals
- Monitor logs via OpenSearch
- Version control of configs
- Event-driven network management with AI
