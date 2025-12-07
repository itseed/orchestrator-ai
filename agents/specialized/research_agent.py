"""
Research Agent
Agent for researching information from various sources
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from monitoring import get_logger
from agents.base import BaseAgent
from config.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()


class ResearchAgent(BaseAgent):
    """Agent for researching information from various sources"""
    
    def __init__(self):
        """Initialize research agent"""
        super().__init__(
            agent_id="research_agent",
            name="Research Agent",
            capabilities=["web_search", "information_aggregation", "citation"],
            description="Researches information from web and aggregates sources"
        )
        self.openai_api_key = settings.OPENAI_API_KEY
        logger.info("ResearchAgent initialized")
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute research task
        
        Task format:
        {
            "query": "What are the latest trends in AI?",
            "sources": ["web", "academic"],  # Optional
            "max_results": 10,
            "include_citations": true
        }
        """
        try:
            query = task.get("query")
            if not query:
                raise ValueError("query is required")
            
            sources = task.get("sources", ["web"])
            max_results = task.get("max_results", 10)
            include_citations = task.get("include_citations", True)
            
            logger.info(
                "Research started",
                query=query,
                sources=sources,
                max_results=max_results
            )
            
            # Perform research
            results = []
            
            if "web" in sources:
                web_results = await self._web_search(query, max_results)
                results.extend(web_results)
            
            if "academic" in sources:
                academic_results = await self._academic_search(query, max_results)
                results.extend(academic_results)
            
            # Aggregate and summarize
            summary = await self._summarize_results(query, results)
            
            response = {
                "status": "success",
                "query": query,
                "summary": summary,
                "results_count": len(results),
                "results": results[:max_results]
            }
            
            if include_citations:
                response["citations"] = self._extract_citations(results)
            
            return response
        
        except Exception as e:
            logger.error("Research failed", error=str(e), exc_info=True)
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _web_search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Perform web search
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of search results
        """
        # Simplified web search implementation
        # In production, integrate with search APIs (Google, Bing, etc.)
        
        logger.info("Web search performed", query=query)
        
        # Mock results for demonstration
        # In production, use actual search API
        results = [
            {
                "title": f"Result {i} for: {query}",
                "url": f"https://example.com/result-{i}",
                "snippet": f"This is a snippet about {query} from result {i}.",
                "source": "web",
                "timestamp": datetime.utcnow().isoformat()
            }
            for i in range(min(max_results, 5))
        ]
        
        return results
    
    async def _academic_search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Perform academic search
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of academic results
        """
        # Simplified academic search
        # In production, integrate with academic databases
        
        logger.info("Academic search performed", query=query)
        
        results = [
            {
                "title": f"Academic Paper {i}: {query}",
                "authors": [f"Author {i}-1", f"Author {i}-2"],
                "journal": f"Journal {i}",
                "year": 2024 - i,
                "url": f"https://academic.example.com/paper-{i}",
                "source": "academic",
                "timestamp": datetime.utcnow().isoformat()
            }
            for i in range(min(max_results, 3))
        ]
        
        return results
    
    async def _summarize_results(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> str:
        """
        Summarize research results
        
        Args:
            query: Original query
            results: List of research results
            
        Returns:
            Summary text
        """
        if not results:
            return f"No results found for query: {query}"
        
        # Use LLM to summarize if available
        if self.openai_api_key:
            try:
                import openai
                client = openai.OpenAI(api_key=self.openai_api_key)
                
                results_text = "\n\n".join([
                    f"Title: {r.get('title', 'N/A')}\nSnippet: {r.get('snippet', r.get('abstract', 'N/A'))}"
                    for r in results[:5]
                ])
                
                prompt = f"""Summarize the following research results for the query: "{query}"

Results:
{results_text}

Provide a comprehensive summary."""
                
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a research assistant that summarizes information."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.5
                )
                
                return response.choices[0].message.content
            except Exception as e:
                logger.warning("OpenAI API call failed, using fallback", error=str(e))
        
        # Fallback: Simple summary
        return f"Found {len(results)} results for query: {query}. Key topics include: {', '.join([r.get('title', '')[:50] for r in results[:3]])}"
    
    def _extract_citations(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract citations from results
        
        Args:
            results: List of research results
            
        Returns:
            List of citations
        """
        citations = []
        
        for result in results:
            citation = {
                "title": result.get("title", "N/A"),
                "url": result.get("url", ""),
                "source": result.get("source", "unknown"),
                "timestamp": result.get("timestamp", datetime.utcnow().isoformat())
            }
            
            if result.get("authors"):
                citation["authors"] = result["authors"]
            
            if result.get("journal"):
                citation["journal"] = result["journal"]
            
            if result.get("year"):
                citation["year"] = result["year"]
            
            citations.append(citation)
        
        return citations
