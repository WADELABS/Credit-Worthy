# CredStack Deployment Guide

This guide covers deploying CredStack to various cloud platforms for 24/7 access.

## Table of Contents
- [Render Deployment](#render-deployment)
- [Heroku Deployment](#heroku-deployment)
- [Railway Deployment](#railway-deployment)
- [Environment Variables](#environment-variables)
- [Database Considerations](#database-considerations)

## Render Deployment

Render is the recommended platform for deploying CredStack due to its free tier with persistent storage.

### Quick Deploy

1. **Fork the repository** to your GitHub account
2. **Click the Deploy button** or visit [render.com](https://render.com)
3. **Create a new Web Service**:
   - Connect your GitHub repository
   - Render will auto-detect `render.yaml`
   - Set the following environment variables:
     ```
     SECRET_KEY=<generate-random-string>
     JWT_SECRET_KEY=<generate-different-random-string>
     FLASK_ENV=production
     ```
4. **Deploy**: Click "Create Web Service"
5. **Wait for deployment** (typically 2-5 minutes)
6. **Access your app** at the provided Render URL

### Render Configuration Details

The `render.yaml` file is pre-configured with:
- Python 3.12 runtime
- Automatic dependency installation
- Gunicorn WSGI server
- Persistent disk storage (1GB) for SQLite database
- Free tier compatible

### Post-Deployment Setup

1. Navigate to your Render URL
2. Register a new admin account
3. Start adding credit accounts
4. Configure automations

## Heroku Deployment

### Prerequisites
- Heroku account
- Heroku CLI installed

### Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/WADELABS/Credit-Worthy.git
   cd Credit-Worthy
   ```

2. **Login to Heroku**:
   ```bash
   heroku login
   ```

3. **Create a new Heroku app**:
   ```bash
   heroku create your-credstack-app
   ```

4. **Set environment variables**:
   ```bash
   # Generate random secrets
   heroku config:set SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
   heroku config:set JWT_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
   heroku config:set FLASK_ENV=production
   ```

5. **Deploy**:
   ```bash
   git push heroku main
   ```

6. **Access your app**:
   ```bash
   heroku open
   ```

### Heroku Database

Heroku's free tier uses an ephemeral filesystem, which means SQLite data is lost on dyno restart. For production:

**Option 1: Use PostgreSQL**
```bash
heroku addons:create heroku-postgresql:mini
heroku config:set DATABASE_URL=$(heroku config:get DATABASE_URL)
```

**Option 2: Use persistent storage** (requires paid plan)

## Railway Deployment

Railway offers a simple deployment experience with generous free tier.

### Steps

1. **Install Railway CLI**:
   ```bash
   npm i -g @railway/cli
   ```

2. **Login**:
   ```bash
   railway login
   ```

3. **Initialize project**:
   ```bash
   cd Credit-Worthy
   railway init
   ```

4. **Set environment variables**:
   ```bash
   railway variables set SECRET_KEY=<your-secret-key>
   railway variables set JWT_SECRET_KEY=<your-jwt-secret>
   railway variables set FLASK_ENV=production
   ```

5. **Deploy**:
   ```bash
   railway up
   ```

6. **Generate domain**:
   ```bash
   railway domain
   ```

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Flask session secret (32+ chars) | `abc123def456...` |
| `JWT_SECRET_KEY` | JWT token signing key (32+ chars) | `xyz789uvw012...` |
| `FLASK_ENV` | Flask environment | `production` |
| `DATABASE_URL` | Database connection string | `sqlite:///database/credstack.db` |

### Optional Variables

| Variable | Description | Required For |
|----------|-------------|--------------|
| `TWILIO_ACCOUNT_SID` | Twilio account SID | SMS notifications |
| `TWILIO_AUTH_TOKEN` | Twilio auth token | SMS notifications |
| `TWILIO_PHONE_NUMBER` | Twilio phone number | SMS notifications |
| `SENDGRID_API_KEY` | SendGrid API key | Email notifications |
| `FROM_EMAIL` | Sender email address | Email notifications |

### Generating Secure Secrets

Use Python to generate secure random strings:

```python
import secrets
print(secrets.token_hex(32))
```

Or use OpenSSL:
```bash
openssl rand -hex 32
```

## Database Considerations

### SQLite (Default)

- **Pros**: Simple, no configuration needed, zero cost
- **Cons**: Single-server only, limited concurrency
- **Best for**: Personal use, demos, small teams

### PostgreSQL (Recommended for Production)

To switch to PostgreSQL:

1. **Update requirements.txt**:
   ```
   psycopg2-binary
   ```

2. **Set DATABASE_URL**:
   ```bash
   export DATABASE_URL=postgresql://user:pass@host:5432/dbname
   ```

3. **Update database.py** to use SQLAlchemy with PostgreSQL

### Backup Strategy

For SQLite deployments:

1. **Set up automated backups** using platform-specific solutions
2. **Download database regularly** for local backup:
   ```bash
   scp user@yourserver:/path/to/credstack.db ./backup/
   ```

## Performance Optimization

### Gunicorn Configuration

The default Procfile uses 2 workers. For better performance:

```
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 4 --timeout 30
```

### Caching

Consider adding Redis for session storage and caching:

```bash
heroku addons:create heroku-redis:mini
```

## Security Checklist

Before deploying to production:

- [ ] Change all default secrets
- [ ] Enable HTTPS (most platforms do this automatically)
- [ ] Set `FLASK_ENV=production`
- [ ] Review security headers in `app.py`
- [ ] Set up regular database backups
- [ ] Enable platform-specific monitoring
- [ ] Review and limit API rate limits
- [ ] Set up uptime monitoring (e.g., UptimeRobot)

## Monitoring and Logs

### Render
```bash
# View logs
render logs --service your-service-name --tail
```

### Heroku
```bash
# View logs
heroku logs --tail

# View app status
heroku ps
```

### Railway
```bash
# View logs
railway logs
```

## Troubleshooting

### Database not persisting
- Verify persistent disk is mounted (Render)
- Check DATABASE_URL path
- Review platform storage documentation

### App crashes on startup
- Check logs for errors
- Verify all environment variables are set
- Ensure `requirements.txt` is complete
- Check Python version compatibility

### 502/503 errors
- App may be starting (wait 1-2 minutes)
- Check worker configuration
- Review memory limits
- Check for startup errors in logs

## Cost Estimates

### Render (Free Tier)
- Web service: Free (750 hours/month)
- Persistent disk: Free (1GB)
- SSL: Free
- **Total: $0/month**

### Heroku (Free Tier - Legacy)
- Dyno: Free (550 hours/month)
- PostgreSQL: $5/month (if needed)
- **Total: $0-5/month**

### Railway (Free Tier)
- $5 free credit/month
- Usage-based pricing after credits
- **Total: $0-10/month**

## Support

For deployment issues:
- Check platform-specific documentation
- Review logs for error messages
- Open an issue on GitHub
- Join our community discussions

---

*Last updated: 2026-02-16*
