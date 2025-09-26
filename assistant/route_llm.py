
#!/usr/bin/env python3
"""
Quantum Loop Debugger - Safe RouteLLM Wrapper
Cost-controlled and whitelisted model access for AI operations
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import requests
import aiohttp

logger = logging.getLogger(__name__)

class RouteLLMClient:
    """
    Safe RouteLLM wrapper with cost controls and model whitelisting
    """
    
    # Whitelisted models with cost per 1K tokens (input/output)
    WHITELISTED_MODELS = {
        'gpt-4o-mini': {'input_cost': 0.00015, 'output_cost': 0.0006, 'max_tokens': 128000},
        'gpt-4o': {'input_cost': 0.005, 'output_cost': 0.015, 'max_tokens': 128000},
        'claude-3-haiku': {'input_cost': 0.00025, 'output_cost': 0.00125, 'max_tokens': 200000},
        'claude-3-sonnet': {'input_cost': 0.003, 'output_cost': 0.015, 'max_tokens': 200000},
        'claude-3-opus': {'input_cost': 0.015, 'output_cost': 0.075, 'max_tokens': 200000},
        'gemini-1.5-flash': {'input_cost': 0.000075, 'output_cost': 0.0003, 'max_tokens': 1000000},
        'gemini-1.5-pro': {'input_cost': 0.00125, 'output_cost': 0.005, 'max_tokens': 2000000}
    }
    
    def __init__(self, config: Dict):
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url', 'https://api.routellm.com/v1')
        self.cost_limit_per_hour = config.get('cost_limit_per_hour', 10.0)
        self.cost_limit_per_day = config.get('cost_limit_per_day', 50.0)
        self.default_model = config.get('default_model', 'gpt-4o-mini')
        self.fallback_model = config.get('fallback_model', 'claude-3-haiku')
        
        # Cost tracking
        self.cost_tracker = {
            'hourly': {'amount': 0.0, 'reset_time': datetime.now() + timedelta(hours=1)},
            'daily': {'amount': 0.0, 'reset_time': datetime.now() + timedelta(days=1)}
        }
        
        # Rate limiting
        self.rate_limiter = {
            'requests_per_minute': 60,
            'requests': [],
            'tokens_per_minute': 100000,
            'tokens': []
        }
        
        if not self.api_key:
            logger.warning("⚠️ RouteLLM API key not provided - LLM features will be limited")
        
        logger.info("🧠 RouteLLM client initialized")
        logger.info(f"💰 Cost limits: ${self.cost_limit_per_hour}/hour, ${self.cost_limit_per_day}/day")

    async def query(self, query: str, model: Optional[str] = None, context: Optional[Dict] = None) -> str:
        """
        Safe LLM query with cost and rate limiting
        """
        if not self.api_key:
            return "❌ RouteLLM API key not configured. Please set ROUTELLM_API_KEY environment variable."
        
        # Use default model if none specified
        if not model:
            model = self.default_model
        
        # Validate model
        if model not in self.WHITELISTED_MODELS:
            logger.warning(f"⚠️ Model {model} not whitelisted, using fallback: {self.fallback_model}")
            model = self.fallback_model
        
        # Check cost limits
        if not self._check_cost_limits():
            return "❌ Cost limit exceeded. Please wait or increase limits."
        
        # Check rate limits
        if not await self._check_rate_limits():
            return "❌ Rate limit exceeded. Please wait before making more requests."
        
        try:
            # Prepare request
            messages = self._prepare_messages(query, context)
            estimated_cost = self._estimate_cost(messages, model)
            
            # Final cost check
            if not self._can_afford(estimated_cost):
                return f"❌ Estimated cost ${estimated_cost:.4f} exceeds remaining budget."
            
            # Make API request
            response = await self._make_request(model, messages)
            
            # Track actual cost
            actual_cost = self._calculate_actual_cost(response, model)
            self._track_cost(actual_cost)
            
            # Extract response content
            content = self._extract_content(response)
            
            logger.info(f"✅ LLM query completed - Model: {model}, Cost: ${actual_cost:.4f}")
            return content
            
        except Exception as e:
            logger.error(f"❌ RouteLLM query failed: {e}")
            return f"❌ LLM query failed: {str(e)}"

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
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': model,
            'messages': messages,
            'max_tokens': min(4000, self.WHITELISTED_MODELS[model]['max_tokens']),
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
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API request failed: {response.status} - {error_text}")
                
                return await response.json()

    def _extract_content(self, response: Dict) -> str:
        """Extract content from API response"""
        try:
            return response['choices'][0]['message']['content']
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to extract content from response: {e}")
            return "❌ Failed to parse LLM response"

    def _estimate_cost(self, messages: List[Dict], model: str) -> float:
        """Estimate cost for the request"""
        model_info = self.WHITELISTED_MODELS[model]
        
        # Rough token estimation (4 chars = 1 token)
        total_chars = sum(len(msg['content']) for msg in messages)
        estimated_input_tokens = total_chars // 4
        estimated_output_tokens = 500  # Conservative estimate
        
        input_cost = (estimated_input_tokens / 1000) * model_info['input_cost']
        output_cost = (estimated_output_tokens / 1000) * model_info['output_cost']
        
        return input_cost + output_cost

    def _calculate_actual_cost(self, response: Dict, model: str) -> float:
        """Calculate actual cost from response"""
        try:
            usage = response.get('usage', {})
            input_tokens = usage.get('prompt_tokens', 0)
            output_tokens = usage.get('completion_tokens', 0)
            
            model_info = self.WHITELISTED_MODELS[model]
            
            input_cost = (input_tokens / 1000) * model_info['input_cost']
            output_cost = (output_tokens / 1000) * model_info['output_cost']
            
            return input_cost + output_cost
            
        except Exception as e:
            logger.warning(f"Failed to calculate actual cost: {e}")
            return self._estimate_cost([], model)  # Fallback to estimation

    def _check_cost_limits(self) -> bool:
        """Check if cost limits are exceeded"""
        now = datetime.now()
        
        # Reset counters if needed
        if now > self.cost_tracker['hourly']['reset_time']:
            self.cost_tracker['hourly'] = {
                'amount': 0.0,
                'reset_time': now + timedelta(hours=1)
            }
        
        if now > self.cost_tracker['daily']['reset_time']:
            self.cost_tracker['daily'] = {
                'amount': 0.0,
                'reset_time': now + timedelta(days=1)
            }
        
        # Check limits
        if self.cost_tracker['hourly']['amount'] >= self.cost_limit_per_hour:
            logger.warning("⚠️ Hourly cost limit exceeded")
            return False
        
        if self.cost_tracker['daily']['amount'] >= self.cost_limit_per_day:
            logger.warning("⚠️ Daily cost limit exceeded")
            return False
        
        return True

    def _can_afford(self, estimated_cost: float) -> bool:
        """Check if we can afford the estimated cost"""
        hourly_remaining = self.cost_limit_per_hour - self.cost_tracker['hourly']['amount']
        daily_remaining = self.cost_limit_per_day - self.cost_tracker['daily']['amount']
        
        return estimated_cost <= min(hourly_remaining, daily_remaining)

    def _track_cost(self, cost: float):
        """Track the actual cost"""
        self.cost_tracker['hourly']['amount'] += cost
        self.cost_tracker['daily']['amount'] += cost

    async def _check_rate_limits(self) -> bool:
        """Check rate limits"""
        now = time.time()
        minute_ago = now - 60
        
        # Clean old requests
        self.rate_limiter['requests'] = [
            req_time for req_time in self.rate_limiter['requests']
            if req_time > minute_ago
        ]
        
        # Check request limit
        if len(self.rate_limiter['requests']) >= self.rate_limiter['requests_per_minute']:
            logger.warning("⚠️ Request rate limit exceeded")
            return False
        
        # Add current request
        self.rate_limiter['requests'].append(now)
        return True

    async def health_check(self) -> Dict:
        """Health check for RouteLLM client"""
        try:
            if not self.api_key:
                return {
                    'status': 'unhealthy',
                    'reason': 'API key not configured'
                }
            
            # Simple test query
            test_response = await self.query(
                "Hello, this is a health check. Please respond with 'OK'.",
                model=self.fallback_model
            )
            
            if "OK" in test_response or "ok" in test_response.lower():
                return {
                    'status': 'healthy',
                    'cost_tracker': self.cost_tracker,
                    'available_models': list(self.WHITELISTED_MODELS.keys())
                }
            else:
                return {
                    'status': 'degraded',
                    'reason': 'Unexpected response from API'
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'reason': str(e)
            }

    def get_cost_summary(self) -> Dict:
        """Get current cost summary"""
        return {
            'hourly': {
                'spent': self.cost_tracker['hourly']['amount'],
                'limit': self.cost_limit_per_hour,
                'remaining': self.cost_limit_per_hour - self.cost_tracker['hourly']['amount'],
                'reset_time': self.cost_tracker['hourly']['reset_time'].isoformat()
            },
            'daily': {
                'spent': self.cost_tracker['daily']['amount'],
                'limit': self.cost_limit_per_day,
                'remaining': self.cost_limit_per_day - self.cost_tracker['daily']['amount'],
                'reset_time': self.cost_tracker['daily']['reset_time'].isoformat()
            }
        }

    def list_available_models(self) -> Dict:
        """List available models with their costs"""
        return {
            model: {
                'input_cost_per_1k': info['input_cost'],
                'output_cost_per_1k': info['output_cost'],
                'max_tokens': info['max_tokens']
            }
            for model, info in self.WHITELISTED_MODELS.items()
        }
