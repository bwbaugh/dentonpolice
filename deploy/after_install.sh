#!/bin/bash
set -o errexit
set -o nounset
set -o pipefail

install_dir="/srv/dentonpolice"

# Using `pushd` and `popd` to play nice with the CloudDeploy agent.
pushd ${install_dir}

# Remove the old virtualenv, if it exists. This could potentially be
#   put in `application_stop.sh`, however it might be useful to keep
#   the virtualenv around for manual debugging.
rm -rf venv/

virtualenv --no-site-packages --python python3 venv
venv/bin/pip install -r requirements.txt

# TODO(bwbaugh|2015-04-19): Create this if needed in the app.
mkdir -p mugs

# Using `pushd` and `popd` to play nice with the CloudDeploy agent.
popd
