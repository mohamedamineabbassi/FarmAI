#!/bin/bash
# ========================================
# FARMAIA - Cache Clear & Turbo Start
# ========================================

echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║  🧹 Clearing Cache & Starting Turbo Mode           ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""

echo "1️⃣  Deleting .angular cache..."
if [ -d ".angular" ]; then
    rm -rf ".angular"
    echo "✅ .angular cache deleted"
else
    echo "ℹ️  .angular not found"
fi

echo ""
echo "2️⃣  Deleting dist folder..."
if [ -d "dist" ]; then
    rm -rf "dist"
    echo "✅ dist deleted"
else
    echo "ℹ️  dist not found"
fi

echo ""
echo "3️⃣  Verifying node_modules..."
if [ ! -d "node_modules" ]; then
    echo "⚠️  Installing npm packages..."
    npm install
else
    echo "✅ node_modules found"
fi

echo ""
echo "4️⃣  Starting TURBO MODE..."
echo ""
echo "⚡ Expected results:"
echo "   - HMR reload: 1-2 seconds"
echo "   - CSS changes: instant"
echo "   - Rebuild time: <3 seconds"
echo ""

npm run start:turbo
