#!/usr/bin/env sh

set -o errexit
set -o nounset
set -o xtrace

mkdir -p /dist_django
cp -r /dist_django/* /usr/share/nginx/html/static/

nginx -g 'daemon off;'
