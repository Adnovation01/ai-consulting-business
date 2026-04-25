from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_cors import CORS
from dotenv import load_dotenv
import threading
import subprocess
import os
import sys
import json
import smtplib
import time
import random
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.database_manager import init_db, get_all_leads, update_lead_action, save_lead

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'fallback-dev-key-change-in-production')
CORS(app)

init_db()

login_manager = LoginManager()
login_manager.init_app(app)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config', 'team.json')

def load_team():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)['users']
    return {}

# ── In-memory state for long-running background jobs ──────────────────────────
scraper_state = {
    'running': False, 'industry': 'dentist', 'leads_found': 0,
    'current_state': 'Idle', 'started_at': None, 'error': None, 'log': []
}
email_state = {
    'running': False, 'sent': 0, 'errors': 0,
    'total': 0, 'current': '', 'done': False
}

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    team = load_team()
    if user_id in team:
        return User(user_id)
    return None

# ══════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json or {}
    username = data.get('username', '')
    password = data.get('password', '')
    team = load_team()
    if username in team and team[username]['password'] == password:
        login_user(User(username))
        return jsonify({'status': 'success', 'message': 'Logged in successfully.',
                        'role': team[username].get('role', 'member')})
    return jsonify({'status': 'error', 'message': 'Invalid credentials.'}), 401

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'status': 'success'})

@app.route('/api/me', methods=['GET'])
@login_required
def get_current_user():
    return jsonify({'status': 'success', 'user': current_user.id})

# ══════════════════════════════════════════════════════════════
# LEADS
# ══════════════════════════════════════════════════════════════
@app.route('/api/leads', methods=['GET'])
@login_required
def get_leads():
    try:
        return jsonify({'status': 'success', 'data': get_all_leads()})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/update-lead', methods=['POST'])
@login_required
def update_lead():
    data = request.json or {}
    lead_id = data.get('lead_id')
    new_action = data.get('action')
    if not lead_id or not new_action:
        return jsonify({'status': 'error', 'message': 'Missing data.'}), 400
    try:
        update_lead_action(lead_id, new_action)
        return jsonify({'status': 'success', 'message': 'Lead updated.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/delete-lead', methods=['POST'])
@login_required
def delete_lead():
    import sqlite3
    data = request.json or {}
    lead_id = data.get('lead_id')
    if not lead_id:
        return jsonify({'status': 'error', 'message': 'Missing lead_id.'}), 400
    try:
        db_path = os.path.join(os.path.dirname(__file__), 'data', 'mission_control.db')
        conn = sqlite3.connect(db_path)
        conn.execute('DELETE FROM leads WHERE id = ?', (lead_id,))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ══════════════════════════════════════════════════════════════
# SCRAPER ENGINE
# ══════════════════════════════════════════════════════════════
def _run_scraper(industry):
    global scraper_state
    script_path = os.path.join(os.path.dirname(__file__), 'src', 'genuine_campaign.py')
    scraper_state.update({
        'running': True, 'industry': industry, 'leads_found': 0,
        'current_state': f'Launching scraper for: {industry}',
        'started_at': datetime.now().strftime('%H:%M:%S'), 'error': None, 'log': []
    })
    try:
        proc = subprocess.Popen(
            [sys.executable, script_path, industry],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, cwd=os.path.dirname(__file__)
        )
        for line in proc.stdout:
            line = line.strip()
            if line:
                scraper_state['log'].append(line)
                scraper_state['log'] = scraper_state['log'][-60:]  # keep last 60 lines
                if 'SAVED TO CLOUD DB' in line or 'SUCCESS' in line.upper():
                    scraper_state['leads_found'] = len(get_all_leads())
                if line.startswith('[') and ']' in line:
                    scraper_state['current_state'] = line
        proc.wait()
        scraper_state['current_state'] = 'Completed'
        scraper_state['leads_found'] = len(get_all_leads())
    except Exception as e:
        scraper_state['error'] = str(e)
        scraper_state['current_state'] = 'Error'
    finally:
        scraper_state['running'] = False

@app.route('/api/start-scraping', methods=['POST'])
@login_required
def start_scraping():
    if scraper_state['running']:
        return jsonify({'status': 'error', 'message': 'Scraper is already running.'}), 409
    data = request.json or {}
    industry = data.get('industry', 'dentist').strip().lower() or 'dentist'
    t = threading.Thread(target=_run_scraper, args=(industry,), daemon=True)
    t.start()
    return jsonify({'status': 'success', 'message': f'Scraper launched for: {industry}'})

@app.route('/api/stop-scraping', methods=['POST'])
@login_required
def stop_scraping():
    scraper_state['running'] = False
    scraper_state['current_state'] = 'Stopped by user'
    return jsonify({'status': 'success'})

@app.route('/api/scraper-status', methods=['GET'])
@login_required
def scraper_status():
    return jsonify({
        'status': 'success',
        'running': scraper_state['running'],
        'industry': scraper_state['industry'],
        'leads_found': scraper_state['leads_found'] or len(get_all_leads()),
        'current_state': scraper_state['current_state'],
        'started_at': scraper_state['started_at'],
        'error': scraper_state['error'],
        'log': scraper_state['log'][-10:]
    })

# ══════════════════════════════════════════════════════════════
# EMAIL ENGINE
# ══════════════════════════════════════════════════════════════
def _generate_email_draft(lead):
    """Generate an email draft from a DB lead record."""
    try:
        import json as _json
        from src.email_generator import generate_personalized_email
        pains = _json.loads(lead.get('pain_points', '[]')) if lead.get('pain_points') else []
        analysis = {
            'hard_pain_points': pains,
            'estimated_revenue_leak': lead.get('leak_amount', 'significant revenue'),
            'market_gap_analysis': pains[0] if pains else 'Local market has digital gaps.',
            'conversion_friction': pains[1] if len(pains) > 1 else '',
            'fomo_intelligence': ''
        }
        draft = generate_personalized_email(
            lead.get('name', 'Business'),
            lead.get('niche', 'Local Business'),
            analysis,
            lead.get('location', 'your area')
        )
        return draft.get('subject', 'A quick question'), draft.get('body', '')
    except Exception as e:
        print(f'[EmailGen] Error: {e}')
        name = lead.get('name', 'Business')
        return f'Question for {name}', f'Hi {name} Team,\n\nI found some AI automation opportunities for your business. Would you be open to a quick 15-minute call?\n\nBest regards,\n{os.getenv("YOUR_NAME", "Pranshu")}'

def _send_one_email(to_email, subject, body):
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', 465))
    email_user = os.getenv('EMAIL_USER', '')
    email_pass = os.getenv('EMAIL_PASS', '')
    sender_name = os.getenv('YOUR_NAME', 'Pranshu')
    bcc = os.getenv('BCC_EMAIL', '')

    if not email_user or not email_pass or 'your_gmail' in email_user:
        return False, 'Gmail credentials not configured in .env'

    try:
        msg = MIMEMultipart()
        msg['From'] = f'{sender_name} <{email_user}>'
        msg['To'] = to_email
        msg['Subject'] = subject
        if bcc:
            msg['Bcc'] = bcc
        msg.attach(MIMEText(body.replace('\n', '<br>'), 'html'))
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(email_user, email_pass)
            server.send_message(msg)
        return True, 'SENT'
    except Exception as e:
        return False, str(e)

def _run_email_campaign():
    global email_state
    import sqlite3
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'mission_control.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    targets = [dict(r) for r in conn.execute("SELECT * FROM leads WHERE action='SEND'").fetchall()]
    conn.close()

    email_state.update({'running': True, 'sent': 0, 'errors': 0, 'total': len(targets), 'done': False})

    for lead in targets:
        if not email_state['running']:
            break
        email_state['current'] = lead.get('name', '')
        subject, body = _generate_email_draft(lead)
        success, msg = _send_one_email(lead.get('email', ''), subject, body)

        conn = sqlite3.connect(db_path)
        if success:
            email_state['sent'] += 1
            conn.execute("UPDATE leads SET action='COMPLETED', status='SENT' WHERE id=?", (lead['id'],))
        else:
            email_state['errors'] += 1
            conn.execute("UPDATE leads SET status=? WHERE id=?", (f'Error: {msg}', lead['id']))
        conn.commit()
        conn.close()
        time.sleep(random.uniform(2, 4))

    email_state.update({'running': False, 'done': True, 'current': ''})

@app.route('/api/send-emails', methods=['POST'])
@login_required
def send_emails():
    if email_state['running']:
        return jsonify({'status': 'error', 'message': 'Email campaign already running.'}), 409
    targets = [l for l in get_all_leads() if l.get('action') == 'SEND']
    if not targets:
        return jsonify({'status': 'error', 'message': 'No leads marked as SEND. Select leads and click Mark → SEND first.'}), 400
    t = threading.Thread(target=_run_email_campaign, daemon=True)
    t.start()
    return jsonify({'status': 'success', 'message': f'Email campaign started for {len(targets)} leads.'})

@app.route('/api/email-status', methods=['GET'])
@login_required
def email_status():
    return jsonify({'status': 'success', **email_state})

# ══════════════════════════════════════════════════════════════
# EXPORT
# ══════════════════════════════════════════════════════════════
@app.route('/api/export-excel', methods=['GET'])
@login_required
def export_excel():
    try:
        # Write outbox.json from DB leads then run excel_manager
        leads = get_all_leads()
        outbox = []
        for lead in leads:
            import json as _json
            pains = _json.loads(lead.get('pain_points', '[]')) if lead.get('pain_points') else []
            subject, body = _generate_email_draft(lead)
            outbox.append({
                'name': lead['name'], 'url': lead.get('website', ''),
                'email': lead.get('email', ''), 'location': lead.get('location', ''),
                'niche': lead.get('niche', 'Business'),
                'analysis': {
                    'hard_pain_points': pains,
                    'estimated_revenue_leak': lead.get('leak_amount', ''),
                    'market_gap_analysis': pains[0] if pains else '',
                    'conversion_friction': '', 'fomo_intelligence': ''
                },
                'email_draft': {'subject': subject, 'body': body}
            })
        os.makedirs('data', exist_ok=True)
        with open('data/outbox.json', 'w', encoding='utf-8') as f:
            json.dump(outbox, f, indent=2)

        # Run excel_manager
        script_path = os.path.join(os.path.dirname(__file__), 'src', 'excel_manager.py')
        subprocess.run([sys.executable, script_path], cwd=os.path.dirname(__file__))

        # Find the generated Excel file
        excel_files = [f for f in os.listdir('.') if f.endswith('_Industry_Master.xlsx')]
        if excel_files:
            excel_file = sorted(excel_files)[-1]
            return send_file(
                os.path.abspath(excel_file),
                as_attachment=True,
                download_name=excel_file,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        return jsonify({'status': 'error', 'message': 'Excel file not generated. Add leads first.'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    leads = get_all_leads()
    return jsonify({
        'status': 'success',
        'total': len(leads),
        'ready': sum(1 for l in leads if l.get('action') == 'READY'),
        'send': sum(1 for l in leads if l.get('action') == 'SEND'),
        'sent': sum(1 for l in leads if l.get('action') == 'COMPLETED'),
        'scraper_running': scraper_state['running'],
        'email_running': email_state['running'],
    })

# ══════════════════════════════════════════════════════════════
# SERVE DASHBOARD
# ══════════════════════════════════════════════════════════════
@app.route('/')
@app.route('/mission-hub')
def serve_dashboard():
    return send_from_directory('dashboard', 'index.html')

@app.route('/dashboard/<path:path>')
def serve_dashboard_files(path):
    return send_from_directory('dashboard', path)

if __name__ == '__main__':
    print("AI Consulting Engine — Full Stack Online")
    port = int(os.getenv('PORT', 5000))
    app.run(debug=os.getenv('FLASK_DEBUG', 'true').lower() == 'true',
            host='0.0.0.0', port=port)
