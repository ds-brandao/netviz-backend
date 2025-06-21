#!/bin/bash

mkdir -p ssh-keys
ssh-keygen -t rsa -b 4096 -f ssh-keys/id_rsa -N "" -C "frr-router" -q
cp ssh-keys/id_rsa.pub ssh-keys/authorized_keys
echo "SSH keys generated" 