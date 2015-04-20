#!/bin/bash
set -o errexit
set -o nounset
set -o pipefail

# TODO(bwbaugh|2015-04-19): Better signal handling in the app.
# Simulate a ^C. It's okay if the program isn't running.
# XXX: Using `SIGTERM` since `SIGINT` wasn't working.
pkill --full --exact -SIGTERM '/srv/dentonpolice/venv/bin/python -m dentonpolice' || true
