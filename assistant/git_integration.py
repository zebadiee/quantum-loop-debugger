
#!/usr/bin/env python3
"""
Quantum Loop Debugger - Git Integration Manager
Handles Git operations for the AI Engineer system
"""

import asyncio
import logging
import os
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class GitManager:
    """
    Git operations manager for AI Engineer
    """
    
    def __init__(self, workspace_path: str, config: Dict):
        self.workspace_path = workspace_path
        self.github_token = config.get('github_token')
        self.auto_commit = config.get('auto_commit', True)
        self.auto_pr = config.get('auto_pr', False)
        
        logger.info("🔀 Git Manager initialized")
        logger.info(f"📁 Workspace: {workspace_path}")
        logger.info(f"🤖 Auto-commit: {self.auto_commit}")
        logger.info(f"🔄 Auto-PR: {self.auto_pr}")

    async def get_status(self) -> Dict:
        """Get current Git status"""
        try:
            result = await self._run_git_command(['status', '--porcelain'])
            
            if result['success']:
                changes = result['output'].strip().split('\n') if result['output'].strip() else []
                
                # Get current branch
                branch_result = await self._run_git_command(['branch', '--show-current'])
                current_branch = branch_result['output'].strip() if branch_result['success'] else 'unknown'
                
                # Get last commit
                commit_result = await self._run_git_command(['log', '-1', '--oneline'])
                last_commit = commit_result['output'].strip() if commit_result['success'] else 'No commits'
                
                return {
                    'success': True,
                    'current_branch': current_branch,
                    'changes': len(changes),
                    'changed_files': changes,
                    'last_commit': last_commit,
                    'clean': len(changes) == 0
                }
            else:
                return {
                    'success': False,
                    'error': result['error']
                }
                
        except Exception as e:
            logger.error(f"❌ Git status error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def commit(self, message: str, files: List[str] = None) -> Dict:
        """Commit changes to Git"""
        try:
            # Add files
            if files:
                for file in files:
                    add_result = await self._run_git_command(['add', file])
                    if not add_result['success']:
                        return {
                            'success': False,
                            'error': f"Failed to add {file}: {add_result['error']}"
                        }
            else:
                # Add all changes
                add_result = await self._run_git_command(['add', '.'])
                if not add_result['success']:
                    return {
                        'success': False,
                        'error': f"Failed to add files: {add_result['error']}"
                    }
            
            # Commit
            commit_result = await self._run_git_command(['commit', '-m', message])
            
            if commit_result['success']:
                logger.info(f"✅ Git commit successful: {message}")
                return {
                    'success': True,
                    'message': message,
                    'output': commit_result['output']
                }
            else:
                return {
                    'success': False,
                    'error': commit_result['error']
                }
                
        except Exception as e:
            logger.error(f"❌ Git commit error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def push(self, branch: str = None, remote: str = 'origin') -> Dict:
        """Push changes to remote repository"""
        try:
            if not self.github_token:
                return {
                    'success': False,
                    'error': 'GitHub token not configured'
                }
            
            # Get current branch if not specified
            if not branch:
                branch_result = await self._run_git_command(['branch', '--show-current'])
                if branch_result['success']:
                    branch = branch_result['output'].strip()
                else:
                    return {
                        'success': False,
                        'error': 'Could not determine current branch'
                    }
            
            # Push
            push_result = await self._run_git_command(['push', remote, branch])
            
            if push_result['success']:
                logger.info(f"✅ Git push successful: {remote}/{branch}")
                return {
                    'success': True,
                    'branch': branch,
                    'remote': remote,
                    'output': push_result['output']
                }
            else:
                return {
                    'success': False,
                    'error': push_result['error']
                }
                
        except Exception as e:
            logger.error(f"❌ Git push error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def create_pull_request(self, title: str, body: str = '', base_branch: str = 'main', head_branch: str = None) -> Dict:
        """Create a pull request (placeholder - would need GitHub API integration)"""
        try:
            # This is a placeholder implementation
            # In a real implementation, you would use GitHub API to create PR
            
            logger.info(f"🔄 PR creation requested: {title}")
            logger.info(f"   Base: {base_branch}, Head: {head_branch}")
            
            return {
                'success': True,
                'title': title,
                'body': body,
                'base_branch': base_branch,
                'head_branch': head_branch,
                'message': 'PR creation would be handled by GitHub API integration'
            }
            
        except Exception as e:
            logger.error(f"❌ PR creation error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def auto_commit(self, message: str) -> Dict:
        """Auto-commit changes if enabled"""
        if not self.auto_commit:
            return {
                'success': False,
                'error': 'Auto-commit is disabled'
            }
        
        return await self.commit(message)

    async def health_check(self) -> Dict:
        """Check Git health"""
        try:
            # Check if we're in a Git repository
            result = await self._run_git_command(['status'])
            
            if result['success']:
                return {
                    'status': 'healthy',
                    'git_available': True,
                    'in_repository': True
                }
            else:
                return {
                    'status': 'unhealthy',
                    'git_available': True,
                    'in_repository': False,
                    'error': result['error']
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'git_available': False,
                'error': str(e)
            }

    async def _run_git_command(self, args: List[str]) -> Dict:
        """Run a Git command and return result"""
        try:
            cmd = ['git'] + args
            
            # Set up environment with GitHub token if available
            env = os.environ.copy()
            if self.github_token:
                env['GIT_ASKPASS'] = 'echo'
                env['GIT_USERNAME'] = 'token'
                env['GIT_PASSWORD'] = self.github_token
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.workspace_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                'success': process.returncode == 0,
                'output': stdout.decode('utf-8'),
                'error': stderr.decode('utf-8'),
                'returncode': process.returncode
            }
            
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': str(e),
                'returncode': -1
            }
