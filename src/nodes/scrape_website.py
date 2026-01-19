from ..state import GraphState, ScrapedWebsiteData, RawGatheringData
from ..tools.website_scraper import WebsiteScraper


async def scrape_website_node(state: GraphState) -> dict:
    """
    Node 2: Scrape the startup's website
    
    This node:
    1. Reads the website URL from state.startup_data.website
    2. Uses WebsiteScraper to visit and extract content
    3. Creates a ScrapedWebsiteData object
    4. Updates raw_gathering_data with website data
    5. Returns updated state
    
    Args:
        state: Current GraphState with website URL and existing raw_gathering_data
        
    Returns:
        dict: Updated state with ScrapedWebsiteData added to raw_gathering_data
        
    Example:
        result = await scrape_website_node(state)
        print(result["status"])  # "website_scraped"
    """
    
    try:
        print("\n" + "="*60)
        print("🌐 NODE 2: SCRAPE WEBSITE")
        print("="*60)
        
        # Step 1: Check if website URL exists
        website_url = state.startup_data.website
        
        if not website_url:
            print("⚠️ No website URL provided")
            print("Status: Skipping website scraping\n")
            
            # Get existing raw_gathering_data
            raw_gathering_data = state.raw_gathering_data or RawGatheringData()
            
            return {
                "status": "no_website",
                "raw_gathering_data": raw_gathering_data
            }
        
        print(f"✓ Website URL found: {website_url}")
        
        # Step 2: Create WebsiteScraper instance
        scraper = WebsiteScraper(timeout=30)
        
        # Step 3: Scrape the website
        print(f"  Scraping website...")
        scrape_result = await scraper.scrape_website(website_url)
        
        # Step 4: Check if scraping was successful
        if not scrape_result.get("success"):
            error_msg = scrape_result.get("error", "Unknown error")
            print(f"  ⚠️ Website scraping failed: {error_msg}")
            print("Status: Continuing with other nodes\n")
            
            # Get existing raw_gathering_data
            raw_gathering_data = state.raw_gathering_data or RawGatheringData()
            
            return {
                "status": "website_scrape_failed",
                "raw_gathering_data": raw_gathering_data,
                "errors": [f"Website scraping failed: {error_msg}"]
            }
        
        print("  ✓ Website scraped successfully")
        
        # Step 5: Extract information from scrape result
        print("  Extracting website information...")
        
        page_title = scrape_result.get("title", "")
        page_description = scrape_result.get("description", "")
        main_text = scrape_result.get("main_text", "")
        links = scrape_result.get("links", [])
        
        print(f"  ✓ Title: {page_title}")
        print(f"  ✓ Description length: {len(page_description)} characters")
        print(f"  ✓ Main text length: {len(main_text)} characters")
        print(f"  ✓ Links found: {len(links)}")
        
        # Step 6: Extract technologies (if any mentioned)
        technologies_detected = []
        common_techs = ["react", "python", "aws", "kubernetes", "nodejs", 
                       "vue", "angular", "django", "flask", "postgresql",
                       "mongodb", "docker", "firebase", "gcp", "azure"]
        
        combined_text = (main_text + " " + page_description).lower()
        for tech in common_techs:
            if tech in combined_text:
                technologies_detected.append(tech.upper())
        
        if technologies_detected:
            print(f"  ✓ Technologies detected: {', '.join(technologies_detected[:5])}")
        
        # Step 7: Create ScrapedWebsiteData object
        print("  Creating ScrapedWebsiteData object...")
        scraped_website_data = ScrapedWebsiteData(
            page_title=page_title,
            page_description=page_description,
            main_content=main_text,
            technologies_detected=technologies_detected
        )
        print("  ✓ ScrapedWebsiteData created")
        
        # Step 8: Update raw_gathering_data
        print("  Updating raw_gathering_data...")
        raw_gathering_data = state.raw_gathering_data or RawGatheringData()
        raw_gathering_data.website_scraped = scraped_website_data
        print("  ✓ Website data added to raw_gathering_data")
        
        # Step 9: Log summary
        print("\n📊 SCRAPING SUMMARY:")
        print(f"   - Website URL: {website_url}")
        print(f"   - Page title: {page_title}")
        print(f"   - Content length: {len(main_text)} characters")
        print(f"   - Links found: {len(links)}")
        print(f"   - Technologies detected: {len(technologies_detected)}")
        
        if technologies_detected:
            print(f"   - Tech stack: {', '.join(technologies_detected[:5])}")
        
        print("\n✅ Node 2 Complete: Website scraped successfully")
        print("="*60 + "\n")
        
        # Step 10: Return updated state
        return {
            "status": "website_scraped",
            "raw_gathering_data": raw_gathering_data
        }
    
    except Exception as e:
        print(f"\n❌ ERROR in Node 2: {str(e)}")
        print("="*60 + "\n")
        
        # Get existing raw_gathering_data
        raw_gathering_data = state.raw_gathering_data or RawGatheringData()
        
        return {
            "status": "error",
            "raw_gathering_data": raw_gathering_data,
            "errors": [f"Website scraping error: {str(e)}"]
        }