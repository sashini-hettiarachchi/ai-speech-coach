# Speech Coach - Production Deployment Guide

This guide provides step-by-step instructions for deploying the Speech Coach application in a production environment using Docker and Docker Compose.

## 🏗️ Architecture Overview

The application consists of three main services:

- **Frontend (Next.js)**: Runs on port 3000
- **Backend (Flask)**: Runs on port 5000  
- **Database (PostgreSQL)**: Runs on port 5433

All services are containerized and orchestrated using Docker Compose.

## 📋 Prerequisites

Before deploying, ensure you have the following installed:

- [Docker](https://docs.docker.com/get-docker/) (version 20.0 or higher)
- [Docker Compose](https://docs.docker.com/compose/install/) (version 2.0 or higher)
- Git (to clone the repository)

### System Requirements

- **CPU**: 2+ cores
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 10GB free space
- **Network**: Ports 3000, 5000, and 5433 available

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/speech-coach.git
cd speech-coach
```

### 2. Configure Environment Variables

Copy the environment template and edit with your values:

```bash
cp .env.production.template .env.production
```

Edit `.env.production` with your configuration:

```bash
# Required: Auth0 Configuration
AUTH0_DOMAIN=your-domain.auth0.com
AUTH0_AUDIENCE=your-backend-audience
AUTH0_CLIENT_ID=your-client-id
AUTH0_CLIENT_SECRET=your-client-secret
AUTH0_SECRET=your-32-character-secret

# Required: OpenAI API Key
OPENAI_API_KEY=your-openai-api-key

# Optional: Google Cloud Storage
GCS_BUCKET_NAME=your-bucket-name
```

### 3. Set Up Google Cloud Storage (Optional)

If you want to use Google Cloud Storage for file uploads:

1. Create a service account in Google Cloud Console
2. Download the service account key as JSON
3. Save it as `backend/key.json`

### 4. Deploy the Application

Run the deployment script:

```bash
./deploy.sh
```

The script will:
- Check dependencies
- Validate configuration
- Build Docker images
- Start all services
- Run database migrations
- Verify service health

### 5. Access the Application

Once deployed, you can access:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **Database**: localhost:5433

## 🛠️ Manual Deployment

If you prefer to deploy manually without the script:

### 1. Build and Start Services

```bash
docker-compose --env-file .env.production up -d --build
```

### 2. Check Service Status

```bash
docker-compose ps
```

### 3. View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### 4. Run Database Migrations

```bash
docker-compose exec backend python -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('Database tables created!')
"
```

## 🔧 Configuration Details

### Auth0 Setup

1. Create an Auth0 application (Single Page Application)
2. Set up allowed callback URLs: `http://localhost:3000/api/auth/callback`
3. Set up allowed logout URLs: `http://localhost:3000`
4. Create an API in Auth0 for the backend
5. Note down the domain, client ID, client secret, and audience

### Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `AUTH0_DOMAIN` | Yes | Your Auth0 domain |
| `AUTH0_AUDIENCE` | Yes | Auth0 API audience |
| `AUTH0_CLIENT_ID` | Yes | Auth0 application client ID |
| `AUTH0_CLIENT_SECRET` | Yes | Auth0 application client secret |
| `AUTH0_SECRET` | Yes | Random 32-character string |
| `OPENAI_API_KEY` | Yes | OpenAI API key for AI features |
| `GCS_BUCKET_NAME` | No | Google Cloud Storage bucket name |
| `DATABASE_HOST` | No | Database host (default: postgres) |
| `DATABASE_PORT` | No | Database port (default: 5432) |
| `DATABASE_NAME` | No | Database name (default: speech_coach) |
| `DATABASE_USER` | No | Database user (default: postgres) |
| `DATABASE_PASSWORD` | No | Database password |

## 🔍 Troubleshooting

### Common Issues

#### 1. Services Fail to Start

**Check logs:**
```bash
docker-compose logs [service-name]
```

**Common causes:**
- Port conflicts (check if ports 3000, 5000, 5433 are available)
- Missing environment variables
- Invalid configuration values

#### 2. Database Connection Errors

**Check database status:**
```bash
docker-compose exec postgres pg_isready -U postgres
```

**Reset database:**
```bash
docker-compose down -v
docker-compose up -d postgres
```

#### 3. Frontend Build Errors

**Rebuild frontend:**
```bash
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

#### 4. Auth0 Authentication Issues

- Verify Auth0 configuration in `.env.production`
- Check Auth0 dashboard for correct callback URLs
- Ensure AUTH0_SECRET is exactly 32 characters

#### 5. OpenAI API Errors

- Verify API key is valid and has sufficient credits
- Check OpenAI service status
- Review backend logs for specific error messages

### Service Health Checks

All services have built-in health checks:

```bash
# Check frontend health
curl http://localhost:3000/api/health

# Check backend health
curl http://localhost:5000/health

# Check detailed backend health (includes tools)
curl http://localhost:5000/api/v1/health
```

## 📊 Monitoring and Maintenance

### Viewing Logs

```bash
# Real-time logs for all services
docker-compose logs -f

# Logs for specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 frontend
```

### Service Management

```bash
# Stop all services
./deploy.sh stop

# Restart all services
./deploy.sh restart

# Check service status
./deploy.sh status

# View logs
./deploy.sh logs
```

### Database Backup

```bash
# Create backup
docker-compose exec postgres pg_dump -U postgres speech_coach > backup.sql

# Restore backup
docker-compose exec -i postgres psql -U postgres speech_coach < backup.sql
```

### Updating the Application

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

## 🔒 Security Considerations

### Production Security Checklist

- [ ] Use strong, unique passwords for database
- [ ] Keep Auth0 secrets secure and rotate regularly
- [ ] Use HTTPS in production (add reverse proxy like nginx)
- [ ] Regularly update Docker images and dependencies
- [ ] Monitor logs for suspicious activity
- [ ] Backup database regularly
- [ ] Limit network access to necessary ports only

### HTTPS Setup (Recommended)

For production, add an nginx reverse proxy with SSL:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api/ {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review service logs for error messages
3. Verify all configuration values
4. Ensure all prerequisites are met

For additional help, please check the project's issue tracker or documentation.

## 📝 License

This project is licensed under the MIT License. See the LICENSE file for details.