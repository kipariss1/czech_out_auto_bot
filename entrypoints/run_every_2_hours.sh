#!/bin/sh
set -eu

INTERVAL_SECONDS="${INTERVAL_SECONDS:-7200}"

if [ "$#" -eq 0 ]; then
  echo "Usage: run_every_2_hours.sh <command> [args...]"
  exit 1
fi

while true; do
  "$@"
  sleep "$INTERVAL_SECONDS"
done
