#!/bin/bash

# Speech Coach Application Deployment Script
# This script will deploy the entire Speech Coach application using Docker Compose

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if required commands exist
check_dependencies() {
    print_status "Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! command -v docker compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "All dependencies are installed."
}

# Function to check if .env.production exists
check_env_file() {
    print_status "Checking environment configuration..."
    
    if [ ! -f ".env.production" ]; then
        print_warning ".env.production file not found."
        print_status "Creating .env.production from template..."
        
        if [ -f ".env.production.template" ]; then
            cp .env.production.template .env.production
            print_warning "Please edit .env.production with your actual configuration values before continuing."
            print_warning "Required values: AUTH0_DOMAIN, AUTH0_AUDIENCE, AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET, AUTH0_SECRET, OPENAI_API_KEY"
            read -p "Press Enter when you have configured .env.production..."
        else
            print_error ".env.production.template not found. Please create environment configuration manually."
            exit 1
        fi
    fi
    
    print_success "Environment configuration found."
}

# Function to check if key.json exists (for Google Cloud Storage)
check_gcs_key() {
    print_status "Checking Google Cloud Storage configuration..."
    
    if [ ! -f "backend/key.json" ]; then
        print_warning "backend/key.json not found."
        print_warning "Google Cloud Storage features will not work without this file."
        print_warning "If you want to use GCS, please:"
        print_warning "1. Download your service account key from Google Cloud Console"
        print_warning "2. Save it as backend/key.json"
        read -p "Continue without GCS? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_success "Google Cloud Storage key found."
    fi
}

# Function to build and start services
deploy_services() {
    print_status "Building and starting services..."
    
    # Load environment variables
    export $(grep -v '^#' .env.production | xargs)
    
    # Build and start services
    if command -v docker-compose &> /dev/null; then
        docker-compose --env-file .env.production down --remove-orphans
        docker-compose --env-file .env.production build --no-cache
        docker-compose --env-file .env.production up -d
    else
        docker compose --env-file .env.production down --remove-orphans
        docker compose --env-file .env.production build --no-cache
        docker compose --env-file .env.production up -d
    fi
    
    print_success "Services are starting up..."
}

# Function to wait for services to be healthy
wait_for_services() {
    print_status "Waiting for services to be healthy..."
    
    # Wait for database
    print_status "Waiting for database to be ready..."
    sleep 10
    
    # Wait for backend
    print_status "Waiting for backend to be ready..."
    for i in {1..30}; do
        if curl -f http://localhost:5000/health &> /dev/null; then
            print_success "Backend is healthy!"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "Backend failed to start within 5 minutes."
            print_status "Checking backend logs..."
            if command -v docker-compose &> /dev/null; then
                docker-compose logs backend
            else
                docker compose logs backend
            fi
            exit 1
        fi
        sleep 10
    done
    
    # Wait for frontend
    print_status "Waiting for frontend to be ready..."
    for i in {1..30}; do
        if curl -f http://localhost:3000/api/health &> /dev/null; then
            print_success "Frontend is healthy!"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "Frontend failed to start within 5 minutes."
            print_status "Checking frontend logs..."
            if command -v docker-compose &> /dev/null; then
                docker-compose logs frontend
            else
                docker compose logs frontend
            fi
            exit 1
        fi
        sleep 10
    done
}

# Function to run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    if command -v docker-compose &> /dev/null; then
        docker-compose exec backend python -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('Database tables created successfully!')
"
    else
        docker compose exec backend python -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('Database tables created successfully!')
"
    fi
    
    print_success "Database migrations completed."
}

# Function to show deployment status
show_status() {
    print_success "🚀 Speech Coach application deployed successfully!"
    echo
    print_status "Services are running on:"
    echo "  📱 Frontend:  http://localhost:3000"
    echo "  🔗 Backend:   http://localhost:5000"
    echo "  🗄️  Database:  localhost:5433"
    echo
    print_status "To view logs:"
    if command -v docker-compose &> /dev/null; then
        echo "  docker-compose logs -f [service_name]"
    else
        echo "  docker compose logs -f [service_name]"
    fi
    echo
    print_status "To stop all services:"
    if command -v docker-compose &> /dev/null; then
        echo "  docker-compose down"
    else
        echo "  docker compose down"
    fi
    echo
}

# Function to show help
show_help() {
    echo "Speech Coach Deployment Script"
    echo
    echo "Usage: $0 [OPTION]"
    echo
    echo "Options:"
    echo "  deploy    Deploy the application (default)"
    echo "  stop      Stop all services"
    echo "  restart   Restart all services"
    echo "  logs      Show logs for all services"
    echo "  status    Show status of all services"
    echo "  help      Show this help message"
    echo
}

# Main function
main() {
    case "${1:-deploy}" in
        deploy)
            print_status "🚀 Starting Speech Coach deployment..."
            check_dependencies
            check_env_file
            check_gcs_key
            deploy_services
            wait_for_services
            run_migrations
            show_status
            ;;
        stop)
            print_status "🛑 Stopping Speech Coach services..."
            if command -v docker-compose &> /dev/null; then
                docker-compose down
            else
                docker compose down
            fi
            print_success "All services stopped."
            ;;
        restart)
            print_status "🔄 Restarting Speech Coach services..."
            if command -v docker-compose &> /dev/null; then
                docker-compose restart
            else
                docker compose restart
            fi
            print_success "All services restarted."
            ;;
        logs)
            print_status "📋 Showing logs for all services..."
            if command -v docker-compose &> /dev/null; then
                docker-compose logs -f
            else
                docker compose logs -f
            fi
            ;;
        status)
            print_status "📊 Checking service status..."
            if command -v docker-compose &> /dev/null; then
                docker-compose ps
            else
                docker compose ps
            fi
            ;;
        help)
            show_help
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"