# Speech Coach - Docker Compose Setup

A complete production-ready deployment setup for the Speech Coach application using Docker and Docker Compose.

## 🚀 Quick Start

1. **Clone and setup environment:**
   ```bash
   git clone <your-repo-url>
   cd speech-coach
   cp .env.production.template .env.production
   # Edit .env.production with your configuration
   ```

2. **Deploy everything:**
   ```bash
   ./deploy.sh
   ```

3. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000
   - Database: localhost:5433

## 📁 Project Structure

```
speech-coach/
├── docker-compose.yml          # Multi-service orchestration
├── deploy.sh                   # One-click deployment script
├── .env.production.template    # Environment configuration template
├── DEPLOYMENT.md              # Comprehensive deployment guide
├── backend/
│   ├── Dockerfile             # Flask backend container
│   ├── .dockerignore          # Docker build exclusions
│   └── ...
└── frontend/
    ├── Dockerfile             # Next.js frontend container
    ├── .dockerignore          # Docker build exclusions
    └── ...
```

## 🐳 Services

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 3000 | Next.js React application |
| Backend | 5000 | Flask API server |
| Database | 5433 | PostgreSQL database |

## 🛠️ Development vs Production

This setup is optimized for production with:

- Multi-stage Docker builds for smaller images
- Non-root user execution for security
- Health checks for all services
- Proper dependency management
- Volume persistence for data
- Graceful error handling

## 📚 Documentation

- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Complete deployment guide
- **[docker-compose.yml](./docker-compose.yml)** - Service definitions
- **[deploy.sh](./deploy.sh)** - Automated deployment script

## 🔧 Configuration

Key configuration files:

- `.env.production` - Production environment variables
- `backend/key.json` - Google Cloud Storage service account (optional)
- Auth0 setup for authentication
- OpenAI API key for AI features

## 🚀 Deployment Commands

```bash
# Deploy application
./deploy.sh deploy

# Stop all services  
./deploy.sh stop

# Restart services
./deploy.sh restart

# View logs
./deploy.sh logs

# Check status
./deploy.sh status
```

## 📞 Need Help?

See [DEPLOYMENT.md](./DEPLOYMENT.md) for comprehensive setup instructions, troubleshooting, and configuration details.