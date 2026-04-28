#!/bin/bash

set -e

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║     AWS Idle Resource Finder - Setup Script              ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✓ Docker is installed"
echo "✓ Docker Compose is installed"
echo ""

# Check for AWS credentials
if [ ! -f "$HOME/.aws/credentials" ]; then
    echo "⚠️  Warning: AWS credentials not found at ~/.aws/credentials"
    echo "   You can still use the application by entering credentials manually in the UI"
    echo ""
else
    echo "✓ AWS credentials found"
    echo ""
fi

# Build and start services
echo "🔨 Building Docker images..."
docker-compose build

echo ""
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║                  ✓ Setup Complete!                       ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo ""
    echo "🌐 Web UI:      http://localhost:3000"
    echo "🔌 Backend API: http://localhost:8000"
    echo ""
    echo "📚 Quick Commands:"
    echo "   View logs:        docker-compose logs -f"
    echo "   Stop services:    docker-compose down"
    echo "   Restart:          docker-compose restart"
    echo "   Run CLI:          docker-compose run --rm backend python cli.py --help"
    echo ""
    echo "📖 For more information, see README.md or QUICKSTART.md"
    echo ""
else
    echo ""
    echo "❌ Error: Services failed to start"
    echo "   Run 'docker-compose logs' to see error details"
    exit 1
fi
