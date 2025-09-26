
#!/usr/bin/env python3
"""
Enhanced AI Engineer Core - Advanced Task Execution with Self-Learning
Integrates memory system and feedback engine for adaptive behavior
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import argparse

from .core import AIEngineer as BaseAIEngineer
from .memory_system import MemorySystem
from .feedback_engine import FeedbackEngine
from .knowledge_system import KnowledgeSystem

logger = logging.getLogger(__name__)

class EnhancedAIEngineer(BaseAIEngineer):
    """
    Enhanced AI Engineer with self-learning capabilities
    Extends the base AI Engineer with memory, feedback, and knowledge systems
    """
    
    def __init__(self, config: Optional[Dict] = None):
        # Initialize base AI Engineer
        super().__init__(config)
        
        # Initialize self-learning components
        self.memory_system = MemorySystem()
        self.feedback_engine = FeedbackEngine()
        self.knowledge_system = KnowledgeSystem()
        
        # Enhanced state management
        self.learning_enabled = True
        self.adaptation_mode = 'automatic'  # 'automatic', 'manual', 'disabled'
        self.confidence_threshold = 0.7
        
        # Performance tracking
        self.task_start_times = {}
        self.learning_metrics = {
            'total_adaptations': 0,
            'successful_adaptations': 0,
            'knowledge_items_learned': 0,
            'memory_experiences': 0
        }
        
        logger.info("🧠 Enhanced AI Engineer initialized with self-learning capabilities")

    async def handle_request(self, request: Dict) -> Dict:
        """
        Enhanced request handler with learning integration
        """
        request_id = request.get('id', f"req_{datetime.now().timestamp()}")
        task_type = request.get('type', 'unknown')
        
        # Record task start time
        self.task_start_times[request_id] = time.time()
        
        # Get adaptive prompt if learning is enabled
        if self.learning_enabled and task_type != 'system_health':
            try:
                context = {
                    'request': request,
                    'timestamp': datetime.now().isoformat(),
                    'session_id': request.get('session_id', 'default')
                }
                
                # Get similar experiences for context
                similar_experiences = await self.memory_system.retrieve_similar_experiences(
                    context, task_type, limit=3, success_only=True
                )
                
                if similar_experiences:
                    logger.info(f"🔍 Found {len(similar_experiences)} similar experiences for context")
                    request['_learning_context'] = {
                        'similar_experiences': [
                            {
                                'action': exp.action_taken,
                                'success': exp.success,
                                'feedback_score': exp.feedback_score,
                                'tags': exp.tags
                            }
                            for exp in similar_experiences
                        ]
                    }
            except Exception as e:
                logger.warning(f"Failed to retrieve learning context: {e}")
        
        # Execute the request using base implementation
        response = await super().handle_request(request)
        
        # Record feedback if learning is enabled
        if self.learning_enabled:
            await self._record_task_feedback(request_id, request, response)
        
        return response

    async def _record_task_feedback(self, 
                                  request_id: str, 
                                  request: Dict, 
                                  response: Dict):
        """
        Record feedback for the completed task
        """
        try:
            # Calculate execution time
            execution_time = time.time() - self.task_start_times.get(request_id, time.time())
            
            # Extract task information
            task_type = request.get('type', 'unknown')
            action = self._extract_action_description(request, response)
            success = response.get('success', False)
            
            # Record in feedback engine
            feedback_id = await self.feedback_engine.record_feedback(
                task_id=request_id,
                task_type=task_type,
                action=action,
                result=response,
                execution_time=execution_time
            )
            
            # Capture experience in memory system
            context = {
                'request_type': task_type,
                'request_params': request,
                'execution_time': execution_time,
                'timestamp': datetime.now().isoformat()
            }
            
            # Calculate feedback score based on response
            feedback_score = self._calculate_feedback_score(response, execution_time)
            
            # Extract tags for categorization
            tags = self._extract_tags(request, response)
            
            experience_id = await self.memory_system.capture_experience(
                task_type=task_type,
                context=context,
                action_taken=action,
                result=response,
                success=success,
                feedback_score=feedback_score,
                tags=tags
            )
            
            # Update learning metrics
            self.learning_metrics['memory_experiences'] += 1
            
            # Clean up
            if request_id in self.task_start_times:
                del self.task_start_times[request_id]
            
            logger.debug(f"📊 Recorded learning data: feedback={feedback_id}, experience={experience_id}")
            
        except Exception as e:
            logger.error(f"Failed to record task feedback: {e}")

    def _extract_action_description(self, request: Dict, response: Dict) -> str:
        """Extract a description of the action taken"""
        task_type = request.get('type', 'unknown')
        
        if task_type == 'fix_patch':
            return f"Generated patch for: {request.get('failure_context', {}).get('error_type', 'unknown error')}"
        elif task_type == 'run_tests':
            return f"Executed tests: {request.get('test_path', 'default')}"
        elif task_type == 'git_operation':
            return f"Git operation: {request.get('operation', 'unknown')}"
        elif task_type == 'llm_query':
            query = request.get('query', '')
            return f"LLM query: {query[:50]}..." if len(query) > 50 else f"LLM query: {query}"
        else:
            return f"Executed {task_type} task"

    def _calculate_feedback_score(self, response: Dict, execution_time: float) -> float:
        """Calculate a feedback score based on response quality"""
        base_score = 1.0 if response.get('success', False) else 0.0
        
        # Adjust for execution time
        if execution_time < 5:
            time_bonus = 0.2
        elif execution_time < 30:
            time_bonus = 0.1
        elif execution_time > 120:
            time_bonus = -0.2
        else:
            time_bonus = 0.0
        
        # Adjust for response quality
        quality_bonus = 0.0
        if 'patch' in response and response['patch']:
            quality_bonus += 0.1
        if 'health' in response and response['health']:
            quality_bonus += 0.1
        if response.get('error'):
            quality_bonus -= 0.2
        
        return max(0.0, min(1.0, base_score + time_bonus + quality_bonus))

    def _extract_tags(self, request: Dict, response: Dict) -> List[str]:
        """Extract tags for categorizing the experience"""
        tags = []
        
        # Task type tag
        task_type = request.get('type', 'unknown')
        tags.append(task_type)
        
        # Success/failure tag
        tags.append('success' if response.get('success', False) else 'failure')
        
        # Specific tags based on task type
        if task_type == 'fix_patch':
            if 'patch' in response:
                tags.append('patch_generated')
            if request.get('auto_apply'):
                tags.append('auto_applied')
        elif task_type == 'git_operation':
            operation = request.get('operation')
            if operation:
                tags.append(f'git_{operation}')
        elif task_type == 'llm_query':
            if request.get('model'):
                tags.append(f"model_{request['model']}")
        
        # Error type tags
        if response.get('error'):
            error_msg = response['error'].lower()
            if 'timeout' in error_msg:
                tags.append('timeout_error')
            elif 'permission' in error_msg:
                tags.append('permission_error')
            elif 'network' in error_msg:
                tags.append('network_error')
        
        return tags

    async def _handle_llm_query(self, request: Dict) -> Dict:
        """Enhanced LLM query handler with adaptive prompts"""
        if not self.learning_enabled:
            return await super()._handle_llm_query(request)
        
        try:
            # Get adaptive prompt
            context = {
                'query': request.get('query', ''),
                'model': request.get('model'),
                'original_context': request.get('context', {})
            }
            
            adaptive_prompt = await self.memory_system.get_adaptive_prompt(
                task_type='llm_query',
                context=context,
                base_prompt=request.get('query', '')
            )
            
            # Update request with adaptive prompt
            enhanced_request = request.copy()
            enhanced_request['query'] = adaptive_prompt
            
            # Add learning context to the prompt if available
            if '_learning_context' in request:
                learning_context = request['_learning_context']
                if learning_context.get('similar_experiences'):
                    context_info = "\n\nBased on similar successful experiences:\n"
                    for i, exp in enumerate(learning_context['similar_experiences'][:2]):
                        context_info += f"- {exp['action']} (success rate: {exp['feedback_score']:.2f})\n"
                    enhanced_request['query'] += context_info
            
            logger.info("🎯 Using adaptive prompt for LLM query")
            return await super()._handle_llm_query(enhanced_request)
            
        except Exception as e:
            logger.warning(f"Failed to use adaptive prompt, falling back to original: {e}")
            return await super()._handle_llm_query(request)

    async def _handle_fix_patch(self, request: Dict) -> Dict:
        """Enhanced patch generation with learning"""
        if not self.learning_enabled:
            return await super()._handle_fix_patch(request)
        
        try:
            # Get similar successful patch experiences
            failure_context = request.get('failure_context', {})
            similar_experiences = await self.memory_system.retrieve_similar_experiences(
                query_context=failure_context,
                task_type='fix_patch',
                limit=3,
                success_only=True
            )
            
            # Enhance failure context with learning insights
            if similar_experiences:
                enhanced_context = failure_context.copy()
                enhanced_context['similar_successful_fixes'] = [
                    {
                        'action': exp.action_taken,
                        'context': exp.context,
                        'feedback_score': exp.feedback_score
                    }
                    for exp in similar_experiences
                ]
                
                enhanced_request = request.copy()
                enhanced_request['failure_context'] = enhanced_context
                
                logger.info(f"🔧 Enhanced patch request with {len(similar_experiences)} similar successful fixes")
                return await super()._handle_fix_patch(enhanced_request)
            
        except Exception as e:
            logger.warning(f"Failed to enhance patch request with learning: {e}")
        
        return await super()._handle_fix_patch(request)

    async def get_learning_status(self) -> Dict[str, Any]:
        """Get comprehensive learning system status"""
        try:
            # Get memory system stats
            memory_stats = await self.memory_system.get_memory_stats()
            
            # Get feedback engine performance summary
            performance_summary = await self.feedback_engine.get_performance_summary()
            
            # Get learning insights
            learning_insights = await self.feedback_engine.get_learning_insights()
            
            # Get knowledge system stats
            knowledge_stats = await self.knowledge_system.get_knowledge_stats()
            
            return {
                'learning_enabled': self.learning_enabled,
                'adaptation_mode': self.adaptation_mode,
                'confidence_threshold': self.confidence_threshold,
                'learning_metrics': self.learning_metrics,
                'memory_system': memory_stats,
                'feedback_engine': performance_summary,
                'learning_insights': learning_insights,
                'knowledge_system': knowledge_stats,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get learning status: {e}")
            return {
                'error': str(e),
                'learning_enabled': self.learning_enabled,
                'timestamp': datetime.now().isoformat()
            }

    async def configure_learning(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Configure learning system parameters"""
        try:
            if 'learning_enabled' in config:
                self.learning_enabled = config['learning_enabled']
            
            if 'adaptation_mode' in config:
                if config['adaptation_mode'] in ['automatic', 'manual', 'disabled']:
                    self.adaptation_mode = config['adaptation_mode']
            
            if 'confidence_threshold' in config:
                threshold = float(config['confidence_threshold'])
                if 0.0 <= threshold <= 1.0:
                    self.confidence_threshold = threshold
            
            # Configure memory system
            if 'memory_config' in config:
                memory_config = config['memory_config']
                if 'max_experiences' in memory_config:
                    self.memory_system.max_experiences = memory_config['max_experiences']
                if 'similarity_threshold' in memory_config:
                    self.memory_system.similarity_threshold = memory_config['similarity_threshold']
            
            # Configure feedback engine
            if 'feedback_config' in config:
                feedback_config = config['feedback_config']
                if 'evaluation_window' in feedback_config:
                    self.feedback_engine.evaluation_window = feedback_config['evaluation_window']
                if 'optimization_threshold' in feedback_config:
                    self.feedback_engine.optimization_threshold = feedback_config['optimization_threshold']
            
            logger.info("⚙️ Learning system configuration updated")
            return {
                'success': True,
                'message': 'Learning configuration updated successfully',
                'current_config': {
                    'learning_enabled': self.learning_enabled,
                    'adaptation_mode': self.adaptation_mode,
                    'confidence_threshold': self.confidence_threshold
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to configure learning system: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def trigger_learning_optimization(self) -> Dict[str, Any]:
        """Manually trigger learning optimization"""
        try:
            # Trigger memory system cleanup
            await self.memory_system.cleanup_old_experiences()
            
            # Force feedback engine optimization check
            await self.feedback_engine._check_optimization_triggers()
            
            # Update learning metrics
            self.learning_metrics['total_adaptations'] += 1
            
            logger.info("🔄 Manual learning optimization triggered")
            return {
                'success': True,
                'message': 'Learning optimization completed',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to trigger learning optimization: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def ingest_knowledge(self, source: str, content: str = None) -> Dict[str, Any]:
        """Ingest knowledge from external sources"""
        try:
            result = await self.knowledge_system.ingest_knowledge(source, content)
            
            if result.get('success'):
                self.learning_metrics['knowledge_items_learned'] += result.get('items_processed', 0)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to ingest knowledge: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def start_enhanced_cli_interface(self):
        """Start enhanced CLI interface with learning commands"""
        print("🚀 Quantum Loop Debugger - Enhanced AI Engineer with Self-Learning")
        print("=" * 70)
        print("Available commands:")
        print("  fix <error_description>  - Generate and apply patch")
        print("  status                   - Check system status")
        print("  test [path]             - Run tests")
        print("  git <operation>         - Git operations")
        print("  query <question>        - Ask AI assistant")
        print("  health                  - System health check")
        print("  openrouter              - OpenRouter status")
        print("  rotate                  - Force model rotation")
        print("  learning                - Learning system status")
        print("  configure <config>      - Configure learning system")
        print("  optimize                - Trigger learning optimization")
        print("  ingest <source>         - Ingest knowledge from source")
        print("  quit                    - Exit")
        print("=" * 70)
        
        while True:
            try:
                user_input = input("\n🧠 Enhanced AI Engineer > ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                # Parse command
                parts = user_input.split(' ', 1)
                command = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ''
                
                # Route enhanced commands
                if command == 'learning':
                    response = await self.get_learning_status()
                elif command == 'configure':
                    try:
                        config = json.loads(args) if args else {}
                        response = await self.configure_learning(config)
                    except json.JSONDecodeError:
                        response = {'success': False, 'error': 'Invalid JSON configuration'}
                elif command == 'optimize':
                    response = await self.trigger_learning_optimization()
                elif command == 'ingest':
                    response = await self.ingest_knowledge(args)
                else:
                    # Use base CLI handling for standard commands
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
                
                # Display response with enhanced formatting
                await self._display_enhanced_response(command, response)
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ CLI Error: {e}")

    async def _display_enhanced_response(self, command: str, response: Dict[str, Any]):
        """Display enhanced response with learning insights"""
        if response.get('success'):
            print("✅ Success!")
            
            if command == 'learning':
                self._display_learning_status(response)
            elif command == 'configure':
                print(f"⚙️ {response.get('message', 'Configuration updated')}")
                if 'current_config' in response:
                    config = response['current_config']
                    print(f"   Learning Enabled: {config['learning_enabled']}")
                    print(f"   Adaptation Mode: {config['adaptation_mode']}")
                    print(f"   Confidence Threshold: {config['confidence_threshold']}")
            elif command == 'optimize':
                print(f"🔄 {response.get('message', 'Optimization completed')}")
            elif command == 'ingest':
                print(f"📚 Knowledge ingestion: {response.get('message', 'Completed')}")
                if 'items_processed' in response:
                    print(f"   Items processed: {response['items_processed']}")
            else:
                # Standard response display
                if 'patch' in response:
                    patch = response['patch']
                    print(f"📝 Generated patch for: {patch.get('file_path', 'unknown')}")
                elif 'health' in response:
                    health = response['health']
                    print(f"🏥 System Health: {health.get('ai_engineer', 'unknown')}")
                elif 'response' in response:
                    print(f"💬 {response['response']}")
                    if response.get('model_used'):
                        print(f"🤖 Model: {response['model_used']}")
                else:
                    print(f"📊 {json.dumps(response, indent=2)}")
        else:
            print(f"❌ Error: {response.get('error', 'Unknown error')}")

    def _display_learning_status(self, status: Dict[str, Any]):
        """Display learning system status"""
        print("🧠 Learning System Status:")
        print(f"   Enabled: {status['learning_enabled']}")
        print(f"   Adaptation Mode: {status['adaptation_mode']}")
        print(f"   Confidence Threshold: {status['confidence_threshold']}")
        
        metrics = status.get('learning_metrics', {})
        print(f"   Total Adaptations: {metrics.get('total_adaptations', 0)}")
        print(f"   Memory Experiences: {metrics.get('memory_experiences', 0)}")
        print(f"   Knowledge Items: {metrics.get('knowledge_items_learned', 0)}")
        
        memory = status.get('memory_system', {})
        if memory:
            print(f"📝 Memory System:")
            print(f"   Total Experiences: {memory.get('total_experiences', 0)}")
            print(f"   Success Rate: {memory.get('success_rate', 0):.2%}")
            print(f"   Recent Activity: {memory.get('recent_activity', 0)}")
        
        feedback = status.get('feedback_engine', {})
        if feedback and 'overall' in feedback:
            overall = feedback['overall']
            print(f"🔄 Feedback Engine:")
            print(f"   Overall Success Rate: {overall.get('success_rate', 0):.2%}")
            print(f"   Average Execution Time: {overall.get('average_execution_time', 0):.1f}s")
            print(f"   Total Events: {overall.get('total_events', 0)}")

# TODO: Implement additional enhanced features
# - Interactive learning mode with user feedback
# - Advanced prompt optimization using reinforcement learning
# - Multi-agent collaboration with shared learning
# - Integration with external AI services for enhanced capabilities
# - Real-time performance monitoring and alerting
# - Automated knowledge discovery from code repositories
