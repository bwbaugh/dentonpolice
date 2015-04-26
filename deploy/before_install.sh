#!/bin/bash
set -o errexit
set -o nounset
set -o pipefail

aptitude --assume-yes install ruby runit
gem install foreman
