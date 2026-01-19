from langgraph.graph import StateGraph, END
from .state import GraphState
from .nodes.parse_pitch_deck import parse_pitch_deck_node
from .nodes.scrape_website import scrape_website_node
from .nodes.search_startup import search_startup_node
from .nodes.llm_structure import llm_structure_node
from .nodes.analyze_competitors import analyze_competitors_node
from .nodes.investment_thesis import generate_investment_thesis_node
from .nodes.startup_creation import startup_creation_node
from .nodes.startupApplication_creation import startup_application_creation_node
from .nodes.startupApplication_creation import startup_application_creation_node
from .nodes.upload_thesis import upload_thesis_node
from .nodes.pitchDeck_upload import pitch_deck_upload_node

def build_research_graph():
    """
    Build the complete LangGraph research workflow
    
    This function:
    1. Creates a StateGraph with GraphState
    2. Adds all 6 nodes
    3. Connects nodes in sequence
    4. Sets entry point
    5. Compiles the graph
    
    Returns:
        Compiled LangGraph ready to execute
        
    Flow:
        Node 1: Parse Pitch Deck
            ↓
        Node 2: Scrape Website
            ↓
        Node 3: Search Startup
            ↓
        Node 4: LLM Structure (with AI Scorecard)
            ↓
        Node 5: Analyze Competitors
            ↓
        Node 6: Generate Investment Thesis PDF
            ↓
        Node 7: Create Startup Entry
            ↓
        Node 8: Create Startup Application
            ↓
        Node 9: Upload Thesis PDF & Scores
            ↓
        Node 10: Upload Pitch Deck
            ↓
        END
    """
    
    print("\n📊 Building LangGraph Research Workflow...")
    print("="*60)
    
    # Step 1: Create StateGraph
    print("  Creating StateGraph...")
    graph = StateGraph(GraphState)
    print("  ✓ StateGraph created")
    
    # Step 2: Add all nodes
    print("  Adding nodes...")
    
    graph.add_node("parse_pitch_deck", parse_pitch_deck_node)
    print("    ✓ Node 1: Parse Pitch Deck added")
    
    graph.add_node("scrape_website", scrape_website_node)
    print("    ✓ Node 2: Scrape Website added")
    
    graph.add_node("search_startup", search_startup_node)
    print("    ✓ Node 3: Search Startup added")
    
    graph.add_node("llm_structure", llm_structure_node)
    print("    ✓ Node 4: LLM Structure (with AI Scorecard) added")
    
    graph.add_node("analyze_competitors", analyze_competitors_node)
    print("    ✓ Node 5: Analyze Competitors added")

    graph.add_node("generate_investment_thesis", generate_investment_thesis_node)
    print("    ✓ Node 6: Generate Investment Thesis PDF added")

    graph.add_node("startup_creation", startup_creation_node)
    print("    ✓ Node 7: Startup Creation added")

    graph.add_node("startup_application_creation", startup_application_creation_node)
    print("    ✓ Node 8: Startup Application Creation added")

    graph.add_node("upload_thesis", upload_thesis_node)
    print("    ✓ Node 9: Upload Thesis added")
    
    graph.add_node("pitch_deck_upload", pitch_deck_upload_node)
    print("    ✓ Node 10: Pitch Deck Upload added")
    
    # Step 3: Connect nodes in sequence (linear flow)
    print("  Connecting nodes...")
    
    graph.add_edge("parse_pitch_deck", "scrape_website")
    print("    ✓ Connected: parse_pitch_deck → scrape_website")
    
    graph.add_edge("scrape_website", "search_startup")
    print("    ✓ Connected: scrape_website → search_startup")
    
    graph.add_edge("search_startup", "llm_structure")
    print("    ✓ Connected: search_startup → llm_structure")
    
    graph.add_edge("llm_structure", "analyze_competitors")
    print("    ✓ Connected: llm_structure → analyze_competitors")
    
    graph.add_edge("analyze_competitors", "generate_investment_thesis")
    print("    ✓ Connected: analyze_competitors → generate_investment_thesis")

    graph.add_edge("generate_investment_thesis", "startup_creation")
    print("    ✓ Connected: generate_investment_thesis → startup_creation")

    graph.add_edge("startup_creation", "startup_application_creation")
    print("    ✓ Connected: startup_creation → startup_application_creation")

    graph.add_edge("startup_application_creation", "upload_thesis")
    print("    ✓ Connected: startup_application_creation → upload_thesis")

    graph.add_edge("upload_thesis", "pitch_deck_upload")
    print("    ✓ Connected: upload_thesis → pitch_deck_upload")

    graph.add_edge("pitch_deck_upload", END)
    print("    ✓ Connected: pitch_deck_upload → END")
    
    # Step 4: Set entry point
    print("  Setting entry point...")
    graph.set_entry_point("parse_pitch_deck")
    print("    ✓ Entry point set to: parse_pitch_deck")
    
    # Step 5: Compile graph
    print("  Compiling graph...")
    compiled_graph = graph.compile()
    print("    ✓ Graph compiled successfully")
    
    print("\n✅ LangGraph Research Workflow built successfully!")
    print("="*60 + "\n")
    
    return compiled_graph
__all__ = ["build_research_graph"]
