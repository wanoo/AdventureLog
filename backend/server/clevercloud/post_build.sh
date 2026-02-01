#!/bin/bash
set -e

echo "=== Clever Cloud Post-Build Hook ==="

# Change to APP_FOLDER
cd "${APP_HOME}/backend/server"
echo "Working directory: $(pwd)"

# Collectstatic
echo "Running collectstatic..."
python manage.py collectstatic --noinput

# Migrate
echo "Running migrations..."
python manage.py migrate --noinput

# Download countries data
echo "Downloading countries data..."
python manage.py download-countries || echo "Warning: download-countries failed, continuing..."

# Create superuser if environment variables are set
if [ -n "$DJANGO_ADMIN_USERNAME" ] && [ -n "$DJANGO_ADMIN_PASSWORD" ] && [ -n "$DJANGO_ADMIN_EMAIL" ]; then
  echo "Creating superuser..."
  python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
from allauth.account.models import EmailAddress
import os

User = get_user_model()
username = os.environ.get('DJANGO_ADMIN_USERNAME')
email = os.environ.get('DJANGO_ADMIN_EMAIL')
password = os.environ.get('DJANGO_ADMIN_PASSWORD')

if not User.objects.filter(username=username).exists():
    superuser = User.objects.create_superuser(
        username=username,
        email=email,
        password=password
    )
    print(f"Superuser {username} created successfully.")

    # Create EmailAddress for AllAuth
    EmailAddress.objects.create(
        user=superuser,
        email=email,
        verified=True,
        primary=True
    )
    print("EmailAddress object created successfully for AllAuth.")
else:
    # Update password if user exists
    superuser = User.objects.get(username=username)
    superuser.set_password(password)
    superuser.email = email
    superuser.is_staff = True
    superuser.is_superuser = True
    superuser.save()
    print(f"Superuser {username} password updated.")
EOF
fi

echo "=== Post-Build Hook Complete ==="
