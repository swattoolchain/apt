#!/bin/bash
# Script to push APT (Allied Performance Testing) to GitHub

set -e

echo "🚀 Pushing APT - Allied Performance Testing to GitHub"
echo "===================================================="

# Navigate to repository
cd /Users/dineshrvl/neuron-automation-repos/neuron-e2e-grid-revamp/neuron-perf-test

# Initialize git if not already initialized
if [ ! -d .git ]; then
    echo "📦 Initializing git repository..."
    git init
fi

# Add remote
echo "🔗 Adding remote repository..."
git remote remove origin 2>/dev/null || true
git remote add origin https://github.com/swattoolchain/apt.git

# Configure git user (if not already configured)
git config user.email "swat.github@gmail.com" || true
git config user.name "SWAT Toolchain" || true

# Add all files
echo "📝 Adding files..."
git add .

# Commit
echo "💾 Creating commit..."
git commit -m "feat: APT - Allied Performance Testing Framework

🎯 Complete enterprise performance testing framework

Features:
- Multi-tool support (Playwright, k6, JMeter)
- Workflow orchestration (Temporal, Airflow, custom)
- Custom metrics collection (API, logs, Prometheus, DB)
- Docker containerization with all tools bundled
- Unified reporting with tool-specific metrics
- Granular step-by-step performance tracking
- Baseline comparison and regression detection
- Complete documentation and examples

Allied tools, unified performance! 🤝
" || echo "Nothing to commit or already committed"

# Push to GitHub
echo "🚀 Pushing to GitHub..."
echo ""
echo "⚠️  You will be prompted for credentials:"
echo "   Username: swat.github@gmail.com"
echo "   Password: Dilemma@54321"
echo ""

git push -u origin main

echo ""
echo "✅ Successfully pushed to https://github.com/swattoolchain/apt"
echo "🎉 APT - Allied Performance Testing is now live!"
