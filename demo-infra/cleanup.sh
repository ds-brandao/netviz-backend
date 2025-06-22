#!/bin/bash

echo "🧹 Cleaning up demo infrastructure..."

# Stop and remove all containers, networks, and volumes defined in docker-compose.yml
echo "📦 Stopping containers and removing everything..."
docker-compose down --volumes --remove-orphans --rmi all

# Clean up SSH keys
echo "🔑 Cleaning up SSH keys..."
rm -rf test-ssh-keys/*

echo "✨ Cleanup completed!"
echo "💡 To set up again: ./setup-ssh.sh && docker-compose up -d" 