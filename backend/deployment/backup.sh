#!/usr/bin/env bash
set -euo pipefail

: "${POSTGRES_DB:?POSTGRES_DB is required}"
: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${POSTGRES_HOST:?POSTGRES_HOST is required}"
: "${BACKUP_DIRECTORY:?BACKUP_DIRECTORY is required}"

umask 077
mkdir -p "${BACKUP_DIRECTORY}"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
target="${BACKUP_DIRECTORY%/}/imsuth-paypoint-${timestamp}.dump"

pg_dump --format=custom --no-owner --no-acl --host="${POSTGRES_HOST}" --username="${POSTGRES_USER}" --dbname="${POSTGRES_DB}" --file="${target}"
if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "${target}" > "${target}.sha256"
else
    shasum -a 256 "${target}" > "${target}.sha256"
fi
echo "Backup created: ${target}"
