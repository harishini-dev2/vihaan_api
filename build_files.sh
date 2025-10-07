#!/usr/bin/env bash
set -e

# install is usually handled by Vercel with requirements.txt, but running again is OK
pip install -r requirements.txt

# collect static files into STATIC_ROOT
python manage.py collectstatic --noinput

# optionally run migrations at build-time (only if DB accessible from Vercel)
python manage.py migrate --noinput || true
