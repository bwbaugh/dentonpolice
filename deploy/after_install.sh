#!/bin/bash
set -o errexit
set -o nounset
set -o pipefail

install_dir="/srv/dentonpolice"

# Remove the old virtualenv, if it exists. This could potentially be
#   put in `application_stop.sh`, however it might be useful to keep
#   the virtualenv around for manual debugging.
rm -rf ${install_dir}/venv/

virtualenv --no-site-packages --python python3 ${install_dir}/venv
${install_dir}/venv/bin/pip install -r ${install_dir}/requirements.txt

# TODO(bwbaugh|2015-04-19): Create this if needed in the app.
mkdir -p ${install_dir}/mugs
