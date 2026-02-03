# Clever Cloud

Clever Cloud is a European PaaS (Platform as a Service) that allows you to deploy applications without managing servers. This guide will walk you through deploying AdventureLog on Clever Cloud.

## Prerequisites

- A [Clever Cloud](https://www.clever-cloud.com/) account
- [Clever Cloud CLI](https://www.clever-cloud.com/doc/cli/) installed on your machine
- Git installed on your machine
- **A custom domain** (required for session cookies - see note below)

::: danger Custom Domain Required
The default `*.cleverapps.io` domains **will not work** for AdventureLog. The `cleverapps.io` domain is on the [Public Suffix List](https://publicsuffix.org/), which means session cookies cannot be shared between the frontend and backend applications.

You **must** use a custom domain where both apps share a parent domain:
- `adventurelog.your-domain.com` (frontend)
- `api.adventurelog.your-domain.com` (backend)

This allows session cookies to be set on `.your-domain.com` and shared between both apps.
:::

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

| Component | Build Size | Runtime Size | Purpose |
|-----------|------------|--------------|---------|
| Frontend | **M** (2GB RAM) | **XS** (512MB RAM) | SvelteKit application |
| Backend | - | **XS** (512MB RAM) | Django REST API |
| Database | - | PostgreSQL Add-on (S or M) | Data storage |
| Cache | - | Redis Add-on (S) | Session & caching |
| Storage | - | FS Bucket Add-on | Media files (persistent) |
| Email | - | Mailpace Add-on | Transactional emails |

::: tip Cost Optimization
The frontend uses **dedicated build instances**: the build runs on a temporary M instance (2GB RAM), while the runtime uses a smaller XS instance (512MB RAM). This significantly reduces costs.
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
clever addon create fs-bucket adventurelog-media --link adventurelog-backend
```

### Mailpace for Emails (Optional)

```bash
clever addon create mailpace adventurelog-email --link adventurelog-backend
```

## Step 4: Configure Custom Domain

::: warning Required Step
You must configure a custom domain before the application will work properly.
:::

### Add Domains to Clever Cloud

```bash
# Replace with your actual domain
clever domain add adventurelog.your-domain.com --alias adventurelog-frontend
clever domain add api.adventurelog.your-domain.com --alias adventurelog-backend
```

### Configure DNS

Add these CNAME records in your DNS provider:

| Type | Name | Value |
|------|------|-------|
| CNAME | `adventurelog` | `domain.cleverapps.io` |
| CNAME | `api.adventurelog` | `domain.cleverapps.io` |

## Step 5: Configure Instance Sizes

### Frontend: Dedicated Build + Small Runtime

The frontend build requires 2GB RAM, but the runtime only needs 512MB. Use dedicated build to optimize costs:

```bash
clever scale --alias adventurelog-frontend --flavor XS --build-flavor M
```

### Backend Size

```bash
clever scale --alias adventurelog-backend --flavor XS
```

## Step 6: Configure Environment Variables

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

# URLs (use your custom domain)
clever env set --alias adventurelog-backend PUBLIC_URL "https://api.adventurelog.your-domain.com"
clever env set --alias adventurelog-backend FRONTEND_URL "https://adventurelog.your-domain.com"
clever env set --alias adventurelog-backend CSRF_TRUSTED_ORIGINS "https://adventurelog.your-domain.com,https://api.adventurelog.your-domain.com"
```

### Configure FS Bucket for Media Persistence

Get your bucket host and configure the mount:

```bash
# Get the bucket host
clever env --alias adventurelog-backend | grep BUCKET_HOST

# Configure the mount (replace BUCKET_HOST with the value from above)
clever env set --alias adventurelog-backend CC_FS_BUCKET "backend/server/media:YOUR-BUCKET-HOST"
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

# Build in post-build hook (runs on dedicated M instance)
clever env set --alias adventurelog-frontend CC_POST_BUILD_HOOK "cd frontend && pnpm run build"

# Run command (runs on XS instance)
clever env set --alias adventurelog-frontend CC_RUN_COMMAND "cd frontend && node build"

# Frontend configuration (use your custom domain)
clever env set --alias adventurelog-frontend ORIGIN "https://adventurelog.your-domain.com"
clever env set --alias adventurelog-frontend PUBLIC_SERVER_URL "https://api.adventurelog.your-domain.com"
clever env set --alias adventurelog-frontend BODY_SIZE_LIMIT "Infinity"
```

## Step 7: Configure Email with Mailpace

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

## Step 8: Deploy

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

::: tip Build Process
The frontend build runs on a dedicated M instance (2GB RAM), then the artifacts are transferred to the XS runtime instance. This may take a few minutes on first deploy.
:::

## Step 9: Verify Deployment

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
| `https://adventurelog.your-domain.com` | Main application |
| `https://api.adventurelog.your-domain.com/api` | REST API |
| `https://api.adventurelog.your-domain.com/admin` | Django Admin Panel |

### Admin Panel Login

To access the Django admin panel:

1. Go to `https://api.adventurelog.your-domain.com/accounts/login/?next=/admin/`
2. Login with your admin credentials
3. You will be redirected to the admin panel

::: tip
Django-allauth handles authentication. The `?next=/admin/` parameter ensures you're redirected to the admin panel after login.
:::

## Troubleshooting

### Login Not Working / Session Not Saved

**Symptom**: After logging in, you're redirected back to the login page.

**Cause**: You're using the default `*.cleverapps.io` domains. Session cookies cannot be shared between different cleverapps.io subdomains.

**Solution**: You **must** use a custom domain. See [Step 4: Configure Custom Domain](#step-4-configure-custom-domain).

### Frontend Build Fails (OOM)

**Symptom**: Build hangs and eventually fails, or logs show the process was killed.

**Solution**: Ensure dedicated build is configured:

```bash
clever scale --alias adventurelog-frontend --flavor XS --build-flavor M
clever restart --alias adventurelog-frontend --without-cache
```

### Media Files Disappear After Restart

**Symptom**: Uploaded images (avatars, attachments) disappear after restarting the backend.

**Cause**: FS Bucket is not properly mounted.

**Solution**: Configure the FS Bucket mount:

```bash
# Get your bucket host
clever env --alias adventurelog-backend | grep BUCKET_HOST

# Set the mount (replace with your actual bucket host)
clever env set --alias adventurelog-backend CC_FS_BUCKET "backend/server/media:bucket-xxx.services.clever-cloud.com"
clever restart --alias adventurelog-backend --without-cache
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
clever env set --alias adventurelog-backend CSRF_TRUSTED_ORIGINS "https://adventurelog.your-domain.com,https://api.adventurelog.your-domain.com"
clever restart --alias adventurelog-backend
```

### Media Files Not Loading (Images, Flags)

**Symptom**: Images like country flags or uploaded media don't load.

**Explanation**: On Clever Cloud, there's no user-controlled Nginx to serve media files via `X-Accel-Redirect`. AdventureLog automatically detects this and serves media files directly through Django.

This is handled automatically - no configuration needed.

### View All Environment Variables

```bash
clever env --alias adventurelog-backend
clever env --alias adventurelog-frontend
```

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
| Frontend (runtime) | XS | ~5€ |
| Frontend (build) | M (temporary) | ~0.50€ |
| Backend | XS | ~5€ |
| PostgreSQL | S | ~10€ |
| Redis | S | ~5€ |
| FS Bucket | - | ~2€ |
| Mailpace | - | Free tier available |
| **Total** | | **~27.50€/month** |

*Prices are estimates and may vary. Check [Clever Cloud pricing](https://www.clever-cloud.com/pricing/) for current rates.*

## Optional Configuration

- [Disable Registration](../configuration/disable_registration.md)
- [Google Maps](../configuration/google_maps_integration.md)
- [Email Configuration](../configuration/email.md)
- [Immich Integration](../configuration/immich_integration.md)
- [Umami Analytics](../configuration/analytics.md)
