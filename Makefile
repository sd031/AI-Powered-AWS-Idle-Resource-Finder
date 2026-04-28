.PHONY: help build up down logs clean restart cli setup-ai ai-status ai-logs test-ai

help:
	@echo "AWS Idle Resource Finder - Make Commands"
	@echo ""
	@echo "Basic Commands:"
	@echo "  make build       - Build Docker images"
	@echo "  make up          - Start all services"
	@echo "  make down        - Stop all services"
	@echo "  make logs        - View logs"
	@echo "  make restart     - Restart all services"
	@echo "  make clean       - Remove containers and images"
	@echo "  make cli         - Run CLI tool"
	@echo ""
	@echo "AI Commands:"
	@echo "  make setup-ai    - Download AI model (Llama 3.2)"
	@echo "  make ai-status   - Check AI availability"
	@echo "  make ai-logs     - View Ollama logs"
	@echo "  make test-ai     - Test AI filtering"
	@echo ""

build:
	docker-compose build

up:
	docker-compose up -d
	@echo ""
	@echo "✓ Services started!"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Backend:  http://localhost:8000"
	@echo ""

down:
	docker-compose down

logs:
	docker-compose logs -f

restart:
	docker-compose restart

clean:
	docker-compose down -v --rmi all

cli:
	docker-compose run --rm backend python cli.py $(ARGS)

setup-ai:
	@echo "Setting up AI filtering..."
	@./setup-ai.sh

ai-status:
	@echo "Checking AI status..."
	@curl -s http://localhost:8000/ai/status | python3 -m json.tool || echo "Error: Backend not running. Run 'make up' first."

ai-logs:
	@docker logs -f aws-resource-finder-ollama

test-ai:
	@echo "Testing AI filtering..."
	@echo "This will check if Ollama is running and the model is available."
	@docker exec aws-resource-finder-ollama ollama list || echo "Error: Ollama container not running"
