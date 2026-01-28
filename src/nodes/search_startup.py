from ..state import GraphState, SerpAPIResults, RawGatheringData
from ..tools.serp_search import SerpAPISearch
from ..tools.tavily_search import TavilySearch
from ..config import Config
import json


async def search_startup_node(state: GraphState) -> dict:
    """
    Node 3: Search for startup information using Tavily Deep Research with SerpAPI Fallback
    
    This node:
    1. Reads startup name and industry from state.startup_data
    2. Attempts Tavily Deep Research first
    3. If Tavily fails or is skipped, falls back to SerpAPI
    4. Updates raw_gathering_data with results
    5. Returns updated state
    """
    
    try:
        print("\n" + "="*60)
        print("🔍 NODE 3: DEEP RESEARCH (TAVILY + SERP)")
        print("="*60)
        
        # Step 1: Get startup information
        startup_name = state.startup_data.name
        industry = state.startup_data.industry or ""
        legal_name = state.startup_data.legal_name or ""
        website = state.startup_data.website or ""
        
        if not startup_name:
            print("⚠️ No startup name provided")
            print("Status: Skipping search\n")
            return {
                "status": "no_startup_name",
                "raw_gathering_data": state.raw_gathering_data or RawGatheringData()
            }
        
        print(f"✓ Startup name: {startup_name}")
        print(f"✓ Industry: {industry}")
        
        raw_gathering_data = state.raw_gathering_data or RawGatheringData()
        
        # Step 2: Try Tavily Deep Research
        tavily_success = False
        if Config.TAVILY_API_KEY:
            print(f"\n  🚀 Attempting Tavily Deep Research...")
            tavily_tool = TavilySearch()
            
            # Construct a comprehensive query
            research_query = f"""
            Analyze the startup "{startup_name}" (Legal Name: "{legal_name}") in the {industry} industry. 
            Website: {website}
            Find detailed information about:
            1. Founders and their backgrounds
            2. Business model, pricing, and revenue streams
            3. Funding history, investors, and amount raised
            4. Market size, target audience, and competitors
            5. Traction, customer reviews, and news
            """
            
            tavily_result = await tavily_tool.run_deep_research(research_query.strip())
            
            if tavily_result["success"]:
                print("  ✓ Tavily Research Successful!")
                tavily_success = True
                
                # Store results
                raw_gathering_data.tavily_report = tavily_result["report"]
                raw_gathering_data.tavily_data = tavily_result.get("data", {})
                
                print(f"  ✓ Report gathered ({len(tavily_result['report'])} chars)")
                print(f"  ✓ Sources: {len(tavily_result.get('sources', []))}")
                
            else:
                print(f"  ⚠️ Tavily Research Failed: {tavily_result.get('error')}")
                print("  falling back to SerpAPI...")
        else:
             print("  ⚠️ No TAVILY_API_KEY found, skipping to SerpAPI...")

        # Step 3: Fallback to SerpAPI if Tavily failed
        if not tavily_success:
            print(f"\n  🔄 Falling back to SerpAPI...")
            search_tool = SerpAPISearch()
            
            search_results = await search_tool.search_startup(
                startup_name=startup_name,
                industry=industry
            )
            
            if search_results.get("success"):
                print("  ✓ SerpAPI Search Successful")
                
                # Organize results (reusing existing logic simplified)
                searches = search_results.get("searches", {})
                news = search_results.get("news", {})
                
                organized_results = {
                    "company_info": searches.get("company_search", {}).get("results", [])[:3],
                    "funding_info": searches.get("funding_search", {}).get("results", [])[:3],
                    "product_info": searches.get("product_search", {}).get("results", [])[:3],
                    "team_info": searches.get("team_search", {}).get("results", [])[:3],
                    "news_articles": news.get("results", [])[:5],
                    "founder_backgrounds": searches.get("founder_backgrounds_search", {}).get("results", [])[:3]
                    # ... add other fields if needed, simplified for fallback
                }
                
                serp_api_results = SerpAPIResults(
                    search_query=startup_name,
                    search_results=organized_results,
                    news_articles=organized_results.get("news_articles", [])
                )
                
                raw_gathering_data.search_results = serp_api_results
                print("  ✓ Search results added to raw_gathering_data")
                
            else:
                print(f"  ❌ SerpAPI Search Failed: {search_results.get('error')}")
                # We return even if both fail, with whatever data we have
        
        print("\n✅ Node 3 Complete")
        print("="*60 + "\n")
        
        return {
            "status": "search_completed",
            "raw_gathering_data": raw_gathering_data
        }
    
    except Exception as e:
        print(f"\n❌ ERROR in Node 3: {str(e)}")
        # import traceback
        # traceback.print_exc()
        return {
            "status": "error",
            "raw_gathering_data": state.raw_gathering_data or RawGatheringData(),
            "errors": [f"Deep Research error: {str(e)}"]
        }