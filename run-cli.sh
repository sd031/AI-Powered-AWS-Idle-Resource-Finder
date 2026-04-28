#!/bin/bash

# Helper script to run the CLI tool with Docker

if [ "$1" == "--help" ] || [ "$1" == "-h" ] || [ -z "$1" ]; then
    echo "AWS Idle Resource Finder - CLI Runner"
    echo ""
    echo "Usage: ./run-cli.sh [OPTIONS]"
    echo ""
    echo "Examples:"
    echo "  ./run-cli.sh --profile production"
    echo "  ./run-cli.sh --regions us-east-1 us-west-2"
    echo "  ./run-cli.sh --export-csv results.csv"
    echo "  ./run-cli.sh --idle-only"
    echo ""
    echo "For full CLI options, run:"
    echo "  ./run-cli.sh --help"
    echo ""
    
    if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
        docker-compose run --rm backend python cli.py --help
    fi
    exit 0
fi

docker-compose run --rm backend python cli.py "$@"
