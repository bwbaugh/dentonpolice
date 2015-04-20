#!/bin/bash
set -o errexit
set -o nounset
set -o pipefail

install_dir="/srv/dentonpolice"
log_location="/var/log/dentonpolice"

# Using `pushd` and `popd` to play nice with the CloudDeploy agent.
pushd ${install_dir}

# TODO(bwbaugh|2015-04-19): Configure proper logging.
mkdir -p ${log_location}
${install_dir}/venv/bin/python -m dentonpolice \
  >> ${log_location}/dentonpolice_stdout.log \
  2>> ${log_location}/dentonpolice_stderr.log \
  < /dev/null &

# Using `pushd` and `popd` to play nice with the CloudDeploy agent.
popd
