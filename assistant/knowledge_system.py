
#!/usr/bin/env python3
"""
Knowledge System for AI Engineer - Document Processing and Insight Synthesis
Handles knowledge ingestion, gap identification, and improvement proposals
"""

import asyncio
import json
import logging
import os
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import sqlite3
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import re
import requests
from urllib.parse import urlparse
import mimetypes

logger = logging.getLogger(__name__)

@dataclass
class KnowledgeItem:
    """Represents a piece of knowledge"""
    id: str
    title: str
    content: str
    source: str
    source_type: str  # 'document', 'url', 'code', 'manual'
    tags: List[str]
    importance_score: float
    confidence_score: float
    created_at: datetime
    last_accessed: datetime
    access_count: int
    related_items: List[str]
    metadata: Dict[str, Any]

@dataclass
class KnowledgeGap:
    """Represents an identified knowledge gap"""
    id: str
    description: str
    context: Dict[str, Any]
    priority: str  # 'high', 'medium', 'low'
    suggested_sources: List[str]
    related_failures: List[str]
    created_at: datetime
    status: str  # 'open', 'in_progress', 'resolved'

@dataclass
class ImprovementProposal:
    """Represents a proposed improvement"""
    id: str
    title: str
    description: str
    category: str  # 'process', 'knowledge', 'tool', 'skill'
    impact_score: float
    effort_score: float
    priority_score: float
    supporting_evidence: List[str]
    implementation_steps: List[str]
    created_at: datetime
    status: str  # 'proposed', 'approved', 'implemented', 'rejected'

class KnowledgeSystem:
    """
    Knowledge system for document processing and insight synthesis
    """
    
    def __init__(self, knowledge_dir: str = "/workspace/knowledge"):
        self.knowledge_dir = Path(knowledge_dir)
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        
        # Database and storage paths
        self.db_path = self.knowledge_dir / "knowledge.db"
        self.vectorizer_path = self.knowledge_dir / "knowledge_vectorizer.pkl"
        self.embeddings_path = self.knowledge_dir / "knowledge_embeddings.npy"
        self.documents_dir = self.knowledge_dir / "documents"
        self.documents_dir.mkdir(exist_ok=True)
        
        # In-memory storage
        self.knowledge_items = {}
        self.knowledge_gaps = {}
        self.improvement_proposals = {}
        self.vectorizer = None
        self.knowledge_embeddings = None
        
        # Configuration
        self.max_knowledge_items = 50000
        self.similarity_threshold = 0.6
        self.importance_decay_days = 90
        self.supported_formats = {'.txt', '.md', '.pdf', '.json', '.py', '.js', '.html', '.xml'}
        
        # Initialize components
        self._initialize_database()
        self._load_vectorizer()
        self._load_knowledge_items()
        
        logger.info(f"📚 Knowledge System initialized at {self.knowledge_dir}")

    def _initialize_database(self):
        """Initialize SQLite database for knowledge storage"""
        with sqlite3.connect(self.db_path) as conn:
            # Knowledge items table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_items (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    content TEXT,
                    source TEXT,
                    source_type TEXT,
                    tags TEXT,
                    importance_score REAL,
                    confidence_score REAL,
                    created_at TEXT,
                    last_accessed TEXT,
                    access_count INTEGER,
                    related_items TEXT,
                    metadata TEXT
                )
            """)
            
            # Knowledge gaps table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_gaps (
                    id TEXT PRIMARY KEY,
                    description TEXT,
                    context TEXT,
                    priority TEXT,
                    suggested_sources TEXT,
                    related_failures TEXT,
                    created_at TEXT,
                    status TEXT
                )
            """)
            
            # Improvement proposals table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS improvement_proposals (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    description TEXT,
                    category TEXT,
                    impact_score REAL,
                    effort_score REAL,
                    priority_score REAL,
                    supporting_evidence TEXT,
                    implementation_steps TEXT,
                    created_at TEXT,
                    status TEXT
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_source_type ON knowledge_items(source_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_importance ON knowledge_items(importance_score)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_gap_priority ON knowledge_gaps(priority)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_proposal_priority ON improvement_proposals(priority_score)")

    def _load_vectorizer(self):
        """Load or create vectorizer for knowledge embeddings"""
        if self.vectorizer_path.exists():
            with open(self.vectorizer_path, 'rb') as f:
                self.vectorizer = pickle.load(f)
            
            if self.embeddings_path.exists():
                self.knowledge_embeddings = np.load(self.embeddings_path)
        else:
            self.vectorizer = TfidfVectorizer(
                max_features=5000,
                stop_words='english',
                ngram_range=(1, 3),
                min_df=2,
                max_df=0.8
            )

    def _save_vectorizer(self):
        """Save vectorizer and embeddings"""
        if self.vectorizer:
            with open(self.vectorizer_path, 'wb') as f:
                pickle.dump(self.vectorizer, f)
        
        if self.knowledge_embeddings is not None:
            np.save(self.embeddings_path, self.knowledge_embeddings)

    def _load_knowledge_items(self):
        """Load knowledge items from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM knowledge_items")
            for row in cursor.fetchall():
                item = KnowledgeItem(
                    id=row[0],
                    title=row[1],
                    content=row[2],
                    source=row[3],
                    source_type=row[4],
                    tags=json.loads(row[5]),
                    importance_score=row[6],
                    confidence_score=row[7],
                    created_at=datetime.fromisoformat(row[8]),
                    last_accessed=datetime.fromisoformat(row[9]),
                    access_count=row[10],
                    related_items=json.loads(row[11]),
                    metadata=json.loads(row[12])
                )
                self.knowledge_items[item.id] = item

    async def ingest_knowledge(self, source: str, content: str = None) -> Dict[str, Any]:
        """
        Ingest knowledge from various sources
        """
        try:
            source_type = self._determine_source_type(source)
            
            if source_type == 'url':
                return await self._ingest_from_url(source)
            elif source_type == 'file':
                return await self._ingest_from_file(source, content)
            elif source_type == 'text':
                return await self._ingest_from_text(source, content)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported source type: {source_type}'
                }
                
        except Exception as e:
            logger.error(f"Failed to ingest knowledge from {source}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _determine_source_type(self, source: str) -> str:
        """Determine the type of knowledge source"""
        if source.startswith(('http://', 'https://')):
            return 'url'
        elif os.path.exists(source):
            return 'file'
        else:
            return 'text'

    async def _ingest_from_url(self, url: str) -> Dict[str, Any]:
        """Ingest knowledge from a URL"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '').lower()
            content = response.text
            
            # Extract title from HTML if possible
            title = self._extract_title_from_html(content) if 'html' in content_type else url
            
            # Process content
            processed_content = self._process_content(content, content_type)
            
            # Create knowledge item
            item_id = await self._create_knowledge_item(
                title=title,
                content=processed_content,
                source=url,
                source_type='url',
                metadata={'content_type': content_type, 'url': url}
            )
            
            return {
                'success': True,
                'message': f'Successfully ingested knowledge from URL: {url}',
                'item_id': item_id,
                'items_processed': 1
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to ingest from URL {url}: {str(e)}'
            }

    async def _ingest_from_file(self, file_path: str, content: str = None) -> Dict[str, Any]:
        """Ingest knowledge from a file"""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return {
                    'success': False,
                    'error': f'File not found: {file_path}'
                }
            
            # Check file extension
            if file_path.suffix.lower() not in self.supported_formats:
                return {
                    'success': False,
                    'error': f'Unsupported file format: {file_path.suffix}'
                }
            
            # Read content if not provided
            if content is None:
                if file_path.suffix.lower() == '.pdf':
                    content = await self._extract_pdf_content(file_path)
                else:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
            
            # Process content
            processed_content = self._process_content(content, file_path.suffix)
            
            # Create knowledge item
            item_id = await self._create_knowledge_item(
                title=file_path.stem,
                content=processed_content,
                source=str(file_path),
                source_type='document',
                metadata={
                    'file_path': str(file_path),
                    'file_size': file_path.stat().st_size,
                    'file_extension': file_path.suffix
                }
            )
            
            return {
                'success': True,
                'message': f'Successfully ingested knowledge from file: {file_path.name}',
                'item_id': item_id,
                'items_processed': 1
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to ingest from file {file_path}: {str(e)}'
            }

    async def _ingest_from_text(self, title: str, content: str) -> Dict[str, Any]:
        """Ingest knowledge from raw text"""
        try:
            if not content:
                return {
                    'success': False,
                    'error': 'No content provided'
                }
            
            # Process content
            processed_content = self._process_content(content, 'text')
            
            # Create knowledge item
            item_id = await self._create_knowledge_item(
                title=title,
                content=processed_content,
                source='manual_input',
                source_type='manual',
                metadata={'input_method': 'text'}
            )
            
            return {
                'success': True,
                'message': f'Successfully ingested knowledge: {title}',
                'item_id': item_id,
                'items_processed': 1
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to ingest text content: {str(e)}'
            }

    def _extract_title_from_html(self, html_content: str) -> str:
        """Extract title from HTML content"""
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
        if title_match:
            return title_match.group(1).strip()
        
        # Try h1 tag
        h1_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html_content, re.IGNORECASE)
        if h1_match:
            return h1_match.group(1).strip()
        
        return "Untitled Document"

    def _process_content(self, content: str, content_type: str) -> str:
        """Process and clean content"""
        # Remove HTML tags if present
        if 'html' in content_type.lower() or '<' in content:
            content = re.sub(r'<[^>]+>', ' ', content)
        
        # Clean up whitespace
        content = re.sub(r'\s+', ' ', content).strip()
        
        # Limit content length
        max_length = 50000  # 50KB limit
        if len(content) > max_length:
            content = content[:max_length] + "... [truncated]"
        
        return content

    async def _extract_pdf_content(self, file_path: Path) -> str:
        """Extract text content from PDF (placeholder - would need PyPDF2 or similar)"""
        # TODO: Implement PDF extraction
        # For now, return a placeholder
        return f"PDF content extraction not implemented for {file_path.name}"

    async def _create_knowledge_item(self,
                                   title: str,
                                   content: str,
                                   source: str,
                                   source_type: str,
                                   metadata: Dict[str, Any] = None) -> str:
        """Create a new knowledge item"""
        # Generate ID
        item_id = hashlib.md5(f"{title}_{source}_{datetime.now().isoformat()}".encode()).hexdigest()
        
        # Extract tags from content
        tags = self._extract_tags(content, title)
        
        # Calculate importance and confidence scores
        importance_score = self._calculate_importance_score(content, tags)
        confidence_score = self._calculate_confidence_score(source_type, content)
        
        # Create knowledge item
        item = KnowledgeItem(
            id=item_id,
            title=title,
            content=content,
            source=source,
            source_type=source_type,
            tags=tags,
            importance_score=importance_score,
            confidence_score=confidence_score,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            access_count=0,
            related_items=[],
            metadata=metadata or {}
        )
        
        # Store in database
        await self._store_knowledge_item(item)
        
        # Update embeddings
        await self._update_knowledge_embeddings()
        
        # Find related items
        await self._find_related_items(item_id)
        
        logger.info(f"📚 Created knowledge item: {item_id} - {title}")
        return item_id

    def _extract_tags(self, content: str, title: str) -> List[str]:
        """Extract tags from content and title"""
        tags = set()
        
        # Technical terms
        tech_terms = [
            'python', 'javascript', 'docker', 'git', 'api', 'database', 'sql',
            'machine learning', 'ai', 'algorithm', 'data', 'web', 'server',
            'client', 'framework', 'library', 'testing', 'debugging', 'deployment'
        ]
        
        content_lower = content.lower()
        title_lower = title.lower()
        
        for term in tech_terms:
            if term in content_lower or term in title_lower:
                tags.add(term.replace(' ', '_'))
        
        # Extract programming languages
        languages = ['python', 'javascript', 'java', 'c++', 'c#', 'go', 'rust', 'php']
        for lang in languages:
            if lang in content_lower:
                tags.add(f'lang_{lang}')
        
        # Extract common patterns
        if 'error' in content_lower or 'exception' in content_lower:
            tags.add('error_handling')
        
        if 'test' in content_lower:
            tags.add('testing')
        
        if 'deploy' in content_lower:
            tags.add('deployment')
        
        if 'config' in content_lower:
            tags.add('configuration')
        
        return list(tags)

    def _calculate_importance_score(self, content: str, tags: List[str]) -> float:
        """Calculate importance score based on content and tags"""
        base_score = 0.5
        
        # Length bonus (longer content is potentially more valuable)
        length_bonus = min(0.3, len(content) / 10000)
        
        # Tag bonus (more tags indicate broader relevance)
        tag_bonus = min(0.2, len(tags) * 0.05)
        
        # Technical content bonus
        tech_keywords = ['algorithm', 'implementation', 'solution', 'best practice', 'tutorial']
        tech_bonus = sum(0.05 for keyword in tech_keywords if keyword in content.lower())
        tech_bonus = min(0.2, tech_bonus)
        
        return min(1.0, base_score + length_bonus + tag_bonus + tech_bonus)

    def _calculate_confidence_score(self, source_type: str, content: str) -> float:
        """Calculate confidence score based on source and content quality"""
        base_scores = {
            'document': 0.8,
            'url': 0.6,
            'manual': 0.7,
            'code': 0.9
        }
        
        base_score = base_scores.get(source_type, 0.5)
        
        # Content quality indicators
        quality_bonus = 0.0
        
        if len(content) > 1000:  # Substantial content
            quality_bonus += 0.1
        
        if any(word in content.lower() for word in ['example', 'tutorial', 'guide']):
            quality_bonus += 0.1
        
        if content.count('\n') > 10:  # Well-structured content
            quality_bonus += 0.05
        
        return min(1.0, base_score + quality_bonus)

    async def _store_knowledge_item(self, item: KnowledgeItem):
        """Store knowledge item in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO knowledge_items
                (id, title, content, source, source_type, tags, importance_score,
                 confidence_score, created_at, last_accessed, access_count,
                 related_items, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.id,
                item.title,
                item.content,
                item.source,
                item.source_type,
                json.dumps(item.tags),
                item.importance_score,
                item.confidence_score,
                item.created_at.isoformat(),
                item.last_accessed.isoformat(),
                item.access_count,
                json.dumps(item.related_items),
                json.dumps(item.metadata)
            ))
        
        self.knowledge_items[item.id] = item

    async def _update_knowledge_embeddings(self):
        """Update TF-IDF embeddings for knowledge items"""
        if not self.knowledge_items:
            return
        
        # Prepare texts for vectorization
        texts = []
        item_ids = []
        
        for item_id, item in self.knowledge_items.items():
            text = f"{item.title} {item.content} {' '.join(item.tags)}"
            texts.append(text)
            item_ids.append(item_id)
        
        # Fit or update vectorizer
        if self.knowledge_embeddings is None:
            self.knowledge_embeddings = self.vectorizer.fit_transform(texts).toarray()
        else:
            # Add new embedding for the latest item
            new_text = texts[-1]
            new_embedding = self.vectorizer.transform([new_text]).toarray()
            self.knowledge_embeddings = np.vstack([self.knowledge_embeddings, new_embedding])
        
        # Save updated vectorizer and embeddings
        self._save_vectorizer()

    async def _find_related_items(self, item_id: str):
        """Find and update related items for a knowledge item"""
        if item_id not in self.knowledge_items or self.knowledge_embeddings is None:
            return
        
        item = self.knowledge_items[item_id]
        item_index = list(self.knowledge_items.keys()).index(item_id)
        
        # Calculate similarities
        item_embedding = self.knowledge_embeddings[item_index:item_index+1]
        similarities = cosine_similarity(item_embedding, self.knowledge_embeddings)[0]
        
        # Find most similar items
        similar_indices = np.argsort(similarities)[::-1][1:6]  # Top 5, excluding self
        
        related_items = []
        for idx in similar_indices:
            if similarities[idx] > self.similarity_threshold:
                related_item_id = list(self.knowledge_items.keys())[idx]
                related_items.append(related_item_id)
        
        # Update related items
        item.related_items = related_items
        await self._store_knowledge_item(item)

    async def search_knowledge(self,
                             query: str,
                             limit: int = 10,
                             min_importance: float = 0.0,
                             tags: List[str] = None) -> List[KnowledgeItem]:
        """Search knowledge items by query"""
        if not self.knowledge_items or self.knowledge_embeddings is None:
            return []
        
        # Create query embedding
        query_embedding = self.vectorizer.transform([query]).toarray()
        
        # Calculate similarities
        similarities = cosine_similarity(query_embedding, self.knowledge_embeddings)[0]
        
        # Get top similar items
        similar_indices = np.argsort(similarities)[::-1]
        
        results = []
        for idx in similar_indices:
            if len(results) >= limit:
                break
            
            if similarities[idx] < self.similarity_threshold:
                break
            
            item_id = list(self.knowledge_items.keys())[idx]
            item = self.knowledge_items[item_id]
            
            # Apply filters
            if item.importance_score < min_importance:
                continue
            
            if tags and not any(tag in item.tags for tag in tags):
                continue
            
            # Update access statistics
            item.last_accessed = datetime.now()
            item.access_count += 1
            await self._store_knowledge_item(item)
            
            results.append(item)
        
        logger.info(f"🔍 Found {len(results)} knowledge items for query: {query}")
        return results

    async def identify_knowledge_gaps(self, context: Dict[str, Any]) -> List[KnowledgeGap]:
        """Identify knowledge gaps based on context"""
        gaps = []
        
        # Analyze failed tasks or errors
        if 'failures' in context:
            for failure in context['failures']:
                gap = await self._analyze_failure_for_gaps(failure)
                if gap:
                    gaps.append(gap)
        
        # Analyze missing knowledge areas
        if 'query' in context:
            query = context['query']
            search_results = await self.search_knowledge(query, limit=3)
            
            if len(search_results) < 2:  # Few relevant results indicate a gap
                gap_id = hashlib.md5(f"gap_{query}_{datetime.now().isoformat()}".encode()).hexdigest()
                gap = KnowledgeGap(
                    id=gap_id,
                    description=f"Limited knowledge about: {query}",
                    context=context,
                    priority='medium',
                    suggested_sources=[
                        f"Search for documentation about {query}",
                        f"Look for tutorials on {query}",
                        f"Find examples of {query} implementation"
                    ],
                    related_failures=[],
                    created_at=datetime.now(),
                    status='open'
                )
                gaps.append(gap)
        
        # Store identified gaps
        for gap in gaps:
            await self._store_knowledge_gap(gap)
        
        return gaps

    async def _analyze_failure_for_gaps(self, failure: Dict[str, Any]) -> Optional[KnowledgeGap]:
        """Analyze a failure to identify knowledge gaps"""
        error_message = failure.get('error', '')
        task_type = failure.get('task_type', 'unknown')
        
        # Check if we have knowledge about this type of error
        search_query = f"{task_type} {error_message}"
        existing_knowledge = await self.search_knowledge(search_query, limit=2)
        
        if len(existing_knowledge) < 1:
            gap_id = hashlib.md5(f"gap_{search_query}_{datetime.now().isoformat()}".encode()).hexdigest()
            
            return KnowledgeGap(
                id=gap_id,
                description=f"Knowledge gap for {task_type} error: {error_message[:100]}",
                context={'failure': failure},
                priority='high' if 'critical' in error_message.lower() else 'medium',
                suggested_sources=[
                    f"Documentation for {task_type} error handling",
                    f"Stack Overflow solutions for: {error_message[:50]}",
                    f"Best practices for {task_type}"
                ],
                related_failures=[failure.get('id', '')],
                created_at=datetime.now(),
                status='open'
            )
        
        return None

    async def _store_knowledge_gap(self, gap: KnowledgeGap):
        """Store knowledge gap in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO knowledge_gaps
                (id, description, context, priority, suggested_sources,
                 related_failures, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                gap.id,
                gap.description,
                json.dumps(gap.context),
                gap.priority,
                json.dumps(gap.suggested_sources),
                json.dumps(gap.related_failures),
                gap.created_at.isoformat(),
                gap.status
            ))
        
        self.knowledge_gaps[gap.id] = gap

    async def generate_improvement_proposals(self, analysis_context: Dict[str, Any]) -> List[ImprovementProposal]:
        """Generate improvement proposals based on analysis"""
        proposals = []
        
        # Analyze performance patterns
        if 'performance_data' in analysis_context:
            performance_proposals = await self._generate_performance_proposals(
                analysis_context['performance_data']
            )
            proposals.extend(performance_proposals)
        
        # Analyze knowledge gaps
        if 'knowledge_gaps' in analysis_context:
            knowledge_proposals = await self._generate_knowledge_proposals(
                analysis_context['knowledge_gaps']
            )
            proposals.extend(knowledge_proposals)
        
        # Store proposals
        for proposal in proposals:
            await self._store_improvement_proposal(proposal)
        
        return proposals

    async def _generate_performance_proposals(self, performance_data: Dict[str, Any]) -> List[ImprovementProposal]:
        """Generate proposals based on performance analysis"""
        proposals = []
        
        # Low success rate areas
        for task_type, metrics in performance_data.get('by_task_type', {}).items():
            success_rate = metrics.get('success_rate', 1.0)
            
            if success_rate < 0.7:
                proposal_id = hashlib.md5(f"perf_{task_type}_{datetime.now().isoformat()}".encode()).hexdigest()
                
                proposal = ImprovementProposal(
                    id=proposal_id,
                    title=f"Improve {task_type} Success Rate",
                    description=f"Current success rate for {task_type} is {success_rate:.1%}. Need to identify and address common failure patterns.",
                    category='process',
                    impact_score=0.8,
                    effort_score=0.6,
                    priority_score=0.8 * (1 - success_rate),
                    supporting_evidence=[
                        f"Success rate: {success_rate:.1%}",
                        f"Total events: {metrics.get('total_events', 0)}"
                    ],
                    implementation_steps=[
                        f"Analyze common failure patterns for {task_type}",
                        "Develop targeted solutions for top failure modes",
                        "Implement improved error handling",
                        "Add specific knowledge for common issues"
                    ],
                    created_at=datetime.now(),
                    status='proposed'
                )
                
                proposals.append(proposal)
        
        return proposals

    async def _generate_knowledge_proposals(self, knowledge_gaps: List[KnowledgeGap]) -> List[ImprovementProposal]:
        """Generate proposals based on knowledge gaps"""
        proposals = []
        
        # High priority gaps
        high_priority_gaps = [gap for gap in knowledge_gaps if gap.priority == 'high']
        
        if high_priority_gaps:
            proposal_id = hashlib.md5(f"knowledge_{datetime.now().isoformat()}".encode()).hexdigest()
            
            proposal = ImprovementProposal(
                id=proposal_id,
                title="Address High Priority Knowledge Gaps",
                description=f"There are {len(high_priority_gaps)} high priority knowledge gaps that need attention.",
                category='knowledge',
                impact_score=0.9,
                effort_score=0.7,
                priority_score=0.9,
                supporting_evidence=[gap.description for gap in high_priority_gaps[:3]],
                implementation_steps=[
                    "Prioritize knowledge gaps by impact",
                    "Research and gather information for top gaps",
                    "Create knowledge items for critical areas",
                    "Validate knowledge through testing"
                ],
                created_at=datetime.now(),
                status='proposed'
            )
            
            proposals.append(proposal)
        
        return proposals

    async def _store_improvement_proposal(self, proposal: ImprovementProposal):
        """Store improvement proposal in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO improvement_proposals
                (id, title, description, category, impact_score, effort_score,
                 priority_score, supporting_evidence, implementation_steps,
                 created_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                proposal.id,
                proposal.title,
                proposal.description,
                proposal.category,
                proposal.impact_score,
                proposal.effort_score,
                proposal.priority_score,
                json.dumps(proposal.supporting_evidence),
                json.dumps(proposal.implementation_steps),
                proposal.created_at.isoformat(),
                proposal.status
            ))
        
        self.improvement_proposals[proposal.id] = proposal

    async def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get knowledge system statistics"""
        with sqlite3.connect(self.db_path) as conn:
            # Knowledge items stats
            items_cursor = conn.execute("SELECT COUNT(*) FROM knowledge_items")
            total_items = items_cursor.fetchone()[0]
            
            # Source type distribution
            source_cursor = conn.execute("""
                SELECT source_type, COUNT(*) 
                FROM knowledge_items 
                GROUP BY source_type
            """)
            source_distribution = dict(source_cursor.fetchall())
            
            # Knowledge gaps stats
            gaps_cursor = conn.execute("SELECT COUNT(*) FROM knowledge_gaps WHERE status = 'open'")
            open_gaps = gaps_cursor.fetchone()[0]
            
            # Improvement proposals stats
            proposals_cursor = conn.execute("SELECT COUNT(*) FROM improvement_proposals WHERE status = 'proposed'")
            pending_proposals = proposals_cursor.fetchone()[0]
            
            # Recent activity
            recent_cursor = conn.execute("""
                SELECT COUNT(*) FROM knowledge_items 
                WHERE created_at > ?
            """, [(datetime.now() - timedelta(days=7)).isoformat()])
            recent_items = recent_cursor.fetchone()[0]
        
        # Calculate average importance
        avg_importance = 0.0
        if self.knowledge_items:
            avg_importance = sum(item.importance_score for item in self.knowledge_items.values()) / len(self.knowledge_items)
        
        return {
            'total_knowledge_items': total_items,
            'source_distribution': source_distribution,
            'open_knowledge_gaps': open_gaps,
            'pending_proposals': pending_proposals,
            'recent_items_added': recent_items,
            'average_importance_score': avg_importance,
            'knowledge_size_mb': self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0,
            'last_updated': datetime.now().isoformat()
        }

# TODO: Implement additional features
# - Advanced PDF and document parsing
# - Integration with external knowledge bases (Wikipedia, Stack Overflow)
# - Automated knowledge validation and verification
# - Knowledge graph construction and visualization
# - Collaborative knowledge building with multiple AI agents
# - Real-time knowledge updates from code repositories
