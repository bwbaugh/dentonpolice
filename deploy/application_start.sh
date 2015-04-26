#!/bin/bash
set -o errexit
set -o nounset
set -o pipefail

runit_sv_dir="/etc/sv"
runit_service_dir="/etc/service"

ln -s ${runit_sv_dir}/arrestinfo-crawler-1 ${runit_service_dir}/arrestinfo-crawler-1
# Prevent a "unable to open supervise/ok: file does not exist" error.
sleep 5
sv start arrestinfo-crawler-1
