#!/bin/bash
# =================================================================
# AI Consulting CRM — VPS Deploy Script
# Run this in your VPS web console (Hetzner/DigitalOcean/Contabo)
# or from any machine with SSH access.
#
# Usage:
#   bash deploy_consulting_crm.sh
#
# After deploying, visit: http://138.252.201.204:5001/mission-hub
# Login: admin / team_password_123
# =================================================================

set -e

APP_DIR="/opt/consulting-crm"
REPO="https://github.com/Adnovation01/ai-consulting-business.git"
SERVICE="consulting-crm"

echo "==> Updating packages..."
apt-get update -qq
apt-get install -y -qq python3-pip python3-venv git \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
    libasound2 libpango-1.0-0 libpangocairo-1.0-0

echo "==> Cloning or updating repo..."
if [ -d "$APP_DIR/.git" ]; then
    cd "$APP_DIR" && git pull origin main
else
    git clone "$REPO" "$APP_DIR"
    cd "$APP_DIR"
fi

echo "==> Setting up Python venv..."
python3 -m venv venv
source venv/bin/activate

echo "==> Installing Python dependencies..."
pip install --quiet -r requirements.txt

echo "==> Installing Playwright Chromium..."
playwright install-deps chromium
playwright install chromium

echo "==> Initializing database..."
python3 -c "from src.database_manager import init_db; init_db()"

echo "==> Creating .env (fill in your keys!)..."
if [ ! -f .env ]; then
    SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    cat > .env << EOF
GEMINI_API_KEY=REPLACE_WITH_YOUR_GEMINI_KEY
SECRET_KEY=$SECRET
FLASK_DEBUG=false
EMAIL_USER=REPLACE_WITH_YOUR_GMAIL
EMAIL_PASS=REPLACE_WITH_YOUR_GMAIL_APP_PASSWORD
BCC_EMAIL=
YOUR_NAME=Pranshu
YOUR_TITLE=AI Strategy Consultant
YOUR_LINKEDIN=https://linkedin.com/in/yourprofile
FROM_EMAIL=REPLACE_WITH_YOUR_GMAIL
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=465
PORT=5001
EOF
    echo "  >> .env created. Edit it with: nano $APP_DIR/.env"
fi

echo "==> Creating systemd service..."
cat > /etc/systemd/system/$SERVICE.service << EOF
[Unit]
Description=AI Consulting CRM (Port 5001)
After=network.target

[Service]
User=root
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/python app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "==> Opening firewall port 5001..."
ufw allow 5001/tcp 2>/dev/null || true

echo "==> Starting service..."
systemctl daemon-reload
systemctl enable $SERVICE
systemctl restart $SERVICE
sleep 3
systemctl status $SERVICE --no-pager

echo ""
echo "================================================================"
echo "  DEPLOYMENT COMPLETE"
echo "  CRM Dashboard: http://138.252.201.204:5001/mission-hub"
echo "  Login: admin / team_password_123"
echo ""
echo "  NEXT: Edit /opt/consulting-crm/.env and add your keys:"
echo "    nano /opt/consulting-crm/.env"
echo "    systemctl restart consulting-crm"
echo "================================================================"
