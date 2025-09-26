
#!/usr/bin/env python3
"""
Quantum Loop Debugger - MCP Client
Client for communicating with MCP (Model Context Protocol) services
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class MCPClient:
    """
    Client for MCP service communication
    """
    
    def __init__(self, service_name: str, base_url: str):
        self.service_name = service_name
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=30)
        
        logger.info(f"🔌 MCP Client initialized for {service_name}")
        logger.info(f"🌐 Base URL: {base_url}")

    async def call_method(self, method: str, params: Dict[str, Any] = None) -> Dict:
        """
        Call a method on the MCP service
        """
        if params is None:
            params = {}
        
        try:
            payload = {
                'method': method,
                'params': params,
                'timestamp': asyncio.get_event_loop().time()
            }
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/mcp/call",
                    json=payload,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        logger.debug(f"✅ MCP call successful: {self.service_name}.{method}")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ MCP call failed: {response.status} - {error_text}")
                        return {
                            'success': False,
                            'error': f"HTTP {response.status}: {error_text}"
                        }
                        
        except asyncio.TimeoutError:
            logger.error(f"⏰ MCP call timeout: {self.service_name}.{method}")
            return {
                'success': False,
                'error': 'Request timeout'
            }
        except Exception as e:
            logger.error(f"❌ MCP call error: {self.service_name}.{method} - {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def health_check(self) -> Dict:
        """
        Check if the MCP service is healthy
        """
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{self.base_url}/health") as response:
                    if response.status == 200:
                        return {
                            'success': True,
                            'status': 'healthy',
                            'service': self.service_name
                        }
                    else:
                        return {
                            'success': False,
                            'status': 'unhealthy',
                            'service': self.service_name,
                            'error': f"HTTP {response.status}"
                        }
        except Exception as e:
            return {
                'success': False,
                'status': 'unreachable',
                'service': self.service_name,
                'error': str(e)
            }

    async def get_capabilities(self) -> Dict:
        """
        Get service capabilities
        """
        return await self.call_method('get_capabilities')

    async def get_status(self) -> Dict:
        """
        Get service status
        """
        return await self.call_method('get_status')
