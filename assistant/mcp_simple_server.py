
#!/usr/bin/env python3
"""
Simplified MCP Learning Server
Provides 3 REST endpoints: /memory, /feedback, /status
"""

import json
import os
import time
from datetime import datetime
from flask import Flask, request, jsonify
from pathlib import Path
import threading
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Data storage paths
MEMORY_DIR = Path("/workspace/memory")
FEEDBACK_DIR = Path("/workspace/feedback")
STATUS_FILE = Path("/workspace/status.json")

# Ensure directories exist
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)

# Global status tracking
server_status = {
    "start_time": datetime.now().isoformat(),
    "requests_count": 0,
    "memory_entries": 0,
    "feedback_entries": 0,
    "last_activity": datetime.now().isoformat(),
    "health": "healthy"
}

def update_status():
    """Update server status"""
    server_status["last_activity"] = datetime.now().isoformat()
    server_status["requests_count"] += 1
    
    # Count entries
    server_status["memory_entries"] = len(list(MEMORY_DIR.glob("*.json")))
    server_status["feedback_entries"] = len(list(FEEDBACK_DIR.glob("*.json")))
    
    # Save status to file
    with open(STATUS_FILE, 'w') as f:
        json.dump(server_status, f, indent=2)

@app.route('/memory', methods=['GET', 'POST'])
def memory_endpoint():
    """Memory storage and retrieval endpoint"""
    update_status()
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400
            
            # Generate memory entry
            timestamp = datetime.now().isoformat()
            memory_id = f"mem_{int(time.time())}"
            
            memory_entry = {
                "id": memory_id,
                "timestamp": timestamp,
                "type": data.get("type", "general"),
                "content": data.get("content", ""),
                "context": data.get("context", {}),
                "importance": data.get("importance", 1)
            }
            
            # Save to file
            memory_file = MEMORY_DIR / f"{memory_id}.json"
            with open(memory_file, 'w') as f:
                json.dump(memory_entry, f, indent=2)
            
            logger.info(f"Stored memory entry: {memory_id}")
            return jsonify({
                "success": True,
                "memory_id": memory_id,
                "message": "Memory stored successfully"
            })
            
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            return jsonify({"error": str(e)}), 500
    
    else:  # GET request
        try:
            # Get query parameters
            limit = int(request.args.get('limit', 10))
            memory_type = request.args.get('type', None)
            
            # Load all memory entries
            memories = []
            for memory_file in sorted(MEMORY_DIR.glob("*.json"), reverse=True):
                try:
                    with open(memory_file, 'r') as f:
                        memory = json.load(f)
                        if memory_type is None or memory.get("type") == memory_type:
                            memories.append(memory)
                            if len(memories) >= limit:
                                break
                except Exception as e:
                    logger.warning(f"Error reading memory file {memory_file}: {e}")
            
            return jsonify({
                "success": True,
                "memories": memories,
                "total_count": len(memories)
            })
            
        except Exception as e:
            logger.error(f"Error retrieving memories: {e}")
            return jsonify({"error": str(e)}), 500

@app.route('/feedback', methods=['GET', 'POST'])
def feedback_endpoint():
    """Feedback storage and retrieval endpoint"""
    update_status()
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400
            
            # Generate feedback entry
            timestamp = datetime.now().isoformat()
            feedback_id = f"fb_{int(time.time())}"
            
            feedback_entry = {
                "id": feedback_id,
                "timestamp": timestamp,
                "action": data.get("action", ""),
                "result": data.get("result", ""),
                "success": data.get("success", False),
                "error": data.get("error", None),
                "duration": data.get("duration", 0),
                "context": data.get("context", {})
            }
            
            # Save to file
            feedback_file = FEEDBACK_DIR / f"{feedback_id}.json"
            with open(feedback_file, 'w') as f:
                json.dump(feedback_entry, f, indent=2)
            
            logger.info(f"Stored feedback entry: {feedback_id}")
            return jsonify({
                "success": True,
                "feedback_id": feedback_id,
                "message": "Feedback stored successfully"
            })
            
        except Exception as e:
            logger.error(f"Error storing feedback: {e}")
            return jsonify({"error": str(e)}), 500
    
    else:  # GET request
        try:
            # Get query parameters
            limit = int(request.args.get('limit', 10))
            success_only = request.args.get('success_only', 'false').lower() == 'true'
            
            # Load all feedback entries
            feedbacks = []
            for feedback_file in sorted(FEEDBACK_DIR.glob("*.json"), reverse=True):
                try:
                    with open(feedback_file, 'r') as f:
                        feedback = json.load(f)
                        if not success_only or feedback.get("success", False):
                            feedbacks.append(feedback)
                            if len(feedbacks) >= limit:
                                break
                except Exception as e:
                    logger.warning(f"Error reading feedback file {feedback_file}: {e}")
            
            # Calculate success rate
            total_feedbacks = len(list(FEEDBACK_DIR.glob("*.json")))
            successful_feedbacks = sum(1 for f in feedbacks if f.get("success", False))
            success_rate = (successful_feedbacks / total_feedbacks * 100) if total_feedbacks > 0 else 0
            
            return jsonify({
                "success": True,
                "feedbacks": feedbacks,
                "total_count": len(feedbacks),
                "success_rate": round(success_rate, 2)
            })
            
        except Exception as e:
            logger.error(f"Error retrieving feedback: {e}")
            return jsonify({"error": str(e)}), 500

@app.route('/status', methods=['GET'])
def status_endpoint():
    """Server status and health monitoring endpoint"""
    update_status()
    
    try:
        # Calculate uptime
        start_time = datetime.fromisoformat(server_status["start_time"])
        uptime_seconds = (datetime.now() - start_time).total_seconds()
        uptime_hours = round(uptime_seconds / 3600, 2)
        
        # Get recent activity summary
        recent_memories = len([f for f in MEMORY_DIR.glob("*.json") 
                              if (time.time() - f.stat().st_mtime) < 3600])  # Last hour
        recent_feedback = len([f for f in FEEDBACK_DIR.glob("*.json") 
                              if (time.time() - f.stat().st_mtime) < 3600])  # Last hour
        
        # Calculate success rate from recent feedback
        recent_feedback_files = [f for f in FEEDBACK_DIR.glob("*.json") 
                                if (time.time() - f.stat().st_mtime) < 3600]
        recent_success_count = 0
        for f in recent_feedback_files:
            try:
                with open(f, 'r') as file:
                    feedback = json.load(file)
                    if feedback.get("success", False):
                        recent_success_count += 1
            except:
                pass
        
        recent_success_rate = (recent_success_count / len(recent_feedback_files) * 100) if recent_feedback_files else 0
        
        status_response = {
            **server_status,
            "uptime_hours": uptime_hours,
            "recent_activity": {
                "memories_last_hour": recent_memories,
                "feedback_last_hour": len(recent_feedback_files),
                "success_rate_last_hour": round(recent_success_rate, 2)
            },
            "endpoints": {
                "/memory": "Memory storage and retrieval",
                "/feedback": "Feedback tracking and analysis",
                "/status": "Server health and metrics"
            }
        }
        
        return jsonify(status_response)
        
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({"error": str(e), "health": "unhealthy"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    logger.info("Starting MCP Simple Learning Server...")
    logger.info(f"Memory directory: {MEMORY_DIR}")
    logger.info(f"Feedback directory: {FEEDBACK_DIR}")
    
    # Initialize status
    update_status()
    
    # Start server
    app.run(host='0.0.0.0', port=8084, debug=False)
