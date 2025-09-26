
#!/usr/bin/env python3
"""
Quantum Loop Debugger - OpenRouter Free Models Client
Automatic failover system for free OpenRouter models with usage tracking
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import aiohttp
from pathlib import Path

logger = logging.getLogger(__name__)

class OpenRouterFree:
    """
    OpenRouter Free Models Client with automatic failover and usage tracking
    """
    
    # Free OpenRouter models with their limits and capabilities
    FREE_MODELS = {
        'meta-llama/llama-3.2-3b-instruct:free': {
            'name': 'Llama 3.2 3B Instruct',
            'context_length': 131072,
            'daily_limit': 200,  # requests per day
            'hourly_limit': 20,  # requests per hour
            'provider': 'Meta',
            'capabilities': ['chat', 'instruct']
        },
        'meta-llama/llama-3.2-1b-instruct:free': {
            'name': 'Llama 3.2 1B Instruct', 
            'context_length': 131072,
            'daily_limit': 200,
            'hourly_limit': 20,
            'provider': 'Meta',
            'capabilities': ['chat', 'instruct']
        },
        'microsoft/phi-3-mini-128k-instruct:free': {
            'name': 'Phi-3 Mini 128K Instruct',
            'context_length': 128000,
            'daily_limit': 200,
            'hourly_limit': 20,
            'provider': 'Microsoft',
            'capabilities': ['chat', 'instruct']
        },
        'microsoft/phi-3-medium-128k-instruct:free': {
            'name': 'Phi-3 Medium 128K Instruct',
            'context_length': 128000,
            'daily_limit': 200,
            'hourly_limit': 20,
            'provider': 'Microsoft',
            'capabilities': ['chat', 'instruct']
        },
        'google/gemma-2-9b-it:free': {
            'name': 'Gemma 2 9B IT',
            'context_length': 8192,
            'daily_limit': 200,
            'hourly_limit': 20,
            'provider': 'Google',
            'capabilities': ['chat', 'instruct']
        },
        'huggingfaceh4/zephyr-7b-beta:free': {
            'name': 'Zephyr 7B Beta',
            'context_length': 32768,
            'daily_limit': 200,
            'hourly_limit': 20,
            'provider': 'HuggingFace',
            'capabilities': ['chat', 'instruct']
        },
        'openchat/openchat-7b:free': {
            'name': 'OpenChat 7B',
            'context_length': 8192,
            'daily_limit': 200,
            'hourly_limit': 20,
            'provider': 'OpenChat',
            'capabilities': ['chat', 'instruct']
        },
        'gryphe/mythomist-7b:free': {
            'name': 'MythoMist 7B',
            'context_length': 32768,
            'daily_limit': 200,
            'hourly_limit': 20,
            'provider': 'Gryphe',
            'capabilities': ['chat', 'creative']
        }
    }
    
    def __init__(self, config: Dict):
        self.api_key = config.get('api_key') or os.getenv('OPENROUTER_API_KEY')
        self.base_url = 'https://openrouter.ai/api/v1'
        self.app_name = config.get('app_name', 'Quantum-Loop-Debugger')
        self.app_url = config.get('app_url', 'https://github.com/zebadiee/quantum-loop-debugger')
        
        # Usage tracking file
        self.usage_file = Path('/workspace/logs/openrouter_usage.json')
        self.usage_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Current active model
        self.current_model = None
        self.model_rotation_index = 0
        
        # Load usage data
        self.usage_data = self._load_usage_data()
        
        # Initialize with first available model
        self._select_next_available_model()
        
        if not self.api_key:
            logger.warning("⚠️ OpenRouter API key not provided - free model features will be limited")
        else:
            logger.info("🔄 OpenRouter Free Models client initialized")
            logger.info(f"🎯 Current active model: {self.current_model}")
            logger.info(f"📊 Available free models: {len(self.FREE_MODELS)}")

    def _load_usage_data(self) -> Dict:
        """Load usage tracking data from file"""
        try:
            if self.usage_file.exists():
                with open(self.usage_file, 'r') as f:
                    data = json.load(f)
                    # Clean old data (older than 24 hours)
                    self._clean_old_usage_data(data)
                    return data
        except Exception as e:
            logger.warning(f"Failed to load usage data: {e}")
        
        # Return default structure
        return {
            'models': {model_id: {'requests': [], 'total_requests': 0, 'last_used': None} 
                      for model_id in self.FREE_MODELS.keys()},
            'rotation_history': [],
            'last_updated': datetime.now().isoformat()
        }

    def _save_usage_data(self):
        """Save usage tracking data to file"""
        try:
            self.usage_data['last_updated'] = datetime.now().isoformat()
            with open(self.usage_file, 'w') as f:
                json.dump(self.usage_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save usage data: {e}")

    def _clean_old_usage_data(self, data: Dict):
        """Clean usage data older than 24 hours"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        for model_id in data.get('models', {}):
            if 'requests' in data['models'][model_id]:
                # Filter requests from last 24 hours
                recent_requests = []
                for req_time_str in data['models'][model_id]['requests']:
                    try:
                        req_time = datetime.fromisoformat(req_time_str)
                        if req_time > cutoff_time:
                            recent_requests.append(req_time_str)
                    except:
                        continue
                data['models'][model_id]['requests'] = recent_requests

    def _select_next_available_model(self) -> bool:
        """Select the next available model with capacity"""
        models_list = list(self.FREE_MODELS.keys())
        attempts = 0
        
        while attempts < len(models_list):
            model_id = models_list[self.model_rotation_index]
            
            if self._check_model_availability(model_id):
                if self.current_model != model_id:
                    old_model = self.current_model
                    self.current_model = model_id
                    
                    # Log model rotation
                    rotation_entry = {
                        'timestamp': datetime.now().isoformat(),
                        'from_model': old_model,
                        'to_model': model_id,
                        'reason': 'quota_rotation' if old_model else 'initialization'
                    }
                    self.usage_data['rotation_history'].append(rotation_entry)
                    
                    # Keep only last 50 rotation entries
                    if len(self.usage_data['rotation_history']) > 50:
                        self.usage_data['rotation_history'] = self.usage_data['rotation_history'][-50:]
                    
                    logger.info(f"🔄 Model rotated: {old_model} → {model_id}")
                    logger.info(f"📝 Reason: {rotation_entry['reason']}")
                
                return True
            
            # Try next model
            self.model_rotation_index = (self.model_rotation_index + 1) % len(models_list)
            attempts += 1
        
        logger.error("❌ No available free models found!")
        return False

    def _check_model_availability(self, model_id: str) -> bool:
        """Check if a model has available quota"""
        if model_id not in self.FREE_MODELS:
            return False
        
        model_info = self.FREE_MODELS[model_id]
        model_usage = self.usage_data['models'].get(model_id, {'requests': []})
        
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)
        
        # Count recent requests
        hourly_requests = 0
        daily_requests = 0
        
        for req_time_str in model_usage.get('requests', []):
            try:
                req_time = datetime.fromisoformat(req_time_str)
                if req_time > hour_ago:
                    hourly_requests += 1
                if req_time > day_ago:
                    daily_requests += 1
            except:
                continue
        
        # Check limits
        hourly_available = hourly_requests < model_info['hourly_limit']
        daily_available = daily_requests < model_info['daily_limit']
        
        logger.debug(f"Model {model_id}: hourly {hourly_requests}/{model_info['hourly_limit']}, "
                    f"daily {daily_requests}/{model_info['daily_limit']}")
        
        return hourly_available and daily_available

    def _track_request(self, model_id: str):
        """Track a request for usage monitoring"""
        if model_id not in self.usage_data['models']:
            self.usage_data['models'][model_id] = {'requests': [], 'total_requests': 0, 'last_used': None}
        
        # Add current request
        now = datetime.now().isoformat()
        self.usage_data['models'][model_id]['requests'].append(now)
        self.usage_data['models'][model_id]['total_requests'] += 1
        self.usage_data['models'][model_id]['last_used'] = now
        
        # Save usage data
        self._save_usage_data()

    async def query(self, query: str, model: Optional[str] = None, context: Optional[Dict] = None) -> str:
        """
        Query with automatic failover between free models
        """
        if not self.api_key:
            return "❌ OpenRouter API key not configured. Please set OPENROUTER_API_KEY environment variable."
        
        # Use current model if none specified
        target_model = model if model and model in self.FREE_MODELS else self.current_model
        
        if not target_model:
            return "❌ No available free models found."
        
        max_retries = len(self.FREE_MODELS)
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Check if current model is still available
                if not self._check_model_availability(target_model):
                    logger.warning(f"⚠️ Model {target_model} quota exhausted, rotating...")
                    if not self._select_next_available_model():
                        return "❌ All free models have exhausted their quotas. Please try again later."
                    target_model = self.current_model
                
                # Prepare request
                messages = self._prepare_messages(query, context)
                
                # Make API request
                response = await self._make_request(target_model, messages)
                
                # Track successful request
                self._track_request(target_model)
                
                # Extract response content
                content = self._extract_content(response)
                
                logger.info(f"✅ Query completed - Model: {target_model}")
                return content
                
            except Exception as e:
                logger.error(f"❌ Query failed with model {target_model}: {e}")
                
                # Try next model
                if not self._select_next_available_model():
                    return f"❌ All free models failed. Last error: {str(e)}"
                
                target_model = self.current_model
                retry_count += 1
                
                # Brief delay before retry
                await asyncio.sleep(1)
        
        return "❌ All free models failed after maximum retries."

    def _prepare_messages(self, query: str, context: Optional[Dict] = None) -> List[Dict]:
        """Prepare messages for the API request"""
        messages = []
        
        # System message with context
        system_content = "You are an AI Engineer assistant for the Quantum Loop Debugger system."
        
        if context:
            if context.get('system_role'):
                system_content = context['system_role']
            
            if context.get('capabilities'):
                system_content += f"\n\nCapabilities: {', '.join(context['capabilities'])}"
            
            if context.get('workspace_info'):
                system_content += f"\n\nWorkspace: {context['workspace_info']}"
        
        messages.append({
            "role": "system",
            "content": system_content
        })
        
        # User query
        messages.append({
            "role": "user", 
            "content": query
        })
        
        return messages

    async def _make_request(self, model: str, messages: List[Dict]) -> Dict:
        """Make the actual API request"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': self.app_url,
            'X-Title': self.app_name
        }
        
        model_info = self.FREE_MODELS[model]
        
        payload = {
            'model': model,
            'messages': messages,
            'max_tokens': min(2000, model_info['context_length'] // 4),  # Conservative limit
            'temperature': 0.7,
            'stream': False
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 429:
                    # Rate limit hit
                    raise Exception(f"Rate limit exceeded for model {model}")
                elif response.status == 402:
                    # Quota exceeded
                    raise Exception(f"Quota exceeded for model {model}")
                elif response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API request failed: {response.status} - {error_text}")
                
                return await response.json()

    def _extract_content(self, response: Dict) -> str:
        """Extract content from API response"""
        try:
            return response['choices'][0]['message']['content']
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to extract content from response: {e}")
            return "❌ Failed to parse OpenRouter response"

    async def health_check(self) -> Dict:
        """Health check for OpenRouter client"""
        try:
            if not self.api_key:
                return {
                    'status': 'unhealthy',
                    'reason': 'API key not configured'
                }
            
            # Check current model availability
            current_available = self._check_model_availability(self.current_model) if self.current_model else False
            
            # Count available models
            available_models = sum(1 for model_id in self.FREE_MODELS.keys() 
                                 if self._check_model_availability(model_id))
            
            return {
                'status': 'healthy' if available_models > 0 else 'degraded',
                'current_model': self.current_model,
                'current_model_available': current_available,
                'available_models_count': available_models,
                'total_models': len(self.FREE_MODELS),
                'usage_summary': self.get_usage_summary()
            }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'reason': str(e)
            }

    def get_usage_summary(self) -> Dict:
        """Get current usage summary for all models"""
        summary = {}
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)
        
        for model_id, model_info in self.FREE_MODELS.items():
            model_usage = self.usage_data['models'].get(model_id, {'requests': []})
            
            # Count recent requests
            hourly_requests = 0
            daily_requests = 0
            
            for req_time_str in model_usage.get('requests', []):
                try:
                    req_time = datetime.fromisoformat(req_time_str)
                    if req_time > hour_ago:
                        hourly_requests += 1
                    if req_time > day_ago:
                        daily_requests += 1
                except:
                    continue
            
            summary[model_id] = {
                'name': model_info['name'],
                'provider': model_info['provider'],
                'hourly_usage': f"{hourly_requests}/{model_info['hourly_limit']}",
                'daily_usage': f"{daily_requests}/{model_info['daily_limit']}",
                'available': self._check_model_availability(model_id),
                'total_requests': model_usage.get('total_requests', 0),
                'last_used': model_usage.get('last_used')
            }
        
        return summary

    def get_rotation_history(self) -> List[Dict]:
        """Get model rotation history"""
        return self.usage_data.get('rotation_history', [])

    def force_model_rotation(self) -> bool:
        """Force rotation to next available model"""
        old_model = self.current_model
        self.model_rotation_index = (self.model_rotation_index + 1) % len(self.FREE_MODELS)
        
        if self._select_next_available_model():
            logger.info(f"🔄 Forced model rotation: {old_model} → {self.current_model}")
            return True
        return False

    def list_available_models(self) -> Dict:
        """List all available free models with their status"""
        models_status = {}
        
        for model_id, model_info in self.FREE_MODELS.items():
            models_status[model_id] = {
                'name': model_info['name'],
                'provider': model_info['provider'],
                'context_length': model_info['context_length'],
                'daily_limit': model_info['daily_limit'],
                'hourly_limit': model_info['hourly_limit'],
                'capabilities': model_info['capabilities'],
                'available': self._check_model_availability(model_id),
                'is_current': model_id == self.current_model
            }
        
        return models_status
