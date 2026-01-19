
import asyncio
import json
import sys
import os
import codecs

# Add the project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, project_root)

from src.tools.pdf_parser import PDFParser
from src.graph import build_research_graph
from src.state import GraphState, StartupData

# Set stdout to UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

async def main():
    pdf_path = r"c:\Users\KIIT\OneDrive\Desktop\startup-research-agent\Foontro pitch Deck.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Error: File not found at {pdf_path}")
        return

    print("="*60)
    print(f"🚀 STARTING MANUAL RESEARCH FLOW")
    print(f"📄 Processing: {pdf_path}")
    print("="*60)

    # 1. Parse PDF (Simulating API behavior)
    print("\n[1/3] Parsing Pitch Deck...")
    parser = PDFParser()
    parse_result = await parser.extract_text_from_path(pdf_path)
    
    if not parse_result['success']:
        print(f"❌ Failed to parse PDF: {parse_result.get('error')}")
        return
        
    pitch_deck_text = parse_result['full_text']
    print(f"   ✓ Extracted {len(pitch_deck_text)} chars")

    # 2. Initialize State
    print("\n[2/3] Initializing Graph State...")
    # Using "Foontro" as the name since it's the pitch deck subject
    startup_data = StartupData(
        name="Foontro",
        description="Extracted from pitch deck",
        industry="Creator Economy" # Optional, but helpful context
    )
    
    initial_state = GraphState(
        startup_data=startup_data,
        pitch_deck_text=pitch_deck_text,
        pitch_deck_file_path=pdf_path,
        status="initialized"
    )
    
    # 3. Run Graph
    print(f"\n[3/3] Running Graph (This may take a few minutes)...")
    graph = build_research_graph()
    
    try:
        final_state = await graph.ainvoke(initial_state)
        
        print("\n" + "="*60)
        print("✅ WORKFLOW COMPLETED")
        print("="*60)
        
        # Output Findings
        findings = final_state.get("research_findings")
        if findings:
            print(f"\n📊 Research Findings for {findings.name}:")
            print(f"   - Industry: {findings.industry}")
            print(f"   - Stage: {findings.startup_stage}")
            print(f"   - Thesis: {findings.thesis_name}")
            print(f"   - Founders: {len(findings.founders)}")
            for f in findings.founders:
                print(f"     • {f.name} ({f.role})")
            
            if findings.ai_scorecard:
                print(f"\n📈 AI Scorecard:")
                print(f"   - Overall Score: {findings.ai_scorecard.overall_score}/10")
                print(f"   - Recommendation: {findings.ai_scorecard.investment_recommendation}")
                print(f"   - Summary: {findings.ai_scorecard.investment_summary[:150]}...")
            
            if final_state.get('thesis_pdf_path'):
                 print(f"\n📄 Thesis PDF generated: {final_state.get('thesis_pdf_path')}")
                 
            # Save findings to file for inspection
            output_file = "research_results.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(findings.model_dump(), f, indent=2, default=str)
            print(f"\n💾 Full results saved to {output_file}")
            
        else:
            print("\n❌ No research findings generated.")
            if final_state.get("errors"):
                print("Errors:", final_state.get("errors"))

    except Exception as e:
        print(f"\n❌ Execution Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
