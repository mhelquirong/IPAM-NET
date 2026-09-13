#!/usr/bin/env bash
set -euo pipefail

cd /opt/netbox/netbox

# The compose file bind-mounts code_branding/ over the copy baked into the image
# so the plugin can be edited without a rebuild. That replaces the build-time
# egg-info, so re-assert the editable install if the import no longer resolves.
if ! python -c "import netbox_code_branding" 2>/dev/null; then
  echo "Re-installing netbox_code_branding (bind mount replaced the build-time install)…"
  pip install -e /opt/netbox/code_branding --no-deps -q
fi

echo "Waiting for PostgreSQL…"
until python -c "
import os, sys, psycopg
try:
    psycopg.connect(
        host=os.environ['DB_HOST'], dbname=os.environ['DB_NAME'],
        user=os.environ['DB_USER'], password=os.environ['DB_PASSWORD'],
    ).close()
except Exception:
    sys.exit(1)
" 2>/dev/null; do
  sleep 1
done

echo "Applying migrations…"
python manage.py migrate --no-input

echo "Collecting static files…"
python manage.py collectstatic --no-input --clear >/dev/null

if [[ -n "${SUPERUSER_NAME:-}" ]]; then
  echo "Ensuring superuser '${SUPERUSER_NAME}' exists…"
  python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
u, created = User.objects.get_or_create(
    username='${SUPERUSER_NAME}',
    defaults={'is_superuser': True, 'is_staff': True, 'email': '${SUPERUSER_EMAIL:-admin@code.sa}'},
)
u.is_superuser = u.is_staff = True
u.set_password('${SUPERUSER_PASSWORD}')
u.save()
print('superuser created' if created else 'superuser updated')
"
fi

echo "Starting NetBox on :8000"
exec python manage.py runserver 0.0.0.0:8000 --insecure
