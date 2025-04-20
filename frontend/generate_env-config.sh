#!/bin/sh

########################################
# Create a file based on the environment variables
# given by the dockerc run -e parameter
# - VITE_API_URL
########################################
cat <<EOF
window.VITE_API_URL="${VITE_API_URL}"
EOF
