
#!/usr/bin/env python3
"""
Quantum Loop Debugger - Main Orchestrator
Self-healing code system with failure detection and automated patch application
"""

import subprocess
import json
import time
import os
import sys
import threading
import requests
from datetime import datetime

class QuantumLoopDebugger:
    def __init__(self, config_file="loop_patch_input.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.dashboard_url = "http://localhost:5000"
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 2)
        self.patch_generator = self.config.get('patch_generator', 'tk_patch_generator.py')
        self.test_script = self.config.get('test_script', 'test_script.py')
        
        print("🔬 Quantum Loop Debugger initialized")
        print(f"📁 Config: {config_file}")
        print(f"🔄 Max retries: {self.max_retries}")
        print(f"⏱️  Retry delay: {self.retry_delay}s")
        print("-" * 50)

    def load_config(self):
        """Load configuration from JSON file"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️  Config file {self.config_file} not found, using defaults")
            return {}
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing config file: {e}")
            return {}

    def update_dashboard(self, data):
        """Update the dashboard with current status"""
        try:
            response = requests.post(f"{self.dashboard_url}/api/update_status", 
                                   json=data, timeout=2)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            # Dashboard might not be running, continue silently
            return False

    def run_test(self):
        """Execute the test script and capture output"""
        print(f"🧪 Running test: {self.test_script}")
        
        # Update dashboard
        self.update_dashboard({
            'status': 'running',
            'current_test': self.test_script,
            'log': f'Executing test: {self.test_script}'
        })
        
        try:
            result = subprocess.run([
                sys.executable, self.test_script
            ], capture_output=True, text=True, timeout=30)
            
            print(f"📊 Test exit code: {result.returncode}")
            
            if result.stdout:
                print("📤 STDOUT:")
                print(result.stdout)
            
            if result.stderr:
                print("📥 STDERR:")
                print(result.stderr)
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            error_msg = f"Test {self.test_script} timed out after 30 seconds"
            print(f"⏰ {error_msg}")
            return {
                'success': False,
                'stdout': '',
                'stderr': error_msg,
                'returncode': -1
            }
        except Exception as e:
            error_msg = f"Error running test: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'stdout': '',
                'stderr': error_msg,
                'returncode': -1
            }

    def generate_patch(self, failure_context):
        """Generate a patch using the LLM-powered patch generator"""
        print("🤖 Generating patch with AI...")
        
        # Update dashboard
        self.update_dashboard({
            'log': 'Generating AI-powered patch...'
        })
        
        try:
            # Create temporary context file for patch generator
            context_file = "temp_failure_context.json"
            with open(context_file, 'w') as f:
                json.dump(failure_context, f, indent=2)
            
            result = subprocess.run([
                sys.executable, self.patch_generator, context_file
            ], capture_output=True, text=True, timeout=60)
            
            # Clean up temporary file
            if os.path.exists(context_file):
                os.remove(context_file)
            
            if result.returncode == 0:
                print("✅ Patch generated successfully")
                self.update_dashboard({
                    'log': 'Patch generated successfully'
                })
                return True
            else:
                print(f"❌ Patch generation failed: {result.stderr}")
                self.update_dashboard({
                    'log': f'Patch generation failed: {result.stderr}',
                    'log_level': 'error'
                })
                return False
                
        except subprocess.TimeoutExpired:
            print("⏰ Patch generation timed out")
            self.update_dashboard({
                'log': 'Patch generation timed out',
                'log_level': 'error'
            })
            return False
        except Exception as e:
            print(f"❌ Error generating patch: {str(e)}")
            self.update_dashboard({
                'log': f'Error generating patch: {str(e)}',
                'log_level': 'error'
            })
            return False

    def apply_patch(self):
        """Apply the generated patch"""
        patch_file = "generated_patch.py"
        
        if not os.path.exists(patch_file):
            print("❌ No patch file found to apply")
            return False
        
        try:
            print("🔧 Applying patch...")
            
            # Update dashboard
            self.update_dashboard({
                'log': 'Applying generated patch...'
            })
            
            # Read and execute the patch
            with open(patch_file, 'r') as f:
                patch_code = f.read()
            
            # Execute the patch in a controlled environment
            exec(patch_code, {'__name__': '__patch__'})
            
            print("✅ Patch applied successfully")
            self.update_dashboard({
                'patch_applied': True,
                'log': 'Patch applied successfully'
            })
            
            return True
            
        except Exception as e:
            print(f"❌ Error applying patch: {str(e)}")
            self.update_dashboard({
                'log': f'Error applying patch: {str(e)}',
                'log_level': 'error'
            })
            return False

    def quantum_loop(self):
        """Main quantum debugging loop with self-healing capabilities"""
        print("🌀 Starting Quantum Loop Debugger...")
        print("🔄 Entering self-healing loop...")
        
        # Update dashboard
        self.update_dashboard({
            'status': 'running',
            'log': 'Quantum Loop Debugger started'
        })
        
        attempt = 0
        
        while attempt < self.max_retries:
            attempt += 1
            print(f"\n🔄 Attempt {attempt}/{self.max_retries}")
            
            # Run the test
            test_result = self.run_test()
            
            if test_result['success']:
                print("✅ Test passed! System is healthy.")
                self.update_dashboard({
                    'status': 'idle',
                    'current_test': None,
                    'log': f'Test passed on attempt {attempt}. System healthy.'
                })
                return True
            
            print(f"❌ Test failed on attempt {attempt}")
            
            # Record failure in dashboard
            failure_context = {
                'attempt': attempt,
                'max_attempts': self.max_retries,
                'error': test_result['stderr'] or test_result['stdout'] or 'Unknown error',
                'returncode': test_result['returncode'],
                'timestamp': datetime.now().isoformat()
            }
            
            self.update_dashboard({
                'failure': {
                    'error': failure_context['error'],
                    'status': f'Failed (attempt {attempt}/{self.max_retries})'
                },
                'log': f'Test failed on attempt {attempt}: {failure_context["error"][:100]}...',
                'log_level': 'error'
            })
            
            if attempt < self.max_retries:
                print("🤖 Attempting self-healing...")
                
                # Generate patch
                if self.generate_patch(failure_context):
                    # Apply patch
                    if self.apply_patch():
                        print(f"⏱️  Waiting {self.retry_delay}s before retry...")
                        time.sleep(self.retry_delay)
                        continue
                
                print("❌ Self-healing failed, retrying without patch...")
                time.sleep(self.retry_delay)
            
        print(f"\n💥 All {self.max_retries} attempts failed!")
        print("🔬 Quantum Loop Debugger could not heal the system")
        
        self.update_dashboard({
            'status': 'error',
            'current_test': None,
            'log': f'All {self.max_retries} attempts failed. System requires manual intervention.',
            'log_level': 'error'
        })
        
        return False

def main():
    """Main entry point"""
    print("=" * 60)
    print("🔬 QUANTUM LOOP DEBUGGER - SELF-HEALING CODE SYSTEM")
    print("=" * 60)
    
    # Check if dashboard is running
    try:
        response = requests.get("http://localhost:5000/api/status", timeout=2)
        print("📊 Dashboard detected at http://localhost:5000")
    except requests.exceptions.RequestException:
        print("⚠️  Dashboard not detected. Start tk_dashboard.py for monitoring.")
    
    debugger = QuantumLoopDebugger()
    
    try:
        success = debugger.quantum_loop()
        
        if success:
            print("\n🎉 SUCCESS: System is now healthy!")
            return 0
        else:
            print("\n💥 FAILURE: System could not be healed automatically")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Quantum Loop Debugger interrupted by user")
        debugger.update_dashboard({
            'status': 'idle',
            'log': 'System interrupted by user'
        })
        return 130
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        debugger.update_dashboard({
            'status': 'error',
            'log': f'Unexpected error: {str(e)}',
            'log_level': 'error'
        })
        return 1

if __name__ == "__main__":
    sys.exit(main())
