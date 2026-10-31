#!/bin/sh
set -eu
# Every application process checks deployment settings before serving or consuming jobs.
# This does not run migrations, collect assets or change operational data.
if [ "${DJANGO_ENV:-development}" = "production" ] || [ "${DJANGO_ENV:-development}" = "staging" ]; then
    python manage.py check --deploy --fail-level ERROR
fi
exec "$@"
