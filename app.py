"""NaviX — main Flask application. Works with flat repo structure."""
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from datetime import datetime
import os

from auth import auth_bp, login_required
from data import INCIDENTS
from engine import (get_state, get_kpis, get_predictions, get_segments,
                    get_incidents, get_zone_scores, get_analytics, calculate_route,
                    set_weather)
from routing import enrich_route_with_street_geometry

# template_folder='.' means Flask looks for .html files in the SAME directory as app.py
# This works whether files are in root OR templates/ subfolder
app = Flask(__name__, template_folder='.', static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', 'navix-dev-secret-2026')
app.config['ORS_API_KEY'] = os.environ.get('ORS_API_KEY', '')
app.register_blueprint(auth_bp)

@app.route('/')
def home():
    return redirect(url_for('dashboard') if session.get('user_email') else url_for('auth.login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', active='dashboard')

@app.route('/map')
@login_required
def map_view():
    return render_template('map.html', active='map')

@app.route('/routes')
@login_required
def routes():
    return render_template('routes.html', active='routes')

@app.route('/analytics')
@login_required
def analytics():
    return render_template('analytics.html', active='analytics')

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html', active='settings')

@app.route('/pricing')
def pricing():
    return render_template('pricing.html', active='pricing',
                           current_plan=session.get('subscription_plan', 'free'))

@app.route('/subscribe/<plan>')
@login_required
def subscribe(plan):
    if plan not in ['free', 'pro', 'premium']:
        flash('Invalid plan.', 'error')
        return redirect(url_for('pricing'))
    session['subscription_plan'] = plan
    flash(f'{"Now on Free plan." if plan=="free" else f"Welcome to {plan.title()}!"}', 'success')
    return redirect(url_for('dashboard'))

@app.route('/api/state')
def api_state(): return jsonify(get_state())

@app.route('/api/kpis')
def api_kpis(): return jsonify(get_kpis())

@app.route('/api/predictions')
def api_predictions(): return jsonify(get_predictions())

@app.route('/api/segments')
def api_segments(): return jsonify(get_segments())

@app.route('/api/incidents')
def api_incidents(): return jsonify(get_incidents())

@app.route('/api/zone-scores')
def api_zone_scores(): return jsonify(get_zone_scores())

@app.route('/api/analytics')
def api_analytics(): return jsonify(get_analytics())

@app.route('/api/weather', methods=['POST'])
def api_weather():
    w = request.json.get('weather', 'clear')
    set_weather(w)
    return jsonify({'ok': True, 'weather': w})

@app.route('/api/route/calculate', methods=['POST'])
def api_route():
    d = request.json or {}
    route = calculate_route(d.get('origin'), d.get('destination'))
    return jsonify(enrich_route_with_street_geometry(route, app.config['ORS_API_KEY']))

@app.route('/healthz')
def healthz(): return jsonify({'status': 'ok', 'time': datetime.utcnow().isoformat()})

@app.context_processor
def inject_globals():
    return {
        'user_email': session.get('user_email'),
        'user_name': session.get('user_name'),
        'subscription_plan': session.get('subscription_plan', 'free'),
        'current_year': datetime.utcnow().year,
        'active_alerts': sum(1 for i in INCIDENTS if i.get('status') == 'active'),
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
