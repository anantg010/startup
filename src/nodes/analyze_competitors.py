from ..state import GraphState, CompetitorAnalysis, Competitor
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from ..config import Config
import json


async def analyze_competitors_node(state: GraphState) -> dict:
    """
    Node 5: Analyze competitors of the startup
    
    This node:
    1. Reads research_findings from state
    2. Extracts startup details (industry, market, business model)
    3. Searches for and analyzes 5 competitors
    4. Creates detailed competitor profiles
    5. Compares each competitor to the focused startup
    6. Returns updated state with competitor analysis
    
    Args:
        state: Current GraphState with research_findings
        
    Returns:
        dict: Updated state with competitor_analysis
        
    Example:
        result = await analyze_competitors_node(state)
        print(result["status"])  # "competitors_analyzed"
    """
    
    try:
        print("\n" + "="*60)
        print("🏢 NODE 5: ANALYZE COMPETITORS")
        print("="*60)
        
        # Step 1: Check if research findings exist
        if not state.research_findings:
            print("⚠️ No research findings available")
            print("Status: Cannot analyze competitors without research data\n")
            
            return {
                "status": "no_research_findings",
                "competitor_analysis": None
            }
        
        research_findings = state.research_findings
        startup_name = research_findings.name
        industry = research_findings.industry
        business_model = research_findings.company_goal or "Not specified"

        focus_market = research_findings.customer_base or "Not specified"
        known_competitors = ", ".join(research_findings.known_competitors) if research_findings.known_competitors else ""
        
        # Extract Market Data for Validation
        initial_tam = research_findings.tam
        initial_sam = research_findings.sam
        initial_som = research_findings.som
        print(f"✓ Initial Market Data: TAM={initial_tam}, SAM={initial_sam}, SOM={initial_som}")
        
        # Extract Tavily report for context
        tavily_report = ""
        raw_data = state.raw_gathering_data
        if raw_data and raw_data.tavily_report:
            tavily_report = raw_data.tavily_report
            print(f"✓ Tavily Report available for context ({len(tavily_report)} chars)")
        
        print(f"✓ Startup: {startup_name}")
        print(f"✓ Industry: {industry}")
        print(f"✓ Business Model: {business_model}")
        print(f"✓ Focus Market: {focus_market}")
        print(f"✓ Known Competitors: {known_competitors if known_competitors else 'None identified explicitly'}")
        
        # Step 2: Create competitor analysis prompt
        print("\n  Creating competitor analysis prompt...")
        
        competitor_prompt = ChatPromptTemplate.from_template("""
You are an expert startup analyst and competitive intelligence specialist with deep knowledge of the Indian startup ecosystem.

Based on the following startup details, identify and analyze 5 major competitors.

STARTUP DETAILS:
Name: {startup_name}
Industry: {industry}
Business Model: {business_model}
Focus Market: {focus_market}
Description: {description}

IMPORTANT GEOGRAPHIC FOCUS:
1. **PRIORITIZE INDIAN MARKET**: First, identify competitors operating in India or targeting the Indian market
2. **GLOBAL FALLBACK**: Only if you cannot find sufficient competitors in the Indian market, then identify competitors from other markets (US, Europe, Asia, etc.)
3. **PREFERENCE ORDER**: India-based > India-focused > Global players with India presence > Global competitors

RAW RESEARCH CONTEXT (TAVILY REPORT):
--------------------------------
{tavily_context}
--------------------------------

KNOWN COMPETITORS FROM ANALYSIS:
{known_competitors}

Your task:
1. **CHECK KNOWN COMPETITORS**: First, verify if the "KNOWN COMPETITORS FROM DATA" are valid and relevant. If they are, prioritize analyzing them.
2. Identify 5 real or realistic competitors in the {industry} space, following the geographic priority above
3. For each competitor, gather and structure information
4. Compare each competitor to the startup in focus
5. Provide market overview and competitive analysis specific to the Indian context where applicable

6. **MARKET DATA VALIDATION**:
   - INPUT DATA PROVIDED: 
     * TAM: {initial_tam}
     * SAM: {initial_sam}
     * SOM: {initial_som}
   - Validate these numbers. **CRITICAL: ALL NUMBERS MUST BE INDIA-CENTRIC (INR).**
   - **MANDATORY ESTIMATION**: If input numbers are missing, incorrect, or Global, YOU MUST ESTIMATE THE **INDIAN MARKET SIZE** (TAM/SAM/SOM) in INR.
   - **DO NOT RETURN NULL**. You MUST provide a professional estimate based on the industry.
   - ALWAYS provide numeric values for 'validated_market_data'.
   - Provide **MAX 2 BRIEF BULLET POINTS** stating the **SOURCE** or **BASIS** of these numbers (e.g., "Based on Statista 2024 report", "Bottom-up estimate: 10M users x ₹500").

For EACH of the 5 competitors, provide:
- name: Company name
- founded_year: Year founded (as integer)
- headquarters: Location
- funding_raised: Total funding in Indian Rupees (INR) (as number)
- current_valuation: Current valuation in Indian Rupees (INR) (as number, or null if unknown)
- revenue: Annual revenue in Indian Rupees (INR) (as number, or null if unknown)
- business_model: How they make money
- focus_market: Their target market
- traction: Their growth metrics and traction
- similarities: How they are similar to {startup_name}

IMPORTANT: Return ONLY valid JSON with this exact structure:
{{
  "competitors": [
    {{
      "name": "Competitor 1",
      "founded_year": 2019,
      "headquarters": "San Francisco, CA",
      "funding_raised": 50000000,
      "current_valuation": 500000000,
      "revenue": 100000000,
      "business_model": "SaaS subscription",
      "focus_market": "Enterprise companies",
      "traction": "1000+ customers, $100M ARR",
      "similarities": "Similar AI-based approach for document processing"
    }},
    ...repeat for 5 competitors...
  ],
  "market_overview": "Brief overview of the competitive landscape in {industry}",
  "competitive_advantages": "What makes {startup_name} different/better",
  "market_threats": "Key threats and challenges in this market",
  "validated_market_data": {{
      "tam": 1000000000,
      "sam": 500000000,
      "som": 50000000,
      "explanation": ["Bullet 1 explaining the numbers", "Bullet 2 explaining the growth"]
  }}
}}

Be specific with numbers and factual. If exact data is unknown, provide realistic estimates based on industry knowledge.
""")
        
        # Step 3: Initialize LLM
        print("  Initializing LLM for competitor analysis...")
        
        llm = ChatOpenAI(
            model=Config.OPENAI_MODEL,
            temperature=0.7,
            api_key=Config.OPENAI_API_KEY
        )
        
        print("  ✓ LLM initialized")
        
        # Step 4: Create chain and call LLM
        print("  Sending data to LLM for competitor analysis...")
        
        chain = competitor_prompt | llm
        
        response = await chain.ainvoke({
            "startup_name": startup_name,
            "industry": industry,
            "business_model": business_model,
            "focus_market": focus_market,
            "known_competitors": known_competitors,
            "description": research_findings.description,
            "tavily_context": tavily_report if tavily_report else "No deep research report available.",
            "initial_tam": initial_tam,
            "initial_sam": initial_sam,
            "initial_som": initial_som
        })
        
        print("  ✓ LLM analysis completed")
        
        # Step 5: Parse LLM response
        print("  Parsing competitor data...")
        
        llm_output = response.content
        
        # Try to extract and parse JSON
        try:
            # Try direct JSON parsing
            competitor_data = json.loads(llm_output)
        except json.JSONDecodeError:
            # If direct parsing fails, try to extract JSON from text
            try:
                start_idx = llm_output.find('{')
                end_idx = llm_output.rfind('}') + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_str = llm_output[start_idx:end_idx]
                    competitor_data = json.loads(json_str)
            except:
                competitor_data = {
                    "competitors": [],
                    "market_overview": "Unable to parse competitor data",
                    "competitive_advantages": "",
                    "market_threats": "",
                    "validated_market_data": {}
                }

        
        print("  ✓ Data parsed successfully")
        
        # Step 6: Create Competitor objects
        print("  Creating competitor objects...")
        
        competitors = []
        competitor_list = competitor_data.get("competitors", [])
        
        for comp_data in competitor_list[:5]:  # Limit to 5
            try:
                competitor = Competitor(
                    name=comp_data.get("name") or "",
                    founded_year=comp_data.get("founded_year"),
                    headquarters=comp_data.get("headquarters") or "",
                    funding_raised=comp_data.get("funding_raised"),
                    current_valuation=comp_data.get("current_valuation"),
                    revenue=comp_data.get("revenue"),
                    business_model=comp_data.get("business_model") or "",
                    focus_market=comp_data.get("focus_market") or "",
                    traction=comp_data.get("traction") or "",
                    similarities=comp_data.get("similarities") or ""
                )
                competitors.append(competitor)
                print(f"    ✓ {competitor.name}")
            except Exception as e:
                print(f"    ⚠️ Error creating competitor: {str(e)}")
        
        print(f"  ✓ {len(competitors)} competitors created")
        
        # Step 7: Create CompetitorAnalysis object
        print("  Creating CompetitorAnalysis object...")
        
        # Validate market data keys exist
        validated_data = competitor_data.get("validated_market_data", {})
        
        competitor_analysis = CompetitorAnalysis(
            startup_name=startup_name,
            competitors=competitors,
            market_overview=competitor_data.get("market_overview") or "",
            competitive_advantages=competitor_data.get("competitive_advantages") or "",
            market_threats=competitor_data.get("market_threats") or "",
            tam=validated_data.get("tam"),
            sam=validated_data.get("sam"),
            som=validated_data.get("som"),
            market_data_explanation=validated_data.get("explanation", [])
        )
        
        print("  ✓ CompetitorAnalysis object created")
        
        # Step 8: Log summary
        print("\n📊 COMPETITOR ANALYSIS SUMMARY:")
        print(f"   - Startup: {startup_name}")
        print(f"   - Industry: {industry}")
        print(f"   - Competitors analyzed: {len(competitors)}")
        
        for i, comp in enumerate(competitors, 1):
            print(f"\n   Competitor {i}: {comp.name}")
            print(f"      Founded: {comp.founded_year}")
            print(f"      Headquarters: {comp.headquarters}")
            print(f"      Funding: ${comp.funding_raised:,}" if comp.funding_raised else "      Funding: Unknown")
            print(f"      Valuation: ${comp.current_valuation:,}" if comp.current_valuation else "      Valuation: Unknown")
            print(f"      Revenue: ${comp.revenue:,}" if comp.revenue else "      Revenue: Unknown")
            print(f"      Business Model: {comp.business_model}")
            print(f"      Traction: {comp.traction[:80]}..." if len(comp.traction) > 80 else f"      Traction: {comp.traction}")
        
        print(f"\n   Market Overview: {competitor_analysis.market_overview[:100]}...")
        print(f"   Competitive Advantages: {competitor_analysis.competitive_advantages[:100]}...")
        print(f"   Market Threats: {competitor_analysis.market_threats[:100]}...")
        
        print("\n✅ Node 5 Complete: Competitor analysis completed successfully")
        print("="*60 + "\n")
        
        # Step 9: Return updated state
        return {
            "status": "competitors_analyzed",
            "competitor_analysis": competitor_analysis
        }
    
    except Exception as e:
        print(f"\n❌ ERROR in Node 5: {str(e)}")
        import traceback
        traceback.print_exc()
        print("="*60 + "\n")
        
        return {
            "status": "error",
            "errors": [f"Competitor analysis error: {str(e)}"]
        }