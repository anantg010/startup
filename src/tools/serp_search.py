import httpx
from typing import Dict, List, Optional
from ..config import Config


class SerpAPISearch:
    """
    Search for startup information using SerpAPI
    Provides Google search results, news, and company information
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize SerpAPI search tool
        
        Args:
            api_key: API key (uses Config based on provider if not provided)
        """
        self.provider = Config.SEARCH_API_PROVIDER
        
        if self.provider == "serpapi":
            self.api_key = api_key or Config.SERPAPI_API_KEY
            self.base_url = "https://serpapi.com/search"
            if not self.api_key:
                print("⚠️ Warning: SERPAPI_API_KEY not found in config")
        else:
            # Default to Serper
            self.api_key = api_key or Config.SERPER_API_KEY
            self.base_url = "https://google.serper.dev"
            if not self.api_key:
                print("⚠️ Warning: SERPER_API_KEY not found in config")
        
        self.timeout = 30

    
    
    async def search(self, query: str, num_results: int = 10) -> Dict:
        """
        Perform a general Google search
        
        Args:
            query: Search query (e.g., "TechCorp AI startup")
            num_results: Number of results to return (max 10-100)
            
        Returns:
            Dict with search results
            
        Example:
            results = await search_tool.search("TechCorp AI", num_results=10)
            print(results["results"])
        """
        try:
            print(f"🔍 Searching for: {query}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if self.provider == "serpapi":
                    # SerpApi Implementation (GET)
                    response = await client.get(
                        self.base_url,
                        params={
                            "api_key": self.api_key,
                            "q": query,
                            "num": num_results,
                            "engine": "google"
                        }
                    )
                else:
                    # Serper Implementation (POST)
                    response = await client.post(
                        f"{self.base_url}/search",
                        headers={
                            "X-API-KEY": self.api_key,
                            "Content-Type": "application/json"
                        },
                        json={
                            "q": query,
                            "num": num_results
                        }
                    )
                
                response.raise_for_status()
                data = response.json()
                
                if self.provider == "serpapi":
                    organic = data.get("organic_results", [])
                    # Normalize answer box if possible
                    answer_box = data.get("answer_box", {})
                    # SerpApi structure slightly different, mapping best effort
                    return {
                        "success": True,
                        "query": query,
                        "results": organic,
                        "answer_box": answer_box,
                        "knowledge_graph": data.get("knowledge_graph", {}),
                        "related_searches": data.get("related_searches", [])
                    }
                else:
                     # Serper structure
                    print(f"  ✓ Found {len(data.get('organic', []))} results")
                    return {
                        "success": True,
                        "query": query,
                        "results": data.get("organic", []),
                        "answer_box": data.get("answerBox", {}),
                        "knowledge_graph": data.get("knowledgeGraph", {}),
                        "related_searches": data.get("relatedSearches", [])
                    }
        
        except httpx.HTTPError as e:
            return {
                "success": False,
                "query": query,
                "error": f"HTTP Error: {str(e)}",
                "results": []
            }
        
        except Exception as e:
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "results": []
            }
    
    
    async def search_news(self, query: str, num_results: int = 10) -> Dict:
        """
        Search for news articles about a startup
        
        Args:
            query: Search query (e.g., "TechCorp funding")
            num_results: Number of news articles
            
        Returns:
            Dict with news results
            
        Example:
            news = await search_tool.search_news("TechCorp raises funding", num_results=5)
            for article in news["results"]:
                print(article["title"], article["link"])
        """
        try:
            print(f"📰 Searching for news: {query}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if self.provider == "serpapi":
                     response = await client.get(
                        self.base_url,
                        params={
                            "api_key": self.api_key,
                            "q": query,
                            "num": num_results,
                            "engine": "google",
                            "tbm": "nws"
                        }
                    )
                else:
                    response = await client.post(
                        f"{self.base_url}/news",
                        headers={
                            "X-API-KEY": self.api_key,
                            "Content-Type": "application/json"
                        },
                        json={
                            "q": query,
                            "num": num_results
                        }
                    )
                
                response.raise_for_status()
                data = response.json()
                
                if self.provider == "serpapi":
                    news_results = data.get("news_results", [])
                else:
                    news_results = data.get("news", [])
                    
                print(f"  ✓ Found {len(news_results)} news articles")
                
                return {
                    "success": True,
                    "query": query,
                    "results": news_results
                }
        
        except Exception as e:
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "results": []
            }
    
    
    async def search_startup(self, startup_name: str, industry: str = None) -> Dict:
        """
        Comprehensive search for startup information
        Performs multiple searches to gather complete info
        
        Args:
            startup_name: Name of the startup
            industry: Industry type (optional, makes search more specific)
            
        Returns:
            Dict with all search results
            
        Example:
            info = await search_tool.search_startup("TechCorp", "AI")
            print(info["company_search"])
            print(info["funding_search"])
            print(info["news"])
        """
        try:
            print(f"🔎 Comprehensive search for: {startup_name}")
            
            # Build search queries - expanded for deeper research
            queries = {
                "company_search": f"{startup_name} company",
                "funding_search": f"{startup_name} funding startup investment",
                "product_search": f"{startup_name} product features",
                "team_search": f"{startup_name} founders team CEO",
                "financials_search": f"{startup_name} revenue ARR MRR metrics",
                "reviews_search": f"{startup_name} customer reviews testimonials",
                "partnerships_search": f"{startup_name} partnerships collaborations",
                "crunchbase_search": f"{startup_name} crunchbase funding rounds investors",
                "linkedin_search": f"{startup_name} linkedin company employees",
                "founder_backgrounds_search": f"{startup_name} founder background education experience",
                "market_search": f"{startup_name} market size TAM industry"
            }
            
            if industry:
                queries["industry_search"] = f"{startup_name} {industry} startup market"

            
            # Perform all searches
            results = {
                "success": True,
                "startup_name": startup_name,
                "industry": industry,
                "searches": {}
            }
            
            for search_type, query in queries.items():
                search_result = await self.search(query, num_results=5)
                results["searches"][search_type] = search_result
            
            # Search for news
            news_result = await self.search_news(f"{startup_name} news", num_results=5)
            results["news"] = news_result
            
            print(f"  ✓ Comprehensive search completed")
            
            return results
        
        except Exception as e:
            return {
                "success": False,
                "startup_name": startup_name,
                "error": str(e),
                "searches": {}
            }
    
    
    async def search_company_info(self, startup_name: str) -> Dict:
        """
        Search for detailed company information
        
        Args:
            startup_name: Name of the startup
            
        Returns:
            Dict with company info
            
        Example:
            info = await search_tool.search_company_info("TechCorp")
            print(info["knowledge_graph"])
        """
        try:
            print(f"🏢 Searching company info: {startup_name}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/search",
                    headers={
                        "X-API-KEY": self.api_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "q": f"{startup_name} company information",
                        "num": 10
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                return {
                    "success": True,
                    "startup_name": startup_name,
                    "knowledge_graph": data.get("knowledgeGraph", {}),
                    "organic_results": data.get("organic", []),
                    "answer_box": data.get("answerBox", {})
                }
        
        except Exception as e:
            return {
                "success": False,
                "startup_name": startup_name,
                "error": str(e),
                "knowledge_graph": {}
            }
    
    
    async def search_competitors(self, startup_name: str, industry: str = None) -> Dict:
        """
        Search for competitor information
        
        Args:
            startup_name: Name of the startup
            industry: Industry type
            
        Returns:
            Dict with competitor information
            
        Example:
            competitors = await search_tool.search_competitors("TechCorp", "AI")
            print(competitors["results"])
        """
        try:
            print(f"⚔️ Searching for competitors of: {startup_name}")
            
            query = f"competitors of {startup_name}"
            if industry:
                query += f" {industry}"
            
            result = await self.search(query, num_results=10)
            
            return {
                "success": result["success"],
                "startup_name": startup_name,
                "competitors_search": result
            }
        
        except Exception as e:
            return {
                "success": False,
                "startup_name": startup_name,
                "error": str(e)
            }
    
    
    async def search_funding(self, startup_name: str) -> Dict:
        """
        Search for funding information
        
        Args:
            startup_name: Name of the startup
            
        Returns:
            Dict with funding information
            
        Example:
            funding = await search_tool.search_funding("TechCorp")
            print(funding["results"])
        """
        try:
            print(f"💰 Searching for funding info: {startup_name}")
            
            queries = {
                "funding_rounds": f"{startup_name} funding rounds",
                "series_funding": f"{startup_name} Series A Series B",
                "investors": f"{startup_name} investors",
                "vc_funding": f"{startup_name} venture capital"
            }
            
            results = {
                "success": True,
                "startup_name": startup_name,
                "searches": {}
            }
            
            for search_type, query in queries.items():
                search_result = await self.search(query, num_results=5)
                results["searches"][search_type] = search_result
            
            return results
        
        except Exception as e:
            return {
                "success": False,
                "startup_name": startup_name,
                "error": str(e),
                "searches": {}
            }
    
    
    async def search_leadership(self, startup_name: str) -> Dict:
        """
        Search for leadership/team information
        
        Args:
            startup_name: Name of the startup
            
        Returns:
            Dict with leadership information
            
        Example:
            team = await search_tool.search_leadership("TechCorp")
            print(team["results"])
        """
        try:
            print(f"👥 Searching for leadership: {startup_name}")
            
            queries = {
                "ceo": f"{startup_name} CEO founder",
                "team": f"{startup_name} team members",
                "leadership": f"{startup_name} leadership",
                "founders": f"{startup_name} founders background"
            }
            
            results = {
                "success": True,
                "startup_name": startup_name,
                "searches": {}
            }
            
            for search_type, query in queries.items():
                search_result = await self.search(query, num_results=5)
                results["searches"][search_type] = search_result
            
            return results
        
        except Exception as e:
            return {
                "success": False,
                "startup_name": startup_name,
                "error": str(e),
                "searches": {}
            }
    
    
    def parse_search_results(self, search_results: Dict) -> List[Dict]:
        """
        Parse and clean search results
        
        Args:
            search_results: Raw search results from search()
            
        Returns:
            List of cleaned results with title, link, snippet
            
        Example:
            raw = await search_tool.search("TechCorp")
            cleaned = search_tool.parse_search_results(raw)
            for item in cleaned:
                print(item["title"], "->", item["link"])
        """
        try:
            if not search_results.get("success"):
                return []
            
            parsed = []
            for item in search_results.get("results", []):
                parsed.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "position": item.get("position", 0)
                })
            
            return parsed
        
        except Exception as e:
            print(f"Error parsing results: {str(e)}")
            return []
    
    
    def extract_key_info(self, search_results: Dict) -> Dict:
        """
        Extract key information from search results
        
        Args:
            search_results: Raw search results
            
        Returns:
            Dict with extracted key information
            
        Example:
            raw = await search_tool.search("TechCorp")
            key_info = search_tool.extract_key_info(raw)
            print(key_info["answer"])
            print(key_info["top_links"])
        """
        try:
            key_info = {
                "answer": search_results.get("answer_box", {}).get("answer", ""),
                "knowledge_graph": search_results.get("knowledge_graph", {}),
                "top_results": [],
                "related_searches": search_results.get("related_searches", [])
            }
            
            # Get top 3 results
            for item in search_results.get("results", [])[:3]:
                key_info["top_results"].append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", "")
                })
            
            return key_info
        
        except Exception as e:
            print(f"Error extracting key info: {str(e)}")
            return {}