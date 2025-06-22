# Ansible Hosts Configuration Guide

This document describes the available hosts configured for Ansible automation in our network infrastructure.

## Host Groups

### Router Group
- **solo_r1**
  - Host: 192.168.0.130
  - SSH Port: 7777
  - User: root
  - Authentication: Password-based (ansible123)

### Switch Group
- **solo_sw1**
  - Host: 192.168.0.130
  - SSH Port: 7771
  - User: root
  - Authentication: Password-based (ansible123)

- **solo_sw2**
  - Host: 192.168.0.130
  - SSH Port: 7778
  - User: root
  - Authentication: Password-based (ansible123)

### Server Group
- **solo_ub**
  - Host: 192.168.0.130
  - SSH Port: 7780
  - User: root
  - Authentication: Password-based (ansible123)

### Infrastructure Group
This group contains all infrastructure devices for collective operations:

- **infra_r1** (Router)
  - Host: 192.168.0.130
  - SSH Port: 7777
  - User: root
  - Authentication: Password-based (ansible123)

- **infra_sw1** (Switch)
  - Host: 192.168.0.130
  - SSH Port: 7771
  - User: root
  - Authentication: Password-based (ansible123)

- **infra_sw2** (Switch)
  - Host: 192.168.0.130
  - SSH Port: 7778
  - User: root
  - Authentication: Password-based (ansible123)

## Usage Notes
- All hosts are configured on the same management IP (192.168.0.130)
- Different SSH ports are used to distinguish between devices
- Password authentication is used across all devices
- Hosts are grouped logically by device type and role
- The 'infra' group provides collective access to all infrastructure devices
