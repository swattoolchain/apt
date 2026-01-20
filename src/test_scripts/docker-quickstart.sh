#!/bin/bash
# Quick start script for Docker-based performance testing

set -e

echo "🚀 Neuron Performance Testing Framework - Docker Quick Start"
echo "============================================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

echo "✅ Docker is installed"

# Build the image
echo ""
echo "📦 Building Docker image..."
docker build -t neuron-perf-test:latest .

echo ""
echo "✅ Image built successfully!"

# Show usage
echo ""
echo "🎯 Quick Commands:"
echo ""
echo "1. Run smoke tests:"
echo "   docker run --rm -v \$(pwd)/tests:/app/tests -v \$(pwd)/performance_results:/app/performance_results neuron-perf-test:latest pytest tests/definitions/ --perf-tags=smoke -v"
echo ""
echo "2. Run all tests:"
echo "   docker run --rm -v \$(pwd)/tests:/app/tests -v \$(pwd)/performance_results:/app/performance_results neuron-perf-test:latest pytest tests/definitions/ -v"
echo ""
echo "3. Start with monitoring stack:"
echo "   docker-compose up -d"
echo ""
echo "4. Interactive shell:"
echo "   docker run -it --rm neuron-perf-test:latest /bin/bash"
echo ""
echo "📖 See docs/DOCKER_USAGE.md for complete guide"
echo ""
echo "✨ Ready to test!"
