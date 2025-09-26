
#!/usr/bin/env python3
"""
Feedback Loop Engine for AI Engineer - Continuous Learning and Improvement
Handles automatic result evaluation, learning from successes/failures, and prompt optimization
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np
from collections import defaultdict, deque
import statistics

logger = logging.getLogger(__name__)

@dataclass
class FeedbackEvent:
    """Represents a feedback event"""
    id: str
    timestamp: datetime
    task_id: str
    task_type: str
    action: str
    result: Dict[str, Any]
    success: bool
    execution_time: float
    error_message: Optional[str]
    user_feedback: Optional[Dict[str, Any]]
    automated_score: float
    improvement_suggestions: List[str]

@dataclass
class PerformanceMetrics:
    """Performance metrics for tracking improvement"""
    success_rate: float
    average_execution_time: float
    error_rate: float
    user_satisfaction: float
    improvement_trend: float
    total_tasks: int
    recent_performance: Dict[str, float]

class FeedbackEngine:
    """
    Feedback loop engine for continuous learning and improvement
    """
    
    def __init__(self, feedback_dir: str = "/workspace/feedback"):
        self.feedback_dir = Path(feedback_dir)
        self.feedback_dir.mkdir(parents=True, exist_ok=True)
        
        # Storage paths
        self.events_file = self.feedback_dir / "feedback_events.jsonl"
        self.metrics_file = self.feedback_dir / "performance_metrics.json"
        self.optimization_log = self.feedback_dir / "optimization_log.jsonl"
        
        # In-memory storage for fast access
        self.recent_events = deque(maxlen=1000)
        self.performance_history = defaultdict(list)
        self.optimization_rules = {}
        self.evaluation_functions = {}
        
        # Configuration
        self.evaluation_window = 100  # Number of recent events to consider
        self.optimization_threshold = 0.7  # Minimum success rate to trigger optimization
        self.learning_rate = 0.1
        self.feedback_weights = {
            'success': 0.4,
            'execution_time': 0.2,
            'user_feedback': 0.3,
            'error_severity': 0.1
        }
        
        # Initialize components
        self._load_historical_data()
        self._setup_evaluation_functions()
        
        logger.info(f"🔄 Feedback Engine initialized at {self.feedback_dir}")

    def _load_historical_data(self):
        """Load historical feedback events and metrics"""
        # Load feedback events
        if self.events_file.exists():
            with open(self.events_file, 'r') as f:
                for line in f:
                    try:
                        event_data = json.loads(line.strip())
                        event = FeedbackEvent(
                            id=event_data['id'],
                            timestamp=datetime.fromisoformat(event_data['timestamp']),
                            task_id=event_data['task_id'],
                            task_type=event_data['task_type'],
                            action=event_data['action'],
                            result=event_data['result'],
                            success=event_data['success'],
                            execution_time=event_data['execution_time'],
                            error_message=event_data.get('error_message'),
                            user_feedback=event_data.get('user_feedback'),
                            automated_score=event_data['automated_score'],
                            improvement_suggestions=event_data['improvement_suggestions']
                        )
                        self.recent_events.append(event)
                    except Exception as e:
                        logger.warning(f"Failed to load feedback event: {e}")
        
        # Load performance metrics
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r') as f:
                    metrics_data = json.load(f)
                    for task_type, history in metrics_data.items():
                        self.performance_history[task_type] = history
            except Exception as e:
                logger.warning(f"Failed to load performance metrics: {e}")

    def _setup_evaluation_functions(self):
        """Setup automated evaluation functions"""
        self.evaluation_functions = {
            'code_generation': self._evaluate_code_generation,
            'bug_fixing': self._evaluate_bug_fixing,
            'test_execution': self._evaluate_test_execution,
            'git_operation': self._evaluate_git_operation,
            'system_monitoring': self._evaluate_system_monitoring,
            'generic': self._evaluate_generic_task
        }

    async def record_feedback(self,
                            task_id: str,
                            task_type: str,
                            action: str,
                            result: Dict[str, Any],
                            execution_time: float,
                            user_feedback: Optional[Dict[str, Any]] = None) -> str:
        """
        Record feedback for a completed task
        """
        # Generate feedback event ID
        event_id = f"fb_{int(time.time() * 1000)}_{hash(task_id) % 10000}"
        
        # Evaluate task automatically
        success, automated_score, error_message, suggestions = await self._evaluate_task(
            task_type, action, result, execution_time
        )
        
        # Create feedback event
        event = FeedbackEvent(
            id=event_id,
            timestamp=datetime.now(),
            task_id=task_id,
            task_type=task_type,
            action=action,
            result=result,
            success=success,
            execution_time=execution_time,
            error_message=error_message,
            user_feedback=user_feedback,
            automated_score=automated_score,
            improvement_suggestions=suggestions
        )
        
        # Store event
        await self._store_feedback_event(event)
        
        # Update performance metrics
        await self._update_performance_metrics(event)
        
        # Trigger optimization if needed
        if len(self.recent_events) % 10 == 0:  # Check every 10 events
            await self._check_optimization_triggers()
        
        logger.info(f"📊 Recorded feedback: {event_id} (success: {success}, score: {automated_score:.2f})")
        return event_id

    async def _evaluate_task(self,
                           task_type: str,
                           action: str,
                           result: Dict[str, Any],
                           execution_time: float) -> Tuple[bool, float, Optional[str], List[str]]:
        """
        Automatically evaluate task performance
        """
        evaluator = self.evaluation_functions.get(task_type, self.evaluation_functions['generic'])
        return await evaluator(action, result, execution_time)

    async def _evaluate_code_generation(self,
                                      action: str,
                                      result: Dict[str, Any],
                                      execution_time: float) -> Tuple[bool, float, Optional[str], List[str]]:
        """Evaluate code generation tasks"""
        success = result.get('success', False)
        error_message = result.get('error')
        suggestions = []
        
        # Base score from success
        score = 1.0 if success else 0.0
        
        # Adjust for execution time
        if execution_time > 30:  # Slow execution
            score *= 0.8
            suggestions.append("Consider optimizing for faster execution")
        elif execution_time < 5:  # Very fast
            score *= 1.1
        
        # Check for code quality indicators
        if 'patch' in result:
            patch_data = result['patch']
            if patch_data.get('file_path'):
                score *= 1.1
                suggestions.append("Good: Generated specific file patch")
            
            if patch_data.get('backup_path'):
                score *= 1.05
                suggestions.append("Good: Created backup before applying patch")
        
        # Penalize for errors
        if error_message:
            if 'syntax' in error_message.lower():
                score *= 0.5
                suggestions.append("Focus on syntax validation before code generation")
            elif 'import' in error_message.lower():
                score *= 0.7
                suggestions.append("Verify import statements and dependencies")
        
        return success, min(score, 1.0), error_message, suggestions

    async def _evaluate_bug_fixing(self,
                                 action: str,
                                 result: Dict[str, Any],
                                 execution_time: float) -> Tuple[bool, float, Optional[str], List[str]]:
        """Evaluate bug fixing tasks"""
        success = result.get('success', False)
        error_message = result.get('error')
        suggestions = []
        
        score = 1.0 if success else 0.0
        
        # Check if tests pass after fix
        if 'test_result' in result:
            test_success = result['test_result'].get('success', False)
            if test_success:
                score *= 1.2
                suggestions.append("Excellent: Fix verified by tests")
            else:
                score *= 0.6
                suggestions.append("Consider running tests to verify fixes")
        
        # Check for proper error handling
        if success and 'error_handling' in action.lower():
            score *= 1.1
            suggestions.append("Good: Included error handling in fix")
        
        # Execution time considerations
        if execution_time > 60:
            score *= 0.9
            suggestions.append("Consider breaking down complex fixes into smaller steps")
        
        return success, min(score, 1.0), error_message, suggestions

    async def _evaluate_test_execution(self,
                                     action: str,
                                     result: Dict[str, Any],
                                     execution_time: float) -> Tuple[bool, float, Optional[str], List[str]]:
        """Evaluate test execution tasks"""
        success = result.get('success', False)
        returncode = result.get('returncode', -1)
        suggestions = []
        
        score = 1.0 if success and returncode == 0 else 0.0
        
        # Check test output quality
        stdout = result.get('stdout', '')
        stderr = result.get('stderr', '')
        
        if stdout and 'passed' in stdout.lower():
            score *= 1.1
            suggestions.append("Good: Tests passed successfully")
        
        if stderr and not success:
            if 'timeout' in stderr.lower():
                suggestions.append("Consider optimizing test performance or increasing timeout")
            elif 'import' in stderr.lower():
                suggestions.append("Check test dependencies and imports")
            elif 'assertion' in stderr.lower():
                suggestions.append("Review test assertions and expected outcomes")
        
        # Execution time evaluation
        if execution_time > 300:  # 5 minutes
            score *= 0.8
            suggestions.append("Tests taking too long - consider optimization")
        
        return success, min(score, 1.0), result.get('error'), suggestions

    async def _evaluate_git_operation(self,
                                    action: str,
                                    result: Dict[str, Any],
                                    execution_time: float) -> Tuple[bool, float, Optional[str], List[str]]:
        """Evaluate Git operations"""
        success = result.get('success', False)
        operation = result.get('operation', '')
        suggestions = []
        
        score = 1.0 if success else 0.0
        
        # Bonus for successful complex operations
        if success:
            if operation in ['create_pr', 'merge']:
                score *= 1.2
                suggestions.append("Excellent: Successfully completed complex Git operation")
            elif operation == 'commit':
                if 'message' in result.get('result', {}):
                    score *= 1.1
                    suggestions.append("Good: Commit included descriptive message")
        
        # Check for common Git issues
        error_message = result.get('error', '')
        if error_message:
            if 'conflict' in error_message.lower():
                suggestions.append("Consider implementing conflict resolution strategies")
            elif 'permission' in error_message.lower():
                suggestions.append("Check Git credentials and repository permissions")
            elif 'branch' in error_message.lower():
                suggestions.append("Verify branch existence and checkout status")
        
        return success, min(score, 1.0), error_message, suggestions

    async def _evaluate_system_monitoring(self,
                                        action: str,
                                        result: Dict[str, Any],
                                        execution_time: float) -> Tuple[bool, float, Optional[str], List[str]]:
        """Evaluate system monitoring tasks"""
        success = result.get('success', False)
        suggestions = []
        
        score = 1.0 if success else 0.0
        
        # Check monitoring data quality
        if 'health' in result:
            health_data = result['health']
            healthy_services = sum(1 for status in health_data.values() 
                                 if isinstance(status, str) and status == 'healthy')
            total_services = len(health_data)
            
            if total_services > 0:
                health_ratio = healthy_services / total_services
                score *= (0.5 + 0.5 * health_ratio)
                
                if health_ratio < 0.8:
                    suggestions.append("Some services are unhealthy - investigate issues")
                else:
                    suggestions.append("Good: Most services are healthy")
        
        # Fast monitoring is good
        if execution_time < 5:
            score *= 1.1
            suggestions.append("Good: Fast monitoring response")
        
        return success, min(score, 1.0), result.get('error'), suggestions

    async def _evaluate_generic_task(self,
                                   action: str,
                                   result: Dict[str, Any],
                                   execution_time: float) -> Tuple[bool, float, Optional[str], List[str]]:
        """Evaluate generic tasks"""
        success = result.get('success', False)
        suggestions = []
        
        score = 1.0 if success else 0.0
        
        # Basic execution time penalty
        if execution_time > 120:  # 2 minutes
            score *= 0.9
            suggestions.append("Consider optimizing task execution time")
        
        # Check for error details
        if not success and result.get('error'):
            suggestions.append("Review error details for improvement opportunities")
        
        return success, score, result.get('error'), suggestions

    async def _store_feedback_event(self, event: FeedbackEvent):
        """Store feedback event to persistent storage"""
        # Add to in-memory storage
        self.recent_events.append(event)
        
        # Append to file
        with open(self.events_file, 'a') as f:
            event_data = asdict(event)
            event_data['timestamp'] = event.timestamp.isoformat()
            f.write(json.dumps(event_data) + '\n')

    async def _update_performance_metrics(self, event: FeedbackEvent):
        """Update performance metrics based on new feedback"""
        task_type = event.task_type
        
        # Calculate current metrics
        recent_events = [e for e in self.recent_events 
                        if e.task_type == task_type][-self.evaluation_window:]
        
        if not recent_events:
            return
        
        # Calculate metrics
        success_rate = sum(1 for e in recent_events if e.success) / len(recent_events)
        avg_execution_time = statistics.mean(e.execution_time for e in recent_events)
        error_rate = sum(1 for e in recent_events if e.error_message) / len(recent_events)
        avg_score = statistics.mean(e.automated_score for e in recent_events)
        
        # Calculate user satisfaction if available
        user_scores = [e.user_feedback.get('satisfaction', 0.5) 
                      for e in recent_events 
                      if e.user_feedback and 'satisfaction' in e.user_feedback]
        user_satisfaction = statistics.mean(user_scores) if user_scores else 0.5
        
        # Calculate improvement trend
        if len(self.performance_history[task_type]) > 0:
            last_success_rate = self.performance_history[task_type][-1]['success_rate']
            improvement_trend = success_rate - last_success_rate
        else:
            improvement_trend = 0.0
        
        # Create metrics object
        metrics = PerformanceMetrics(
            success_rate=success_rate,
            average_execution_time=avg_execution_time,
            error_rate=error_rate,
            user_satisfaction=user_satisfaction,
            improvement_trend=improvement_trend,
            total_tasks=len(recent_events),
            recent_performance={
                'last_24h': self._calculate_recent_performance(task_type, hours=24),
                'last_7d': self._calculate_recent_performance(task_type, hours=168),
                'last_30d': self._calculate_recent_performance(task_type, hours=720)
            }
        )
        
        # Store metrics
        self.performance_history[task_type].append({
            'timestamp': datetime.now().isoformat(),
            'success_rate': success_rate,
            'average_execution_time': avg_execution_time,
            'error_rate': error_rate,
            'user_satisfaction': user_satisfaction,
            'improvement_trend': improvement_trend,
            'total_tasks': len(recent_events)
        })
        
        # Keep only recent history
        if len(self.performance_history[task_type]) > 100:
            self.performance_history[task_type] = self.performance_history[task_type][-100:]
        
        # Save to file
        await self._save_performance_metrics()

    def _calculate_recent_performance(self, task_type: str, hours: int) -> float:
        """Calculate performance for recent time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_events = [e for e in self.recent_events 
                        if e.task_type == task_type and e.timestamp > cutoff_time]
        
        if not recent_events:
            return 0.0
        
        return sum(1 for e in recent_events if e.success) / len(recent_events)

    async def _save_performance_metrics(self):
        """Save performance metrics to file"""
        with open(self.metrics_file, 'w') as f:
            json.dump(dict(self.performance_history), f, indent=2)

    async def _check_optimization_triggers(self):
        """Check if optimization should be triggered"""
        for task_type, events in self._group_recent_events_by_type().items():
            if len(events) < 10:  # Need minimum events for optimization
                continue
            
            success_rate = sum(1 for e in events if e.success) / len(events)
            
            if success_rate < self.optimization_threshold:
                await self._trigger_optimization(task_type, events)

    def _group_recent_events_by_type(self) -> Dict[str, List[FeedbackEvent]]:
        """Group recent events by task type"""
        groups = defaultdict(list)
        for event in list(self.recent_events)[-self.evaluation_window:]:
            groups[event.task_type].append(event)
        return dict(groups)

    async def _trigger_optimization(self, task_type: str, events: List[FeedbackEvent]):
        """Trigger optimization for underperforming task type"""
        logger.info(f"🔧 Triggering optimization for {task_type}")
        
        # Analyze failure patterns
        failed_events = [e for e in events if not e.success]
        common_errors = defaultdict(int)
        common_suggestions = defaultdict(int)
        
        for event in failed_events:
            if event.error_message:
                # Extract error type
                error_type = self._extract_error_type(event.error_message)
                common_errors[error_type] += 1
            
            for suggestion in event.improvement_suggestions:
                common_suggestions[suggestion] += 1
        
        # Generate optimization recommendations
        recommendations = []
        
        # Most common errors
        if common_errors:
            top_error = max(common_errors.items(), key=lambda x: x[1])
            recommendations.append(f"Address common error: {top_error[0]} (occurs in {top_error[1]} cases)")
        
        # Most common suggestions
        if common_suggestions:
            top_suggestion = max(common_suggestions.items(), key=lambda x: x[1])
            recommendations.append(f"Implement: {top_suggestion[0]} (suggested {top_suggestion[1]} times)")
        
        # Performance-based recommendations
        avg_execution_time = statistics.mean(e.execution_time for e in events)
        if avg_execution_time > 60:
            recommendations.append("Optimize execution time - currently averaging {:.1f}s".format(avg_execution_time))
        
        # Log optimization event
        optimization_event = {
            'timestamp': datetime.now().isoformat(),
            'task_type': task_type,
            'success_rate': sum(1 for e in events if e.success) / len(events),
            'total_events': len(events),
            'failed_events': len(failed_events),
            'common_errors': dict(common_errors),
            'recommendations': recommendations
        }
        
        with open(self.optimization_log, 'a') as f:
            f.write(json.dumps(optimization_event) + '\n')
        
        logger.info(f"📈 Generated {len(recommendations)} optimization recommendations for {task_type}")

    def _extract_error_type(self, error_message: str) -> str:
        """Extract error type from error message"""
        error_message = error_message.lower()
        
        if 'timeout' in error_message:
            return 'timeout'
        elif 'permission' in error_message or 'access' in error_message:
            return 'permission'
        elif 'syntax' in error_message:
            return 'syntax'
        elif 'import' in error_message or 'module' in error_message:
            return 'import'
        elif 'connection' in error_message or 'network' in error_message:
            return 'network'
        elif 'file' in error_message and 'not found' in error_message:
            return 'file_not_found'
        else:
            return 'unknown'

    async def get_performance_summary(self, task_type: str = None) -> Dict[str, Any]:
        """Get performance summary for analysis"""
        if task_type:
            events = [e for e in self.recent_events if e.task_type == task_type]
            task_types = [task_type]
        else:
            events = list(self.recent_events)
            task_types = list(set(e.task_type for e in events))
        
        summary = {
            'overall': {
                'total_events': len(events),
                'success_rate': sum(1 for e in events if e.success) / max(len(events), 1),
                'average_execution_time': statistics.mean(e.execution_time for e in events) if events else 0,
                'average_score': statistics.mean(e.automated_score for e in events) if events else 0
            },
            'by_task_type': {},
            'recent_trends': {},
            'optimization_opportunities': []
        }
        
        # Per task type analysis
        for tt in task_types:
            tt_events = [e for e in events if e.task_type == tt]
            if tt_events:
                summary['by_task_type'][tt] = {
                    'total_events': len(tt_events),
                    'success_rate': sum(1 for e in tt_events if e.success) / len(tt_events),
                    'average_execution_time': statistics.mean(e.execution_time for e in tt_events),
                    'average_score': statistics.mean(e.automated_score for e in tt_events),
                    'error_rate': sum(1 for e in tt_events if e.error_message) / len(tt_events)
                }
        
        # Recent trends
        for period, hours in [('24h', 24), ('7d', 168), ('30d', 720)]:
            cutoff = datetime.now() - timedelta(hours=hours)
            recent_events = [e for e in events if e.timestamp > cutoff]
            if recent_events:
                summary['recent_trends'][period] = {
                    'success_rate': sum(1 for e in recent_events if e.success) / len(recent_events),
                    'total_events': len(recent_events)
                }
        
        # Optimization opportunities
        for tt in task_types:
            tt_events = [e for e in events if e.task_type == tt]
            if len(tt_events) >= 5:
                success_rate = sum(1 for e in tt_events if e.success) / len(tt_events)
                if success_rate < 0.8:
                    summary['optimization_opportunities'].append({
                        'task_type': tt,
                        'success_rate': success_rate,
                        'priority': 'high' if success_rate < 0.5 else 'medium'
                    })
        
        return summary

    async def get_learning_insights(self) -> Dict[str, Any]:
        """Get insights about learning progress and patterns"""
        insights = {
            'learning_velocity': {},
            'success_patterns': {},
            'failure_patterns': {},
            'improvement_areas': [],
            'strengths': []
        }
        
        # Calculate learning velocity (improvement over time)
        for task_type in set(e.task_type for e in self.recent_events):
            task_events = [e for e in self.recent_events if e.task_type == task_type]
            if len(task_events) >= 10:
                # Split into early and recent halves
                mid_point = len(task_events) // 2
                early_events = task_events[:mid_point]
                recent_events = task_events[mid_point:]
                
                early_success = sum(1 for e in early_events if e.success) / len(early_events)
                recent_success = sum(1 for e in recent_events if e.success) / len(recent_events)
                
                insights['learning_velocity'][task_type] = {
                    'improvement': recent_success - early_success,
                    'early_success_rate': early_success,
                    'recent_success_rate': recent_success
                }
        
        # Success patterns
        successful_events = [e for e in self.recent_events if e.success]
        if successful_events:
            # Most successful task types
            task_success = defaultdict(list)
            for event in successful_events:
                task_success[event.task_type].append(event.automated_score)
            
            for task_type, scores in task_success.items():
                insights['success_patterns'][task_type] = {
                    'average_score': statistics.mean(scores),
                    'consistency': 1.0 - (statistics.stdev(scores) if len(scores) > 1 else 0),
                    'count': len(scores)
                }
        
        # Failure patterns
        failed_events = [e for e in self.recent_events if not e.success]
        if failed_events:
            error_types = defaultdict(int)
            for event in failed_events:
                if event.error_message:
                    error_type = self._extract_error_type(event.error_message)
                    error_types[error_type] += 1
            
            insights['failure_patterns'] = dict(error_types)
        
        # Improvement areas (low success rate task types)
        task_performance = {}
        for task_type in set(e.task_type for e in self.recent_events):
            task_events = [e for e in self.recent_events if e.task_type == task_type]
            if len(task_events) >= 5:
                success_rate = sum(1 for e in task_events if e.success) / len(task_events)
                task_performance[task_type] = success_rate
        
        # Sort by performance
        sorted_performance = sorted(task_performance.items(), key=lambda x: x[1])
        
        # Bottom 3 are improvement areas
        insights['improvement_areas'] = [
            {'task_type': tt, 'success_rate': sr} 
            for tt, sr in sorted_performance[:3] if sr < 0.8
        ]
        
        # Top 3 are strengths
        insights['strengths'] = [
            {'task_type': tt, 'success_rate': sr} 
            for tt, sr in sorted_performance[-3:] if sr > 0.8
        ]
        
        return insights

# TODO: Implement additional features
# - A/B testing for different approaches
# - Reinforcement learning integration
# - Automated prompt optimization using genetic algorithms
# - Integration with external monitoring systems
# - Real-time feedback collection from users
# - Predictive failure detection
