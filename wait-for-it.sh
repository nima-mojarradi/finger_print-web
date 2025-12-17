#!/usr/bin/env bash
# Use this script to test if a given TCP host/port is available

set -e

TIMEOUT=15
QUIET=0
HOST=""
PORT=""

print_usage() {
    echo "Usage: wait-for-it.sh host:port [-t timeout] [-- command args]"
}

while [[ $# -gt 0 ]]
do
    case "$1" in
        *:* )
        HOST=$(echo $1 | cut -d: -f1)
        PORT=$(echo $1 | cut -d: -f2)
        shift
        ;;
        -t)
        TIMEOUT=$2
        shift 2
        ;;
        --)
        shift
        break
        ;;
        *)
        break
        ;;
    esac
done

if [ -z "$HOST" ] || [ -z "$PORT" ]; then
    print_usage
    exit 1
fi

echo "Waiting for $HOST:$PORT (timeout: $TIMEOUT)..."

for i in $(seq $TIMEOUT) ; do
    nc -z "$HOST" "$PORT" >/dev/null 2>&1 && break
    sleep 1
done

nc -z "$HOST" "$PORT" >/dev/null 2>&1
STATUS=$?

if [ $STATUS -ne 0 ]; then
    echo "Timeout waiting for $HOST:$PORT"
    exit 1
fi

echo "$HOST:$PORT is available"

if [ $# -gt 0 ]; then
    exec "$@"
fi