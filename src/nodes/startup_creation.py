import requests
import json
from ..state import GraphState
from ..config import Config

def startup_creation_node(state: GraphState) -> dict:
    print("🚀 NODE 7: CREATE STARTUP ENTRY")

    
    try:
        # Check if research findings exist
        if not state.research_findings:
            print("⚠️ No research findings available")
            return {
                "status": "skipped_api_entry",
                "errors": ["No research findings available for API entry"]
            }
            
        research_findings = state.research_findings
        startup_data = state.startup_data
        
        # Thesis ID Mapping
        THESIS_MAPPING = {
            "CONSUMER": "efa9a64e-da53-462b-9270-3fe4dc52ec91",
            "HEALTHCARE": "76adc22b-4d75-4263-9745-b1a49e1f7af1",
            "IMPACT_SDG": "6b596708-3c7a-47ea-80db-a869e7cd3b49",
            "SINGULARITY_AI": "74d241c1-c0b9-450d-926e-bef49d8e877e",
            "EMC": "d4a8f75b-272c-415e-b744-285e9eda4a04",
            "RUMS": "6ddbc09f-31ba-44b6-9100-ecfaafd056cc",
            "RETAIN": "ed011499-8d8e-4580-b8ad-6fbd2b6ce0dc",
            "OTHERS": "f1371624-94ab-4b47-8206-c6d776b2859a"
        }
        
        # Determine Thesis ID
        thesis_name = research_findings.thesis_name
        thesis_id = THESIS_MAPPING.get(thesis_name, THESIS_MAPPING["OTHERS"])
        
        # Prepare Payload
        print(f"  Preparing API payload for: {research_findings.name}")
        print(f"  Thesis: {thesis_name} -> ID: {thesis_id}")
        
        # Handle numeric fields
        # If DB is numeric, we should send numbers (int or float)
        # Using 0 as fallback for numeric fields
        funding_raised = 0
        if research_findings.funding_raised:
            try:
                funding_raised = int(research_findings.funding_raised)
            except (ValueError, TypeError):
                funding_raised = 0
                
        funding_ask = 0
        if research_findings.funding_ask_amount:
            try:
                funding_ask = int(research_findings.funding_ask_amount)
            except (ValueError, TypeError):
                funding_ask = 0
        
        payload = {
            "status": "DRAFT",
            "organizationId": Config.PLATFORM_ORG_ID,
            "evaluationStage": "APPLICATION_RECEIVED",
            "thesisId": thesis_id,
            "thesisName": thesis_name,
            "name": research_findings.name,
            "legalName": research_findings.legal_name or research_findings.name,
            "description": research_findings.description or "",
            "stage": research_findings.startup_stage or "EARLY_TRACTION",
            "location": research_findings.location or "",
            "website": research_findings.website or "",
            "companyEmail": research_findings.company_email or startup_data.email or "",
            "companyPhone": research_findings.company_phone or "",
            "ceoName": research_findings.ceo_name or "",
            "ceoEmail": research_findings.ceo_email or "",
            "ceoPhone": research_findings.ceo_phone or "",
            "ceoLinkedinUrl": research_findings.ceo_linkedin_url or "",
            "companyGoal": research_findings.company_goal or "",
            "startupIndustryDomain": research_findings.industry or "",
            "fundingRaised": funding_raised,
            "fundingAskAmount": funding_ask,
            "startupSource": "WEBSITE_INBOUND",
            "dataRoomGDriveLinkPrimary": state.pitch_deck_url or ""
        }
        url = "https://platform-be.dev.indiaaccelerator.live/v1/api/startup"
        
        api_key = Config.PLATFORM_API_KEY
        if not api_key:
            print("⚠️ Method Config.PLATFORM_API_KEY is not set in .env")
        
        headers = {
            'x-api-key': api_key, # Fallback removed
            'Content-Type': 'application/json'
        }
        
        print("  Sending POST request to API...")
        
        response = requests.post(url, headers=headers, json=payload)
        
        print(f"  API Response Status: {response.status_code}")
        
        if response.status_code == 200 or response.status_code == 201:
            print("  ✓ Startup entry created successfully")
            resp_data = response.json()
            
            # Try to extract startupId (handling potential variations)
            startup_id = resp_data.get("startupId") or resp_data.get("id") or resp_data.get("data", {}).get("id") or resp_data.get("data", {}).get("startupId")
            
            
            if startup_id:
                print(f"  ✓ Captured startupId: {startup_id}")
            else:
                print("  ⚠️ Could not find startupId in response structure")
                print(f"  Response keys: {resp_data.keys()}")
            
            return {
                "status": "startup_entry_created",
                "api_response": resp_data,
                "startup_id": startup_id
            }
        else:
            print(f"  ❌ API Error: {response.text}")
            return {
                "status": "api_error",
                "errors": [f"API Error {response.status_code}: {response.text}"]
            }

    except Exception as e:
        print(f"\n❌ ERROR in Node 7: {str(e)}")
        import traceback
        traceback.print_exc()
        print("="*60 + "\n")
        
        return {
            "status": "error",
            "errors": [f"Startup entry creation error: {str(e)}"]
        }