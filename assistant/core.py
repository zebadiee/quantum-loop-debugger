
#!/usr/bin/env python3
"""
Quantum Loop Debugger - AI Engineer Core
Main orchestrator for AI-powered development workflows with OpenRouter integration
"""

import asyncio
import json
import logging
import os
import sys
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Any
import argparse

from .openrouter_client import OpenRouterFree
from .git_integration import GitManager
from .tools.mcp_client import MCPClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/workspace/logs/ai_engineer.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class AIEngineer:
    """
    AI Engineer - The brain of the quantum loop debugger system
    Orchestrates patch generation, testing, monitoring, and Git operations
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._load_config()
        self.workspace_path = os.getenv('WORKSPACE_PATH', '/workspace')
        
        # Initialize components with OpenRouter Free Models
        self.llm_client = OpenRouterFree(self.config.get('openrouter', {}))
        self.git_manager = GitManager(self.workspace_path, self.config.get('git', {}))
        
        # MCP clients for existing services
        self.mcp_clients = {
            'patch': MCPClient('patch-mcp', 'http://patch-mcp:8081'),
            'dashboard': MCPClient('dashboard-mcp', 'http://dashboard-mcp:8082'),
            'auto_retry': MCPClient('auto-retry', 'http://auto-retry:8083')
        }
        
        # State management
        self.active_sessions = {}
        self.task_queue = asyncio.Queue()
        
        logger.info("🤖 AI Engineer initialized successfully")
        logger.info(f"📁 Workspace: {self.workspace_path}")
        logger.info(f"🔄 LLM Client: OpenRouter Free Models")

    def _load_config(self) -> Dict:
        """Load configuration from environment and config files"""
        config = {
            'openrouter': {
                'api_key': os.getenv('OPENROUTER_API_KEY'),
                'app_name': 'Quantum-Loop-Debugger',
                'app_url': 'https://github.com/zebadiee/quantum-loop-debugger'
            },
            'git': {
                'github_token': os.getenv('GITHUB_TOKEN'),
                'auto_commit': os.getenv('AUTO_COMMIT', 'true').lower() == 'true',
                'auto_pr': os.getenv('AUTO_PR', 'false').lower() == 'true'
            },
            'mcp': {
                'timeout': int(os.getenv('MCP_TIMEOUT', '30')),
                'retry_attempts': int(os.getenv('MCP_RETRY_ATTEMPTS', '3'))
            }
        }
        
        # Load from config file if exists
        config_file = os.path.join(self.workspace_path, 'config', 'ai_engineer.json')
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    file_config = json.load(f)
                    config.update(file_config)
            except Exception as e:
                logger.warning(f"Failed to load config file: {e}")
        
        return config

    async def handle_request(self, request: Dict) -> Dict:
        """
        Main request handler - routes requests to appropriate handlers
        """
        request_type = request.get('type', 'unknown')
        request_id = request.get('id', f"req_{datetime.now().timestamp()}")
        
        logger.info(f"🎯 Handling request {request_id}: {request_type}")
        
        try:
            if request_type == 'fix_patch':
                return await self._handle_fix_patch(request)
            elif request_type == 'status_check':
                return await self._handle_status_check(request)
            elif request_type == 'run_tests':
                return await self._handle_run_tests(request)
            elif request_type == 'git_operation':
                return await self._handle_git_operation(request)
            elif request_type == 'llm_query':
                return await self._handle_llm_query(request)
            elif request_type == 'system_health':
                return await self._handle_system_health(request)
            elif request_type == 'openrouter_status':
                return await self._handle_openrouter_status(request)
            elif request_type == 'force_model_rotation':
                return await self._handle_force_model_rotation(request)
            else:
                return await self._handle_generic_query(request)
                
        except Exception as e:
            logger.error(f"❌ Error handling request {request_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'request_id': request_id,
                'timestamp': datetime.now().isoformat()
            }

    async def _handle_fix_patch(self, request: Dict) -> Dict:
        """Handle patch generation and application requests"""
        logger.info("🔧 Processing fix/patch request")
        
        # Get failure context
        failure_context = request.get('failure_context', {})
        auto_apply = request.get('auto_apply', False)
        
        try:
            # Request patch from MCP patch generator
            patch_response = await self.mcp_clients['patch'].call_method(
                'generate_patch',
                {'failure_context': failure_context}
            )
            
            if not patch_response.get('success'):
                return {
                    'success': False,
                    'error': 'Patch generation failed',
                    'details': patch_response
                }
            
            patch_data = patch_response.get('patch', {})
            
            # If auto_apply is enabled, apply the patch
            if auto_apply and patch_data:
                apply_result = await self._apply_patch(patch_data)
                patch_data['apply_result'] = apply_result
                
                # If patch applied successfully and auto_commit is enabled
                if apply_result.get('success') and self.config['git']['auto_commit']:
                    commit_result = await self.git_manager.auto_commit(
                        f"Auto-fix: {failure_context.get('error_type', 'Unknown error')}"
                    )
                    patch_data['commit_result'] = commit_result
            
            return {
                'success': True,
                'patch': patch_data,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Patch generation error: {e}")
            return {
                'success': False,
                'error': f"Patch generation failed: {str(e)}"
            }

    async def _handle_status_check(self, request: Dict) -> Dict:
        """Handle system status and monitoring requests"""
        logger.info("📊 Processing status check request")
        
        try:
            # Get status from dashboard MCP
            dashboard_response = await self.mcp_clients['dashboard'].call_method(
                'get_system_status',
                {}
            )
            
            # Get auto-retry status
            retry_response = await self.mcp_clients['auto_retry'].call_method(
                'get_retry_status',
                {}
            )
            
            # Get OpenRouter status
            openrouter_health = await self.llm_client.health_check()
            
            # Combine status information
            status = {
                'success': True,
                'dashboard': dashboard_response,
                'auto_retry': retry_response,
                'openrouter': openrouter_health,
                'ai_engineer': {
                    'active_sessions': len(self.active_sessions),
                    'queue_size': self.task_queue.qsize(),
                    'workspace': self.workspace_path,
                    'git_status': await self.git_manager.get_status()
                },
                'timestamp': datetime.now().isoformat()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"❌ Status check error: {e}")
            return {
                'success': False,
                'error': f"Status check failed: {str(e)}"
            }

    async def _handle_openrouter_status(self, request: Dict) -> Dict:
        """Handle OpenRouter specific status requests"""
        logger.info("🔄 Processing OpenRouter status request")
        
        try:
            return {
                'success': True,
                'current_model': self.llm_client.current_model,
                'available_models': self.llm_client.list_available_models(),
                'usage_summary': self.llm_client.get_usage_summary(),
                'rotation_history': self.llm_client.get_rotation_history(),
                'health': await self.llm_client.health_check(),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ OpenRouter status error: {e}")
            return {
                'success': False,
                'error': f"OpenRouter status check failed: {str(e)}"
            }

    async def _handle_force_model_rotation(self, request: Dict) -> Dict:
        """Handle forced model rotation requests"""
        logger.info("🔄 Processing forced model rotation request")
        
        try:
            old_model = self.llm_client.current_model
            success = self.llm_client.force_model_rotation()
            
            return {
                'success': success,
                'old_model': old_model,
                'new_model': self.llm_client.current_model,
                'message': f"Model rotated from {old_model} to {self.llm_client.current_model}" if success else "No available models for rotation",
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Model rotation error: {e}")
            return {
                'success': False,
                'error': f"Model rotation failed: {str(e)}"
            }

    async def _handle_run_tests(self, request: Dict) -> Dict:
        """Handle test execution requests"""
        logger.info("🧪 Processing test execution request")
        
        test_path = request.get('test_path', 'test_script.py')
        test_args = request.get('args', [])
        
        try:
            # Run tests using subprocess
            cmd = ['python', test_path] + test_args
            result = subprocess.run(
                cmd,
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'command': ' '.join(cmd),
                'timestamp': datetime.now().isoformat()
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Test execution timed out',
                'timeout': 300
            }
        except Exception as e:
            logger.error(f"❌ Test execution error: {e}")
            return {
                'success': False,
                'error': f"Test execution failed: {str(e)}"
            }

    async def _handle_git_operation(self, request: Dict) -> Dict:
        """Handle Git operations (commit, push, PR, etc.)"""
        logger.info("🔀 Processing Git operation request")
        
        operation = request.get('operation')
        params = request.get('params', {})
        
        try:
            if operation == 'commit':
                result = await self.git_manager.commit(
                    params.get('message', 'AI Engineer auto-commit'),
                    params.get('files', [])
                )
            elif operation == 'push':
                result = await self.git_manager.push(
                    params.get('branch'),
                    params.get('remote', 'origin')
                )
            elif operation == 'create_pr':
                result = await self.git_manager.create_pull_request(
                    params.get('title'),
                    params.get('body', ''),
                    params.get('base_branch', 'main'),
                    params.get('head_branch')
                )
            elif operation == 'status':
                result = await self.git_manager.get_status()
            else:
                return {
                    'success': False,
                    'error': f"Unknown Git operation: {operation}"
                }
            
            return {
                'success': True,
                'operation': operation,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Git operation error: {e}")
            return {
                'success': False,
                'error': f"Git operation failed: {str(e)}"
            }

    async def _handle_llm_query(self, request: Dict) -> Dict:
        """Handle LLM queries through OpenRouter Free Models"""
        logger.info("🧠 Processing LLM query request")
        
        query = request.get('query', '')
        model = request.get('model')
        context = request.get('context', {})
        
        try:
            response = await self.llm_client.query(
                query=query,
                model=model,
                context=context
            )
            
            return {
                'success': True,
                'response': response,
                'model_used': self.llm_client.current_model,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ LLM query error: {e}")
            return {
                'success': False,
                'error': f"LLM query failed: {str(e)}"
            }

    async def _handle_system_health(self, request: Dict) -> Dict:
        """Handle system health check requests"""
        logger.info("🏥 Processing system health check")
        
        try:
            health_status = {
                'ai_engineer': 'healthy',
                'mcp_services': {},
                'git': await self.git_manager.health_check(),
                'openrouter': await self.llm_client.health_check(),
                'workspace': os.path.exists(self.workspace_path),
                'timestamp': datetime.now().isoformat()
            }
            
            # Check MCP services
            for service_name, client in self.mcp_clients.items():
                try:
                    health_response = await client.call_method('health_check', {})
                    health_status['mcp_services'][service_name] = 'healthy' if health_response.get('success') else 'unhealthy'
                except:
                    health_status['mcp_services'][service_name] = 'unreachable'
            
            return {
                'success': True,
                'health': health_status
            }
            
        except Exception as e:
            logger.error(f"❌ Health check error: {e}")
            return {
                'success': False,
                'error': f"Health check failed: {str(e)}"
            }

    async def _handle_generic_query(self, request: Dict) -> Dict:
        """Handle generic queries by routing to OpenRouter"""
        logger.info("❓ Processing generic query")
        
        query = request.get('query', request.get('message', ''))
        
        # Use OpenRouter for generic queries
        return await self._handle_llm_query({
            'query': query,
            'context': {
                'system_role': 'AI Engineer Assistant',
                'capabilities': [
                    'Code analysis and debugging',
                    'Patch generation and application',
                    'Git operations and workflow management',
                    'System monitoring and health checks',
                    'Test execution and validation'
                ]
            }
        })

    async def _apply_patch(self, patch_data: Dict) -> Dict:
        """Apply a generated patch to the codebase"""
        try:
            file_path = patch_data.get('file_path')
            patch_content = patch_data.get('patch_content')
            
            if not file_path or not patch_content:
                return {
                    'success': False,
                    'error': 'Invalid patch data'
                }
            
            full_path = os.path.join(self.workspace_path, file_path)
            
            # Create backup
            backup_path = f"{full_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if os.path.exists(full_path):
                subprocess.run(['cp', full_path, backup_path])
            
            # Apply patch
            with open(full_path, 'w') as f:
                f.write(patch_content)
            
            return {
                'success': True,
                'file_path': file_path,
                'backup_path': backup_path
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def start_cli_interface(self):
        """Start interactive CLI interface"""
        print("🚀 Quantum Loop Debugger - AI Engineer")
        print("=" * 50)
        print("Available commands:")
        print("  fix <error_description>  - Generate and apply patch")
        print("  status                   - Check system status")
        print("  test [path]             - Run tests")
        print("  git <operation>         - Git operations")
        print("  query <question>        - Ask AI assistant")
        print("  health                  - System health check")
        print("  openrouter              - OpenRouter status")
        print("  rotate                  - Force model rotation")
        print("  quit                    - Exit")
        print("=" * 50)
        
        while True:
            try:
                user_input = input("\n🤖 AI Engineer > ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                # Parse command
                parts = user_input.split(' ', 1)
                command = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ''
                
                # Route command
                if command == 'fix':
                    request = {
                        'type': 'fix_patch',
                        'failure_context': {'error': args},
                        'auto_apply': True
                    }
                elif command == 'status':
                    request = {'type': 'status_check'}
                elif command == 'test':
                    request = {
                        'type': 'run_tests',
                        'test_path': args if args else 'test_script.py'
                    }
                elif command == 'git':
                    request = {
                        'type': 'git_operation',
                        'operation': 'status' if not args else args.split()[0],
                        'params': {}
                    }
                elif command == 'query':
                    request = {
                        'type': 'llm_query',
                        'query': args
                    }
                elif command == 'health':
                    request = {'type': 'system_health'}
                elif command == 'openrouter':
                    request = {'type': 'openrouter_status'}
                elif command == 'rotate':
                    request = {'type': 'force_model_rotation'}
                else:
                    request = {
                        'type': 'llm_query',
                        'query': user_input
                    }
                
                # Process request
                response = await self.handle_request(request)
                
                # Display response
                if response.get('success'):
                    print("✅ Success!")
                    if 'patch' in response:
                        patch = response['patch']
                        print(f"📝 Generated patch for: {patch.get('file_path', 'unknown')}")
                    elif 'health' in response:
                        health = response['health']
                        print(f"🏥 System Health: {health.get('ai_engineer', 'unknown')}")
                        if 'openrouter' in health:
                            or_health = health['openrouter']
                            print(f"🔄 OpenRouter: {or_health.get('status', 'unknown')}")
                            print(f"   Current Model: {or_health.get('current_model', 'none')}")
                            print(f"   Available Models: {or_health.get('available_models_count', 0)}/{or_health.get('total_models', 0)}")
                        for service, status in health.get('mcp_services', {}).items():
                            print(f"   {service}: {status}")
                    elif 'current_model' in response:
                        print(f"🔄 Current Model: {response['current_model']}")
                        print(f"📊 Available Models: {len([m for m in response.get('available_models', {}).values() if m.get('available')])}")
                        if response.get('rotation_history'):
                            print("📈 Recent Rotations:")
                            for rotation in response['rotation_history'][-3:]:
                                print(f"   {rotation['timestamp']}: {rotation['from_model']} → {rotation['to_model']}")
                    elif 'response' in response:
                        print(f"💬 {response['response']}")
                        if response.get('model_used'):
                            print(f"🤖 Model: {response['model_used']}")
                    else:
                        print(f"📊 {json.dumps(response, indent=2)}")
                else:
                    print(f"❌ Error: {response.get('error', 'Unknown error')}")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ CLI Error: {e}")

    async def start_server(self, port: int = 8080):
        """Start HTTP server for API requests"""
        from aiohttp import web, web_request
        
        async def handle_request(request: web_request.Request):
            """Handle API requests"""
            try:
                data = await request.json()
                response = await self.handle_request(data)
                return web.json_response(response)
            except Exception as e:
                logger.error(f"❌ API request error: {e}")
                return web.json_response({
                    'success': False,
                    'error': str(e)
                }, status=500)
        
        async def health_check(request: web_request.Request):
            """Health check endpoint"""
            return web.json_response({
                'status': 'healthy',
                'service': 'ai-engineer',
                'timestamp': datetime.now().isoformat()
            })
        
        app = web.Application()
        app.router.add_post('/api/request', handle_request)
        app.router.add_get('/health', health_check)
        
        logger.info(f"🌐 Starting AI Engineer server on port {port}")
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        
        # Keep server running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("🛑 Server shutdown requested")
        finally:
            await runner.cleanup()

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Quantum Loop Debugger - AI Engineer')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--mode', choices=['cli', 'server'], default='cli', help='Run mode')
    parser.add_argument('--port', type=int, default=8080, help='Server port (server mode only)')
    
    args = parser.parse_args()
    
    # Load configuration
    config = None
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    # Initialize AI Engineer
    ai_engineer = AIEngineer(config)
    
    # Create logs directory
    os.makedirs('/workspace/logs', exist_ok=True)
    
    if args.mode == 'cli':
        await ai_engineer.start_cli_interface()
    else:
        await ai_engineer.start_server(args.port)

if __name__ == "__main__":
    asyncio.run(main())
