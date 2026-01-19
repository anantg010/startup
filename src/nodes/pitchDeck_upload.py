import requests
import os
from ..state import GraphState
from ..config import Config

def pitch_deck_upload_node(state: GraphState) -> dict:
    print("\n" + "="*60)
    print("🚀 NODE 10: UPLOAD PITCH DECK")
    print("="*60)
    
    try:
        # 1. Validation
        if not state.startup_id:
            print("⚠️ No startup_id available. Skipping upload.")
            return {"status": "skipped_pitch_deck_upload_no_startup_id"}
            
        if not state.application_id:
            print("⚠️ No application_id available. Skipping upload.")
            return {"status": "skipped_pitch_deck_upload_no_app_id"}
            
        if not state.pitch_deck_file_path or not os.path.exists(state.pitch_deck_file_path):
            print("⚠️ No pitch deck file found in state.pitch_deck_file_path. Skipping upload.")
            return {"status": "skipped_pitch_deck_upload_no_file"}
            
        print(f"  Preparing upload for Startup ID: {state.startup_id}")
        print(f"  File Path: {state.pitch_deck_file_path}")
        
        # 2. API Request
        url = "https://platform-be.dev.indiaaccelerator.live/v1/api/n8n/startup-document"
        
        api_key = Config.PLATFORM_API_KEY
        headers = {
            'x-api-key': api_key or '0lf+JP0Y6B9x4Ylt9ICprNhQ/p4='
        }
        
        # open file in binary mode
        with open(state.pitch_deck_file_path, 'rb') as f:
            # Prepare multipart/form-data payload
            # requests takes 'files' and 'data'. 
            # 'files' handles the file upload. 'data' handles the form fields.
            
            files = {
                'file': ('pitch_deck.pdf', f, 'application/pdf')
            }
            
            data_fields = {
                "startupId": state.startup_id,
                "documentType": "PITCH_DECK",
                "startupApplicationId": state.application_id
            }
            
            print("  Sending POST request to Document Upload API...")
            response = requests.post(url, headers=headers, data=data_fields, files=files)
            
        print(f"  API Response Status: {response.status_code}")
        
        if response.status_code == 200 or response.status_code == 201:
            print("  ✓ Pitch deck upload successful")
            try:
                print(f"  Response: {response.json()}")
            except:
                print(f"  Response: {response.text}")
                
            return {
                "status": "pitch_deck_upload_complete",
                "pitch_deck_upload_response": response.json() if response.text and response.text.strip().startswith('{') else response.text
            }
        else:
            print(f"  ❌ Upload Error: {response.text}")
            return {
                "status": "pitch_deck_upload_error",
                "errors": [f"Pitch Deck Upload API Error {response.status_code}: {response.text}"]
            }
            
    except Exception as e:
        print(f"\n❌ ERROR in Node 10: {str(e)}")
        import traceback
        traceback.print_exc()
        print("="*60 + "\n")
        
        return {
            "status": "error",
            "errors": [f"Pitch deck upload error: {str(e)}"]
        }
