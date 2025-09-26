
from flask import Flask, render_template_string, jsonify
import json
import os
from datetime import datetime
import threading
import time
import requests
import asyncio
import aiohttp

app = Flask(__name__)

# Global variables to store system state
system_state = {
    'status': 'idle',
    'last_failure': None,
    'patches_applied': 0,
    'uptime': datetime.now(),
    'current_test': None,
    'logs': [],
    'openrouter': {
        'current_model': None,
        'available_models': 0,
        'total_models': 0,
        'usage_summary': {},
        'rotation_history': [],
        'last_updated': None
    }
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

async def fetch_openrouter_status():
    """Fetch OpenRouter status from AI Engineer service"""
    try:
        async with aiohttp.ClientSession() as session:
            # Try to get status from AI Engineer service
            async with session.post(
                'http://ai-engineer:8080/api/request',
                json={'type': 'openrouter_status'},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        system_state['openrouter'].update({
                            'current_model': data.get('current_model'),
                            'available_models': len([m for m in data.get('available_models', {}).values() if m.get('available')]),
                            'total_models': len(data.get('available_models', {})),
                            'usage_summary': data.get('usage_summary', {}),
                            'rotation_history': data.get('rotation_history', [])[-10:],  # Last 10 rotations
                            'last_updated': datetime.now().isoformat()
                        })
                        add_log(f"OpenRouter status updated - Current model: {data.get('current_model')}", 'info')
                    else:
                        add_log(f"Failed to get OpenRouter status: {data.get('error')}", 'warning')
                else:
                    add_log(f"OpenRouter status request failed: {response.status}", 'warning')
    except Exception as e:
        add_log(f"Error fetching OpenRouter status: {str(e)}", 'error')

def update_openrouter_status():
    """Background thread to update OpenRouter status"""
    while True:
        try:
            # Run async function in thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(fetch_openrouter_status())
            loop.close()
        except Exception as e:
            add_log(f"OpenRouter status update error: {str(e)}", 'error')
        
        time.sleep(30)  # Update every 30 seconds

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
            max-width: 1400px;
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
        
        /* OpenRouter specific styles */
        .openrouter-section {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .openrouter-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .model-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .model-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 15px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .model-card.active {
            border-color: #4CAF50;
            background: rgba(76, 175, 80, 0.1);
        }
        .model-card.unavailable {
            opacity: 0.5;
            border-color: #F44336;
        }
        .model-name {
            font-weight: bold;
            margin-bottom: 5px;
        }
        .model-provider {
            font-size: 0.9em;
            opacity: 0.7;
            margin-bottom: 10px;
        }
        .model-usage {
            font-size: 0.8em;
            display: flex;
            justify-content: space-between;
        }
        .rotation-history {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 15px;
            max-height: 200px;
            overflow-y: auto;
        }
        .rotation-entry {
            padding: 5px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            font-size: 0.9em;
        }
        .rotation-entry:last-child {
            border-bottom: none;
        }
        
        .logs-section {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .logs-section h3 {
            margin: 0 0 15px 0;
            font-size: 1.3em;
        }
        .logs-container {
            max-height: 300px;
            overflow-y: auto;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 10px;
            padding: 15px;
        }
        .log-entry {
            margin-bottom: 8px;
            padding: 5px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }
        .log-info { background: rgba(33, 150, 243, 0.2); }
        .log-warning { background: rgba(255, 193, 7, 0.2); }
        .log-error { background: rgba(244, 67, 54, 0.2); }
        .log-success { background: rgba(76, 175, 80, 0.2); }
        
        .refresh-btn {
            background: rgba(255, 255, 255, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.3);
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
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        .updating {
            animation: pulse 1s infinite;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Quantum Loop Debugger</h1>
            <p>Self-healing AI Development System with OpenRouter Free Models</p>
            <p>Uptime: <span id="uptime">{{ uptime }}</span></p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>System Status</h3>
                <div class="stat-value status-{{ status }}">{{ status.upper() }}</div>
            </div>
            <div class="stat-card">
                <h3>Patches Applied</h3>
                <div class="stat-value">{{ patches_applied }}</div>
            </div>
            <div class="stat-card">
                <h3>Current Test</h3>
                <div class="stat-value">{{ current_test or 'None' }}</div>
            </div>
            <div class="stat-card">
                <h3>Last Failure</h3>
                <div class="stat-value">{{ last_failure or 'None' }}</div>
            </div>
        </div>
        
        <!-- OpenRouter Status Section -->
        <div class="openrouter-section">
            <div class="openrouter-header">
                <h3>🔄 OpenRouter Free Models Status</h3>
                <button class="refresh-btn" onclick="refreshOpenRouterStatus()">Refresh Status</button>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>Current Model</h3>
                    <div class="stat-value" id="current-model">{{ openrouter.current_model or 'None' }}</div>
                </div>
                <div class="stat-card">
                    <h3>Available Models</h3>
                    <div class="stat-value">{{ openrouter.available_models }}/{{ openrouter.total_models }}</div>
                </div>
                <div class="stat-card">
                    <h3>Last Updated</h3>
                    <div class="stat-value" style="font-size: 1em;">
                        {{ openrouter.last_updated.split('T')[1][:8] if openrouter.last_updated else 'Never' }}
                    </div>
                </div>
                <div class="stat-card">
                    <h3>Model Rotations</h3>
                    <div class="stat-value">{{ openrouter.rotation_history|length }}</div>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px;">
                <div>
                    <h4>Model Usage Summary</h4>
                    <div class="model-grid" id="model-usage">
                        {% for model_id, usage in openrouter.usage_summary.items() %}
                        <div class="model-card {% if usage.available %}{% if model_id == openrouter.current_model %}active{% endif %}{% else %}unavailable{% endif %}">
                            <div class="model-name">{{ usage.name }}</div>
                            <div class="model-provider">{{ usage.provider }}</div>
                            <div class="model-usage">
                                <span>Hourly: {{ usage.hourly_usage }}</span>
                                <span>Daily: {{ usage.daily_usage }}</span>
                            </div>
                            <div class="model-usage">
                                <span>Total: {{ usage.total_requests }}</span>
                                <span>{% if usage.available %}✅ Available{% else %}❌ Quota Full{% endif %}</span>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
                
                <div>
                    <h4>Recent Model Rotations</h4>
                    <div class="rotation-history">
                        {% for rotation in openrouter.rotation_history %}
                        <div class="rotation-entry">
                            <div>{{ rotation.timestamp.split('T')[1][:8] }}</div>
                            <div>{{ rotation.from_model or 'None' }} → {{ rotation.to_model }}</div>
                            <div style="opacity: 0.7; font-size: 0.8em;">{{ rotation.reason }}</div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>
        
        <div class="logs-section">
            <h3>📋 System Logs</h3>
            <div class="logs-container">
                {% for log in logs %}
                <div class="log-entry log-{{ log.level }}">
                    <strong>{{ log.timestamp }}</strong> [{{ log.level.upper() }}] {{ log.message }}
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
    
    <script>
        // Auto-refresh every 30 seconds
        setInterval(function() {
            location.reload();
        }, 30000);
        
        // Update uptime every second
        let startTime = new Date('{{ uptime }}');
        setInterval(function() {
            let now = new Date();
            let diff = now - startTime;
            let hours = Math.floor(diff / (1000 * 60 * 60));
            let minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            let seconds = Math.floor((diff % (1000 * 60)) / 1000);
            document.getElementById('uptime').textContent = 
                hours + 'h ' + minutes + 'm ' + seconds + 's';
        }, 1000);
        
        async function refreshOpenRouterStatus() {
            const btn = document.querySelector('.refresh-btn');
            btn.classList.add('updating');
            btn.textContent = 'Updating...';
            
            try {
                const response = await fetch('/api/refresh-openrouter');
                if (response.ok) {
                    setTimeout(() => location.reload(), 2000);
                } else {
                    throw new Error('Failed to refresh');
                }
            } catch (error) {
                console.error('Refresh failed:', error);
                btn.textContent = 'Refresh Failed';
                setTimeout(() => {
                    btn.textContent = 'Refresh Status';
                    btn.classList.remove('updating');
                }, 3000);
            }
        }
        
        // Force model rotation
        async function forceRotation() {
            try {
                const response = await fetch('/api/force-rotation', { method: 'POST' });
                if (response.ok) {
                    setTimeout(() => location.reload(), 2000);
                }
            } catch (error) {
                console.error('Rotation failed:', error);
            }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def dashboard():
    """Main dashboard route"""
    uptime_delta = datetime.now() - system_state['uptime']
    uptime_str = f"{uptime_delta.days}d {uptime_delta.seconds//3600}h {(uptime_delta.seconds//60)%60}m"
    
    return render_template_string(DASHBOARD_HTML, 
                                uptime=uptime_str,
                                **system_state)

@app.route('/api/status')
def api_status():
    """API endpoint for system status"""
    return jsonify(system_state)

@app.route('/api/refresh-openrouter')
def api_refresh_openrouter():
    """API endpoint to refresh OpenRouter status"""
    try:
        # Trigger immediate update
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(fetch_openrouter_status())
        loop.close()
        
        add_log("OpenRouter status manually refreshed", 'info')
        return jsonify({'success': True})
    except Exception as e:
        add_log(f"Manual OpenRouter refresh failed: {str(e)}", 'error')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/force-rotation', methods=['POST'])
def api_force_rotation():
    """API endpoint to force model rotation"""
    try:
        # Send rotation request to AI Engineer
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def force_rotation():
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'http://ai-engineer:8080/api/request',
                    json={'type': 'force_model_rotation'},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return await response.json()
        
        result = loop.run_until_complete(force_rotation())
        loop.close()
        
        if result.get('success'):
            add_log(f"Model rotation forced: {result.get('old_model')} → {result.get('new_model')}", 'info')
            return jsonify({'success': True, 'result': result})
        else:
            add_log(f"Model rotation failed: {result.get('error')}", 'error')
            return jsonify({'success': False, 'error': result.get('error')}), 500
            
    except Exception as e:
        add_log(f"Force rotation request failed: {str(e)}", 'error')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/logs')
def api_logs():
    """API endpoint for logs"""
    return jsonify({'logs': system_state['logs']})

def update_system_status():
    """Background thread to update system status"""
    while True:
        try:
            # Update system status based on various factors
            # This is a placeholder - in real implementation, you'd check actual system health
            system_state['status'] = 'running'
            
            # Simulate some activity
            if system_state['current_test'] is None:
                system_state['current_test'] = 'test_script.py'
            
        except Exception as e:
            add_log(f"Status update error: {str(e)}", 'error')
            system_state['status'] = 'error'
        
        time.sleep(10)  # Update every 10 seconds

# MCP Server functionality
class MCPServer:
    def __init__(self, name, port):
        self.name = name
        self.port = port
        
    async def handle_method(self, method, params):
        """Handle MCP method calls"""
        if method == 'get_system_status':
            return {
                'success': True,
                'status': system_state,
                'timestamp': datetime.now().isoformat()
            }
        elif method == 'add_log':
            message = params.get('message', '')
            level = params.get('level', 'info')
            add_log(message, level)
            return {'success': True}
        elif method == 'health_check':
            return {
                'success': True,
                'service': self.name,
                'status': 'healthy',
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'success': False,
                'error': f'Unknown method: {method}'
            }

def start_mcp_server(port):
    """Start MCP server (placeholder implementation)"""
    # This would typically start an actual MCP server
    # For now, we'll just log that it's starting
    add_log(f"MCP server starting on port {port}", 'info')

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Quantum Loop Debugger Dashboard')
    parser.add_argument('--port', type=int, default=5000, help='Web server port')
    parser.add_argument('--mcp-mode', action='store_true', help='Enable MCP server mode')
    parser.add_argument('--mcp-port', type=int, default=8082, help='MCP server port')
    
    args = parser.parse_args()
    
    # Initialize system
    add_log("🚀 Quantum Loop Debugger Dashboard starting...", 'info')
    add_log("🔄 OpenRouter Free Models integration enabled", 'info')
    
    # Start background threads
    status_thread = threading.Thread(target=update_system_status, daemon=True)
    status_thread.start()
    
    openrouter_thread = threading.Thread(target=update_openrouter_status, daemon=True)
    openrouter_thread.start()
    
    if args.mcp_mode:
        add_log(f"🔌 Starting MCP server on port {args.mcp_port}", 'info')
        start_mcp_server(args.mcp_port)
    
    # Start web server
    add_log(f"🌐 Starting web dashboard on port {args.port}", 'info')
    app.run(host='0.0.0.0', port=args.port, debug=False)
