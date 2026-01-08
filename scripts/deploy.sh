#!/bin/bash
# Auto-deploy script for family-budget
# Checks for new commits on origin/main and deploys if found

set -e
cd ~/projects/family-budget

BRANCH="main"
if ! git show-ref --verify --quiet "refs/remotes/origin/$BRANCH"; then
    BRANCH="master"
fi

# Fetch latest from remote
git fetch origin "$BRANCH" --quiet

# Get current and remote commit
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse "origin/$BRANCH")

# Exit if already up to date
if [ "$LOCAL" = "$REMOTE" ]; then
    exit 0
fi

echo "[$(date)] New commits detected, deploying..."

# Pull and rebuild
git reset --hard "origin/$BRANCH"
export APP_VERSION=$(cat VERSION)
docker compose build --quiet --build-arg APP_VERSION="$APP_VERSION"
docker compose down
docker compose up -d

# Health check
sleep 3
if curl -sf http://localhost:8086/budget/login > /dev/null; then
    echo "[$(date)] ✅ Deploy successful: $(git log -1 --oneline)"
else
    echo "[$(date)] ❌ Health check failed!"
    docker compose logs --tail 10
    exit 1
fi
