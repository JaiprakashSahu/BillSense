#!/bin/bash
# BillSense — One-time setup script
# Run: chmod +x setup.sh && ./setup.sh

set -e

echo ""
echo "============================================"
echo "  BillSense — Setup"
echo "============================================"
echo ""

# 1. Check Python
echo "[1/5] Checking Python..."
python3 --version || { echo "Python 3 is required. Install it first."; exit 1; }

# 2. Install Python dependencies
echo "[2/5] Installing Python dependencies..."
pip3 install -r requirements.txt

# 3. Check Node.js
echo "[3/5] Checking Node.js..."
node --version || { echo "Node.js is required. Install it first."; exit 1; }

# 4. Install frontend dependencies
echo "[4/5] Installing frontend dependencies..."
cd frontend && npm install && cd ..

# 5. Check .env
echo "[5/5] Checking .env..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "  Created .env from .env.example"
    echo "  → Edit .env and add your GROQ_API_KEY"
else
    echo "  .env already exists"
fi

echo ""
echo "============================================"
echo "  Setup complete!"
echo ""
echo "  Next steps:"
echo "    1. Add your Groq API key to .env"
echo "    2. Place bill PDFs in data/raw_pdfs/"
echo "    3. Run: make pipeline"
echo "    4. Run: make dev"
echo "    5. Open: http://localhost:3000"
echo "============================================"
echo ""
