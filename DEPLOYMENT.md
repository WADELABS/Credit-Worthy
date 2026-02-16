# CredStack Deployment Guide 🚀

This guide provides instructions for deploying CredStack to various hosting platforms.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Platform-Specific Guides](#platform-specific-guides)
  - [Render](#deploy-to-render)
  - [Heroku](#deploy-to-heroku)
  - [Railway](#deploy-to-railway)
  - [Docker](#docker-deployment)
- [Post-Deployment](#post-deployment)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying CredStack, ensure you have:
- A GitHub account with the repository forked/cloned
- Access to a hosting platform (Render, Heroku, Railway, etc.)
- Basic understanding of environment variables
- (Optional) Custom domain configured

## Environment Variables

CredStack requires the following environment variables to be configured:

### Required Variables

```env
SECRET_KEY=your-secret-key-here-change-this
JWT_SECRET_KEY=your-jwt-secret-change-this
FLASK_ENV=production
DATABASE_URL=sqlite:///database/credstack.db
```

### Optional Variables (for notifications)

```env
# Twilio for SMS notifications
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=+15555555555

# SendGrid for email notifications
SENDGRID_API_KEY=your-sendgrid-key
FROM_EMAIL=alerts@credstack.com
```

> **Security Note**: Never commit actual secret keys to version control. Use platform-specific secret management.

## Platform-Specific Guides

### Deploy to Render

Render is recommended for its simplicity and generous free tier.

#### Option 1: Using render.yaml (Recommended)

1. **Fork/Clone the repository** to your GitHub account

2. **Connect to Render**:
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Render will automatically detect `render.yaml`

3. **Configure Environment Variables**:
   - Render will auto-generate `SECRET_KEY` and `JWT_SECRET_KEY`
   - Add any optional variables (Twilio, SendGrid) in the dashboard

4. **Deploy**:
   - Click "Apply" to start deployment
   - Render will build and deploy automatically
   - Your app will be available at `https://your-app-name.onrender.com`

#### Option 2: Manual Setup

1. **Create New Web Service**:
   - Go to Render Dashboard
   - Click "New +" → "Web Service"
   - Connect your repository

2. **Configure Build Settings**:
   - **Name**: `credstack` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && python setup.py`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: Free or Starter

3. **Add Environment Variables**:
   ```
   SECRET_KEY=generate-random-value
   JWT_SECRET_KEY=generate-different-random-value
   FLASK_ENV=production
   DATABASE_URL=sqlite:///database/credstack.db
   ```

4. **Add Persistent Disk** (for database):
   - Go to your service settings
   - Add a disk at `/opt/render/project/src/database`
   - Size: 1GB (free tier allows up to 1GB)

5. **Deploy**: Click "Create Web Service"

### Deploy to Heroku

1. **Install Heroku CLI** (if not already installed):
   ```bash
   curl https://cli-assets.heroku.com/install.sh | sh
   ```

2. **Login to Heroku**:
   ```bash
   heroku login
   ```

3. **Create a new Heroku app**:
   ```bash
   heroku create your-app-name
   ```

4. **Set Environment Variables**:
   ```bash
   heroku config:set SECRET_KEY=$(openssl rand -hex 32)
   heroku config:set JWT_SECRET_KEY=$(openssl rand -hex 32)
   heroku config:set FLASK_ENV=production
   heroku config:set DATABASE_URL=sqlite:///database/credstack.db
   ```

5. **Deploy**:
   ```bash
   git push heroku main
   ```

6. **Initialize Database**:
   ```bash
   heroku run python setup.py
   ```

7. **Open Your App**:
   ```bash
   heroku open
   ```

> **Note**: Heroku's ephemeral filesystem means database changes reset on restart. For production, consider using Heroku Postgres addon.

### Deploy to Railway

1. **Connect to Railway**:
   - Go to [Railway](https://railway.app/)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository

2. **Configure Settings**:
   - Railway auto-detects Python and Procfile
   - Add environment variables in Settings → Variables:
     ```
     SECRET_KEY=generate-random-value
     JWT_SECRET_KEY=generate-different-random-value
     FLASK_ENV=production
     DATABASE_URL=sqlite:///database/credstack.db
     ```

3. **Add Volume** (for persistent database):
   - Go to Settings → Volumes
   - Add volume at `/app/database`

4. **Deploy**: Railway deploys automatically on git push

### Docker Deployment

A Dockerfile is coming soon! For now, you can create a basic one:

```dockerfile
FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python setup.py

EXPOSE 5000

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
```

## Post-Deployment

### 1. Verify Deployment
- Visit your deployed URL
- Register a new account
- Test core functionality:
  - Dashboard loads correctly
  - Can add credit accounts
  - Automation settings work
  - API endpoints respond

### 2. Set Up Custom Domain (Optional)

#### Render:
- Go to Settings → Custom Domains
- Add your domain
- Configure DNS with provided values

#### Heroku:
```bash
heroku domains:add www.yourdomain.com
```

### 3. Enable HTTPS
Most platforms (Render, Heroku, Railway) provide automatic HTTPS. Verify:
- URL uses `https://`
- Certificate is valid
- No mixed content warnings

### 4. Monitor Your Application
- Set up monitoring/alerting (most platforms include this)
- Check logs regularly: `heroku logs --tail` or via platform dashboard
- Monitor database size and usage

## Troubleshooting

### Application Won't Start

**Check logs**:
- Render: Dashboard → Logs
- Heroku: `heroku logs --tail`
- Railway: Project → Deployments → Logs

**Common issues**:
- Missing environment variables
- Incorrect `DATABASE_URL`
- Database not initialized

**Solution**: Verify all environment variables and run migrations.

### Database Issues

**Error**: `database locked` or `unable to open database file`

**Solutions**:
1. Ensure persistent storage is configured
2. For Render: Add disk mount at `/opt/render/project/src/database`
3. For Heroku: Consider using Heroku Postgres

### 500 Internal Server Error

**Debug steps**:
1. Check application logs
2. Verify `SECRET_KEY` and `JWT_SECRET_KEY` are set
3. Ensure database is initialized
4. Check file permissions

### Memory Issues

If you hit memory limits on free tiers:
1. Reduce worker count in Procfile: `--workers 1`
2. Upgrade to a paid tier
3. Optimize database queries

### Port Binding Issues

Ensure your start command uses the platform's `PORT` environment variable:
```bash
gunicorn app:app --bind 0.0.0.0:$PORT
```

### CORS Issues (API Access)

If you need to allow cross-origin requests, add to `app.py`:
```python
from flask_cors import CORS
CORS(app)
```

And add `flask-cors` to `requirements.txt`.

## Production Checklist

Before going live, verify:

- [ ] All environment variables set correctly
- [ ] Secret keys are random and secure
- [ ] Database is properly initialized
- [ ] HTTPS is enabled
- [ ] Error logging is configured
- [ ] Backups are set up (for database)
- [ ] Rate limiting is enabled (already configured)
- [ ] Security headers are set (already configured)
- [ ] Application monitoring is active
- [ ] Custom domain configured (if applicable)

## Need Help?

- **Documentation**: Check [README.md](README.md) and [docs/API.md](docs/API.md)
- **Issues**: Open an issue on GitHub
- **Security**: Email security@credstack.com

---

**Happy Deploying!** 🚀

*CredStack - Automating credit optimization with precision and privacy.*
