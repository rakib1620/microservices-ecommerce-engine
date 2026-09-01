#!/bin/sh
set -e

# Inject the runtime API_URL into index.html before starting nginx.
# This allows the same image to be deployed to dev/staging/prod
# without rebuilding — a core production practice.
: "${API_URL:=http://localhost:8000}"

sed -i "s|__API_URL__|${API_URL}|g" /usr/share/nginx/html/index.html

exec nginx -g "daemon off;"
