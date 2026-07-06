#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "=== 배포 시작: $(date) ==="
docker compose -f docker-compose.yml up -d --build
docker compose -f docker-compose.yml ps
docker compose -f docker-compose.yml logs --tail 30 printqueue
echo "=== 배포 완료: $(date) ==="