#!/bin/bash
# Auto-deploy script for family-budget
# Checks for new commits on origin/main and deploys if found

set -e

PROJECT_DIR=~/projects/family-budget
cd "$PROJECT_DIR"

# Backup database before deploy to prevent data loss
backup_database() {
    local DATA_DIR="$PROJECT_DIR/data"
    local DB_FILE="$DATA_DIR/budget.db"
    local BACKUP_FILE="$DATA_DIR/budget.db.backup-$(date +%Y%m%d-%H%M%S)"
    local MAX_BACKUPS=10

    # Check if database exists
    if [ ! -f "$DB_FILE" ]; then
        echo "No database to backup"
        return 0
    fi

    # Create backup
    echo "Creating backup: $BACKUP_FILE"
    cp "$DB_FILE" "$BACKUP_FILE" || {
        echo "ERROR: Backup failed!"
        return 1
    }

    # Cleanup old backups (keep last 10)
    echo "Cleaning old backups (keeping last $MAX_BACKUPS)..."
    ls -t "$DATA_DIR"/budget.db.backup-* 2>/dev/null | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm

    echo "Backup complete"
    return 0
}

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

# Backup database before taking down containers
backup_database || {
    echo "[$(date)] ❌ Backup failed - aborting deploy"
    exit 1
}

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
