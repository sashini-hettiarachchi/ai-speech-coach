#!/bin/bash

# Build Docker Images Script for Speech Coach
# This script builds the Docker images with consistent naming for deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

print_header() {
    echo
    echo "========================================="
    echo "🐳 Speech Coach Docker Image Builder"
    echo "========================================="
    echo
}

# Function to check Docker installation
check_docker() {
    print_status "Checking Docker installation..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running. Please start Docker."
        exit 1
    fi
    
    print_success "Docker is available and running."
}

# Function to build backend image
build_backend() {
    print_status "Building backend Docker image..."
    
    cd backend
    
    # Build with consistent naming
    docker build -t ai-speech-coach/backend:latest .
    
    print_success "Backend image built successfully!"
    cd ..
}

# Function to build frontend image
build_frontend() {
    print_status "Building frontend Docker image..."
    
    cd frontend
    
    # Build with consistent naming
    docker build -t ai-speech-coach/frontend:latest .
    
    print_success "Frontend image built successfully!"
    cd ..
}

# Function to export images
export_images() {
    print_status "Exporting Docker images for deployment..."
    
    # Create docker-exports directory if it doesn't exist
    mkdir -p docker-exports
    
    # Export backend image
    print_status "Exporting backend image..."
    docker save ai-speech-coach/backend:latest | gzip > docker-exports/speech-coach-backend-v1.0.0.tar.gz
    
    # Export frontend image
    print_status "Exporting frontend image..."
    docker save ai-speech-coach/frontend:latest | gzip > docker-exports/speech-coach-frontend-v1.0.0.tar.gz
    
    print_success "Images exported to docker-exports/ directory"
}

# Function to show image info
show_images() {
    print_status "Built Docker images:"
    echo
    docker images | grep -E "(ai-speech-coach|speech-coach)" | head -10
    echo
    
    if [ -d "docker-exports" ]; then
        print_status "Exported image files:"
        ls -lh docker-exports/*.tar.gz 2>/dev/null || echo "No exported images found"
        echo
    fi
}

# Function to clean old images
clean_images() {
    print_status "Cleaning old Docker images..."
    
    # Remove dangling images
    docker image prune -f
    
    # Remove old speech-coach images
    docker rmi $(docker images | grep -E "(ai-speech-coach|speech-coach)" | grep -v latest | awk '{print $3}') 2>/dev/null || true
    
    print_success "Cleaned old images."
}

# Main build function
build_all() {
    print_header
    
    check_docker
    build_backend
    build_frontend
    show_images
    
    print_success "🎉 All images built successfully!"
    echo
    print_status "Next steps:"
    echo "1. docker compose --env-file .env.production down"
    echo "2. docker compose --env-file .env.production up -d"
}

# Help function
show_help() {
    cat << EOF
Speech Coach Docker Image Builder

Usage: $0 [COMMAND]

Commands:
  build     Build all Docker images (default)
  backend   Build only backend image
  frontend  Build only frontend image
  export    Export images for deployment
  clean     Clean old Docker images
  show      Show current images
  help      Show this help message

Examples:
  $0                # Build all images
  $0 build          # Build all images
  $0 backend        # Build only backend
  $0 export         # Export images to tar.gz files
  $0 clean          # Clean old images

EOF
}

# Main script logic
case "${1:-build}" in
    build)
        build_all
        ;;
    backend)
        print_header
        check_docker
        build_backend
        show_images
        ;;
    frontend)
        print_header
        check_docker
        build_frontend
        show_images
        ;;
    export)
        print_header
        check_docker
        export_images
        show_images
        ;;
    clean)
        print_header
        check_docker
        clean_images
        show_images
        ;;
    show)
        show_images
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac