#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "=== 배포 시작: $(date) ==="

# 현재 커밋 기록
BEFORE=$(git rev-parse HEAD)

git fetch origin main
git reset --hard origin/main

AFTER=$(git rev-parse HEAD)

# Requirements/Dockerfile 변경 확인
if git diff --name-only $BEFORE $AFTER | grep -qE "app/requirements.txt|app/Dockerfile"; then
    echo ">> Requirements/Dockerfile 변경: 재빌드"
    docker compose -f docker-compose.yml up -d --build
else
    echo ">> 컨테이너 재시작"
    docker compose -f docker-compose.yml restart printqueue
fi

docker compose -f docker-compose.yml ps
echo "=== 배포 완료: $(date) ==="