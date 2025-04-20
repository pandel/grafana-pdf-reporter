#!/bin/sh

cd /usr/share/nginx/html
rm -f env-config.js
"/bin/sh" /generate_env-config.sh > ./env-config.js


