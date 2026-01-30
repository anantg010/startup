import requests
import json
from ..state import GraphState
from ..config import Config

def startup_application_creation_node(state: GraphState) -> dict:
    """
    Node 7: Create startup application in the platform backend API.
    
    This node:
    1. Checks for startup_id in state
    2. Prepares payload with static IDs and startup name
    3. Sends POST request to the API
    4. Captures application_id from response
    
    Args:
        state: Current GraphState with startup_id and research_findings
        
    Returns:
        dict: Updated state with api_status and application_id
    """
    
    print("\n" + "="*60)
    print("🚀 NODE 8: CREATE STARTUP APPLICATION")
    print("="*60)
    
    try:
        # Check if startup_id exists
        if not state.startup_id:
            print("⚠️ No startup_id available (previous step might have failed)")
            return {
                "status": "skipped_application_creation",
                "errors": ["No startup_id available for application creation"]
            }
            
        research_findings = state.research_findings
        startup_name = research_findings.name if research_findings else (state.startup_data.name if state.startup_data else "Unknown Startup")
        
        # Static IDs as requested
        PROGRAM_ID = Config.PLATFORM_PROGRAM_ID
        EVALUATION_STAGE_ID = Config.PLATFORM_EVALUATION_STAGE_ID
        STATUS = "SUBMITTED"
        
        # Prepare Payload
        print(f"  Preparing Application payload for: {startup_name}")
        print(f"  Startup ID: {state.startup_id}")
        
        payload = {
            "startupId": state.startup_id,
            "programId": PROGRAM_ID,
            "status": STATUS,
            "evaluationStageId": EVALUATION_STAGE_ID,
            "fullName": startup_name
        }
        
        # API Configuration
        url = "https://platform-be.dev.indiaaccelerator.live/v1/api/startup-application"
        
        api_key = Config.PLATFORM_API_KEY
        headers = {
            'x-api-key': api_key,
            'Content-Type': 'application/json'
        }
        
        print("  Sending POST request to API...")
        
        response = requests.post(url, headers=headers, json=payload)
        
        print(f"  API Response Status: {response.status_code}")
        
        if response.status_code == 200 or response.status_code == 201:
            print("  ✓ Startup Application created successfully")
            resp_data = response.json()
        
            application_id = resp_data.get("id") or resp_data.get("applicationId") or resp_data.get("data", {}).get("id")
            
            if application_id:
                print(f"  ✓ Captured application_id: {application_id}")
            else:
                print("  ℹ️ Application ID not explicitly found in top-level response keys")
            
            return {
                "status": "application_created",
                "api_response_app": resp_data,
                "application_id": application_id
            }
        else:
            print(f"  ❌ API Error: {response.text}")
            return {
                "status": "api_error_app",
                "errors": [f"Application API Error {response.status_code}: {response.text}"]
            }

    except Exception as e:
        print(f"\n❌ ERROR in Node 8: {str(e)}")
        import traceback
        traceback.print_exc()
        print("="*60 + "\n")
        
        return {
            "status": "error",
            "errors": [f"Startup application creation error: {str(e)}"]
        }