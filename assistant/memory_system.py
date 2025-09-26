
#!/usr/bin/env python3
"""
Memory System for AI Engineer - MCP-Based Experience Capture and Learning
Handles experience storage, prompt adaptation, and contextual memory retrieval
"""

import asyncio
import json
import logging
import os
import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle

logger = logging.getLogger(__name__)

@dataclass
class Experience:
    """Represents a single experience/interaction"""
    id: str
    timestamp: datetime
    task_type: str
    context: Dict[str, Any]
    action_taken: str
    result: Dict[str, Any]
    success: bool
    feedback_score: float
    tags: List[str]
    embedding: Optional[List[float]] = None

@dataclass
class PromptTemplate:
    """Represents an adaptive prompt template"""
    id: str
    name: str
    template: str
    success_rate: float
    usage_count: int
    last_updated: datetime
    context_tags: List[str]
    performance_metrics: Dict[str, float]

class MemorySystem:
    """
    MCP-based memory system for capturing experiences and adapting prompts
    """
    
    def __init__(self, memory_dir: str = "/workspace/memory"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # Database for structured storage
        self.db_path = self.memory_dir / "experiences.db"
        self.vectorizer_path = self.memory_dir / "vectorizer.pkl"
        self.embeddings_path = self.memory_dir / "embeddings.npy"
        
        # Initialize components
        self.vectorizer = None
        self.experience_embeddings = None
        self.experiences_cache = {}
        self.prompt_templates = {}
        
        # Configuration
        self.max_experiences = 10000
        self.similarity_threshold = 0.7
        self.adaptation_threshold = 0.8
        
        self._initialize_database()
        self._load_vectorizer()
        self._load_prompt_templates()
        
        logger.info(f"🧠 Memory System initialized at {self.memory_dir}")

    def _initialize_database(self):
        """Initialize SQLite database for experience storage"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS experiences (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    task_type TEXT,
                    context TEXT,
                    action_taken TEXT,
                    result TEXT,
                    success BOOLEAN,
                    feedback_score REAL,
                    tags TEXT,
                    embedding_index INTEGER
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS prompt_templates (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    template TEXT,
                    success_rate REAL,
                    usage_count INTEGER,
                    last_updated TEXT,
                    context_tags TEXT,
                    performance_metrics TEXT
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_task_type ON experiences(task_type)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_success ON experiences(success)
            """)

    def _load_vectorizer(self):
        """Load or create TF-IDF vectorizer for experience embeddings"""
        if self.vectorizer_path.exists():
            with open(self.vectorizer_path, 'rb') as f:
                self.vectorizer = pickle.load(f)
            
            if self.embeddings_path.exists():
                self.experience_embeddings = np.load(self.embeddings_path)
        else:
            self.vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )

    def _save_vectorizer(self):
        """Save vectorizer and embeddings to disk"""
        if self.vectorizer:
            with open(self.vectorizer_path, 'wb') as f:
                pickle.dump(self.vectorizer, f)
        
        if self.experience_embeddings is not None:
            np.save(self.embeddings_path, self.experience_embeddings)

    def _load_prompt_templates(self):
        """Load prompt templates from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM prompt_templates")
            for row in cursor.fetchall():
                template = PromptTemplate(
                    id=row[0],
                    name=row[1],
                    template=row[2],
                    success_rate=row[3],
                    usage_count=row[4],
                    last_updated=datetime.fromisoformat(row[5]),
                    context_tags=json.loads(row[6]),
                    performance_metrics=json.loads(row[7])
                )
                self.prompt_templates[template.id] = template

    async def capture_experience(self, 
                                task_type: str,
                                context: Dict[str, Any],
                                action_taken: str,
                                result: Dict[str, Any],
                                success: bool,
                                feedback_score: float = 0.0,
                                tags: List[str] = None) -> str:
        """
        Capture a new experience and store it in memory
        """
        experience_id = hashlib.md5(
            f"{task_type}_{action_taken}_{datetime.now().isoformat()}".encode()
        ).hexdigest()
        
        experience = Experience(
            id=experience_id,
            timestamp=datetime.now(),
            task_type=task_type,
            context=context,
            action_taken=action_taken,
            result=result,
            success=success,
            feedback_score=feedback_score,
            tags=tags or []
        )
        
        # Store in database
        await self._store_experience(experience)
        
        # Update embeddings
        await self._update_embeddings()
        
        # Trigger prompt adaptation if needed
        if success and feedback_score > self.adaptation_threshold:
            await self._adapt_prompts(experience)
        
        logger.info(f"📝 Captured experience: {experience_id} (success: {success})")
        return experience_id

    async def _store_experience(self, experience: Experience):
        """Store experience in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO experiences 
                (id, timestamp, task_type, context, action_taken, result, 
                 success, feedback_score, tags, embedding_index)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                experience.id,
                experience.timestamp.isoformat(),
                experience.task_type,
                json.dumps(experience.context),
                experience.action_taken,
                json.dumps(experience.result),
                experience.success,
                experience.feedback_score,
                json.dumps(experience.tags),
                len(self.experiences_cache)
            ))
        
        self.experiences_cache[experience.id] = experience

    async def _update_embeddings(self):
        """Update TF-IDF embeddings for all experiences"""
        if not self.experiences_cache:
            return
        
        # Prepare text data for vectorization
        texts = []
        for exp in self.experiences_cache.values():
            text = f"{exp.task_type} {exp.action_taken} {' '.join(exp.tags)}"
            if exp.context:
                text += f" {json.dumps(exp.context)}"
            texts.append(text)
        
        # Fit or transform vectorizer
        if self.experience_embeddings is None:
            self.experience_embeddings = self.vectorizer.fit_transform(texts).toarray()
        else:
            # Add new embeddings
            new_embeddings = self.vectorizer.transform([texts[-1]]).toarray()
            self.experience_embeddings = np.vstack([self.experience_embeddings, new_embeddings])
        
        # Save updated vectorizer and embeddings
        self._save_vectorizer()

    async def retrieve_similar_experiences(self, 
                                         query_context: Dict[str, Any],
                                         task_type: str = None,
                                         limit: int = 5,
                                         success_only: bool = False) -> List[Experience]:
        """
        Retrieve experiences similar to the given context
        """
        if not self.experiences_cache or self.experience_embeddings is None:
            return []
        
        # Create query embedding
        query_text = f"{task_type or ''} {json.dumps(query_context)}"
        query_embedding = self.vectorizer.transform([query_text]).toarray()
        
        # Calculate similarities
        similarities = cosine_similarity(query_embedding, self.experience_embeddings)[0]
        
        # Get top similar experiences
        similar_indices = np.argsort(similarities)[::-1]
        
        results = []
        for idx in similar_indices:
            if len(results) >= limit:
                break
            
            if similarities[idx] < self.similarity_threshold:
                break
            
            # Find experience by index
            for exp in self.experiences_cache.values():
                if hash(exp.id) % len(self.experiences_cache) == idx:
                    if success_only and not exp.success:
                        continue
                    if task_type and exp.task_type != task_type:
                        continue
                    
                    results.append(exp)
                    break
        
        logger.info(f"🔍 Retrieved {len(results)} similar experiences")
        return results

    async def get_success_patterns(self, task_type: str = None) -> Dict[str, Any]:
        """
        Analyze success patterns from stored experiences
        """
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT * FROM experiences WHERE success = 1"
            params = []
            
            if task_type:
                query += " AND task_type = ?"
                params.append(task_type)
            
            cursor = conn.execute(query, params)
            successful_experiences = cursor.fetchall()
        
        if not successful_experiences:
            return {"patterns": [], "success_rate": 0.0}
        
        # Analyze patterns
        patterns = {
            "common_actions": {},
            "common_tags": {},
            "context_patterns": {},
            "success_rate": 0.0,
            "total_experiences": 0
        }
        
        for exp_data in successful_experiences:
            action = exp_data[4]  # action_taken
            tags = json.loads(exp_data[8])  # tags
            
            # Count common actions
            patterns["common_actions"][action] = patterns["common_actions"].get(action, 0) + 1
            
            # Count common tags
            for tag in tags:
                patterns["common_tags"][tag] = patterns["common_tags"].get(tag, 0) + 1
        
        # Calculate success rate
        total_query = "SELECT COUNT(*) FROM experiences"
        if task_type:
            total_query += " WHERE task_type = ?"
            cursor = conn.execute(total_query, [task_type])
        else:
            cursor = conn.execute(total_query)
        
        total_count = cursor.fetchone()[0]
        patterns["success_rate"] = len(successful_experiences) / max(total_count, 1)
        patterns["total_experiences"] = total_count
        
        logger.info(f"📊 Analyzed {len(successful_experiences)} successful experiences")
        return patterns

    async def _adapt_prompts(self, experience: Experience):
        """
        Adapt prompt templates based on successful experiences
        """
        # Find relevant prompt templates
        relevant_templates = []
        for template in self.prompt_templates.values():
            if any(tag in template.context_tags for tag in experience.tags):
                relevant_templates.append(template)
        
        # Update template performance metrics
        for template in relevant_templates:
            template.usage_count += 1
            template.last_updated = datetime.now()
            
            # Update success rate (exponential moving average)
            alpha = 0.1
            template.success_rate = (
                alpha * (1.0 if experience.success else 0.0) + 
                (1 - alpha) * template.success_rate
            )
            
            # Update performance metrics
            if "feedback_scores" not in template.performance_metrics:
                template.performance_metrics["feedback_scores"] = []
            
            template.performance_metrics["feedback_scores"].append(experience.feedback_score)
            
            # Keep only recent scores
            if len(template.performance_metrics["feedback_scores"]) > 100:
                template.performance_metrics["feedback_scores"] = \
                    template.performance_metrics["feedback_scores"][-100:]
            
            # Save updated template
            await self._save_prompt_template(template)

    async def _save_prompt_template(self, template: PromptTemplate):
        """Save prompt template to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO prompt_templates
                (id, name, template, success_rate, usage_count, last_updated, 
                 context_tags, performance_metrics)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                template.id,
                template.name,
                template.template,
                template.success_rate,
                template.usage_count,
                template.last_updated.isoformat(),
                json.dumps(template.context_tags),
                json.dumps(template.performance_metrics)
            ))

    async def get_adaptive_prompt(self, 
                                task_type: str,
                                context: Dict[str, Any],
                                base_prompt: str = None) -> str:
        """
        Get an adaptive prompt based on past experiences and success patterns
        """
        # Get similar successful experiences
        similar_experiences = await self.retrieve_similar_experiences(
            context, task_type, limit=3, success_only=True
        )
        
        # Get success patterns
        patterns = await self.get_success_patterns(task_type)
        
        # Find best matching prompt template
        best_template = None
        best_score = 0.0
        
        for template in self.prompt_templates.values():
            if task_type in template.context_tags:
                score = template.success_rate * (1 + np.log(template.usage_count + 1))
                if score > best_score:
                    best_score = score
                    best_template = template
        
        # Build adaptive prompt
        if best_template:
            adaptive_prompt = best_template.template
        else:
            adaptive_prompt = base_prompt or f"Task: {task_type}\nContext: {json.dumps(context)}"
        
        # Add insights from similar experiences
        if similar_experiences:
            adaptive_prompt += "\n\nBased on similar successful experiences:\n"
            for i, exp in enumerate(similar_experiences[:2]):
                adaptive_prompt += f"{i+1}. {exp.action_taken} (score: {exp.feedback_score:.2f})\n"
        
        # Add success patterns
        if patterns["common_actions"]:
            top_actions = sorted(
                patterns["common_actions"].items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3]
            adaptive_prompt += f"\nMost successful actions: {', '.join([a[0] for a in top_actions])}"
        
        logger.info(f"🎯 Generated adaptive prompt for {task_type}")
        return adaptive_prompt

    async def cleanup_old_experiences(self, days_to_keep: int = 30):
        """
        Clean up old experiences to maintain performance
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM experiences WHERE timestamp < ?",
                [cutoff_date.isoformat()]
            )
            deleted_count = cursor.rowcount
        
        # Rebuild cache and embeddings
        await self._rebuild_cache()
        
        logger.info(f"🧹 Cleaned up {deleted_count} old experiences")

    async def _rebuild_cache(self):
        """Rebuild in-memory cache from database"""
        self.experiences_cache.clear()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM experiences ORDER BY timestamp DESC")
            for row in cursor.fetchall():
                experience = Experience(
                    id=row[0],
                    timestamp=datetime.fromisoformat(row[1]),
                    task_type=row[2],
                    context=json.loads(row[3]),
                    action_taken=row[4],
                    result=json.loads(row[5]),
                    success=bool(row[6]),
                    feedback_score=row[7],
                    tags=json.loads(row[8])
                )
                self.experiences_cache[experience.id] = experience
        
        # Rebuild embeddings
        self.experience_embeddings = None
        await self._update_embeddings()

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        with sqlite3.connect(self.db_path) as conn:
            # Total experiences
            total_cursor = conn.execute("SELECT COUNT(*) FROM experiences")
            total_experiences = total_cursor.fetchone()[0]
            
            # Success rate
            success_cursor = conn.execute("SELECT COUNT(*) FROM experiences WHERE success = 1")
            successful_experiences = success_cursor.fetchone()[0]
            
            # Task type distribution
            task_cursor = conn.execute("""
                SELECT task_type, COUNT(*) 
                FROM experiences 
                GROUP BY task_type 
                ORDER BY COUNT(*) DESC
            """)
            task_distribution = dict(task_cursor.fetchall())
            
            # Recent activity
            recent_cursor = conn.execute("""
                SELECT COUNT(*) FROM experiences 
                WHERE timestamp > ?
            """, [(datetime.now() - timedelta(days=7)).isoformat()])
            recent_activity = recent_cursor.fetchone()[0]
        
        return {
            "total_experiences": total_experiences,
            "successful_experiences": successful_experiences,
            "success_rate": successful_experiences / max(total_experiences, 1),
            "task_distribution": task_distribution,
            "recent_activity": recent_activity,
            "prompt_templates": len(self.prompt_templates),
            "memory_size_mb": self.db_path.stat().st_size / (1024 * 1024),
            "last_updated": datetime.now().isoformat()
        }

# TODO: Implement additional features
# - Semantic clustering of experiences
# - Automated prompt template generation
# - Integration with external knowledge bases
# - Multi-modal experience capture (text, code, images)
# - Federated learning across multiple AI Engineer instances
