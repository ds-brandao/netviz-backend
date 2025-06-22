# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **network infrastructure demo environment** that simulates a multi-tier network topology using Docker containers. It's part of the larger "Self-Healing Network" project that uses AI and Ansible for automated network configuration management.

We want to create the following network topology:

```mermaid
graph LR
    Client["Client<br/>(accessing app)<br/>192.168.10.10"]
    Switch1["Switch 1<br/>(Layer 2)"]
    Router["Router<br/>(FRR)<br/>192.168.10.254 | 192.168.30.254"]
    Switch2["Switch 2<br/>(Layer 2)"]
    Server["Server<br/>(HTTP app)<br/>192.168.30.10:8080"]
    
    Client --> Switch1
    Switch1 --> Router
    Router --> Switch2
    Switch2 --> Server
    
    style Client fill:#e1f5e1,stroke:#4caf50,stroke-width:2px
    style Server fill:#e3f2fd,stroke:#2196f3,stroke-width:2px
    style Router fill:#fff3e0,stroke:#ff9800,stroke-width:2px
    style Switch1 fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px
    style Switch2 fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px
```

the goal here is to create a network where the client can access the server via the router and switches.

## Testing

we need to have a e2e testing framework to test the network.