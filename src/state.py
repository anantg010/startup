from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from datetime import datetime

class ExtractedPitchDeck(BaseModel):
    """Extracted content from pitch deck PDF"""
    raw_text: str = Field("", description="Full extracted text from PDF")
    key_points: List[str] = Field(default_factory=list, description="Key points extracted")


class ScrapedWebsiteData(BaseModel):
    """Data scraped from startup website"""
    page_title: str = Field("", description="Website page title")
    page_description: str = Field("", description="Meta description from website")
    main_content: str = Field("", description="Main page content/text")
    technologies_detected: List[str] = Field(default_factory=list, description="Tech stack detected")


class SerpAPIResults(BaseModel):
    """Search results from SerpAPI"""   
    search_query: str = Field("", description="What was searched for")
    search_results: Dict = Field(default_factory=dict, description="Search results from Google")
    news_articles: List[dict] = Field(default_factory=list, description="News articles about startup")


class RawGatheringData(BaseModel):
    """All raw data gathered before LLM processing"""
    pitch_deck_extracted: Optional[ExtractedPitchDeck] = Field(None, description="Data from pitch deck")
    website_scraped: Optional[ScrapedWebsiteData] = Field(None, description="Data from website")
    search_results: Optional[SerpAPIResults] = Field(None, description="Search results")


# ==================== Founder Profile Model ====================

class FounderProfile(BaseModel):
    """Detailed founder information"""
    name: str = Field("", description="Founder name")
    role: str = Field("", description="Role in company (CEO, CTO, etc.)")
    linkedin_url: str = Field("", description="LinkedIn profile URL")
    education: List[str] = Field(default_factory=list, description="Educational background")
    previous_companies: List[str] = Field(default_factory=list, description="Previous companies worked at")
    previous_exits: List[str] = Field(default_factory=list, description="Previous startup exits or acquisitions")
    years_experience: int = Field(0, description="Years of relevant experience")
    domain_expertise: str = Field("", description="Domain expertise and specializations")
    notable_achievements: List[str] = Field(default_factory=list, description="Notable achievements")


# ==================== AI Scorecard Models ====================

class ScoreDetail(BaseModel):
    """Individual score with justification"""
    score: float = Field(0.0, description="Score from 0-10")
    max_score: float = Field(10.0, description="Maximum possible score")
    weight: float = Field(0.0, description="Weight in overall score (0-1)")
    justification: str = Field("", description="Reasoning for this score")
    strengths: List[str] = Field(default_factory=list, description="Strengths identified")
    weaknesses: List[str] = Field(default_factory=list, description="Weaknesses identified")


class AIScorecard(BaseModel):
    """AI-generated scorecard for startup evaluation"""
    # Individual Scores (7 parameters)
    founders_score: ScoreDetail = Field(default_factory=ScoreDetail, description="Founders evaluation (25% weight)")
    market_score: ScoreDetail = Field(default_factory=ScoreDetail, description="Market evaluation (20% weight)")
    product_score: ScoreDetail = Field(default_factory=ScoreDetail, description="Product evaluation (15% weight)")
    traction_score: ScoreDetail = Field(default_factory=ScoreDetail, description="Traction evaluation (20% weight)")
    team_score: ScoreDetail = Field(default_factory=ScoreDetail, description="Team evaluation (10% weight)")
    financials_score: ScoreDetail = Field(default_factory=ScoreDetail, description="Financials evaluation (10% weight)")
    competition_score: ScoreDetail = Field(default_factory=ScoreDetail, description="Competition evaluation")
    
    # Overall Score and Recommendation
    overall_score: float = Field(0.0, description="Weighted average score (0-10)")
    investment_recommendation: str = Field(
        "", 
        description="Investment recommendation",
        json_schema_extra={
            "enum": ["STRONG_BUY", "BUY", "HOLD", "PASS"]
        }
    )
    investment_summary: str = Field("", description="Brief investment summary")
    key_risks: List[str] = Field(default_factory=list, description="Key risks identified")
    key_opportunities: List[str] = Field(default_factory=list, description="Key opportunities identified")


# ==================== Startup Information Model ====================

class StartupData(BaseModel):
    """
    Startup information provided via API/form
    This is the basic information about the startup
    """
    name: str = Field(..., description="Company name")
    legal_name: Optional[str] = Field(None, description="Legal company name")
    industry: Optional[str] = Field(None, description="Industry/domain (e.g., AI, HealthTech)")
    description: Optional[str] = Field(None, description="Company overview/description")
    email: Optional[str] = Field(None, description="Contact email")
    website: Optional[str] = Field(None, description="Company website URL")
    founders: Optional[str] = Field(None, description="Founders names (comma separated)")
    stage: Optional[str] = Field(None, description="Funding stage (e.g., Seed, Series A)")
    team_size: Optional[int] = Field(None, description="Number of employees")
    founded_year: Optional[int] = Field(None, description="Year company was founded")
    location: Optional[str] = Field(None, description="Company headquarters location")
    ceo_linkedin_url: Optional[str] = Field(None, description="CEO LinkedIn profile URL")


# ==================== Research Findings Model ====================

class ResearchFindings(BaseModel):
    """
    Structured research findings from web research
    Contains analyzed data about the startup
    """
    # Basic Startup Information
    name: str = Field("", description="Name of the startup")
    legal_name: str = Field("", description="Legal name of the startup")
    description: str = Field("", description="About the startup")
    location: str = Field("", description="Startup headquarters location")
    website: str = Field("", description="Company website URL")
    company_email: Optional[str] = Field(None, description="Company email address")
    company_phone: Optional[str] = Field(None, description="Company phone number")
    industry: str = Field("", description="Industry of the startup")
    startup_industry_domain: str = Field("", description="Startup industry domain")

    # Thesis Classification
    thesis_name: str = Field(
        "OTHERS",
        description="Thesis category",
        json_schema_extra={
            "enum": [
                "CONSUMER",
                "HEALTHCARE",
                "IMPACT_SDG",
                "SINGULARITY_AI",
                "EMC",
                "RUMS",
                "RETAIN",
                "OTHERS"
            ]
        }
    )
    
    # Startup Stage Classification
    startup_stage: str = Field(
        "",
        description="Phase of development based on product maturity, market validation, customer traction, and financial growth",
        json_schema_extra={
            "enum": [
                "IDEA",
                "MVP",
                "EARLY_TRACTION",
                "GROWTH",
                "SCALE_UP",
                "EXPANSION_LATE_STAGE"
            ]
        }
    )
    
    # CEO Information
    ceo_name: str = Field("", description="CEO name")
    ceo_email: str = Field("", description="CEO email")
    ceo_phone: str = Field("", description="CEO phone number")
    ceo_linkedin_url: str = Field("", description="CEO LinkedIn URL")
    
    # Company Details
    company_goal: str = Field("", description="Company's main goal and vision")
    employee_count: int = Field(0, description="Number of employees")
    
    # Funding Information
    funding_raised: Optional[float] = Field(None, description="Total funding raised in numeric value (INR)")
    funding_ask_amount: Optional[float] = Field(None, description="Funding ask amount in numeric value (INR)")
    
    # Analysis Fields
    company_info: Dict = Field(default_factory=dict, description="Company background information")
    market_analysis: str = Field("", description="Market opportunity and size analysis")
    team_insights: str = Field("", description="Team background and experience analysis")
    competitive_landscape: str = Field("", description="Competitors and competitive advantages")
    funding_info: Optional[Dict] = Field(None, description="Funding history and details")
    news_mentions: List[str] = Field(default_factory=list, description="Recent news articles")
    social_presence: Optional[Dict] = Field(None, description="Social media information")
    technology_stack: Optional[str] = Field(None, description="Technology stack used")
    customer_base: Optional[str] = Field(None, description="Customer information")
    
    # ===== ENHANCED FIELDS =====
    
    # Detailed Founder Profiles
    founders: List[FounderProfile] = Field(default_factory=list, description="Detailed founder profiles")
    
    # Product & Business Details
    product_description: str = Field("", description="Detailed product/service description")
    unique_value_proposition: str = Field("", description="What makes the product unique")
    technology_moat: str = Field("", description="Technological advantages and IP")
    business_model_details: str = Field("", description="Detailed business model explanation")
    revenue_model: str = Field("", description="How the company makes money")
    pricing_strategy: str = Field("", description="Pricing information")
    
    # Financial Metrics
    current_mrr: Optional[float] = Field(None, description="Monthly Recurring Revenue")
    current_arr: Optional[float] = Field(None, description="Annual Recurring Revenue")
    yoy_growth_rate: Optional[float] = Field(None, description="Year over year growth rate %")
    customer_acquisition_cost: Optional[float] = Field(None, description="CAC")
    lifetime_value: Optional[float] = Field(None, description="LTV")
    burn_rate: Optional[float] = Field(None, description="Monthly burn rate")
    runway_months: Optional[int] = Field(None, description="Runway in months")
    
    # Traction & Metrics
    key_metrics: Dict = Field(default_factory=dict, description="Key performance metrics")
    total_customers: Optional[int] = Field(None, description="Total number of customers")
    active_users: Optional[int] = Field(None, description="Number of active users")
    retention_rate: Optional[float] = Field(None, description="Customer retention rate %")
    
    # Market Details
    tam: Optional[float] = Field(None, description="Total Addressable Market in INR")
    sam: Optional[float] = Field(None, description="Serviceable Addressable Market in INR")
    som: Optional[float] = Field(None, description="Serviceable Obtainable Market in INR")
    market_growth_rate: Optional[float] = Field(None, description="Market growth rate %")
    
    # Additional Details
    partnerships: List[str] = Field(default_factory=list, description="Notable partnerships")
    awards_recognition: List[str] = Field(default_factory=list, description="Awards and recognition")
    investment_highlights: List[str] = Field(default_factory=list, description="Key investment highlights")
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk factors")
    
    # AI Scorecard
    ai_scorecard: Optional[AIScorecard] = Field(None, description="AI-generated scorecard")
    
    # Enhanced Competitor Data
    known_competitors: List[str] = Field(default_factory=list, description="List of competitors extracted from source documents")


class Competitor(BaseModel):
    """Individual competitor information"""
    name: str = Field("", description="Competitor company name")
    founded_year: Optional[int] = Field(None, description="Year company was founded")
    headquarters: str = Field("", description="Headquarters location")
    funding_raised: Optional[float] = Field(None, description="Total funding raised (in INR)")
    current_valuation: Optional[float] = Field(None, description="Current valuation (in INR)")
    revenue: Optional[float] = Field(None, description="Annual revenue (in INR)")
    business_model: str = Field("", description="How the company makes money")
    focus_market: str = Field("", description="Primary target market/customers")
    traction: str = Field("", description="Current traction, growth metrics, customer count")
    similarities: str = Field("", description="Similarities with the startup in focus")


class CompetitorAnalysis(BaseModel):
    """Complete competitor analysis for a startup"""
    startup_name: str = Field("", description="Name of the startup being analyzed")
    competitors: List[Competitor] = Field(default_factory=list, description="List of 5 competitors")
    market_overview: str = Field("", description="Overall market landscape and competitive position")
    competitive_advantages: str = Field("", description="What sets the focused startup apart")
    market_threats: str = Field("", description="Competitive threats and challenges")


# ==================== Main Graph State ====================

class GraphState(BaseModel):
    """
    Main state object for the LangGraph workflow
    This state flows through all nodes and gets updated at each step
    """
    
    # ===== INPUT DATA =====
    startup_data: StartupData = Field(..., description="Input startup data from API")
    pitch_deck_text: Optional[str] = Field(None, description="Extracted text from pitch deck PDF")
    pitch_deck_url: Optional[str] = Field(None, description="Google Drive URL for pitch deck")
    pitch_deck_file_path: Optional[str] = Field(None, description="Local path to uploaded pitch deck file")
    
    # ===== RAW DATA GATHERING =====
    raw_gathering_data: Optional[RawGatheringData] = Field(
        None, 
        description="Raw data collected from PDF, website, and search"
    )
    
    # ===== PROCESSING DATA =====
    research_findings: Optional[ResearchFindings] = Field(None, description="Processed research findings")
    structured_data: Optional[Dict] = Field(None, description="Structured data from LLM")
    
    # ===== WORKFLOW METADATA =====
    status: str = Field("initialized", description="Current workflow status")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")
    started_at: datetime = Field(default_factory=datetime.now, description="When workflow started")
    completed_at: Optional[datetime] = Field(None, description="When workflow completed")
    
    # ===== COMPETITOR ANALYSIS =====
    competitor_analysis: Optional[CompetitorAnalysis] = Field(None, description="Competitor analysis with 5 competitors")
    
    # ===== OUTPUT FILES =====
    thesis_pdf_path: Optional[str] = Field(None, description="Path to generated investment thesis PDF")
    
    # ===== API INTEGRATION =====
    startup_id: Optional[str] = Field(None, description="ID of the created startup from API")
    application_id: Optional[str] = Field(None, description="ID of the created application from API")


# ==================== Helper Functions ====================

def create_initial_state(startup_data: Dict) -> GraphState:
    """
    Create an initial graph state from startup data dictionary
    
    Args:
        startup_data: Dictionary with startup information
        
    Returns:
        GraphState: Initial state object ready for workflow
        
    Example:
        data = {
            "name": "TechCorp",
            "industry": "AI",
            "description": "AI startup",
            "email": "contact@techcorp.com"
        }
        state = create_initial_state(data)
    """
    startup = StartupData(**startup_data)
    return GraphState(startup_data=startup)


def add_error(state: GraphState, error: str) -> GraphState:
    """
    Add an error message to the state
    
    Args:
        state: Current graph state
        error: Error message to add
        
    Returns:
        GraphState: Updated state with error added
        
    Example:
        state = add_error(state, "Website scraping failed")
    """
    state.errors.append(error)
    return state