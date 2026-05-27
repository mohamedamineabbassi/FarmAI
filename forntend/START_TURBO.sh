#!/bin/bash
# ========================================
# FARMAIA - Frontend Turbo Start Script
# ========================================

echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║  🚀 FarmAI Frontend - TURBO MODE START            ║"
echo "║  Ultra-fast development environment                ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "⚠️  node_modules not found. Installing dependencies..."
    echo ""
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ npm install failed!"
        exit 1
    fi
fi

# Check if Angular CLI is installed
if [ ! -d "node_modules/@angular/cli" ]; then
    echo "⚠️  Angular CLI not found. Installing..."
    npm install -g @angular/cli
fi

echo "✅ Starting development server..."
echo "📍 Server will run on: http://localhost:4200"
echo "🔄 File watching: ACTIVE (500ms polling)"
echo "💾 Changes auto-reload: ENABLED"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

# Clear .angular cache for fresh build
if [ -d ".angular" ]; then
    echo "🧹 Clearing Angular cache..."
    rm -rf .angular
fi

# Start the turbo server
npm run start:turbo
