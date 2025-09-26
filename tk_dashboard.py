
from flask import Flask, render_template_string, jsonify
import json
import os
from datetime import datetime
import threading
import time

app = Flask(__name__)

# Global variables to store system state
system_state = {
    'status': 'idle',
    'last_failure': None,
    'patches_applied': 0,
    'uptime': datetime.now(),
    'current_test': None,
    'logs': []
}

def add_log(message, level='info'):
    """Add a log entry with timestamp"""
    log_entry = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'message': message,
        'level': level
    }
    system_state['logs'].append(log_entry)
    # Keep only last 50 logs
    if len(system_state['logs']) > 50:
        system_state['logs'] = system_state['logs'][-50:]

# HTML template for the dashboard
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Quantum Loop Debugger Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 2.5em;
            margin: 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
            margin: 10px 0;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .stat-card h3 {
            margin: 0 0 10px 0;
            font-size: 1.1em;
            opacity: 0.8;
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }
        .status-running { color: #4CAF50; }
        .status-idle { color: #FFC107; }
        .status-error { color: #F44336; }
        .logs-section {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .logs-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .logs-container {
            max-height: 400px;
            overflow-y: auto;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 10px;
            padding: 15px;
        }
        .log-entry {
            margin-bottom: 8px;
            padding: 8px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }
        .log-info { background: rgba(33, 150, 243, 0.2); }
        .log-warning { background: rgba(255, 193, 7, 0.2); }
        .log-error { background: rgba(244, 67, 54, 0.2); }
        .log-success { background: rgba(76, 175, 80, 0.2); }
        .timestamp {
            color: #ccc;
            font-size: 0.8em;
        }
        .refresh-btn {
            background: rgba(255, 255, 255, 0.2);
            border: none;
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 0.9em;
            transition: all 0.3s ease;
        }
        .refresh-btn:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-2px);
        }
        .quantum-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔬 Quantum Loop Debugger</h1>
            <p>Self-Healing Code System Dashboard</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>System Status</h3>
                <div class="stat-value status-{{ status_class }}">
                    <span class="quantum-indicator" style="background-color: {{ status_color }};"></span>
                    {{ status.title() }}
                </div>
            </div>
            
            <div class="stat-card">
                <h3>Patches Applied</h3>
                <div class="stat-value">{{ patches_applied }}</div>
            </div>
            
            <div class="stat-card">
                <h3>System Uptime</h3>
                <div class="stat-value">{{ uptime }}</div>
            </div>
            
            <div class="stat-card">
                <h3>Current Test</h3>
                <div class="stat-value" style="font-size: 1.2em;">
                    {{ current_test or 'None' }}
                </div>
            </div>
        </div>
        
        {% if last_failure %}
        <div class="stat-card" style="margin-bottom: 30px;">
            <h3>Last Failure</h3>
            <div style="font-size: 1em; text-align: left;">
                <strong>Time:</strong> {{ last_failure.timestamp }}<br>
                <strong>Error:</strong> {{ last_failure.error }}<br>
                <strong>Status:</strong> {{ last_failure.status }}
            </div>
        </div>
        {% endif %}
        
        <div class="logs-section">
            <div class="logs-header">
                <h3>System Logs</h3>
                <button class="refresh-btn" onclick="refreshLogs()">🔄 Refresh</button>
            </div>
            <div class="logs-container" id="logs-container">
                {% for log in logs %}
                <div class="log-entry log-{{ log.level }}">
                    <span class="timestamp">[{{ log.timestamp }}]</span>
                    {{ log.message }}
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
    
    <script>
        function refreshLogs() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    location.reload();
                })
                .catch(error => console.error('Error:', error));
        }
        
        // Auto-refresh every 5 seconds
        setInterval(refreshLogs, 5000);
    </script>
</body>
</html>
'''

@app.route('/')
def dashboard():
    """Main dashboard route"""
    # Calculate uptime
    uptime_delta = datetime.now() - system_state['uptime']
    hours = uptime_delta.seconds // 3600
    minutes = (uptime_delta.seconds % 3600) // 60
    uptime_str = f"{uptime_delta.days}d {hours}h {minutes}m"
    
    # Determine status styling
    status_classes = {
        'running': 'running',
        'idle': 'idle',
        'error': 'error'
    }
    
    status_colors = {
        'running': '#4CAF50',
        'idle': '#FFC107',
        'error': '#F44336'
    }
    
    return render_template_string(DASHBOARD_HTML,
                                status=system_state['status'],
                                status_class=status_classes.get(system_state['status'], 'idle'),
                                status_color=status_colors.get(system_state['status'], '#FFC107'),
                                patches_applied=system_state['patches_applied'],
                                uptime=uptime_str,
                                current_test=system_state['current_test'],
                                last_failure=system_state['last_failure'],
                                logs=list(reversed(system_state['logs'])))

@app.route('/api/status')
def api_status():
    """API endpoint for system status"""
    return jsonify(system_state)

@app.route('/api/update_status', methods=['POST'])
def update_status():
    """API endpoint to update system status"""
    try:
        from flask import request
        data = request.get_json()
        
        if 'status' in data:
            system_state['status'] = data['status']
            add_log(f"Status updated to: {data['status']}")
        
        if 'current_test' in data:
            system_state['current_test'] = data['current_test']
            add_log(f"Current test: {data['current_test']}")
        
        if 'failure' in data:
            system_state['last_failure'] = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'error': data['failure'].get('error', 'Unknown error'),
                'status': data['failure'].get('status', 'Failed')
            }
            add_log(f"Failure recorded: {data['failure'].get('error', 'Unknown')}", 'error')
        
        if 'patch_applied' in data and data['patch_applied']:
            system_state['patches_applied'] += 1
            add_log("Patch successfully applied", 'success')
        
        if 'log' in data:
            add_log(data['log'], data.get('log_level', 'info'))
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def run_dashboard():
    """Run the dashboard server"""
    add_log("Quantum Loop Debugger Dashboard starting...")
    add_log("Dashboard available at http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

if __name__ == '__main__':
    # Add initial log entries
    add_log("System initialized", 'success')
    add_log("Monitoring for failures and patches...")
    
    run_dashboard()
