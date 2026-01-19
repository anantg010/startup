
import asyncio
import json
import sys
import os
import codecs

# Add the project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, project_root)

from src.tools.serp_search import SerpAPISearch

# Set stdout to UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

async def main():
    startup_name = "Foontro"
    
    print("="*60)
    print(f"🔍 STARTING SERP API SEARCH FOR: {startup_name}")
    print("="*60)

    try:
        search_tool = SerpAPISearch()
        if not search_tool.api_key:
            print("❌ Error: API key missing. Please check Config.")
            return

        # Perform comprehensive startup search
        print("\n[1/1] Running comprehensive search...")
        results = await search_tool.search_startup(startup_name)
        
        # Output Results
        if results.get("success"):
            print("\n✅ SEARCH COMPLETED SUCCESSFULLY")
            
            # Save detailed results to file
            output_file = "serp_results.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, default=str)
            print(f"💾 Full results saved to {output_file}")
            
            # Print Summary to console
            print("\n📊 SUMMARY OF FINDINGS:")
            
            # 1. Knowledge Graph
            if "company_search" in results.get("searches", {}):
                 kg = results["searches"]["company_search"].get("knowledge_graph", {})
                 if kg:
                     print(f"   • Knowledge Graph: {kg}")
            
            # 2. Top Company Search Results
            print("\n   • Top Company Search Results:")
            comp_search = results.get("searches", {}).get("company_search", {}).get("results", [])
            for res in comp_search[:3]:
                print(f"     - {res.get('title')}: {res.get('link')}")
                
            # 3. News
            print("\n   • Recent News:")
            news_items = results.get("news", {}).get("results", [])
            if news_items:
                for item in news_items[:3]:
                    print(f"     - {item.get('title')} ({item.get('date')})")
            else:
                print("     - No recent news found.")

        else:
            print(f"\n❌ Search Failed: {results.get('error')}")

    except Exception as e:
        print(f"\n❌ Execution Failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
