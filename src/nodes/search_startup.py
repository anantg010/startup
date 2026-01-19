from ..state import GraphState, SerpAPIResults, RawGatheringData
from ..tools.serp_search import SerpAPISearch
import json


async def search_startup_node(state: GraphState) -> dict:
    """
    Node 3: Search for startup information using SerpAPI
    
    This node:
    1. Reads startup name and industry from state.startup_data
    2. Performs comprehensive searches using SerpAPI
    3. Gathers company info, funding, news, and competitors
    4. Creates a SerpAPIResults object
    5. Updates raw_gathering_data with search results
    6. Returns updated state
    
    Args:
        state: Current GraphState with startup name and existing raw_gathering_data
        
    Returns:
        dict: Updated state with SerpAPIResults added to raw_gathering_data
        
    Example:
        result = await search_startup_node(state)
        print(result["status"])  # "search_completed"
    """
    
    try:
        print("\n" + "="*60)
        print("🔍 NODE 3: SEARCH STARTUP")
        print("="*60)
        
        # Step 1: Get startup information
        startup_name = state.startup_data.name
        industry = state.startup_data.industry
        
        if not startup_name:
            print("⚠️ No startup name provided")
            print("Status: Skipping search\n")
            
            raw_gathering_data = state.raw_gathering_data or RawGatheringData()
            
            return {
                "status": "no_startup_name",
                "raw_gathering_data": raw_gathering_data
            }
        
        print(f"✓ Startup name: {startup_name}")
        print(f"✓ Industry: {industry}")
        
        # Step 2: Create SerpAPISearch instance
        search_tool = SerpAPISearch()
        
        # Step 3: Perform comprehensive startup search
        print(f"\n  Performing comprehensive search...")
        search_results = await search_tool.search_startup(
            startup_name=startup_name,
            industry=industry
        )
        
        # Step 4: Check if search was successful
        if not search_results.get("success"):
            error_msg = search_results.get("error", "Unknown error")
            print(f"  ⚠️ Search failed: {error_msg}")
            print("Status: Continuing with other nodes\n")
            
            raw_gathering_data = state.raw_gathering_data or RawGatheringData()
            
            return {
                "status": "search_failed",
                "raw_gathering_data": raw_gathering_data,
                "errors": [f"Startup search failed: {error_msg}"]
            }
        
        print("  ✓ Comprehensive search completed")
        
        # Step 5: Extract and organize search results
        print("  Organizing search results...")
        
        searches = search_results.get("searches", {})
        news = search_results.get("news", {})
        
        # Count total results
        total_results = 0
        for search_type, search_data in searches.items():
            if search_data.get("success"):
                result_count = len(search_data.get("results", []))
                total_results += result_count
                print(f"    ✓ {search_type}: {result_count} results")
        
        news_count = len(news.get("results", []))
        total_results += news_count
        print(f"    ✓ News articles: {news_count} results")
        
        print(f"  ✓ Total results gathered: {total_results}")
        
        # Step 6: Extract top results from each search type
        print("  Extracting key information...")
        
        organized_results = {
            "company_info": [],
            "funding_info": [],
            "product_info": [],
            "team_info": [],
            "news_articles": [],
            "financials_info": [],      # Financial metrics and revenue data
            "customer_reviews": [],     # Customer testimonials and reviews
            "partnerships": [],         # Strategic partnerships
            "industry_analysis": [],    # Industry and market data
            "crunchbase_info": [],      # Crunchbase funding data
            "linkedin_info": [],        # LinkedIn company info
            "founder_backgrounds": []   # Detailed founder information
        }

        
        # Extract company search results
        company_search = searches.get("company_search", {})
        if company_search.get("success"):
            for result in company_search.get("results", [])[:3]:
                organized_results["company_info"].append({
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "snippet": result.get("snippet", "")
                })
        
        # Extract funding search results
        funding_search = searches.get("funding_search", {})
        if funding_search.get("success"):
            for result in funding_search.get("results", [])[:3]:
                organized_results["funding_info"].append({
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "snippet": result.get("snippet", "")
                })
        
        # Extract product search results
        product_search = searches.get("product_search", {})
        if product_search.get("success"):
            for result in product_search.get("results", [])[:3]:
                organized_results["product_info"].append({
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "snippet": result.get("snippet", "")
                })
        
        # Extract team search results
        team_search = searches.get("team_search", {})
        if team_search.get("success"):
            for result in team_search.get("results", [])[:3]:
                organized_results["team_info"].append({
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "snippet": result.get("snippet", "")
                })
        
        # Extract news articles
        if news.get("success"):
            for article in news.get("results", [])[:5]:
                organized_results["news_articles"].append({
                    "title": article.get("title", ""),
                    "link": article.get("link", ""),
                    "snippet": article.get("snippet", "")
                })
        
        # Extract financials search results
        financials_search = searches.get("financials_search", {})
        if financials_search.get("success"):
            for result in financials_search.get("results", [])[:3]:
                organized_results["financials_info"].append({
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "snippet": result.get("snippet", "")
                })
        
        # Extract customer reviews
        reviews_search = searches.get("reviews_search", {})
        if reviews_search.get("success"):
            for result in reviews_search.get("results", [])[:3]:
                organized_results["customer_reviews"].append({
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "snippet": result.get("snippet", "")
                })
        
        # Extract partnerships
        partnerships_search = searches.get("partnerships_search", {})
        if partnerships_search.get("success"):
            for result in partnerships_search.get("results", [])[:3]:
                organized_results["partnerships"].append({
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "snippet": result.get("snippet", "")
                })
        
        # Extract industry analysis
        market_search = searches.get("market_search", {})
        if market_search.get("success"):
            for result in market_search.get("results", [])[:3]:
                organized_results["industry_analysis"].append({
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "snippet": result.get("snippet", "")
                })
        
        # Extract crunchbase info
        crunchbase_search = searches.get("crunchbase_search", {})
        if crunchbase_search.get("success"):
            for result in crunchbase_search.get("results", [])[:3]:
                organized_results["crunchbase_info"].append({
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "snippet": result.get("snippet", "")
                })
        
        # Extract linkedin info
        linkedin_search = searches.get("linkedin_search", {})
        if linkedin_search.get("success"):
            for result in linkedin_search.get("results", [])[:3]:
                organized_results["linkedin_info"].append({
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "snippet": result.get("snippet", "")
                })
        
        # Extract founder backgrounds
        founder_search = searches.get("founder_backgrounds_search", {})
        if founder_search.get("success"):
            for result in founder_search.get("results", [])[:3]:
                organized_results["founder_backgrounds"].append({
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "snippet": result.get("snippet", "")
                })
        
        print("  ✓ Results organized into categories")
        
        # Step 7: Create SerpAPIResults object
        print("  Creating SerpAPIResults object...")
        serp_api_results = SerpAPIResults(
            search_query=startup_name,
            search_results=organized_results,
            news_articles=organized_results.get("news_articles", [])
        )
        print("  ✓ SerpAPIResults created")
        
        # Step 8: Update raw_gathering_data
        print("  Updating raw_gathering_data...")
        raw_gathering_data = state.raw_gathering_data or RawGatheringData()
        raw_gathering_data.search_results = serp_api_results
        print("  ✓ Search results added to raw_gathering_data")
        
        # Step 9: Log summary
        print("\n📊 SEARCH SUMMARY:")
        print(f"   - Startup searched: {startup_name}")
        print(f"   - Industry: {industry}")
        print(f"   - Company info results: {len(organized_results['company_info'])}")
        print(f"   - Funding info results: {len(organized_results['funding_info'])}")
        print(f"   - Product info results: {len(organized_results['product_info'])}")
        print(f"   - Team info results: {len(organized_results['team_info'])}")
        print(f"   - News articles: {len(organized_results['news_articles'])}")
        print(f"   - Financials info: {len(organized_results['financials_info'])}")
        print(f"   - Partnerships: {len(organized_results['partnerships'])}")
        print(f"   - Industry analysis: {len(organized_results['industry_analysis'])}")
        print(f"   - Founder backgrounds: {len(organized_results['founder_backgrounds'])}")
        print(f"   - Total results: {total_results}")
        
        print("\n✅ Node 3 Complete: Search completed successfully")
        print("="*60 + "\n")
        
        # Step 10: Return updated state
        return {
            "status": "search_completed",
            "raw_gathering_data": raw_gathering_data
        }
    
    except Exception as e:
        print(f"\n❌ ERROR in Node 3: {str(e)}")
        print("="*60 + "\n")
        
        raw_gathering_data = state.raw_gathering_data or RawGatheringData()
        
        return {
            "status": "error",
            "raw_gathering_data": raw_gathering_data,
            "errors": [f"Startup search error: {str(e)}"]
        }