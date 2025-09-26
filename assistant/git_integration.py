
#!/usr/bin/env python3
"""
Quantum Loop Debugger - Git Integration
Automated Git operations for commits, PRs, and branch management
"""

import asyncio
import json
import logging
import os
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Any
import requests

logger = logging.getLogger(__name__)

class GitManager:
    """
    Git integration manager for automated version control operations
    """
    
    def __init__(self, workspace_path: str, config: Dict):
        self.workspace_path = workspace_path
        self.github_token = config.get('github_token')
        self.auto_commit = config.get('auto_commit', True)
        self.auto_pr = config.get('auto_pr', False)
        self.default_branch = config.get('default_branch', 'main')
        
        # Git configuration
        self.git_config = {
            'user.name': config.get('git_user_name', 'AI Engineer'),
            'user.email': config.get('git_user_email', 'ai-engineer@quantum-debugger.local')
        }
        
        logger.info("🔀 Git Manager initialized")
        logger.info(f"📁 Workspace: {workspace_path}")

    async def get_status(self) -> Dict:
        """Get current Git status"""
        try:
            # Get basic status
            status_result = await self._run_git_command(['status', '--porcelain'])
            branch_result = await self._run_git_command(['branch', '--show-current'])
            remote_result = await self._run_git_command(['remote', '-v'])
            
            # Parse status
            modified_files = []
            untracked_files = []
            staged_files = []
            
            for line in status_result.get('stdout', '').strip().split('\n'):
                if not line:
                    continue
                
                status_code = line[:2]
                file_path = line[3:]
                
                if status_code[0] in ['M', 'A', 'D', 'R', 'C']:
                    staged_files.append(file_path)
                if status_code[1] in ['M', 'D']:
                    modified_files.append(file_path)
                if status_code == '??':
                    untracked_files.append(file_path)
            
            return {
                'success': True,
                'current_branch': branch_result.get('stdout', '').strip(),
                'modified_files': modified_files,
                'untracked_files': untracked_files,
                'staged_files': staged_files,
                'remote_info': remote_result.get('stdout', '').strip(),
                'is_clean': len(modified_files) == 0 and len(untracked_files) == 0 and len(staged_files) == 0
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get Git status: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def commit(self, message: str, files: Optional[List[str]] = None) -> Dict:
        """Create a Git commit"""
        try:
            # Configure Git user if needed
            await self._ensure_git_config()
            
            # Add files
            if files:
                for file_path in files:
                    add_result = await self._run_git_command(['add', file_path])
                    if not add_result.get('success'):
                        return {
                            'success': False,
                            'error': f"Failed to add file {file_path}: {add_result.get('error')}"
                        }
            else:
                # Add all changes
                add_result = await self._run_git_command(['add', '.'])
                if not add_result.get('success'):
                    return {
                        'success': False,
                        'error': f"Failed to add files: {add_result.get('error')}"
                    }
            
            # Create commit
            commit_result = await self._run_git_command(['commit', '-m', message])
            
            if commit_result.get('success'):
                # Get commit hash
                hash_result = await self._run_git_command(['rev-parse', 'HEAD'])
                commit_hash = hash_result.get('stdout', '').strip()
                
                return {
                    'success': True,
                    'commit_hash': commit_hash,
                    'message': message,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': commit_result.get('error', 'Commit failed')
                }
                
        except Exception as e:
            logger.error(f"❌ Commit failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def push(self, branch: Optional[str] = None, remote: str = 'origin') -> Dict:
        """Push changes to remote repository"""
        try:
            if not branch:
                # Get current branch
                branch_result = await self._run_git_command(['branch', '--show-current'])
                branch = branch_result.get('stdout', '').strip()
            
            if not branch:
                return {
                    'success': False,
                    'error': 'No branch specified and could not determine current branch'
                }
            
            # Push to remote
            push_result = await self._run_git_command(['push', remote, branch])
            
            return {
                'success': push_result.get('success', False),
                'branch': branch,
                'remote': remote,
                'output': push_result.get('stdout', ''),
                'error': push_result.get('error') if not push_result.get('success') else None
            }
            
        except Exception as e:
            logger.error(f"❌ Push failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def create_branch(self, branch_name: str, base_branch: Optional[str] = None) -> Dict:
        """Create a new branch"""
        try:
            if not base_branch:
                base_branch = self.default_branch
            
            # Ensure we're on the base branch
            checkout_result = await self._run_git_command(['checkout', base_branch])
            if not checkout_result.get('success'):
                return {
                    'success': False,
                    'error': f"Failed to checkout base branch {base_branch}"
                }
            
            # Pull latest changes
            pull_result = await self._run_git_command(['pull', 'origin', base_branch])
            if not pull_result.get('success'):
                logger.warning(f"⚠️ Failed to pull latest changes: {pull_result.get('error')}")
            
            # Create and checkout new branch
            branch_result = await self._run_git_command(['checkout', '-b', branch_name])
            
            return {
                'success': branch_result.get('success', False),
                'branch_name': branch_name,
                'base_branch': base_branch,
                'error': branch_result.get('error') if not branch_result.get('success') else None
            }
            
        except Exception as e:
            logger.error(f"❌ Branch creation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def create_pull_request(self, title: str, body: str = '', base_branch: str = None, head_branch: str = None) -> Dict:
        """Create a pull request using GitHub API"""
        try:
            if not self.github_token:
                return {
                    'success': False,
                    'error': 'GitHub token not configured'
                }
            
            if not base_branch:
                base_branch = self.default_branch
            
            if not head_branch:
                # Get current branch
                branch_result = await self._run_git_command(['branch', '--show-current'])
                head_branch = branch_result.get('stdout', '').strip()
            
            # Get repository info
            remote_result = await self._run_git_command(['remote', 'get-url', 'origin'])
            remote_url = remote_result.get('stdout', '').strip()
            
            # Parse repository owner and name from URL
            repo_info = self._parse_repo_info(remote_url)
            if not repo_info:
                return {
                    'success': False,
                    'error': 'Could not parse repository information from remote URL'
                }
            
            # Create PR via GitHub API
            pr_data = {
                'title': title,
                'body': body,
                'head': head_branch,
                'base': base_branch
            }
            
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.post(
                f"https://api.github.com/repos/{repo_info['owner']}/{repo_info['repo']}/pulls",
                json=pr_data,
                headers=headers
            )
            
            if response.status_code == 201:
                pr_info = response.json()
                return {
                    'success': True,
                    'pr_number': pr_info['number'],
                    'pr_url': pr_info['html_url'],
                    'title': title,
                    'head_branch': head_branch,
                    'base_branch': base_branch
                }
            else:
                return {
                    'success': False,
                    'error': f"GitHub API error: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            logger.error(f"❌ PR creation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def auto_commit(self, message: str, files: Optional[List[str]] = None) -> Dict:
        """Automatically commit changes if auto_commit is enabled"""
        if not self.auto_commit:
            return {
                'success': False,
                'error': 'Auto-commit is disabled'
            }
        
        return await self.commit(message, files)

    async def health_check(self) -> Dict:
        """Health check for Git operations"""
        try:
            # Check if we're in a Git repository
            git_check = await self._run_git_command(['status'])
            
            if not git_check.get('success'):
                return {
                    'status': 'unhealthy',
                    'reason': 'Not in a Git repository or Git not available'
                }
            
            # Check Git configuration
            config_check = await self._ensure_git_config()
            
            # Check remote connectivity
            remote_check = await self._run_git_command(['remote', '-v'])
            
            return {
                'status': 'healthy',
                'git_available': True,
                'config_set': config_check,
                'has_remote': bool(remote_check.get('stdout', '').strip()),
                'github_token_configured': bool(self.github_token)
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'reason': str(e)
            }

    async def _run_git_command(self, args: List[str]) -> Dict:
        """Run a Git command and return the result"""
        try:
            cmd = ['git'] + args
            result = subprocess.run(
                cmd,
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Git command timed out'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def _ensure_git_config(self) -> bool:
        """Ensure Git is properly configured"""
        try:
            for key, value in self.git_config.items():
                config_result = await self._run_git_command(['config', key, value])
                if not config_result.get('success'):
                    logger.warning(f"⚠️ Failed to set Git config {key}: {config_result.get('error')}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Git configuration failed: {e}")
            return False

    def _parse_repo_info(self, remote_url: str) -> Optional[Dict]:
        """Parse repository owner and name from remote URL"""
        try:
            # Handle both HTTPS and SSH URLs
            if remote_url.startswith('https://github.com/'):
                # HTTPS: https://github.com/owner/repo.git
                parts = remote_url.replace('https://github.com/', '').replace('.git', '').split('/')
            elif remote_url.startswith('git@github.com:'):
                # SSH: git@github.com:owner/repo.git
                parts = remote_url.replace('git@github.com:', '').replace('.git', '').split('/')
            else:
                return None
            
            if len(parts) >= 2:
                return {
                    'owner': parts[0],
                    'repo': parts[1]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to parse repo info: {e}")
            return None
