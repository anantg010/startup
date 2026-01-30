from ..state import GraphState, ExtractedPitchDeck, RawGatheringData
from ..tools.pdf_parser import PDFParser


async def parse_pitch_deck_node(state: GraphState) -> dict:
    """
    Node 1: Parse and extract data from pitch deck
    
    This node:
    1. Reads the pitch_deck_text from state
    2. Extracts key information using PDFParser
    3. Creates an ExtractedPitchDeck object
    4. Stores it in raw_gathering_data
    5. Returns updated state
    
    Args:
        state: Current GraphState with pitch_deck_text
        
    Returns:
        dict: Updated state with ExtractedPitchDeck
        
    Example:
        result = await parse_pitch_deck_node(state)
        print(result["status"])  # "pitch_deck_parsed"
    """
    
    try:
        print("\n" + "="*60)
        print("📄 NODE 1: PARSE PITCH DECK")
        print("="*60)
        
        # Step 1: Check for pitch deck input (Text OR URL)
        pitch_deck_input_found = False
        
        # Case A: URL provided
        # Case A: URL provided
        if state.pitch_deck_url and not state.pitch_deck_text:
            print(f"✓ Pitch deck URL found: {state.pitch_deck_url}")
            import os
            import requests # Import requests for direct download
            
            # Create temp directory ensuring it exists
            temp_dir = "temp_downloads"
            os.makedirs(temp_dir, exist_ok=True)
            output_path = os.path.join(temp_dir, "downloaded_pitch_deck.pdf")
            
            download_success = False
            
            # Direct download (e.g. Supabase, S3, etc.)
            print("  Downloading pitch deck from URL...")
            try:
                # Basic header to mimic browser if needed, though often not needed for public signed URLs
                # headers = {'User-Agent': 'Mozilla/5.0'} 
                response = requests.get(state.pitch_deck_url, stream=True)
                
                if response.status_code == 200:
                    with open(output_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    download_success = True
                    print("  ✓ Download successful")
                else:
                    print(f"  ❌ Download failed with status: {response.status_code}")
            except Exception as e:
                print(f"  ❌ Download error: {str(e)}")

            if download_success:
                # Use PDFParser to split text
                parser = PDFParser()
                # Need to run async method
                result = await parser.extract_text_from_path(output_path)
                
                if result['success']:
                    state.pitch_deck_text = result['full_text']
                    pitch_deck_input_found = True
                    print(f"  ✓ Extracted {len(state.pitch_deck_text)} chars from downloaded PDF")
                else:
                    print(f"  ❌ Extraction failed: {result.get('error')}")
            else:
                print("  ❌ Download failed or file empty")
        
        # Case B: Text already provided
        elif state.pitch_deck_text:
             print(f"✓ Pitch deck text directly provided ({len(state.pitch_deck_text)} characters)")
             pitch_deck_input_found = True
             
        if not pitch_deck_input_found:
            print("⚠️ No pitch deck provided (URL or Text)")
            print("Status: Skipping pitch deck parsing\n")
            
            return {
                "status": "no_pitch_deck",
                "raw_gathering_data": RawGatheringData()
            }
        
        # Step 2: Create PDFParser instance
        parser = PDFParser()
        
        # Step 3: Extract key information from pitch deck text
        print("  Extracting key phrases...")
        key_points = parser.extract_key_phrases(
            state.pitch_deck_text,
            num_phrases=15
        )
        print(f"  ✓ Found {len(key_points)} key phrases")
        
        # Step 4: Count slides (pages)
        slides_count = state.pitch_deck_text.count("--- Page")
        if slides_count == 0:
            slides_count = 1  # At least 1 slide
        
        print(f"  ✓ Estimated {slides_count} slides")
        
        # Step 5: Create ExtractedPitchDeck object
        print("  Creating ExtractedPitchDeck object...")
        extracted_pitch_deck = ExtractedPitchDeck(
            raw_text=state.pitch_deck_text,
            slides_count=slides_count,
            key_points=key_points
        )
        print("  ✓ ExtractedPitchDeck created")
        
        # Step 6: Create RawGatheringData with pitch deck data
        print("  Storing in raw_gathering_data...")
        raw_gathering_data = RawGatheringData(
            pitch_deck_extracted=extracted_pitch_deck,
            website_scraped=None,
            search_results=None
        )
        print("  ✓ Raw gathering data created")
        
        # Step 7: Log summary
        print("\n📊 PARSING SUMMARY:")
        print(f"   - Total characters: {len(state.pitch_deck_text)}")
        print(f"   - Estimated slides: {slides_count}")
        print(f"   - Key phrases extracted: {len(key_points)}")
        
        if key_points:
            print(f"   - Sample phrases:")
            for phrase in key_points[:3]:
                print(f"     • {phrase}")
        
        print("\n✅ Node 1 Complete: Pitch deck parsed successfully")
        print("="*60 + "\n")
        
        # Step 8: Return updated state
        return {
            "status": "pitch_deck_parsed",
            "raw_gathering_data": raw_gathering_data
        }
    
    except Exception as e:
        print(f"\n❌ ERROR in Node 1: {str(e)}")
        print("="*60 + "\n")
        
        return {
            "status": "error",
            "errors": [f"Pitch deck parsing error: {str(e)}"]
        }