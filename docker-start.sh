#!/bin/bash

# Docker startup script for LimAuto
set -e

echo "🐳 Starting LimAuto with Docker"
echo "================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if we want development or production mode
MODE=${1:-dev}

case $MODE in
    "dev"|"development")
        echo "🚀 Starting in DEVELOPMENT mode"
        echo "   - Backend: http://localhost:8000"
        echo "   - Frontend: http://localhost:3000"
        echo "   - Redis: localhost:6379"
        echo ""
        docker-compose -f docker-compose.dev.yml up --build
        ;;
    "prod"|"production")
        echo "🚀 Starting in PRODUCTION mode"
        echo "   - Application: http://localhost"
        echo "   - API: http://localhost/api/"
        echo ""
        docker-compose --profile production up --build -d
        echo "✅ Services started in background"
        echo "📊 Check status: docker-compose ps"
        echo "📝 View logs: docker-compose logs -f"
        ;;
    "stop")
        echo "🛑 Stopping all services..."
        docker-compose -f docker-compose.dev.yml down
        docker-compose --profile production down
        echo "✅ All services stopped"
        ;;
    "clean")
        echo "🧹 Cleaning up Docker resources..."
        docker-compose -f docker-compose.dev.yml down -v
        docker-compose --profile production down -v
        docker system prune -f
        echo "✅ Cleanup complete"
        ;;
    *)
        echo "Usage: $0 [dev|prod|stop|clean]"
        echo ""
        echo "Commands:"
        echo "  dev   - Start development environment (default)"
        echo "  prod  - Start production environment"
        echo "  stop  - Stop all services"
        echo "  clean - Stop services and clean up volumes"
        exit 1
        ;;
esac