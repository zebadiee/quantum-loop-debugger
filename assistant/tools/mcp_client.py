
#!/usr/bin/env python3
"""
Quantum Loop Debugger - MCP Client
Client for communicating with MCP (Model Context Protocol) services
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
import aiohttp

logger = logging.getLogger(__name__)

class MCPClient:
    """
    Client for communicating with MCP services
    """
    
    def __init__(self, service_name: str, base_url: str, timeout: int = 30):
        self.service_name = service_name
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        
        logger.info(f"🔌 MCP Client initialized for {service_name} at {base_url}")

    async def call_method(self, method: str, params: Dict[str, Any]) -> Dict:
        """
        Call a method on the MCP service
        """
        try:
            payload = {
                'jsonrpc': '2.0',
                'id': f"{self.service_name}_{method}_{asyncio.get_event_loop().time()}",
                'method': method,
                'params': params
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/rpc",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        return {
                            'success': False,
                            'error': f"HTTP {response.status}: {error_text}"
                        }
                    
                    result = await response.json()
                    
                    if 'error' in result:
                        return {
                            'success': False,
                            'error': result['error']
                        }
                    
                    return {
                        'success': True,
                        **result.get('result', {})
                    }
                    
        except asyncio.TimeoutError:
            logger.error(f"❌ MCP call to {self.service_name}.{method} timed out")
            return {
                'success': False,
                'error': f"Request to {self.service_name} timed out"
            }
        except Exception as e:
            logger.error(f"❌ MCP call to {self.service_name}.{method} failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def health_check(self) -> Dict:
        """
        Check if the MCP service is healthy
        """
        return await self.call_method('health_check', {})

    async def get_capabilities(self) -> Dict:
        """
        Get the capabilities of the MCP service
        """
        return await self.call_method('get_capabilities', {})
