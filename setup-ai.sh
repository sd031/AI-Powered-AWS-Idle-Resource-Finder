#!/bin/bash

set -e

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║     AWS Idle Resource Finder - AI Setup                  ║"
echo "║     Downloading Llama 3.2 Model (~2GB)                    ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Check if Ollama container is running
if ! docker ps | grep -q "aws-resource-finder-ollama"; then
    echo "⚠️  Ollama container is not running."
    echo "   Starting services first..."
    docker-compose up -d ollama
    echo "   Waiting for Ollama to be ready..."
    sleep 5
fi

echo "📥 Pulling Llama 3.2 model..."
echo "   This may take 2-3 minutes depending on your internet speed."
echo ""

docker exec aws-resource-finder-ollama ollama pull llama3.2:latest

if [ $? -eq 0 ]; then
    echo ""
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║                  ✓ AI Model Ready!                       ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo ""
    echo "🎉 Llama 3.2 model has been downloaded successfully!"
    echo ""
    echo "You can now enable AI filtering in the web UI:"
    echo "   1. Go to http://localhost:3000"
    echo "   2. Check 'Enable AI Filtering' in Configuration"
    echo "   3. Run your analysis"
    echo ""
else
    echo ""
    echo "❌ Error: Failed to pull AI model"
    echo "   Please check your internet connection and try again."
    exit 1
fi
