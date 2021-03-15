#!/usr/bin/env sh

set -o errexit
set -o pipefail
set -o nounset
set -o xtrace

pipenv run python manage.py migrate
# for django-admin page
pipenv run python manage.py collectstatic --noinput
pipenv run python manage.py runserver 127.0.0.1:8000
