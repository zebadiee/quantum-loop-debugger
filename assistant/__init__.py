
"""
Quantum Loop Debugger - AI Engineer Assistant
Enhanced AI-powered development assistant with MCP integration and Self-Learning
"""

from .core import AIEngineer
from .enhanced_core import EnhancedAIEngineer
from .memory_system import MemorySystem
from .feedback_engine import FeedbackEngine
from .knowledge_system import KnowledgeSystem
from .mcp_learning_server import MCPLearningServer
from .openrouter_client import OpenRouterFree
from .git_integration import GitManager
from .route_llm import RouteLLM

__version__ = "2.0.0"
__author__ = "Quantum Loop Debugger Team"
__description__ = "AI Engineer service with self-learning capabilities for automated development workflows"

__all__ = [
    'AIEngineer',
    'EnhancedAIEngineer',
    'MemorySystem',
    'FeedbackEngine',
    'KnowledgeSystem',
    'MCPLearningServer',
    'OpenRouterFree', 
    'GitManager',
    'RouteLLM'
]"
