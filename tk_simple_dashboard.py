
#!/usr/bin/env python3
"""
Streamlined Dashboard for Self-Learning AI Engineer
Shows active model rotation, memory updates, and real-time metrics
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import requests
import json
import threading
import time
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Engineer Self-Learning Dashboard")
        self.root.geometry("1000x700")
        
        # Configuration
        self.mcp_server_url = "http://localhost:8084"
        self.update_interval = 5  # seconds
        self.running = True
        
        # Data storage
        self.current_model = "gpt-3.5-turbo"
        self.model_rotation = ["gpt-3.5-turbo", "claude-3-haiku", "llama-3.1-8b"]
        self.rotation_index = 0
        
        self.setup_ui()
        self.start_updates()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="AI Engineer Self-Learning Dashboard", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Left panel - Status and Controls
        left_frame = ttk.LabelFrame(main_frame, text="System Status", padding="10")
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Model rotation section
        model_frame = ttk.LabelFrame(left_frame, text="Active Model & Rotation", padding="5")
        model_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.current_model_label = ttk.Label(model_frame, text=f"Current: {self.current_model}", 
                                           font=('Arial', 10, 'bold'))
        self.current_model_label.pack(anchor=tk.W)
        
        self.rotation_label = ttk.Label(model_frame, text="Rotation: " + " → ".join(self.model_rotation))
        self.rotation_label.pack(anchor=tk.W)
        
        # Manual rotation button
        rotate_btn = ttk.Button(model_frame, text="Rotate Model", command=self.rotate_model)
        rotate_btn.pack(pady=(5, 0))
        
        # Metrics section
        metrics_frame = ttk.LabelFrame(left_frame, text="Real-time Metrics", padding="5")
        metrics_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.uptime_label = ttk.Label(metrics_frame, text="Uptime: --")
        self.uptime_label.pack(anchor=tk.W)
        
        self.requests_label = ttk.Label(metrics_frame, text="Total Requests: --")
        self.requests_label.pack(anchor=tk.W)
        
        self.memory_count_label = ttk.Label(metrics_frame, text="Memory Entries: --")
        self.memory_count_label.pack(anchor=tk.W)
        
        self.feedback_count_label = ttk.Label(metrics_frame, text="Feedback Entries: --")
        self.feedback_count_label.pack(anchor=tk.W)
        
        self.success_rate_label = ttk.Label(metrics_frame, text="Success Rate: --%")
        self.success_rate_label.pack(anchor=tk.W)
        
        # Health status
        health_frame = ttk.LabelFrame(left_frame, text="Health Status", padding="5")
        health_frame.pack(fill=tk.X)
        
        self.health_label = ttk.Label(health_frame, text="Status: Checking...", 
                                     font=('Arial', 10, 'bold'))
        self.health_label.pack(anchor=tk.W)
        
        self.last_update_label = ttk.Label(health_frame, text="Last Update: --")
        self.last_update_label.pack(anchor=tk.W)
        
        # Right panel - Activity Feed
        right_frame = ttk.LabelFrame(main_frame, text="Recent Activity", padding="10")
        right_frame.grid(row=1, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Activity log
        self.activity_text = scrolledtext.ScrolledText(right_frame, width=50, height=20)
        self.activity_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Control buttons
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill=tk.X)
        
        refresh_btn = ttk.Button(button_frame, text="Refresh", command=self.manual_refresh)
        refresh_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        clear_btn = ttk.Button(button_frame, text="Clear Log", command=self.clear_activity_log)
        clear_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Memory visualization section
        memory_frame = ttk.LabelFrame(main_frame, text="Memory Updates Visualization", padding="10")
        memory_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        # Memory stats
        self.memory_stats_text = scrolledtext.ScrolledText(memory_frame, width=40, height=10)
        self.memory_stats_text.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def rotate_model(self):
        """Manually rotate to next model"""
        self.rotation_index = (self.rotation_index + 1) % len(self.model_rotation)
        self.current_model = self.model_rotation[self.rotation_index]
        self.current_model_label.config(text=f"Current: {self.current_model}")
        self.log_activity(f"Model rotated to: {self.current_model}")
    
    def log_activity(self, message):
        """Add message to activity log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        self.activity_text.insert(tk.END, log_message)
        self.activity_text.see(tk.END)
        
        # Keep only last 100 lines
        lines = self.activity_text.get("1.0", tk.END).split('\n')
        if len(lines) > 100:
            self.activity_text.delete("1.0", f"{len(lines)-100}.0")
    
    def clear_activity_log(self):
        """Clear the activity log"""
        self.activity_text.delete("1.0", tk.END)
        self.log_activity("Activity log cleared")
    
    def manual_refresh(self):
        """Manually refresh all data"""
        self.log_activity("Manual refresh triggered")
        self.update_dashboard()
    
    def fetch_mcp_status(self):
        """Fetch status from MCP server"""
        try:
            response = requests.get(f"{self.mcp_server_url}/status", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            logger.error(f"Error fetching MCP status: {e}")
            return None
    
    def fetch_recent_memories(self):
        """Fetch recent memory entries"""
        try:
            response = requests.get(f"{self.mcp_server_url}/memory?limit=5", timeout=5)
            if response.status_code == 200:
                return response.json().get("memories", [])
            else:
                return []
        except Exception as e:
            logger.error(f"Error fetching memories: {e}")
            return []
    
    def fetch_recent_feedback(self):
        """Fetch recent feedback entries"""
        try:
            response = requests.get(f"{self.mcp_server_url}/feedback?limit=5", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get("feedbacks", []), data.get("success_rate", 0)
            else:
                return [], 0
        except Exception as e:
            logger.error(f"Error fetching feedback: {e}")
            return [], 0
    
    def update_dashboard(self):
        """Update all dashboard components"""
        try:
            # Fetch MCP status
            status_data = self.fetch_mcp_status()
            
            if status_data:
                # Update metrics
                self.uptime_label.config(text=f"Uptime: {status_data.get('uptime_hours', 0):.1f}h")
                self.requests_label.config(text=f"Total Requests: {status_data.get('requests_count', 0)}")
                self.memory_count_label.config(text=f"Memory Entries: {status_data.get('memory_entries', 0)}")
                self.feedback_count_label.config(text=f"Feedback Entries: {status_data.get('feedback_entries', 0)}")
                
                # Update health status
                health = status_data.get('health', 'unknown')
                health_color = 'green' if health == 'healthy' else 'red'
                self.health_label.config(text=f"Status: {health.title()}", foreground=health_color)
                
                # Update recent activity
                recent_activity = status_data.get('recent_activity', {})
                recent_memories = recent_activity.get('memories_last_hour', 0)
                recent_feedback = recent_activity.get('feedback_last_hour', 0)
                recent_success_rate = recent_activity.get('success_rate_last_hour', 0)
                
                self.success_rate_label.config(text=f"Success Rate: {recent_success_rate:.1f}%")
                
                if recent_memories > 0 or recent_feedback > 0:
                    self.log_activity(f"Recent activity: {recent_memories} memories, {recent_feedback} feedback")
                
                self.status_var.set(f"Connected - Last update: {datetime.now().strftime('%H:%M:%S')}")
                
            else:
                self.health_label.config(text="Status: Disconnected", foreground='red')
                self.status_var.set("Disconnected from MCP server")
            
            # Update memory visualization
            self.update_memory_visualization()
            
            # Update last update time
            self.last_update_label.config(text=f"Last Update: {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")
            self.status_var.set(f"Update error: {str(e)}")
    
    def update_memory_visualization(self):
        """Update memory visualization section"""
        try:
            memories = self.fetch_recent_memories()
            
            # Clear previous content
            self.memory_stats_text.delete("1.0", tk.END)
            
            if memories:
                self.memory_stats_text.insert(tk.END, "Recent Memory Entries:\n\n")
                
                for i, memory in enumerate(memories, 1):
                    timestamp = memory.get('timestamp', '')[:19]  # Remove microseconds
                    memory_type = memory.get('type', 'general')
                    content = memory.get('content', '')[:100] + "..." if len(memory.get('content', '')) > 100 else memory.get('content', '')
                    importance = memory.get('importance', 1)
                    
                    entry_text = f"{i}. [{timestamp}] ({memory_type})\n"
                    entry_text += f"   Importance: {importance}/5\n"
                    entry_text += f"   Content: {content}\n\n"
                    
                    self.memory_stats_text.insert(tk.END, entry_text)
            else:
                self.memory_stats_text.insert(tk.END, "No recent memory entries found.")
                
        except Exception as e:
            logger.error(f"Error updating memory visualization: {e}")
            self.memory_stats_text.delete("1.0", tk.END)
            self.memory_stats_text.insert(tk.END, f"Error loading memory data: {e}")
    
    def update_loop(self):
        """Main update loop running in background thread"""
        while self.running:
            try:
                self.update_dashboard()
                time.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error in update loop: {e}")
                time.sleep(self.update_interval)
    
    def start_updates(self):
        """Start the background update thread"""
        self.update_thread = threading.Thread(target=self.update_loop, daemon=True)
        self.update_thread.start()
        self.log_activity("Dashboard started - Auto-refresh enabled")
    
    def on_closing(self):
        """Handle window closing"""
        self.running = False
        self.root.destroy()

def main():
    root = tk.Tk()
    dashboard = SimpleDashboard(root)
    
    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", dashboard.on_closing)
    
    # Start the GUI
    root.mainloop()

if __name__ == "__main__":
    main()
