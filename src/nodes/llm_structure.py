from ..state import GraphState, ResearchFindings, RawGatheringData, FounderProfile, AIScorecard, ScoreDetail
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from ..config import Config
import json


def _extract_text_from_field(value) -> str:
    """
    Extract plain text from a field that might be:
    - A string
    - A dict (extract relevant text values)
    - A JSON string (parse and extract)
    - None
    
    Returns plain text suitable for PDF display.
    """
    if value is None:
        return ""
    
    if isinstance(value, str):
        # Check if it's a JSON string
        if value.strip().startswith('{'):
            try:
                parsed = json.loads(value)
                return _extract_text_from_field(parsed)
            except json.JSONDecodeError:
                return value
        return value
    
    if isinstance(value, dict):
        # Extract text from common keys
        text_parts = []
        for key in ['text', 'content', 'description', 'summary', 'analysis', 
                    'market_analysis', 'competitive_landscape', 'team_insights']:
            if key in value and value[key]:
                text_parts.append(str(value[key]))
        
        # If no common keys found, join all string values
        if not text_parts:
            for k, v in value.items():
                if isinstance(v, str) and v and k not in ['tam', 'sam', 'som', 'market_growth_rate']:
                    text_parts.append(str(v))
        
        return " ".join(text_parts) if text_parts else ""
    
    if isinstance(value, list):
        return ", ".join(str(item) for item in value if item)
    
    return str(value) if value else ""

async def llm_structure_node(state: GraphState) -> dict:
    """
    Node 4: Use LLM to analyze and structure all gathered data
    
    This node:
    1. Reads complete raw_gathering_data (PDF + Website + Search)
    2. Combines all data into a comprehensive context
    3. Sends to LLM with detailed prompt
    4. LLM analyzes and structures the data
    5. Generates AI Scorecard with 7 parameters
    6. Creates ResearchFindings object with all enhanced fields
    7. Returns updated state
    
    Args:
        state: Current GraphState with complete raw_gathering_data
        
    Returns:
        dict: Updated state with ResearchFindings including AI Scorecard
        
    Example:
        result = await llm_structure_node(state)
        print(result["status"])  # "structured_by_llm"
    """
    
    try:
        print("\n" + "="*60)
        print("🤖 NODE 4: LLM STRUCTURE (ENHANCED)")
        print("="*60)
        
        # Step 1: Get all raw data from previous nodes
        print("  Gathering all collected data...")
        
        raw_gathering_data = state.raw_gathering_data or RawGatheringData()
        
        pitch_deck_text = ""
        website_text = ""
        search_results = {}
        
        if raw_gathering_data.pitch_deck_extracted:
            pitch_deck_text = raw_gathering_data.pitch_deck_extracted.raw_text
            print(f"    ✓ Pitch deck: {len(pitch_deck_text)} characters")
        
        if raw_gathering_data.website_scraped:
            website_text = raw_gathering_data.website_scraped.main_content
            print(f"    ✓ Website: {len(website_text)} characters")
        
        if raw_gathering_data.search_results:
            search_results = raw_gathering_data.search_results.search_results
            print(f"    ✓ Search results: {len(search_results)} categories")
        
        # Step 2: Build comprehensive context for LLM
        print("  Building comprehensive context for LLM analysis...")
        
        context = f"""
STARTUP INFORMATION
===================
Name: {state.startup_data.name}
Legal Name: {state.startup_data.legal_name or state.startup_data.name}
Industry: {state.startup_data.industry}
Description: {state.startup_data.description}
Email: {state.startup_data.email}
Website: {state.startup_data.website or 'Not provided'}
Founders: {state.startup_data.founders or 'Not provided'}
Stage: {state.startup_data.stage or 'Not provided'}
Team Size: {state.startup_data.team_size or 'Not provided'}
Founded Year: {state.startup_data.founded_year or 'Not provided'}
Location: {state.startup_data.location or 'Not provided'}
CEO LinkedIn: {state.startup_data.ceo_linkedin_url or 'Not provided'}

PITCH DECK CONTENT
==================
{pitch_deck_text if pitch_deck_text else 'Pitch deck not provided'}

WEBSITE CONTENT
===============
{website_text if website_text else 'Website not scraped'}

SEARCH RESULTS (Comprehensive)
==============================
{json.dumps(search_results, indent=2) if search_results else 'No search results available'}

TAVILY DEEP RESEARCH REPORT
===========================
{raw_gathering_data.tavily_report if raw_gathering_data.tavily_report else 'No deep research report available'}

TAVILY RAW DATA (Source Details)
================================
{json.dumps(raw_gathering_data.tavily_data, indent=2) if raw_gathering_data.tavily_data else 'No raw data available'}
"""
        
        print("  ✓ Context built successfully")
        
        # Step 3: Create comprehensive LLM prompt
        print("  Creating comprehensive LLM prompt...")
        
        prompt_template = ChatPromptTemplate.from_template("""
You are an expert startup analyst, venture capital investor, and due diligence professional.

Analyze the following startup information gathered from multiple sources (pitch deck, website, and comprehensive web search):

{context}

Your task is to provide an EXTREMELY DETAILED and COMPREHENSIVE analysis. Extract every piece of relevant information and provide thorough assessments. This will be used to generate an investment thesis document.

Please provide a comprehensive analysis and structure the information into the following fields:

=== BASIC INFORMATION ===
1. name - Startup name
2. legal_name - Legal company name
3. description - Detailed company overview (5-7 sentences covering what they do, how they do it, and why)
4. location - Headquarters location
5. website - Company website URL
6. company_email - Company email
7. company_phone - Company phone number
8. industry - Industry category
9. startup_industry_domain - Specific domain/vertical

=== THESIS CLASSIFICATION ===
10. thesis_name - Categorize into ONE of these thesis categories:
    - CONSUMER: B2C products/services for end-users (e-commerce, D2C, lifestyle, travel, fintech for individuals)
    - HEALTHCARE: Healthcare, medical tech, wellness, diagnostics, pharma (telemedicine, medical devices, mental health)
    - IMPACT_SDG: Social Good, Sustainability, UN SDGs (clean energy, education access, climate tech)
    - SINGULARITY_AI: Deep-tech AI, Quantum, Neurotech (LLMs, AGI, autonomous robotics)
    - EMC: Enterprise Modern Cloud B2B (DevOps, cloud infrastructure, enterprise SaaS)
    - RUMS: Remote work, Utilities, Mobility, Space (EVs, drones, satellites)
    - RETAIN: HR, employee experience, team culture (payroll, hiring, L&D tools)
    - OTHERS: Only if nothing else fits

11. startup_stage - Classify as one of:
    - IDEA: Pre-product, concept only
    - MVP: Working prototype, testing with early users
    - EARLY_TRACTION: Initial paying customers, product-market fit signals
    - GROWTH: Proven PMF, scaling customer acquisition
    - SCALE_UP: Rapid expansion, Series B/C
    - EXPANSION_LATE_STAGE: Mature, preparing for exit/IPO

=== CEO/FOUNDER INFORMATION ===
12. ceo_name - CEO or lead founder name
13. ceo_email - CEO email
14. ceo_phone - CEO phone
15. ceo_linkedin_url - CEO LinkedIn URL

=== DETAILED FOUNDER PROFILES ===
16. founders - List of founder profiles, each with:
    - name: Full name
    - role: Role (CEO, CTO, COO, etc.)
    - linkedin_url: LinkedIn URL
    - education: List of educational background (universities, degrees)
    - previous_companies: List of previous companies worked at
    - previous_exits: List of any previous startup exits or acquisitions
    - years_experience: Years of relevant experience (integer)
    - domain_expertise: Area of expertise
    - notable_achievements: List of notable achievements

=== COMPANY DETAILS ===
17. company_goal - Company's main goal and vision (detailed, 3-5 sentences)
18. employee_count - Number of employees (integer)
19. company_info - Company background as object/dict
20. team_insights - Detailed team background analysis (3-5 sentences)

=== PRODUCT & BUSINESS ===
21. product_description - Detailed product/service description (5-7 sentences)
22. unique_value_proposition - What makes the product unique (2-3 sentences)
23. technology_moat - Technological advantages, IP, patents (2-3 sentences)
24. business_model_details - Detailed business model explanation (3-5 sentences)
25. revenue_model - How the company makes money
26. pricing_strategy - Pricing information
27. technology_stack - Technologies used

=== FINANCIAL METRICS ===
28. funding_raised - Total funding raised in INR (number, null if unknown)
29. funding_ask_amount - Current funding ask in INR (number, null if unknown)
30. funding_info - Funding history as object/dict
31. current_mrr - Monthly Recurring Revenue in INR (number, null if unknown)
32. current_arr - Annual Recurring Revenue in INR (number, null if unknown)
33. yoy_growth_rate - Year over year growth rate percentage (number, null if unknown)
34. customer_acquisition_cost - CAC in INR (number, null if unknown)
35. lifetime_value - LTV in INR (number, null if unknown)
36. burn_rate - Monthly burn rate in INR (number, null if unknown)
37. runway_months - Runway in months (integer, null if unknown)

=== TRACTION & METRICS ===
38. total_customers - Total number of customers (integer, null if unknown)
39. active_users - Number of active users (integer, null if unknown)
40. retention_rate - Customer retention rate percentage (number, null if unknown)
41. key_metrics - Key performance metrics as object/dict
42. customer_base - Target and current customers description

=== MARKET ANALYSIS ===
43. market_analysis - Detailed market opportunity analysis (5-7 sentences)
44. tam - Total Addressable Market in INR (number, null if unknown)
45. sam - Serviceable Addressable Market in INR (number, null if unknown)
46. som - Serviceable Obtainable Market in INR (number, null if unknown)
47. market_growth_rate - Market growth rate percentage (number, null if unknown)
48. competitive_landscape - Detailed competitive analysis (5-7 sentences)
49. known_competitors - List of specific competitor names mentioned in the "Tavily Deep Research Report" or Pitch Deck (array of strings). Extract AS MANY AS POSSIBLE.

=== ADDITIONAL INFO ===
50. partnerships - List of notable partnerships
51. awards_recognition - List of awards and recognition
52. news_mentions - List of recent news articles/mentions
53. social_presence - Social media information as object/dict

=== INVESTMENT ANALYSIS ===
54. investment_highlights - List of 5-7 key investment highlights (compelling reasons to invest)
55. risk_factors - List of 5-7 identified risk factors

=== AI SCORECARD (CRITICAL) ===
56. ai_scorecard - Generate a comprehensive evaluation scorecard with these parameters:

    For EACH of the 7 scoring categories below, provide:
    - score: A score from 0-10 (use decimals like 7.5)
    - weight: The weight (Founders=0.25, Market=0.20, Product=0.15, Traction=0.20, Team=0.10, Financials=0.10, Competition=0.10)
    - justification: 2-3 sentence reasoning for the score
    - strengths: List of 2-3 strengths in this category
    - weaknesses: List of 2-3 weaknesses in this category

    SCORING CATEGORIES:
    
    a) founders_score (25% weight): Evaluate founders on:
       - Track record and previous exits
       - Domain expertise and industry experience
       - Education and credentials
       - Complementary skill sets
       - Vision and execution capability
       
    b) market_score (20% weight): Evaluate market on:
       - Market size (TAM/SAM/SOM)
       - Market growth rate
       - Timing and trends
       - Regulatory environment
       - Customer pain point severity
       
    c) product_score (15% weight): Evaluate product on:
       - Product-market fit signals
       - Differentiation and moat
       - Technology innovation
       - User experience
       - Scalability
       
    d) traction_score (20% weight): Evaluate traction on:
       - Revenue and growth rate
       - Customer acquisition
       - User engagement and retention
       - Key metrics momentum
       - Proof points
       
    e) team_score (10% weight): Evaluate team on:
       - Team completeness
       - Relevant experience
       - Advisors and board
       - Culture and values
       - Hiring and talent
       
    f) financials_score (10% weight): Evaluate financials on:
       - Unit economics (LTV/CAC)
       - Burn rate and runway
       - Revenue model clarity
       - Path to profitability
       - Capital efficiency
       
    g) competition_score (weighted in analysis): Evaluate competition on:
       - Competitive positioning
       - Barriers to entry/moat
       - Differentiation clarity
       - Market share potential
       - Threat assessment

    Also provide:
    - overall_score: Weighted average of all scores (calculate using weights)
    - investment_recommendation: Based on overall_score:
      * "STRONG_BUY" if >= 8.0
      * "BUY" if >= 6.5
      * "HOLD" if >= 5.0
      * "PASS" if < 5.0
    - investment_summary: 3-5 sentence advisory summary for investors (focus on advice/recommendation rather than just description)
    - key_risks: Top 5 risks to monitor
    - key_opportunities: Top 5 opportunities for growth

IMPORTANT INSTRUCTIONS:
- Return ONLY valid JSON
- Be EXTREMELY DETAILED in all text fields
- Use proper data types (numbers for metrics, arrays for lists)
- For unknown values, use null (not "Not specified" or "Unknown")
- Make the analysis thorough enough for investment decision-making
- The AI Scorecard is CRITICAL - provide thoughtful, justified scores

JSON Response:
""")
        
        print("  ✓ Comprehensive prompt created")
        
        # Step 4: Initialize LLM
        print("  Initializing LLM (OpenAI GPT-4o)...")
        
        llm = ChatOpenAI(
            model=Config.OPENAI_MODEL,
            temperature=0.7,
            api_key=Config.OPENAI_API_KEY
        )
        
        print("  ✓ LLM initialized")
        
        # Step 5: Create chain and call LLM
        print("  Sending data to LLM for comprehensive analysis...")
        print("  (This may take longer due to detailed extraction)")
        
        chain = prompt_template | llm
        
        response = await chain.ainvoke({
            "context": context
        })
        
        print("  ✓ LLM analysis completed")
        
        # Step 6: Parse LLM response
        print("  Parsing LLM response...")
        
        llm_output = response.content
        
        # Save LLM output to file for debugging
        import os
        debug_dir = "outputs"
        if not os.path.exists(debug_dir):
            os.makedirs(debug_dir)
        
        debug_file = f"{debug_dir}/debug_llm_output.json"
        with open(debug_file, "w", encoding="utf-8") as f:
            f.write(llm_output)
        print(f"  ✓ LLM output saved to {debug_file} for debugging")
        
        # Try to extract JSON from response
        try:
            # Try direct JSON parsing
            structured_data = json.loads(llm_output)
        except json.JSONDecodeError:
            # If direct parsing fails, try to extract JSON from text
            try:
                start_idx = llm_output.find('{')
                end_idx = llm_output.rfind('}') + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_str = llm_output[start_idx:end_idx]
                    structured_data = json.loads(json_str)
                else:
                    structured_data = {"raw_response": llm_output}
            except:
                structured_data = {"raw_response": llm_output}
        
        # CRITICAL FIX: Flatten nested structure from LLM
        # LLM returns: {"BASIC_INFORMATION": {"name": "..."}} 
        # Code expects: {"name": "..."}
        print("  Flattening nested JSON structure...")
        
        def flatten_nested_json(data):
            """Flatten nested JSON sections into a single level"""
            if not isinstance(data, dict):
                return data
            
            flattened = {}
            
            # Map of section names to expected field mappings
            section_mappings = {
                "BASIC_INFORMATION": ["name", "legal_name", "description", "location", "website", 
                                      "company_email", "company_phone", "industry", "startup_industry_domain"],
                "THESIS_CLASSIFICATION": ["thesis_name", "startup_stage"],
                "CEO/FOUNDER_INFORMATION": ["ceo_name", "ceo_email", "ceo_phone", "ceo_linkedin_url"],
                "DETAILED_FOUNDER_PROFILES": ["founders"],
                "COMPANY_DETAILS": ["company_goal", "employee_count", "company_info", "team_insights"],
                "PRODUCT & BUSINESS": ["product_description", "unique_value_proposition", "technology_moat",
                                        "business_model_details", "revenue_model", "pricing_strategy", "technology_stack"],
                "FINANCIAL_METRICS": ["funding_raised", "funding_ask_amount", "funding_info", "current_mrr",
                                       "current_arr", "yoy_growth_rate", "customer_acquisition_cost", 
                                       "lifetime_value", "burn_rate", "runway_months"],
                "TRACTION & METRICS": ["total_customers", "active_users", "retention_rate", "key_metrics", "customer_base"],
                "TRACTION & METRICS": ["total_customers", "active_users", "retention_rate", "key_metrics", "customer_base"],
                "MARKET_ANALYSIS": ["market_analysis", "tam", "sam", "som", "market_growth_rate", "competitive_landscape", "known_competitors"],
                "ADDITIONAL_INFO": ["partnerships", "awards_recognition", "news_mentions", "social_presence"],
                "ADDITIONAL_INFO": ["partnerships", "awards_recognition", "news_mentions", "social_presence"],
                "INVESTMENT_ANALYSIS": ["investment_highlights", "risk_factors"],
                "AI_SCORECARD": ["founders_score", "market_score", "product_score", "traction_score",
                                  "team_score", "financials_score", "competition_score", "overall_score",
                                  "investment_recommendation", "investment_summary", "key_risks", "key_opportunities"]
            }
            
            for key, value in data.items():
                if isinstance(value, dict):
                    # Normalize key for comparison (handle lowercase, mixed case, etc.)
                    normalized_key = key.upper().replace(" ", "_").replace("&", "").replace("/", "").replace("-", "_")
                    
                    # Check if this is a section that should be flattened
                    section_keys = [s.upper().replace(" ", "_").replace("&", "").replace("/", "") for s in section_mappings.keys()]
                    is_section = normalized_key in section_keys
                    
                    # Also check common patterns that indicate nested sections
                    is_nested_section = (
                        normalized_key.endswith("_INFORMATION") or
                        normalized_key.endswith("_CLASSIFICATION") or
                        normalized_key.endswith("_DETAILS") or
                        normalized_key.endswith("_PROFILES") or
                        normalized_key.endswith("_BUSINESS") or
                        normalized_key.endswith("_METRICS") or
                        normalized_key.endswith("_ANALYSIS") or
                        normalized_key.endswith("_INFO") or
                        normalized_key.endswith("_SCORECARD") or
                        "FOUNDER" in normalized_key or
                        "CEO" in normalized_key or
                        "PRODUCT" in normalized_key or
                        "FINANCIAL" in normalized_key or
                        "TRACTION" in normalized_key or
                        "MARKET" in normalized_key or
                        "INVESTMENT" in normalized_key or
                        "AI_SCORECARD" in normalized_key or
                        "COMPANY" in normalized_key or
                        "THESIS" in normalized_key or
                        "BASIC" in normalized_key
                    )
                    
                    if is_section or is_nested_section:
                        # Flatten this section
                        for sub_key, sub_value in value.items():
                            flattened[sub_key] = sub_value
                    else:
                        flattened[key] = value
                else:
                    flattened[key] = value
            
            return flattened
        
        structured_data = flatten_nested_json(structured_data)
        print(f"  ✓ Flattened JSON - now has {len(structured_data)} top-level keys")
        
        # Save parsed structured data for debugging
        debug_parsed_file = f"{debug_dir}/debug_structured_data.json"
        with open(debug_parsed_file, "w", encoding="utf-8") as f:
            json.dump(structured_data, f, indent=2, default=str)
        print(f"  ✓ Parsed data saved to {debug_parsed_file}")
        
        # Log key fields for quick debugging
        print("\n  📝 LLM EXTRACTED DATA SUMMARY:")
        print(f"     - founders: {len(structured_data.get('founders', []))} items")
        print(f"     - product_description: {'Yes' if structured_data.get('product_description') else 'No'}")
        print(f"     - unique_value_proposition: {'Yes' if structured_data.get('unique_value_proposition') else 'No'}")
        print(f"     - business_model_details: {'Yes' if structured_data.get('business_model_details') else 'No'}")
        print(f"     - funding_raised: {structured_data.get('funding_raised')}")
        print(f"     - current_mrr: {structured_data.get('current_mrr')}")
        print(f"     - current_arr: {structured_data.get('current_arr')}")
        print(f"     - tam: {structured_data.get('tam')}")
        print(f"     - sam: {structured_data.get('sam')}")
        print(f"     - total_customers: {structured_data.get('total_customers')}")
        print(f"     - ai_scorecard: {'Yes' if structured_data.get('ai_scorecard') else 'No'}")
        print(f"     - team_insights: {'Yes' if structured_data.get('team_insights') else 'No'}")
        print(f"     - market_analysis: {'Yes' if structured_data.get('market_analysis') else 'No'}")
        
        print("\n  ✓ Response parsed successfully")
        
        # Step 7: Create FounderProfile objects
        print("  Creating FounderProfile objects...")
        
        founders_data = structured_data.get("founders", [])
        founders = []
        for f in founders_data:
            if isinstance(f, dict):
                founder = FounderProfile(
                    name=f.get("name") or "",
                    role=f.get("role") or "",
                    linkedin_url=f.get("linkedin_url") or "",
                    education=f.get("education", []) if isinstance(f.get("education"), list) else [],
                    previous_companies=f.get("previous_companies", []) if isinstance(f.get("previous_companies"), list) else [],
                    previous_exits=f.get("previous_exits", []) if isinstance(f.get("previous_exits"), list) else [],
                    years_experience=int(f.get("years_experience", 0)) if f.get("years_experience") else 0,
                    domain_expertise=f.get("domain_expertise") or "",
                    notable_achievements=f.get("notable_achievements", []) if isinstance(f.get("notable_achievements"), list) else []
                )
                founders.append(founder)
        
        print(f"  ✓ Created {len(founders)} founder profiles")
        
        # Step 8: Create AIScorecard object
        print("  Creating AIScorecard object...")
        
        # After flattening, scorecard fields are at top level (not nested under ai_scorecard)
        # Try to get from ai_scorecard first (if not flattened), then from top level
        scorecard_data = structured_data.get("ai_scorecard") or structured_data
        
        # Check if we have scorecard data at top level
        if structured_data.get("founders_score"):
            scorecard_data = structured_data  # Use flattened structure
            print("  ✓ Using flattened scorecard data")
        elif isinstance(scorecard_data, dict) and scorecard_data.get("founders_score"):
            print("  ✓ Using nested ai_scorecard data")
        else:
            print("  ⚠️ No scorecard data found, using defaults")
            scorecard_data = {}
        
        def create_score_detail(data, weight):
            if isinstance(data, dict):
                return ScoreDetail(
                    score=float(data.get("score", 0)),
                    max_score=10.0,
                    weight=weight,
                    justification=data.get("justification", ""),
                    strengths=data.get("strengths", []) if isinstance(data.get("strengths"), list) else [],
                    weaknesses=data.get("weaknesses", []) if isinstance(data.get("weaknesses"), list) else []
                )
            return ScoreDetail(score=0, weight=weight)
        
        ai_scorecard = AIScorecard(
            founders_score=create_score_detail(scorecard_data.get("founders_score"), 0.25),
            market_score=create_score_detail(scorecard_data.get("market_score"), 0.20),
            product_score=create_score_detail(scorecard_data.get("product_score"), 0.15),
            traction_score=create_score_detail(scorecard_data.get("traction_score"), 0.20),
            team_score=create_score_detail(scorecard_data.get("team_score"), 0.10),
            financials_score=create_score_detail(scorecard_data.get("financials_score"), 0.10),
            competition_score=create_score_detail(scorecard_data.get("competition_score"), 0.10),
            overall_score=float(scorecard_data.get("overall_score", 0)),
            investment_recommendation=scorecard_data.get("investment_recommendation", "HOLD"),
            investment_summary=scorecard_data.get("investment_summary", ""),
            key_risks=scorecard_data.get("key_risks", []) if isinstance(scorecard_data.get("key_risks"), list) else [],
            key_opportunities=scorecard_data.get("key_opportunities", []) if isinstance(scorecard_data.get("key_opportunities"), list) else []
        )
        
        print(f"  ✓ AIScorecard created with overall score: {ai_scorecard.overall_score}")
        
        # Step 9: Create ResearchFindings object with all enhanced fields
        print("  Creating enhanced ResearchFindings object...")
        
        research_findings = ResearchFindings(
            # Basic Information
            name=structured_data.get("name") or state.startup_data.name or "",
            legal_name=structured_data.get("legal_name") or state.startup_data.legal_name or state.startup_data.name or "",
            description=structured_data.get("description") or state.startup_data.description or "",
            location=structured_data.get("location") or state.startup_data.location or "",
            website=structured_data.get("website") or state.startup_data.website or "",
            company_email=structured_data.get("company_email"),
            company_phone=structured_data.get("company_phone"),
            industry=structured_data.get("industry") or state.startup_data.industry or "",
            startup_industry_domain=structured_data.get("startup_industry_domain") or state.startup_data.industry or "",
            thesis_name=structured_data.get("thesis_name") or "OTHERS",
            startup_stage=structured_data.get("startup_stage") or state.startup_data.stage or "",
            
            # CEO Information
            ceo_name=structured_data.get("ceo_name") or "",
            ceo_email=structured_data.get("ceo_email") or "",
            ceo_phone=structured_data.get("ceo_phone") or "",
            ceo_linkedin_url=structured_data.get("ceo_linkedin_url") or state.startup_data.ceo_linkedin_url or "",
            
            # Company Details - fallback to API input data
            company_goal=structured_data.get("company_goal") or "",
            employee_count=int(structured_data.get("employee_count") or state.startup_data.team_size or 0),
            company_info=structured_data.get("company_info") or {"founded_year": state.startup_data.founded_year} if state.startup_data.founded_year else {},
            
            # Analysis Fields - extract text properly (not JSON)
            market_analysis=_extract_text_from_field(structured_data.get("market_analysis") or ""),
            team_insights=_extract_text_from_field(structured_data.get("team_insights") or ""),
            competitive_landscape=_extract_text_from_field(structured_data.get("competitive_landscape") or ""),
            funding_info=structured_data.get("funding_info"),
            news_mentions=structured_data.get("news_mentions", []),
            social_presence=structured_data.get("social_presence"),
            technology_stack=_extract_text_from_field(structured_data.get("technology_stack") or ""),
            customer_base=_extract_text_from_field(structured_data.get("customer_base") or ""),
            
            # Enhanced Fields - Founders
            founders=founders,
            
            # Enhanced Fields - Product & Business
            product_description=structured_data.get("product_description") or "",
            unique_value_proposition=structured_data.get("unique_value_proposition") or "",
            technology_moat=structured_data.get("technology_moat") or "",
            business_model_details=structured_data.get("business_model_details") or "",
            revenue_model=structured_data.get("revenue_model") or "",
            pricing_strategy=structured_data.get("pricing_strategy") or "",
            
            # Enhanced Fields - Financials
            funding_raised=structured_data.get("funding_raised"),
            funding_ask_amount=structured_data.get("funding_ask_amount"),
            current_mrr=structured_data.get("current_mrr"),
            current_arr=structured_data.get("current_arr"),
            yoy_growth_rate=structured_data.get("yoy_growth_rate"),
            customer_acquisition_cost=structured_data.get("customer_acquisition_cost"),
            lifetime_value=structured_data.get("lifetime_value"),
            burn_rate=structured_data.get("burn_rate"),
            runway_months=int(structured_data.get("runway_months")) if structured_data.get("runway_months") else None,
            
            # Enhanced Fields - Traction
            key_metrics=structured_data.get("key_metrics") or {},
            total_customers=int(structured_data.get("total_customers")) if structured_data.get("total_customers") else None,
            active_users=int(structured_data.get("active_users")) if structured_data.get("active_users") else None,
            retention_rate=structured_data.get("retention_rate"),
            
            # Enhanced Fields - Market
            tam=structured_data.get("tam"),
            sam=structured_data.get("sam"),
            som=structured_data.get("som"),
            market_growth_rate=structured_data.get("market_growth_rate"),
            
            # Enhanced Fields - Additional
            partnerships=structured_data.get("partnerships", []) if isinstance(structured_data.get("partnerships"), list) else [],
            awards_recognition=structured_data.get("awards_recognition", []) if isinstance(structured_data.get("awards_recognition"), list) else [],
            investment_highlights=structured_data.get("investment_highlights", []) if isinstance(structured_data.get("investment_highlights"), list) else [],
            risk_factors=structured_data.get("risk_factors", []) if isinstance(structured_data.get("risk_factors"), list) else [],
            
            # Enhanced Fields - Competitors
            known_competitors=structured_data.get("known_competitors", []) if isinstance(structured_data.get("known_competitors"), list) else [],
            
            # AI Scorecard
            ai_scorecard=ai_scorecard
        )
        
        print("  ✓ Enhanced ResearchFindings object created")
        
        # Step 10: Log comprehensive summary
        print("\n📊 COMPREHENSIVE ANALYSIS SUMMARY:")
        print(f"   - Company: {research_findings.name}")
        print(f"   - Industry: {research_findings.industry}")
        print(f"   - Thesis Category: {research_findings.thesis_name}")
        print(f"   - Stage: {research_findings.startup_stage}")
        print(f"   - Employees: {research_findings.employee_count}")
        print(f"   - CEO: {research_findings.ceo_name}")
        print(f"   - Founders: {len(founders)} profiles")
        print(f"   - Funding Raised: ₹{research_findings.funding_raised:,.0f}" if research_findings.funding_raised else "   - Funding Raised: Not available")
        
        print("\n📈 AI SCORECARD:")
        print(f"   - Founders Score: {ai_scorecard.founders_score.score}/10 (25% weight)")
        print(f"   - Market Score: {ai_scorecard.market_score.score}/10 (20% weight)")
        print(f"   - Product Score: {ai_scorecard.product_score.score}/10 (15% weight)")
        print(f"   - Traction Score: {ai_scorecard.traction_score.score}/10 (20% weight)")
        print(f"   - Team Score: {ai_scorecard.team_score.score}/10 (10% weight)")
        print(f"   - Financials Score: {ai_scorecard.financials_score.score}/10 (10% weight)")
        print(f"   - Competition Score: {ai_scorecard.competition_score.score}/10")
        print(f"   - OVERALL SCORE: {ai_scorecard.overall_score}/10")
        print(f"   - RECOMMENDATION: {ai_scorecard.investment_recommendation}")
        
        print("\n✅ Node 4 Complete: Comprehensive LLM analysis completed successfully")
        print("="*60 + "\n")
        
        # Step 11: Return updated state with ResearchFindings
        return {
            "status": "structured_by_llm",
            "research_findings": research_findings
        }
    
    except Exception as e:
        print(f"\n❌ ERROR in Node 4: {str(e)}")
        import traceback
        traceback.print_exc()
        print("="*60 + "\n")
        
        return {
            "status": "error",
            "errors": [f"LLM structuring error: {str(e)}"]
        }