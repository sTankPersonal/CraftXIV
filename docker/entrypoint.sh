#!/usr/bin/env bash
set -euo pipefail

flask db upgrade

exec gunicorn --bind 0.0.0.0:5000 app.wsgi:app
