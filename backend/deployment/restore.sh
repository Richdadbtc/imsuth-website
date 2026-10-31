#!/usr/bin/env bash
set -euo pipefail

: "${ALLOW_PAYPOINT_RESTORE:?Set ALLOW_PAYPOINT_RESTORE to the exact value YES after approval}"
: "${POSTGRES_DB:?POSTGRES_DB is required}"
: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${POSTGRES_HOST:?POSTGRES_HOST is required}"
: "${RESTORE_FILE:?RESTORE_FILE is required}"

if [[ "${ALLOW_PAYPOINT_RESTORE}" != "YES" ]]; then
    echo "Restore not authorized. Set ALLOW_PAYPOINT_RESTORE=YES only in an approved restore window." >&2
    exit 1
fi
if [[ ! -f "${RESTORE_FILE}" || ! -f "${RESTORE_FILE}.sha256" ]]; then
    echo "Restore file or checksum is missing." >&2
    exit 1
fi

if command -v sha256sum >/dev/null 2>&1; then
    sha256sum --check "${RESTORE_FILE}.sha256"
else
    shasum -a 256 --check "${RESTORE_FILE}.sha256"
fi
pg_restore --clean --if-exists --no-owner --no-acl --single-transaction --host="${POSTGRES_HOST}" --username="${POSTGRES_USER}" --dbname="${POSTGRES_DB}" "${RESTORE_FILE}"
echo "Restore completed. Run migrations and the approved validation checklist before reopening access."
