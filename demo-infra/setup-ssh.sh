#!/bin/bash

rm -rf test-ssh-keys/*
mkdir -p test-ssh-keys
ssh-keygen -t rsa -b 4096 -f test-ssh-keys/id_rsa -N "" -C "network-devices" -q
cp test-ssh-keys/id_rsa.pub test-ssh-keys/authorized_keys
echo "SSH keys generated" 