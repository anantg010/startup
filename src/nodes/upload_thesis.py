import requests
import json
import os
from ..state import GraphState
from ..config import Config

def upload_thesis_node(state: GraphState) -> dict:

    print("\n" + "="*60)
    print("🚀 NODE 9: UPLOAD THESIS PDF & SCORES")
    print("="*60)
    
    try:
        # 1. Validation
        if not state.startup_id:
            print("⚠️ No startup_id available. Skipping upload.")
            return {"status": "skipped_upload_no_id"}
            
        if not state.thesis_pdf_path or not os.path.exists(state.thesis_pdf_path):
            print("⚠️ No thesis PDF found. Skipping upload.")
            return {"status": "skipped_upload_no_pdf"}
            
        if not state.research_findings or not state.research_findings.ai_scorecard:
            print("⚠️ No AI scorecard data found. Skipping upload.")
            return {"status": "skipped_upload_no_scores"}

        scorecard = state.research_findings.ai_scorecard
        
        # 2. Prepare Data Fields
        # Helper to join list strings
        def join_list(items):
            return ", ".join(items) if items else ""
            
        data_fields = {
            "startupId": state.startup_id,
            "overallScore": scorecard.overall_score,

            "foundersScore": scorecard.founders_score.score,
            "teamScore": scorecard.team_score.score,
            "tractionScore": scorecard.traction_score.score,
            "productScore": scorecard.product_score.score,
            "marketScore": scorecard.market_score.score,
            "financialsScore": scorecard.financials_score.score,

            "foundersStrengths": join_list(scorecard.founders_score.strengths),
            "foundersWeaknesses": join_list(scorecard.founders_score.weaknesses),
            
            "teamStrengths": join_list(scorecard.team_score.strengths),
            "teamWeaknesses": join_list(scorecard.team_score.weaknesses),
            
            "tractionStrengths": join_list(scorecard.traction_score.strengths),
            "tractionWeaknesses": join_list(scorecard.traction_score.weaknesses),
            
            "productStrengths": join_list(scorecard.product_score.strengths),
            "productWeaknesses": join_list(scorecard.product_score.weaknesses),
            
            "marketStrengths": join_list(scorecard.market_score.strengths),
            "marketWeaknesses": join_list(scorecard.market_score.weaknesses),
            
            "financialsStrengths": join_list(scorecard.financials_score.strengths),
            "financialsWeaknesses": join_list(scorecard.financials_score.weaknesses),
        } 
        
        print(f"  Preparing upload for Startup ID: {state.startup_id}")
        print(f"  PDF Path: {state.thesis_pdf_path}")
        print(f"  Overall Score: {data_fields['overallScore']}")
        
        # 3. API Request
        url = "https://platform-be.dev.indiaaccelerator.live/v1/api/ai-score"
        
        api_key = Config.PLATFORM_API_KEY
        headers = {
            'x-api-key': api_key
        }
        
        # open file in binary mode
        with open(state.thesis_pdf_path, 'rb') as f:
            files = {
                'file': ('ai-analysis.pdf', f, 'application/pdf')
            }
            
            print("  Sending POST request to Upload API...")
            response = requests.post(url, headers=headers, data=data_fields, files=files)
            
        print(f"  API Response Status: {response.status_code}")
        
        if response.status_code == 200 or response.status_code == 201:
            print("  ✓ Upload successful")
            try:
                print(f"  Response: {response.json()}")
            except:
                print(f"  Response: {response.text}")
                
            return {
                "status": "upload_complete",
                "upload_response": response.json() if response.text and response.text.strip().startswith('{') else response.text
            }
        else:
            print(f"  ❌ Upload Error: {response.text}")
            return {
                "status": "upload_error",
                "errors": [f"Upload API Error {response.status_code}: {response.text}"]
            }
            
    except Exception as e:
        print(f"\n❌ ERROR in Node 9: {str(e)}")
        import traceback
        traceback.print_exc()
        print("="*60 + "\n")
        
        return {
            "status": "error",
            "errors": [f"Upload error: {str(e)}"]
        }