#!/usr/bin/env bash
# /srv/xiaoyi/bin/deploy_from_github.sh

set -euo pipefail

PROJECT_ROOT="/var/www/zyd-bot"
BACKUP_SCRIPT="/srv/xiaoyi/bin/backup.sh"
SERVICE_NAME="zyd-bot"
ENV_FILE="${PROJECT_ROOT}/backend/.env"
DB_FILE="${PROJECT_ROOT}/backend/data/prod.db"
TIMESTAMP="$(date +"%Y%m%d_%H%M%S")"
# Comma-separated tool directory names to skip during sub-tool builds.
# Default is empty to build all smart tools.
SKIP_SUBTOOLS="${SKIP_SUBTOOLS:-}"

echo ">>> [1/11] Starting deploy (${TIMESTAMP})..."

echo ">>> [2/11] Running backup..."
if [ -f "$BACKUP_SCRIPT" ]; then
    bash "$BACKUP_SCRIPT"
else
    echo "WARNING: backup script not found: $BACKUP_SCRIPT"
fi

echo ">>> [3/11] Snapshotting private files..."
mkdir -p "${PROJECT_ROOT}/backend/data/snapshots"
[ -f "$ENV_FILE" ] && cp "$ENV_FILE" "${PROJECT_ROOT}/backend/data/snapshots/.env.${TIMESTAMP}.bak"
[ -f "$DB_FILE" ] && cp "$DB_FILE" "${PROJECT_ROOT}/backend/data/snapshots/prod.db.${TIMESTAMP}.bak"

cd "$PROJECT_ROOT"
CURRENT_COMMIT="$(git rev-parse HEAD)"
echo "$CURRENT_COMMIT" > "${PROJECT_ROOT}/.last_deployed_commit"
echo ">>> [4/11] Recorded current commit: $CURRENT_COMMIT"

echo ">>> [5/11] Fetching latest code from origin/main..."
git fetch origin main
if ! git pull --ff-only origin main; then
    echo "ERROR: git pull failed. Clean up local server changes first."
    exit 1
fi

echo ">>> [6/11] Installing backend dependencies..."
cd "${PROJECT_ROOT}/backend"
if [ -d "venv" ]; then
    # shellcheck disable=SC1091
    source venv/bin/activate
fi
pip install -r requirements.txt

echo ">>> [7/11] Building frontend..."
cd "${PROJECT_ROOT}/frontend"
npm install
npm run build

echo ">>> [7.1/11] Building sub-tools..."
if ! command -v find >/dev/null 2>&1; then
    echo "ERROR: find command is required but not available."
    exit 1
fi

should_skip_tool() {
    local tool_name="$1"
    local item
    IFS=',' read -r -a skip_list <<< "$SKIP_SUBTOOLS"
    for item in "${skip_list[@]}"; do
        item="$(echo "$item" | xargs)"
        if [ -n "$item" ] && [ "$item" = "$tool_name" ]; then
            return 0
        fi
    done
    return 1
}

while IFS= read -r -d '' pkg; do
    tool_path="$(dirname "$pkg")"
    tool_name="$(basename "$tool_path")"
    if should_skip_tool "$tool_name"; then
        echo "    Skipping tool: $tool_name"
        continue
    fi
    echo "    Building tool: $tool_name"
    (
        cd "$tool_path"
        npm install --no-audit --no-fund
        npm run build
    )
done < <(
    find "$PROJECT_ROOT" \
        \( \
            -path "$PROJECT_ROOT/backend" -o \
            -path "$PROJECT_ROOT/frontend" -o \
            -path "$PROJECT_ROOT/frontend-uniapp" -o \
            -path "$PROJECT_ROOT/frontend-uniapp-old-webpack" \
        \) -prune -o \
        -name "package.json" -not -path "*/node_modules/*" -print0
)

cd "$PROJECT_ROOT"

echo ">>> [8/11] Restarting service: $SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

echo ">>> [9/11] Validating nginx config..."
sudo nginx -t

echo ">>> [10/11] Reloading nginx..."
sudo systemctl reload nginx

echo ">>> [11/11] Running health checks..."
sleep 3
BACKEND_HEALTH="$(curl -s http://127.0.0.1:8000/)"
FRONTEND_HEALTH="$(curl -kIs https://127.0.0.1/ | head -n 1 || true)"

echo "Backend (8000): $BACKEND_HEALTH"
echo "Frontend (HTTPS): $FRONTEND_HEALTH"

echo "=========================================="
echo "Deploy finished at commit $(git rev-parse --short HEAD)"
echo "Finished at: $(date)"
echo "=========================================="
