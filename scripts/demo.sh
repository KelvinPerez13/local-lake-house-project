#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
if [ ! -f .env ]; then
    echo 'Crie .env a partir de .env.example antes de executar.' >&2
    exit 1
fi
docker compose up -d --build
docker compose --profile jobs run --build --rm ingestion
docker compose --profile jobs run --build --rm spark
docker compose --profile jobs run --rm spark python -m tests.smoke
