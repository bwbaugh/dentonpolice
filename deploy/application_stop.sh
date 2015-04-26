#!/bin/bash
set -o errexit
set -o nounset
set -o pipefail

install_dir="/srv/dentonpolice"
runit_sv_dir="/etc/sv"
runit_service_dir="/etc/service"

sv stop arrestinfo-crawler-1
unlink ${runit_service_dir}/arrestinfo-crawler-1
sleep 5
rm -rf ${runit_sv_dir}/arrestinfo-crawler-1
sleep 5

# Using `pushd` and `popd` to play nice with the CloudDeploy agent.
pushd ${install_dir}

rm -rf venv/

# Using `pushd` and `popd` to play nice with the CloudDeploy agent.
popd
