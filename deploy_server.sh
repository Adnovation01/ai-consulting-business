#!/bin/bash

# =================================================================
# 🚀 AI CONSULTING ENGINE: VPS DEPLOYMENT SCRIPT 🚀
# Run this on your Ubuntu/Debian VPS to go live.
# =================================================================

echo "⚡ Starting Mission Control Deployment..."

# 1. Update & Install System Dependencies
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv git libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libasound2 libpango-1.0-0 libpangocairo-1.0-0

# 2. Setup Virtual Environment
echo "📦 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate

# 3. Install Python Core
pip install --upgrade pip
pip install flask flask-login flask-cors playwright requests beautifulsoup4 pandas openpyxl sqlite3

# 4. Install Stealth Browsers
echo "🕵️ Installing Playwright Stealth Browsers..."
playwright install-deps chromium
playwright install chromium

# 5. Initialize Database
echo "🗄️ Initializing Cloud Database..."
python3 -c "from src.database_manager import init_db; init_db()"

# 6. Setup Background Runner (PM2 is recommended)
echo "🎯 Deployment Complete."
echo "-------------------------------------------------------"
echo "TO RUN THE ENGINE 24/7, USE:"
echo "python3 app.py"
echo "-------------------------------------------------------"
echo "Check your VPS IP and update your website JavaScript API_URL."
echo "-------------------------------------------------------"
