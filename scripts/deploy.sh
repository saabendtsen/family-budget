#!/bin/bash
set -e

cd ~/projects/family-budget

echo "=== Pulling latest code ==="
git fetch origin master
git reset --hard origin/master

echo "=== Building Docker image ==="
docker compose build

echo "=== Restarting container ==="
docker compose down
docker compose up -d

echo "=== Waiting for startup ==="
sleep 3

echo "=== Health check ==="
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8086/budget/login | grep -q "200"; then
    echo "✅ Deploy successful!"
else
    echo "❌ Health check failed!"
    docker compose logs --tail 20
    exit 1
fi
