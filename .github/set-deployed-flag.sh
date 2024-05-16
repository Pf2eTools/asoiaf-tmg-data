#!/bin/bash

set -e

# Set the IS_DEPLOYED variable for production.
sed -i 's/IS_DEPLOYED\s*=\s*undefined/IS_DEPLOYED='"true"'/g' web/js/utils.js
