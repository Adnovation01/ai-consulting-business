from flask import Flask, jsonify, request, session, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_cors import CORS
from dotenv import load_dotenv
import threading
import subprocess
import os
import sys
import json
from src.database_manager import init_db, get_all_leads, update_lead_action

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'fallback-dev-key-change-in-production')
CORS(app) 

# Ensure DB is ready on startup
init_db()

login_manager = LoginManager()
login_manager.init_app(app)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config', 'team.json')

def load_team():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)['users']
    return {}

# ==========================================
# USERS DATABASE (MVP Phase)
# ==========================================
users = {'admin': {'password': 'team_password_123'}}

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    team = load_team()
    if user_id in team:
        return User(user_id)
    return None

# ==========================================
# AUTHENTICATION ROUTES
# ==========================================
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    team = load_team()
    if username in team and team[username]['password'] == password:
        user = User(username)
        login_user(user)
        return jsonify({'status': 'success', 'message': 'Logged in successfully.', 'role': team[username].get('role', 'member')})
    
    return jsonify({'status': 'error', 'message': 'Invalid credentials.'}), 401

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'status': 'success', 'message': 'Logged out successfully.'})

@app.route('/api/me', methods=['GET'])
@login_required
def get_current_user():
    return jsonify({'status': 'success', 'user': current_user.id})

# ==========================================
# DASHBOARD API ROUTES
# ==========================================
@app.route('/api/leads', methods=['GET'])
@login_required
def get_leads():
    try:
        leads = get_all_leads()
        return jsonify({'status': 'success', 'data': leads})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ==========================================
# SCRAPING ENGINE ROUTE
# ==========================================
def run_scraper_background(industry):
    """
    Runs the genuine_campaign in a subprocess so it doesn't block the API.
    We pass the industry dynamically as a command line argument.
    """
    script_path = os.path.join(os.path.dirname(__file__), 'src', 'genuine_campaign.py')
    try:
        # We will modify genuine_campaign.py to optionally accept an industry sys argument
        subprocess.run([sys.executable, script_path, industry])
    except Exception as e:
        print(f"Background Scraper Error: {e}")

    return jsonify({
        'status': 'success', 
        'message': f'Engine started! It is now actively researching {industry} across nationwide directories in the background.'
    })

# ==========================================
# LEAD UPDATE ROUTE (The "SEND" Bridge)
# ==========================================
@app.route('/api/update-lead', methods=['POST'])
@login_required
def update_lead():
    data = request.json
    lead_id = data.get('lead_id')
    new_action = data.get('action') 
    
    if not lead_id or not new_action:
        return jsonify({'status': 'error', 'message': 'Missing data.'}), 400

    try:
        update_lead_action(lead_id, new_action)
        return jsonify({'status': 'success', 'message': f'Lead status updated.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ==========================================
# SERVE WEB CRM (Mission Hub)
# ==========================================
@app.route('/')
@app.route('/mission-hub')
def serve_dashboard():
    return send_from_directory('dashboard', 'index.html')

@app.route('/dashboard/<path:path>')
@login_required
def serve_dashboard_files(path):
    return send_from_directory('dashboard', path)


if __name__ == '__main__':
    print("AI Consulting Engine Online Backend is starting...")
    port = int(os.getenv('PORT', 5000))
    app.run(debug=os.getenv('FLASK_DEBUG', 'true').lower() == 'true', host='0.0.0.0', port=port)
