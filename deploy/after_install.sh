#!/bin/bash
set -o errexit
set -o nounset
set -o pipefail

install_dir="/srv/dentonpolice"
runit_sv_dir="/etc/sv"
application_name="arrestinfo"

# Using `pushd` and `popd` to play nice with the CloudDeploy agent.
pushd ${install_dir}

virtualenv --no-site-packages --python python3 venv
venv/bin/pip install -r requirements.txt

# TODO(bwbaugh|2015-04-19): Create this if needed in the app.
mkdir -p mugs

# Set up the application as a service.
# XXX: https://github.com/ddollar/foreman/issues/402
export HOME="/root"
foreman export \
  --app=${application_name} \
  --log=/var/log/${application_name} \
  --user=root \
  runit \
  ${runit_sv_dir}
unset HOME

# Using `pushd` and `popd` to play nice with the CloudDeploy agent.
popd
