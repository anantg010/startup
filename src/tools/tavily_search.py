import httpx
import asyncio
import json
from typing import Dict, List, Optional, Any
from ..config import Config

class TavilySearch:
    """
    Search for startup information using Tavily Deep Research
    Provides comprehensive research reports
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize Tavily search tool
        
        Args:
            api_key: API key (uses Config if not provided)
        """
        self.api_key = api_key or Config.TAVILY_API_KEY
        self.base_url = "https://api.tavily.com"
        self.timeout = 120  # Research takes time
        
        if not self.api_key:
            print("⚠️ Warning: TAVILY_API_KEY not found in config")

    async def create_research_task(self, query: str, model: str = "auto") -> Dict:
        """
        Initiate a research task (POST /research)
        """
        try:
            print(f"🚀 Initiating Tavily Research: {query}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/research",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "input": query,
                        "model": model,
                        "citation_format": "apa"
                    }
                )
                
                if response.status_code == 401:
                    return {"success": False, "error": "Unauthorized: Invalid API Key"}
                
                response.raise_for_status()
                return {"success": True, "data": response.json()}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_research_status(self, request_id: str) -> Dict:
        """
        Get research task status (GET /research/{id})
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/research/{request_id}",
                    headers={
                        "Authorization": f"Bearer {self.api_key}"
                    }
                )
                
                response.raise_for_status()
                return {"success": True, "data": response.json()}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def run_deep_research(self, query: str, poll_interval: int = 40) -> Dict:
        """
        Run deep research and wait for results (Polling)
        poll_interval: seconds to wait between checks (default 40s)
        """
        # 1. Start Research
        task = await self.create_research_task(query)
        if not task["success"]:
            return task
        
        request_id = task["data"].get("request_id")
        if not request_id:
            return {"success": False, "error": "No request_id returned"}
            
        print(f"  ✓ Task Started (ID: {request_id})")
        
        # 2. Poll for completion
        # User requested timeout increase to ~700s
        # 700s / 40s = 17.5 -> 18 retries (720s total)
        max_retries = 18  
        
        for i in range(max_retries):
            status_res = await self.get_research_status(request_id)
            if not status_res["success"]:
                print(f"  ⚠️ Polling error: {status_res['error']}")
                await asyncio.sleep(poll_interval)
                continue
                
            data = status_res["data"]
            status = data.get("status")
            
            if status == "completed":
                print(f"  ✓ Research Completed in {data.get('response_time', '?')}s")
                return {
                    "success": True,
                    "report": data.get("content", ""),
                    "sources": data.get("sources", []),
                    "data": data
                }
            
            elif status == "failed":
                return {"success": False, "error": "Research task failed on server side"}
            
            if i % 2 == 0:
                print(f"  ⏳ Research in progress... ({status})")
                
            await asyncio.sleep(poll_interval)
            
        return {"success": False, "error": "Research timed out"}