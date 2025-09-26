
#!/usr/bin/env python3
"""
Simple Knowledge Ingestion System
Processes PDFs to extract 3 key insights and integrates with MCP server
"""

import json
import requests
import PyPDF2
import re
from pathlib import Path
from datetime import datetime
import logging
from typing import List, Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleKnowledgeProcessor:
    def __init__(self, mcp_server_url="http://localhost:8084"):
        self.mcp_server_url = mcp_server_url
        self.knowledge_dir = Path("/workspace/knowledge")
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text content from PDF file"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
            return ""
    
    def extract_key_insights(self, text: str, max_insights: int = 3) -> List[Dict[str, Any]]:
        """Extract key insights from text using simple heuristics"""
        insights = []
        
        # Clean and prepare text
        text = re.sub(r'\s+', ' ', text).strip()
        sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 20]
        
        # Heuristic 1: Look for sentences with key indicator words
        key_indicators = [
            'important', 'critical', 'essential', 'key', 'significant',
            'conclusion', 'result', 'finding', 'discovery', 'insight',
            'recommend', 'suggest', 'propose', 'should', 'must',
            'therefore', 'thus', 'consequently', 'in summary'
        ]
        
        scored_sentences = []
        for sentence in sentences:
            score = 0
            sentence_lower = sentence.lower()
            
            # Score based on key indicators
            for indicator in key_indicators:
                if indicator in sentence_lower:
                    score += 2
            
            # Score based on sentence length (prefer medium length)
            if 50 <= len(sentence) <= 200:
                score += 1
            
            # Score based on presence of numbers/data
            if re.search(r'\d+%|\d+\.\d+|\$\d+', sentence):
                score += 1
            
            # Score based on capitalized words (potential proper nouns/concepts)
            caps_count = len(re.findall(r'\b[A-Z][a-z]+', sentence))
            if caps_count >= 2:
                score += 1
            
            if score > 0:
                scored_sentences.append((sentence, score))
        
        # Sort by score and take top insights
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        
        for i, (sentence, score) in enumerate(scored_sentences[:max_insights]):
            insights.append({
                "id": f"insight_{i+1}",
                "content": sentence,
                "confidence_score": score,
                "type": self._classify_insight_type(sentence),
                "extracted_at": datetime.now().isoformat()
            })
        
        # If we don't have enough insights, add some from the beginning and end
        if len(insights) < max_insights:
            remaining_needed = max_insights - len(insights)
            
            # Add first few meaningful sentences
            for sentence in sentences[:remaining_needed]:
                if len(sentence) > 30 and sentence not in [i["content"] for i in insights]:
                    insights.append({
                        "id": f"insight_{len(insights)+1}",
                        "content": sentence,
                        "confidence_score": 1,
                        "type": "contextual",
                        "extracted_at": datetime.now().isoformat()
                    })
                    if len(insights) >= max_insights:
                        break
        
        return insights[:max_insights]
    
    def _classify_insight_type(self, sentence: str) -> str:
        """Classify the type of insight based on content"""
        sentence_lower = sentence.lower()
        
        if any(word in sentence_lower for word in ['recommend', 'suggest', 'should', 'must', 'propose']):
            return "recommendation"
        elif any(word in sentence_lower for word in ['result', 'finding', 'discovered', 'found']):
            return "finding"
        elif any(word in sentence_lower for word in ['conclusion', 'summary', 'therefore', 'thus']):
            return "conclusion"
        elif any(word in sentence_lower for word in ['method', 'approach', 'technique', 'process']):
            return "methodology"
        else:
            return "general"
    
    def store_knowledge_locally(self, pdf_path: str, insights: List[Dict[str, Any]]) -> str:
        """Store extracted knowledge locally"""
        try:
            knowledge_entry = {
                "source_file": pdf_path,
                "processed_at": datetime.now().isoformat(),
                "insights_count": len(insights),
                "insights": insights,
                "metadata": {
                    "processor_version": "1.0",
                    "extraction_method": "simple_heuristic"
                }
            }
            
            # Generate filename
            pdf_name = Path(pdf_path).stem
            knowledge_file = self.knowledge_dir / f"knowledge_{pdf_name}_{int(datetime.now().timestamp())}.json"
            
            # Save to file
            with open(knowledge_file, 'w') as f:
                json.dump(knowledge_entry, f, indent=2)
            
            logger.info(f"Stored knowledge locally: {knowledge_file}")
            return str(knowledge_file)
            
        except Exception as e:
            logger.error(f"Error storing knowledge locally: {e}")
            return ""
    
    def send_to_mcp_server(self, insights: List[Dict[str, Any]], source_file: str) -> bool:
        """Send insights to MCP server"""
        try:
            for insight in insights:
                memory_data = {
                    "type": "knowledge_insight",
                    "content": insight["content"],
                    "context": {
                        "source_file": source_file,
                        "insight_type": insight["type"],
                        "confidence_score": insight["confidence_score"],
                        "insight_id": insight["id"]
                    },
                    "importance": min(insight["confidence_score"], 5)  # Cap at 5
                }
                
                response = requests.post(
                    f"{self.mcp_server_url}/memory",
                    json=memory_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    logger.info(f"Sent insight to MCP server: {insight['id']}")
                else:
                    logger.warning(f"Failed to send insight {insight['id']}: {response.status_code}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending to MCP server: {e}")
            return False
    
    def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Main method to process a PDF and extract insights"""
        logger.info(f"Processing PDF: {pdf_path}")
        
        # Extract text
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            return {"success": False, "error": "Failed to extract text from PDF"}
        
        # Extract insights
        insights = self.extract_key_insights(text)
        if not insights:
            return {"success": False, "error": "No insights could be extracted"}
        
        # Store locally
        local_file = self.store_knowledge_locally(pdf_path, insights)
        
        # Send to MCP server
        mcp_success = self.send_to_mcp_server(insights, pdf_path)
        
        result = {
            "success": True,
            "pdf_path": pdf_path,
            "insights_extracted": len(insights),
            "insights": insights,
            "local_storage": local_file,
            "mcp_integration": mcp_success,
            "processed_at": datetime.now().isoformat()
        }
        
        logger.info(f"PDF processing complete: {len(insights)} insights extracted")
        return result
    
    def get_stored_knowledge(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve stored knowledge entries"""
        try:
            knowledge_files = sorted(self.knowledge_dir.glob("*.json"), reverse=True)
            knowledge_entries = []
            
            for knowledge_file in knowledge_files[:limit]:
                try:
                    with open(knowledge_file, 'r') as f:
                        entry = json.load(f)
                        knowledge_entries.append(entry)
                except Exception as e:
                    logger.warning(f"Error reading knowledge file {knowledge_file}: {e}")
            
            return knowledge_entries
            
        except Exception as e:
            logger.error(f"Error retrieving stored knowledge: {e}")
            return []

def main():
    """Example usage"""
    processor = SimpleKnowledgeProcessor()
    
    # Example: Process a PDF file
    # pdf_path = "/path/to/your/document.pdf"
    # result = processor.process_pdf(pdf_path)
    # print(json.dumps(result, indent=2))
    
    print("Knowledge processor initialized. Use process_pdf(path) to process documents.")

if __name__ == "__main__":
    main()
