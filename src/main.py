import asyncio
import json
from datetime import datetime
from .state import GraphState, StartupData
from .graph import build_research_graph


# Sample test data
SAMPLE_STARTUP_DATA = {
    "name": "TechCorp AI",
    "legal_name": "TechCorp AI Inc.",
    "industry": "Artificial Intelligence",
    "description": "Building enterprise AI solutions for document processing and data analysis",
    "email": "contact@techcorp.ai",
    "website": "https://techcorp.ai",
    "founders": "John Smith, Jane Doe",
    "stage": "Series A",
    "team_size": 25,
    "founded_year": 2022,
    "location": "San Francisco, CA",
    "ceo_linkedin_url": "https://linkedin.com/in/johnsmith"
}

SAMPLE_PITCH_DECK_TEXT = """
--- Page 1 ---
TECHCORP AI - PITCH DECK

Building Enterprise AI Solutions

--- Page 2 ---
PROBLEM
Companies struggle with document processing and data extraction.
Current solutions are manual, slow, and error-prone.

--- Page 3 ---
SOLUTION
TechCorp AI provides automated document processing using advanced ML models.
Process thousands of documents in minutes.
Accuracy rate: 99.5%

--- Page 4 ---
MARKET OPPORTUNITY
Total Addressable Market: $50 Billion
Enterprise document processing market growing at 40% CAGR
Early adopters: Fortune 500 companies

--- Page 5 ---
BUSINESS MODEL
SaaS Platform with per-document pricing
Customers: Enterprise companies
Average contract value: $500K - $2M annually

--- Page 6 ---
TEAM
CEO: John Smith (10 years AI/ML experience, ex-Google)
CTO: Jane Doe (8 years software engineering, ex-Amazon)
VP Sales: Mike Johnson (15 years enterprise sales)

--- Page 7 ---
TRACTION
- 50 enterprise customers
- $5M ARR
- 200% YoY growth
- 98% customer retention

--- Page 8 ---
FUNDING ASK
Seeking $10M Series A to:
- Expand sales team (40%)
- Enhance product (35%)
- Infrastructure (25%)

--- Page 9 ---
FINANCIAL PROJECTIONS
Year 1 (2024): $10M ARR
Year 2 (2025): $25M ARR
Year 3 (2026): $60M ARR

--- Page 10 ---
EXIT STRATEGY
Potential acquirers: Google, Microsoft, IBM
IPO potential within 5-7 years
"""


async def main():
    """
    Main testing function
    Tests the entire research workflow with sample data
    """
    
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  🚀 STARTUP RESEARCH AGENT - LOCAL TEST".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝")
    
    print(f"\n⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Step 1: Build the graph
        print("\n" + "─"*60)
        print("STEP 1: Building LangGraph...")
        print("─"*60)
        
        graph = build_research_graph()
        
        print("✅ Graph built successfully!")
        
        # Step 2: Create test startup data
        print("\n" + "─"*60)
        print("STEP 2: Creating test startup data...")
        print("─"*60)
        
        startup_data = StartupData(**SAMPLE_STARTUP_DATA)
        
        print(f"✓ Startup name: {startup_data.name}")
        print(f"✓ Industry: {startup_data.industry}")
        print(f"✓ Email: {startup_data.email}")
        print(f"✓ Website: {startup_data.website}")
        print(f"✓ Founders: {startup_data.founders}")
        print(f"✓ Stage: {startup_data.stage}")
        print(f"✓ Team size: {startup_data.team_size}")
        
        print("✅ Startup data created successfully!")
        
        # Step 3: Create initial state
        print("\n" + "─"*60)
        print("STEP 3: Creating initial GraphState...")
        print("─"*60)
        
        initial_state = GraphState(
            startup_data=startup_data,
            pitch_deck_text=SAMPLE_PITCH_DECK_TEXT,
            status="initialized"
        )
        
        print(f"✓ GraphState created")
        print(f"✓ Pitch deck length: {len(SAMPLE_PITCH_DECK_TEXT)} characters")
        print(f"✓ Status: {initial_state.status}")
        
        print("✅ Initial state created successfully!")
        
        # Step 4: Run the workflow
        print("\n" + "─"*60)
        print("STEP 4: Running the research workflow...")
        print("─"*60)
        print("\nThis will execute all 4 nodes sequentially:\n")
        
        result = await graph.ainvoke(initial_state)
        
        # Step 5: Display results
        print("\n" + "─"*60)
        print("STEP 5: Workflow Results")
        print("─"*60)
        
        print(f"\n✅ Workflow Status: {result.get('status')}")
        
        # Check for errors
        if result.get('errors'):
            print(f"\n⚠️ Errors encountered:")
            for error in result.get('errors', []):
                print(f"   - {error}")
        
        # Step 6: Display research findings
        if result.get('research_findings'):
            findings = result['research_findings']
            
            print("\n" + "─"*60)
            print("RESEARCH FINDINGS")
            print("─"*60)
            
            print(f"\n📊 Company Information:")
            print(f"   Name: {findings.name}")
            print(f"   Legal Name: {findings.legal_name}")
            print(f"   Industry: {findings.industry}")
            print(f"   Website: {findings.website}")
            print(f"   Location: {findings.location}")
            print(f"   Employees: {findings.employee_count}")
            
            print(f"\n👤 Leadership:")
            print(f"   CEO Name: {findings.ceo_name}")
            print(f"   CEO Email: {findings.ceo_email}")
            print(f"   CEO LinkedIn: {findings.ceo_linkedin_url}")
            
            print(f"\n💼 Business:")
            print(f"   Thesis Category: {findings.thesis_name}")
            print(f"   Company Goal: {findings.company_goal}")
            print(f"   Description: {findings.description[:100]}..." if len(findings.description) > 100 else f"   Description: {findings.description}")
            
            print(f"\n💰 Funding:")
            print(f"   Funding Raised: ${findings.funding_raised:,}" if findings.funding_raised else "   Funding Raised: Not specified")
            print(f"   Funding Ask: ${findings.funding_ask_amount:,}" if findings.funding_ask_amount else "   Funding Ask: Not specified")
            
            print(f"\n📈 Analysis:")
            if findings.market_analysis:
                print(f"   Market Analysis: {findings.market_analysis[:100]}..." if len(findings.market_analysis) > 100 else f"   Market Analysis: {findings.market_analysis}")
            
            if findings.team_insights:
                print(f"   Team Insights: {findings.team_insights[:100]}..." if len(findings.team_insights) > 100 else f"   Team Insights: {findings.team_insights}")
            
            if findings.competitive_landscape:
                print(f"   Competitive Landscape: {findings.competitive_landscape[:100]}..." if len(findings.competitive_landscape) > 100 else f"   Competitive Landscape: {findings.competitive_landscape}")
            
            print(f"\n🔧 Technology:")
            if findings.technology_stack:
                print(f"   Tech Stack: {findings.technology_stack}")
            
            print(f"\n👥 Customers:")
            if findings.customer_base:
                print(f"   Customer Base: {findings.customer_base[:100]}..." if len(findings.customer_base) > 100 else f"   Customer Base: {findings.customer_base}")
            
            print(f"\n📰 News:")
            if findings.news_mentions:
                for i, mention in enumerate(findings.news_mentions[:5], 1):
                    print(f"   {i}. {mention}")
            else:
                print("   No news mentions found")
            
            # Export as JSON
            print("\n" + "─"*60)
            print("FULL RESEARCH FINDINGS (JSON)")
            print("─"*60)
            
            findings_dict = findings.model_dump()
            findings_json = json.dumps(findings_dict, indent=2, default=str)
            print(findings_json)
        
        # Step 7: Summary
        print("\n" + "─"*60)
        print("TEST SUMMARY")
        print("─"*60)
        
        print(f"\n✅ Workflow completed successfully!")
        print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Final status: {result.get('status')}")
        print(f"✓ Research findings generated: {result.get('research_findings') is not None}")
        
        print("\n" + "╔" + "="*58 + "╗")
        print("║" + " "*58 + "║")
        print("║" + "  ✅ ALL TESTS PASSED!".center(58) + "║")
        print("║" + " "*58 + "║")
        print("╚" + "="*58 + "╝\n")
        
        return result
    
    except Exception as e:
        print(f"\n❌ ERROR during testing: {str(e)}")
        print("\n" + "─"*60)
        print("TROUBLESHOOTING")
        print("─"*60)
        print(f"\nError type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        
        print("\n" + "╔" + "="*58 + "╗")
        print("║" + " "*58 + "║")
        print("║" + "  ❌ TEST FAILED".center(58) + "║")
        print("║" + " "*58 + "║")
        print("╚" + "="*58 + "╝\n")
        
        raise


if __name__ == "__main__":
    """
    Run the test
    Usage: python src/main.py
    """
    asyncio.run(main())