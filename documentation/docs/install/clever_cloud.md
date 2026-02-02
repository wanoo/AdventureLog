# Clever Cloud

Clever Cloud is a European PaaS (Platform as a Service) that allows you to deploy applications without managing servers. This guide will walk you through deploying AdventureLog on Clever Cloud.

## Prerequisites

- A [Clever Cloud](https://www.clever-cloud.com/) account
- [Clever Cloud CLI](https://www.clever-cloud.com/doc/cli/) installed on your machine
- Git installed on your machine

### Installing Clever Cloud CLI

```bash
npm install -g clever-tools
```

Then login to your account:

```bash
clever login
```

## Architecture Overview

AdventureLog on Clever Cloud requires:

| Component | Type | Recommended Size | Purpose |
|-----------|------|------------------|---------|
| Frontend | Node.js | **M** (2GB RAM) | SvelteKit application |
| Backend | Python | **XS** (512MB RAM) | Django REST API |
| Database | PostgreSQL Add-on | S or M | Data storage |
| Cache | Redis Add-on | S | Session & caching |
| Storage | FS Bucket Add-on | - | Media files |
| Email | Mailpace Add-on | - | Transactional emails |

::: warning Instance Sizes
The frontend **requires at least M size** (2GB RAM) for the build process. Using smaller instances (XS or S) will cause Out of Memory (OOM) errors during the Vite/SvelteKit build.
:::

## Step 1: Clone the Repository

```bash
git clone https://github.com/seanmorley15/AdventureLog.git
cd AdventureLog
```

## Step 2: Create the Applications

### Create the Backend Application (Python)

```bash
clever create --type python adventurelog-backend
```

### Create the Frontend Application (Node.js)

```bash
clever create --type node adventurelog-frontend
```

### Link Both Applications

After creating, link them to your local repository:

```bash
clever link adventurelog-backend --alias adventurelog-backend
clever link adventurelog-frontend --alias adventurelog-frontend
```

## Step 3: Create Add-ons

### PostgreSQL Database

```bash
clever addon create postgresql-addon adventurelog-postgres --plan s_sml --link adventurelog-backend
```

### Redis Cache

```bash
clever addon create redis-addon adventurelog-redis --plan s_mono --link adventurelog-backend
```

### FS Bucket for Media Storage

```bash
clever addon create fs-bucket-addon adventurelog-media --link adventurelog-backend
```

### Mailpace for Emails (Optional)

```bash
clever addon create mailpace-addon adventurelog-email --link adventurelog-backend
```

## Step 4: Configure Instance Sizes

### Scale the Frontend (Required)

The frontend build requires more memory. **This is mandatory to avoid OOM errors**:

```bash
clever scale --alias adventurelog-frontend --flavor M
```

### Backend Size (Optional)

The backend runs fine on XS, but you can scale if needed:

```bash
clever scale --alias adventurelog-backend --flavor XS
```

## Step 5: Configure Environment Variables

### Get Your Application URLs

First, get the default URLs assigned by Clever Cloud:

```bash
clever domain --alias adventurelog-backend
clever domain --alias adventurelog-frontend
```

Note down these URLs (format: `app-xxxxxxxx.cleverapps.io`).

### Backend Environment Variables

```bash
# Application folder
clever env set --alias adventurelog-backend APP_FOLDER "backend/server"

# Post-build hook for migrations and setup
clever env set --alias adventurelog-backend CC_POST_BUILD_HOOK "backend/server/clevercloud/post_build.sh"

# Python configuration
clever env set --alias adventurelog-backend CC_PYTHON_VERSION "3"
clever env set --alias adventurelog-backend CC_PYTHON_MODULE "main.wsgi:application"

# Django configuration
clever env set --alias adventurelog-backend SECRET_KEY "$(openssl rand -base64 32)"
clever env set --alias adventurelog-backend DEBUG "False"
clever env set --alias adventurelog-backend DISABLE_REGISTRATION "False"

# Admin user (created automatically on first deploy)
clever env set --alias adventurelog-backend DJANGO_ADMIN_USERNAME "admin"
clever env set --alias adventurelog-backend DJANGO_ADMIN_PASSWORD "your-secure-password"
clever env set --alias adventurelog-backend DJANGO_ADMIN_EMAIL "admin@example.com"

# URLs (replace with your actual Clever Cloud app URLs)
clever env set --alias adventurelog-backend PUBLIC_URL "https://app-BACKEND-ID.cleverapps.io"
clever env set --alias adventurelog-backend FRONTEND_URL "https://app-FRONTEND-ID.cleverapps.io"
clever env set --alias adventurelog-backend CSRF_TRUSTED_ORIGINS "https://app-FRONTEND-ID.cleverapps.io,https://app-BACKEND-ID.cleverapps.io"
```

### Database Configuration

The PostgreSQL add-on automatically sets `POSTGRESQL_ADDON_*` variables. Map them to Django's expected format:

```bash
# Get the PostgreSQL credentials
clever env --alias adventurelog-backend | grep POSTGRESQL

# Set the PG* variables using the values from above
clever env set --alias adventurelog-backend PGHOST "your-postgresql-host"
clever env set --alias adventurelog-backend PGDATABASE "your-database-name"
clever env set --alias adventurelog-backend PGUSER "your-database-user"
clever env set --alias adventurelog-backend PGPASSWORD "your-database-password"
clever env set --alias adventurelog-backend PGPORT "your-database-port"
```

### Frontend Environment Variables

```bash
# Application folder
clever env set --alias adventurelog-frontend APP_FOLDER "frontend"

# Node.js configuration
clever env set --alias adventurelog-frontend CC_NODE_BUILD_TOOL "pnpm"
clever env set --alias adventurelog-frontend CC_NODE_DEV_DEPENDENCIES "install"
clever env set --alias adventurelog-frontend CC_PRE_RUN_HOOK "cd frontend && pnpm run build"
clever env set --alias adventurelog-frontend CC_RUN_COMMAND "cd frontend && node build"

# Frontend configuration (replace with your actual URLs)
clever env set --alias adventurelog-frontend ORIGIN "https://app-FRONTEND-ID.cleverapps.io"
clever env set --alias adventurelog-frontend PUBLIC_SERVER_URL "https://app-BACKEND-ID.cleverapps.io"
clever env set --alias adventurelog-frontend BODY_SIZE_LIMIT "Infinity"
```

## Step 6: Configure Email with Mailpace

If you created the Mailpace add-on, configure the email settings:

```bash
# Get Mailpace credentials
clever env --alias adventurelog-backend | grep MAILPACE

# Configure Django email settings
clever env set --alias adventurelog-backend EMAIL_BACKEND "email"
clever env set --alias adventurelog-backend EMAIL_HOST "smtp.mailpace.com"
clever env set --alias adventurelog-backend EMAIL_PORT "587"
clever env set --alias adventurelog-backend EMAIL_USE_TLS "True"
clever env set --alias adventurelog-backend EMAIL_USE_SSL "False"
clever env set --alias adventurelog-backend EMAIL_HOST_USER "your-mailpace-api-token"
clever env set --alias adventurelog-backend EMAIL_HOST_PASSWORD "your-mailpace-api-token"
clever env set --alias adventurelog-backend DEFAULT_FROM_EMAIL "noreply@your-verified-domain.com"
```

::: tip Mailpace Setup
1. After creating the add-on, access the Mailpace dashboard from Clever Cloud console
2. Verify your sending domain (add DNS records)
3. Get your API token from the Mailpace dashboard
4. Use the API token for both `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD`
:::

## Step 7: Deploy

### Deploy the Backend First

```bash
clever deploy --alias adventurelog-backend
```

Wait for the deployment to complete. The post_build hook will:
- Run database migrations
- Download country/region data
- Create the admin superuser

### Deploy the Frontend

```bash
clever deploy --alias adventurelog-frontend
```

::: warning Build Time
The frontend build may take several minutes due to the SvelteKit compilation process. This is normal.
:::

## Step 8: Verify Deployment

Check the status of your applications:

```bash
clever status --alias adventurelog-backend
clever status --alias adventurelog-frontend
```

View logs if needed:

```bash
clever logs --alias adventurelog-backend
clever logs --alias adventurelog-frontend
```

## Accessing the Application

| URL | Purpose |
|-----|---------|
| `https://app-FRONTEND-ID.cleverapps.io` | Main application |
| `https://app-BACKEND-ID.cleverapps.io/api` | REST API |
| `https://app-BACKEND-ID.cleverapps.io/admin` | Django Admin Panel |

### Admin Panel Login

To access the Django admin panel:

1. Go to `https://app-BACKEND-ID.cleverapps.io/accounts/login/`
2. Login with your admin credentials
3. Navigate to `https://app-BACKEND-ID.cleverapps.io/admin/`

::: tip
Django-allauth handles authentication. You must login via `/accounts/login/` first, then access `/admin/`.
:::

## Troubleshooting

### Frontend Build Fails (OOM)

**Symptom**: Build hangs and eventually fails, or logs show the process was killed.

**Solution**: Scale to a larger instance:

```bash
clever scale --alias adventurelog-frontend --flavor M
clever restart --alias adventurelog-frontend --without-cache
```

### "No Country Data Available"

**Symptom**: Message saying "No country data available - Please check the documentation for updating regional data."

**Solution**: The `media` folder wasn't created or download failed. Redeploy:

```bash
clever restart --alias adventurelog-backend --without-cache
```

### Admin Password Not Working

**Symptom**: Can't login to admin after changing `DJANGO_ADMIN_PASSWORD`.

**Solution**: Environment variable changes require rebuilding to run the post_build hook:

```bash
clever restart --alias adventurelog-backend --without-cache
```

### CSRF Errors

**Symptom**: Form submissions fail with CSRF errors.

**Solution**: Ensure `CSRF_TRUSTED_ORIGINS` includes both URLs:

```bash
clever env set --alias adventurelog-backend CSRF_TRUSTED_ORIGINS "https://frontend-url.cleverapps.io,https://backend-url.cleverapps.io"
clever restart --alias adventurelog-backend
```

### Media Files Not Loading (Images, Flags)

**Symptom**: Images like country flags or uploaded media don't load.

**Explanation**: On Clever Cloud, there's no user-controlled Nginx to serve media files via `X-Accel-Redirect`. AdventureLog automatically detects this and serves media files directly through Django.

This is handled automatically - no configuration needed. If you're using a custom setup with Nginx (like Docker), you can set `NGINX_MEDIA_ACCEL=true` to use Nginx for serving protected media.

### View All Environment Variables

```bash
clever env --alias adventurelog-backend
clever env --alias adventurelog-frontend
```

## Custom Domain

To add a custom domain:

```bash
# For the frontend (main app)
clever domain add your-domain.com --alias adventurelog-frontend

# For the backend API (optional)
clever domain add api.your-domain.com --alias adventurelog-backend
```

Then configure your DNS:
- Add a CNAME record pointing to `domain.cleverapps.io`

Don't forget to update the environment variables with your new domains:

```bash
# Update backend URLs
clever env set --alias adventurelog-backend PUBLIC_URL "https://api.your-domain.com"
clever env set --alias adventurelog-backend FRONTEND_URL "https://your-domain.com"
clever env set --alias adventurelog-backend CSRF_TRUSTED_ORIGINS "https://your-domain.com,https://api.your-domain.com"

# Update frontend URLs
clever env set --alias adventurelog-frontend ORIGIN "https://your-domain.com"
clever env set --alias adventurelog-frontend PUBLIC_SERVER_URL "https://api.your-domain.com"
```

See [Clever Cloud documentation](https://www.clever-cloud.com/doc/administrate/domain-names/) for more details.

## Updating AdventureLog

To update to a new version:

```bash
git pull origin main
clever deploy --alias adventurelog-backend
clever deploy --alias adventurelog-frontend
```

## Cost Estimation

| Component | Size | Estimated Monthly Cost |
|-----------|------|------------------------|
| Frontend | M | ~15€ |
| Backend | XS | ~5€ |
| PostgreSQL | S | ~10€ |
| Redis | S | ~5€ |
| FS Bucket | - | ~2€ |
| Mailpace | - | Free tier available |
| **Total** | | **~37€/month** |

*Prices are estimates and may vary. Check [Clever Cloud pricing](https://www.clever-cloud.com/pricing/) for current rates.*

## Optional Configuration

- [Disable Registration](../configuration/disable_registration.md)
- [Google Maps](../configuration/google_maps_integration.md)
- [Email Configuration](../configuration/email.md)
- [Immich Integration](../configuration/immich_integration.md)
- [Umami Analytics](../configuration/analytics.md)
