#!/usr/bin/env python3
"""
Enhanced Dashboard for Quantum Loop Debugger with Self-Learning Metrics
Displays learning metrics, memory status, feedback analytics, and knowledge insights
"""

from flask import Flask, render_template_string, jsonify, request
import json
import os
from datetime import datetime, timedelta
import threading
import time
import requests
import asyncio
import aiohttp
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    },
    'learning': {
        'memory_stats': {},
        'feedback_summary': {},
        'learning_insights': {},
        'knowledge_stats': {},
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
    # Keep only last 100 logs
    if len(system_state['logs']) > 100:
        system_state['logs'] = system_state['logs'][-100:]

async def fetch_openrouter_status():
    """Fetch OpenRouter status from AI Engineer service"""
    try:
        async with aiohttp.ClientSession() as session:
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
                            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        add_log("OpenRouter status updated", 'info')
                    else:
                        add_log(f"OpenRouter status error: {data.get('error')}", 'warning')
                else:
                    add_log(f"OpenRouter status HTTP error: {response.status}", 'warning')
    except Exception as e:
        add_log(f"Failed to fetch OpenRouter status: {e}", 'error')

async def fetch_learning_status():
    """Fetch learning system status from MCP Learning Server"""
    try:
        async with aiohttp.ClientSession() as session:
            # Get learning status from Enhanced AI Engineer
            async with session.post(
                'http://ai-engineer:8080/api/request',
                json={'type': 'learning_status'},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        system_state['learning'].update({
                            'memory_stats': data.get('memory_system', {}),
                            'feedback_summary': data.get('feedback_engine', {}),
                            'learning_insights': data.get('learning_insights', {}),
                            'knowledge_stats': data.get('knowledge_system', {}),
                            'learning_metrics': data.get('learning_metrics', {}),
                            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        add_log("Learning status updated", 'info')
                    else:
                        add_log(f"Learning status error: {data.get('error')}", 'warning')
                else:
                    add_log(f"Learning status HTTP error: {response.status}", 'warning')
            
            # Also try to get status directly from MCP Learning Server
            try:
                async with session.get(
                    'http://mcp-learning:8084/status',
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as mcp_response:
                    if mcp_response.status == 200:
                        mcp_data = await mcp_response.json()
                        if mcp_data.get('success'):
                            # Merge MCP server data
                            system_state['learning']['mcp_server_status'] = mcp_data.get('status', {})
                            add_log("MCP Learning Server status updated", 'info')
            except Exception as mcp_e:
                add_log(f"MCP Learning Server not available: {mcp_e}", 'debug')
                
    except Exception as e:
        add_log(f"Failed to fetch learning status: {e}", 'error')

async def fetch_system_status():
    """Fetch general system status"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'http://ai-engineer:8080/api/request',
                json={'type': 'system_health'},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        health = data.get('health', {})
                        system_state['status'] = health.get('ai_engineer', 'unknown')
                        add_log("System health updated", 'info')
                    else:
                        add_log(f"System health error: {data.get('error')}", 'warning')
                        system_state['status'] = 'error'
                else:
                    add_log(f"System health HTTP error: {response.status}", 'warning')
                    system_state['status'] = 'error'
    except Exception as e:
        add_log(f"Failed to fetch system status: {e}", 'error')
        system_state['status'] = 'offline'

def background_updater():
    """Background thread to update system status"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    while True:
        try:
            # Update all status information
            loop.run_until_complete(fetch_system_status())
            loop.run_until_complete(fetch_openrouter_status())
            loop.run_until_complete(fetch_learning_status())
            
            # Sleep for 30 seconds
            time.sleep(30)
        except Exception as e:
            add_log(f"Background updater error: {e}", 'error')
            time.sleep(60)  # Wait longer on error

# Start background updater
updater_thread = threading.Thread(target=background_updater, daemon=True)
updater_thread.start()

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template_string(ENHANCED_DASHBOARD_TEMPLATE)

@app.route('/api/status')
def api_status():
    """API endpoint for status data"""
    return jsonify(system_state)

@app.route('/api/trigger_action', methods=['POST'])
def trigger_action():
    """Trigger various actions"""
    try:
        data = request.get_json()
        action = data.get('action')
        
        if action == 'force_model_rotation':
            # Trigger model rotation
            response = requests.post(
                'http://ai-engineer:8080/api/request',
                json={'type': 'force_model_rotation'},
                timeout=10
            )
            return jsonify(response.json())
        
        elif action == 'trigger_optimization':
            # Trigger learning optimization
            response = requests.post(
                'http://ai-engineer:8080/api/request',
                json={'type': 'trigger_optimization'},
                timeout=10
            )
            return jsonify(response.json())
        
        elif action == 'cleanup_memory':
            # Trigger memory cleanup
            response = requests.post(
                'http://mcp-learning:8084/memory/cleanup',
                json={'days_to_keep': 30},
                timeout=10
            )
            return jsonify(response.json())
        
        else:
            return jsonify({'success': False, 'error': 'Unknown action'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/learning_insights')
def learning_insights():
    """Get detailed learning insights"""
    try:
        response = requests.get(
            'http://mcp-learning:8084/feedback/insights',
            timeout=10
        )
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/knowledge_search', methods=['POST'])
def knowledge_search():
    """Search knowledge base"""
    try:
        data = request.get_json()
        response = requests.post(
            'http://mcp-learning:8084/knowledge/search',
            json=data,
            timeout=10
        )
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Enhanced Dashboard HTML Template
ENHANCED_DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quantum Loop Debugger - Enhanced Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 40px rgba(0,0,0,0.15);
        }
        
        .card h3 {
            color: #4a5568;
            margin-bottom: 20px;
            font-size: 1.3em;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 10px;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-healthy { background-color: #48bb78; }
        .status-warning { background-color: #ed8936; }
        .status-error { background-color: #f56565; }
        .status-offline { background-color: #a0aec0; }
        
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #e2e8f0;
        }
        
        .metric:last-child {
            border-bottom: none;
        }
        
        .metric-label {
            font-weight: 500;
            color: #4a5568;
        }
        
        .metric-value {
            font-weight: 600;
            color: #2d3748;
        }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background-color: #e2e8f0;
            border-radius: 4px;
            overflow: hidden;
            margin: 5px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #48bb78, #38a169);
            transition: width 0.3s ease;
        }
        
        .log-container {
            max-height: 300px;
            overflow-y: auto;
            background: #f7fafc;
            border-radius: 8px;
            padding: 15px;
        }
        
        .log-entry {
            padding: 5px 0;
            border-bottom: 1px solid #e2e8f0;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }
        
        .log-entry:last-child {
            border-bottom: none;
        }
        
        .log-timestamp {
            color: #718096;
            margin-right: 10px;
        }
        
        .log-info { color: #3182ce; }
        .log-warning { color: #d69e2e; }
        .log-error { color: #e53e3e; }
        
        .action-buttons {
            display: flex;
            gap: 10px;
            margin-top: 15px;
            flex-wrap: wrap;
        }
        
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9em;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        
        .btn-secondary {
            background: #e2e8f0;
            color: #4a5568;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        .learning-metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        
        .learning-metric {
            text-align: center;
            padding: 15px;
            background: #f7fafc;
            border-radius: 8px;
        }
        
        .learning-metric-value {
            font-size: 1.8em;
            font-weight: 700;
            color: #2d3748;
            margin-bottom: 5px;
        }
        
        .learning-metric-label {
            font-size: 0.9em;
            color: #718096;
        }
        
        .chart-container {
            height: 200px;
            margin-top: 15px;
            background: #f7fafc;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #718096;
        }
        
        .knowledge-search {
            margin-top: 15px;
        }
        
        .search-input {
            width: 100%;
            padding: 10px;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            font-size: 1em;
        }
        
        .search-results {
            margin-top: 10px;
            max-height: 200px;
            overflow-y: auto;
        }
        
        .search-result {
            padding: 10px;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            margin-bottom: 5px;
            background: #f7fafc;
        }
        
        .search-result-title {
            font-weight: 600;
            color: #2d3748;
            margin-bottom: 5px;
        }
        
        .search-result-content {
            font-size: 0.9em;
            color: #4a5568;
        }
        
        @media (max-width: 768px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .learning-metrics {
                grid-template-columns: repeat(2, 1fr);
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 Quantum Loop Debugger</h1>
            <p>Enhanced AI Engineer with Self-Learning Capabilities</p>
        </div>
        
        <div class="dashboard-grid">
            <!-- System Status Card -->
            <div class="card">
                <h3>🔧 System Status</h3>
                <div class="metric">
                    <span class="metric-label">AI Engineer Status</span>
                    <span class="metric-value">
                        <span id="system-status-indicator" class="status-indicator status-offline"></span>
                        <span id="system-status">Loading...</span>
                    </span>
                </div>
                <div class="metric">
                    <span class="metric-label">Uptime</span>
                    <span class="metric-value" id="uptime">Calculating...</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Patches Applied</span>
                    <span class="metric-value" id="patches-applied">0</span>
                </div>
                <div class="action-buttons">
                    <button class="btn btn-primary" onclick="triggerAction('force_model_rotation')">🔄 Rotate Model</button>
                    <button class="btn btn-secondary" onclick="refreshStatus()">🔄 Refresh</button>
                </div>
            </div>
            
            <!-- OpenRouter Status Card -->
            <div class="card">
                <h3>🤖 OpenRouter Status</h3>
                <div class="metric">
                    <span class="metric-label">Current Model</span>
                    <span class="metric-value" id="current-model">Loading...</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Available Models</span>
                    <span class="metric-value" id="available-models">0/0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Model Rotations</span>
                    <span class="metric-value" id="model-rotations">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Last Updated</span>
                    <span class="metric-value" id="openrouter-updated">Never</span>
                </div>
            </div>
            
            <!-- Learning System Status Card -->
            <div class="card">
                <h3>🧠 Learning System</h3>
                <div class="learning-metrics">
                    <div class="learning-metric">
                        <div class="learning-metric-value" id="total-experiences">0</div>
                        <div class="learning-metric-label">Experiences</div>
                    </div>
                    <div class="learning-metric">
                        <div class="learning-metric-value" id="success-rate">0%</div>
                        <div class="learning-metric-label">Success Rate</div>
                    </div>
                    <div class="learning-metric">
                        <div class="learning-metric-value" id="knowledge-items">0</div>
                        <div class="learning-metric-label">Knowledge Items</div>
                    </div>
                    <div class="learning-metric">
                        <div class="learning-metric-value" id="adaptations">0</div>
                        <div class="learning-metric-label">Adaptations</div>
                    </div>
                </div>
                <div class="action-buttons">
                    <button class="btn btn-primary" onclick="triggerAction('trigger_optimization')">⚡ Optimize</button>
                    <button class="btn btn-secondary" onclick="triggerAction('cleanup_memory')">🧹 Cleanup</button>
                </div>
            </div>
            
            <!-- Memory System Card -->
            <div class="card">
                <h3>💾 Memory System</h3>
                <div class="metric">
                    <span class="metric-label">Total Experiences</span>
                    <span class="metric-value" id="memory-experiences">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Successful Experiences</span>
                    <span class="metric-value" id="memory-successful">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Recent Activity (7d)</span>
                    <span class="metric-value" id="memory-recent">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Memory Size</span>
                    <span class="metric-value" id="memory-size">0 MB</span>
                </div>
            </div>
            
            <!-- Feedback Engine Card -->
            <div class="card">
                <h3>📊 Feedback Engine</h3>
                <div class="metric">
                    <span class="metric-label">Overall Success Rate</span>
                    <span class="metric-value" id="feedback-success-rate">0%</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Avg Execution Time</span>
                    <span class="metric-value" id="feedback-exec-time">0s</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Total Events</span>
                    <span class="metric-value" id="feedback-events">0</span>
                </div>
                <div class="chart-container">
                    <span>Performance Trend Chart (Coming Soon)</span>
                </div>
            </div>
            
            <!-- Knowledge System Card -->
            <div class="card">
                <h3>📚 Knowledge System</h3>
                <div class="metric">
                    <span class="metric-label">Knowledge Items</span>
                    <span class="metric-value" id="knowledge-total">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Open Knowledge Gaps</span>
                    <span class="metric-value" id="knowledge-gaps">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Pending Proposals</span>
                    <span class="metric-value" id="knowledge-proposals">0</span>
                </div>
                <div class="knowledge-search">
                    <input type="text" class="search-input" placeholder="Search knowledge base..." id="knowledge-search-input">
                    <div class="search-results" id="knowledge-search-results"></div>
                </div>
            </div>
            
            <!-- System Logs Card -->
            <div class="card">
                <h3>📝 System Logs</h3>
                <div class="log-container" id="log-container">
                    <div class="log-entry">
                        <span class="log-timestamp">Loading...</span>
                        <span class="log-info">Initializing dashboard...</span>
                    </div>
                </div>
            </div>
            
            <!-- Learning Insights Card -->
            <div class="card">
                <h3>💡 Learning Insights</h3>
                <div id="learning-insights-content">
                    <div class="metric">
                        <span class="metric-label">Learning Velocity</span>
                        <span class="metric-value" id="learning-velocity">Calculating...</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Top Strength</span>
                        <span class="metric-value" id="top-strength">Analyzing...</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Improvement Area</span>
                        <span class="metric-value" id="improvement-area">Analyzing...</span>
                    </div>
                    <div class="chart-container">
                        <span>Learning Progress Chart (Coming Soon)</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let systemData = {};
        
        // Fetch system status
        async function fetchStatus() {
            try {
                const response = await fetch('/api/status');
                systemData = await response.json();
                updateDashboard();
            } catch (error) {
                console.error('Failed to fetch status:', error);
            }
        }
        
        // Update dashboard with latest data
        function updateDashboard() {
            // System Status
            const status = systemData.status || 'offline';
            document.getElementById('system-status').textContent = status;
            document.getElementById('system-status-indicator').className = 
                `status-indicator status-${status === 'healthy' ? 'healthy' : status === 'error' ? 'error' : 'offline'}`;
            
            // Uptime
            if (systemData.uptime) {
                const uptime = new Date(systemData.uptime);
                const now = new Date();
                const diff = Math.floor((now - uptime) / 1000 / 60); // minutes
                document.getElementById('uptime').textContent = `${diff} minutes`;
            }
            
            document.getElementById('patches-applied').textContent = systemData.patches_applied || 0;
            
            // OpenRouter Status
            const openrouter = systemData.openrouter || {};
            document.getElementById('current-model').textContent = openrouter.current_model || 'Unknown';
            document.getElementById('available-models').textContent = 
                `${openrouter.available_models || 0}/${openrouter.total_models || 0}`;
            document.getElementById('model-rotations').textContent = 
                (openrouter.rotation_history || []).length;
            document.getElementById('openrouter-updated').textContent = 
                openrouter.last_updated || 'Never';
            
            // Learning System
            const learning = systemData.learning || {};
            const memoryStats = learning.memory_stats || {};
            const feedbackSummary = learning.feedback_summary || {};
            const knowledgeStats = learning.knowledge_stats || {};
            const learningMetrics = learning.learning_metrics || {};
            
            document.getElementById('total-experiences').textContent = 
                memoryStats.total_experiences || 0;
            document.getElementById('success-rate').textContent = 
                `${Math.round((memoryStats.success_rate || 0) * 100)}%`;
            document.getElementById('knowledge-items').textContent = 
                knowledgeStats.total_knowledge_items || 0;
            document.getElementById('adaptations').textContent = 
                learningMetrics.total_adaptations || 0;
            
            // Memory System
            document.getElementById('memory-experiences').textContent = 
                memoryStats.total_experiences || 0;
            document.getElementById('memory-successful').textContent = 
                memoryStats.successful_experiences || 0;
            document.getElementById('memory-recent').textContent = 
                memoryStats.recent_activity || 0;
            document.getElementById('memory-size').textContent = 
                `${(memoryStats.memory_size_mb || 0).toFixed(1)} MB`;
            
            // Feedback Engine
            const overall = feedbackSummary.overall || {};
            document.getElementById('feedback-success-rate').textContent = 
                `${Math.round((overall.success_rate || 0) * 100)}%`;
            document.getElementById('feedback-exec-time').textContent = 
                `${(overall.average_execution_time || 0).toFixed(1)}s`;
            document.getElementById('feedback-events').textContent = 
                overall.total_events || 0;
            
            // Knowledge System
            document.getElementById('knowledge-total').textContent = 
                knowledgeStats.total_knowledge_items || 0;
            document.getElementById('knowledge-gaps').textContent = 
                knowledgeStats.open_knowledge_gaps || 0;
            document.getElementById('knowledge-proposals').textContent = 
                knowledgeStats.pending_proposals || 0;
            
            // Learning Insights
            const insights = learning.learning_insights || {};
            const learningVelocity = Object.keys(insights.learning_velocity || {}).length;
            document.getElementById('learning-velocity').textContent = 
                learningVelocity > 0 ? `${learningVelocity} areas improving` : 'Analyzing...';
            
            const strengths = insights.strengths || [];
            document.getElementById('top-strength').textContent = 
                strengths.length > 0 ? strengths[0].task_type : 'Analyzing...';
            
            const improvements = insights.improvement_areas || [];
            document.getElementById('improvement-area').textContent = 
                improvements.length > 0 ? improvements[0].task_type : 'None identified';
            
            // Update logs
            updateLogs();
        }
        
        // Update logs display
        function updateLogs() {
            const logContainer = document.getElementById('log-container');
            const logs = systemData.logs || [];
            
            logContainer.innerHTML = logs.slice(-20).map(log => `
                <div class="log-entry">
                    <span class="log-timestamp">${log.timestamp}</span>
                    <span class="log-${log.level}">${log.message}</span>
                </div>
            `).join('');
            
            logContainer.scrollTop = logContainer.scrollHeight;
        }
        
        // Trigger actions
        async function triggerAction(action) {
            try {
                const response = await fetch('/api/trigger_action', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ action })
                });
                
                const result = await response.json();
                if (result.success) {
                    alert(`Action "${action}" completed successfully!`);
                } else {
                    alert(`Action "${action}" failed: ${result.error}`);
                }
                
                // Refresh status after action
                setTimeout(fetchStatus, 2000);
            } catch (error) {
                alert(`Failed to trigger action: ${error.message}`);
            }
        }
        
        // Refresh status
        function refreshStatus() {
            fetchStatus();
        }
        
        // Knowledge search
        document.getElementById('knowledge-search-input').addEventListener('input', async (e) => {
            const query = e.target.value.trim();
            if (query.length < 3) {
                document.getElementById('knowledge-search-results').innerHTML = '';
                return;
            }
            
            try {
                const response = await fetch('/api/knowledge_search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ query, limit: 5 })
                });
                
                const result = await response.json();
                if (result.success && result.results) {
                    const resultsHtml = result.results.map(item => `
                        <div class="search-result">
                            <div class="search-result-title">${item.title}</div>
                            <div class="search-result-content">${item.content.substring(0, 100)}...</div>
                        </div>
                    `).join('');
                    
                    document.getElementById('knowledge-search-results').innerHTML = resultsHtml;
                } else {
                    document.getElementById('knowledge-search-results').innerHTML = 
                        '<div class="search-result">No results found</div>';
                }
            } catch (error) {
                console.error('Knowledge search failed:', error);
            }
        });
        
        // Initialize dashboard
        fetchStatus();
        
        // Auto-refresh every 30 seconds
        setInterval(fetchStatus, 30000);
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    print("🚀 Starting Enhanced Quantum Loop Debugger Dashboard...")
    print("📊 Dashboard will be available at http://localhost:5000")
    print("🧠 Enhanced with self-learning metrics and insights")
    
    # Initial status fetch
    add_log("Enhanced Dashboard starting up", 'info')
    
    app.run(host='0.0.0.0', port=5000, debug=False)
