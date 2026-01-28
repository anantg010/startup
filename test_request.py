import requests
import sys

def test_research_startup():
    url = "http://localhost:8000/research-startup"
    
    # Sample data mimicking a real startup request
    payload = {
        "name": "EcoCharge Solutions",
        "industry": "Clean Energy / EV Charging",
        "description": "EcoCharge Solutions provides AI-optimized charging stations for electric vehicles that reduce grid load and lower costs for operators. We use machine learning to predict peak demand and adjust charging rates accordingly.",
        "stage": "Seed",
        "location": "Austin, Texas",
        "website": "www.ecocharge-example.com",
        "founded_year": 2024,
        "team_size": 12
    }

    print(f"🚀 Sending test request to {url}...")
    print(f"📝 Startup: {payload['name']}")
    
    try:
        response = requests.post(url, data=payload)
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Success!")
            print(f"Status: {result.get('status')}")
            
            pdf_path = result.get('thesis_pdf_path')
            if pdf_path:
                print(f"\n📄 PDF Generated at: {pdf_path}")
                print("Please open this file to verify the L1 Call Recommendation placement.")
            else:
                print("\n⚠️ No PDF path returned in response.")
        else:
            print(f"\n❌ Error: Status Code {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to the server.")
        print("Make sure the API server is running (python src/api.py)")

if __name__ == "__main__":
    test_research_startup()
