from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import os
from io import BytesIO
from datetime import datetime
from typing import Optional
from .state import GraphState, StartupData
from .graph import build_research_graph
from .tools.pdf_parser import PDFParser

# Initialize FastAPI app
app = FastAPI(
    title="Startup Research Agent API",
    description="AI-powered startup research and analysis",
    version="1.0.0"
)

# Add CORS middleware (allows requests from anywhere)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Build graph once at startup
print("🚀 Initializing Startup Research Agent API...")
research_graph = build_research_graph()
print("✅ API initialized successfully!\n")


@app.get("/")
async def root():
    """
    Root endpoint - API information
    """
    return {
        "status": "online",
        "service": "Startup Research Agent",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "research": "/research-startup",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    Returns API status
    """
    return {
        "status": "healthy",
        "service": "Startup Research Agent",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/research-startup")
async def research_startup(
    name: str = Form(...),
    industry: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    legal_name: Optional[str] = Form(None),
    website: Optional[str] = Form(None),
    founders: Optional[str] = Form(None),
    stage: Optional[str] = Form(None),
    team_size: Optional[int] = Form(None),
    founded_year: Optional[int] = Form(None),
    location: Optional[str] = Form(None),
    ceo_linkedin_url: Optional[str] = Form(None),
    google_drive_link: Optional[str] = Form(None),
    pitch_deck: Optional[UploadFile] = File(None)
):
    try:
        print("\n" + "="*60)
        print("📥 NEW REQUEST RECEIVED")
        print("="*60)
        print(f"Startup: {name}")
        print(f"Industry: {industry}")
        print(f"Email: {email}")
        
        # Step 1: Extract pitch deck if uploaded
        pitch_deck_text = None
        
        if pitch_deck:
            print(f"\n📄 Processing pitch deck: {pitch_deck.filename}")
            try:
                pdf_content = await pitch_deck.read()
                print(f"   Pitch deck size: {len(pdf_content)} bytes")
                
                # Use PDFParser to extract text
                parser = PDFParser()
                parse_result = await parser.extract_text_from_bytes(pdf_content)
                
                if parse_result.get("success"):
                    pitch_deck_text = parse_result.get("full_text", "")
                    print(f"   ✓ Extracted {len(pitch_deck_text)} characters from PDF")
                else:
                    error = parse_result.get("error", "Unknown error")
                    print(f"   ⚠️ Failed to parse PDF: {error}")
                    # Continue without pitch deck
            
            except Exception as e:
                print(f"   ⚠️ Error processing pitch deck: {str(e)}")
                # Continue without pitch deck
        
        elif google_drive_link:
            print(f"\n🔗 Google Drive Link received: {google_drive_link}")
            
        # Extract pitch_deck path if saved
        pitch_deck_path = None
        if pitch_deck:
             # Create uploads directory if not exists
            upload_dir = "uploads"
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            
            # Save file
            file_path = f"{upload_dir}/{pitch_deck.filename}"
            with open(file_path, "wb") as buffer:
                # Reset cursor if read previously
                await pitch_deck.seek(0)
                buffer.write(await pitch_deck.read())
            
            pitch_deck_path = file_path
            print(f"   ✓ Saved pitch deck to: {pitch_deck_path}")
        
        # Step 2: Create startup data
        print("\n📝 Creating startup data...")
        
        startup_data = StartupData(
            name=name,
            legal_name=legal_name or name,
            industry=industry,
            description=description,
            email=email,
            website=website,
            founders=founders,
            stage=stage,
            team_size=team_size,
            founded_year=founded_year,
            location=location,
            ceo_linkedin_url=ceo_linkedin_url
        )
        
        print("   ✓ Startup data created")
        
        # Step 3: Create initial state
        print("📊 Creating initial GraphState...")
        
        initial_state = GraphState(
            startup_data=startup_data,
            pitch_deck_text=pitch_deck_text,
            pitch_deck_url=google_drive_link,
            pitch_deck_file_path=os.path.abspath(pitch_deck_path) if pitch_deck_path else None,
            status="initialized"
        )
        
        print("   ✓ GraphState created")
        
        # Step 4: Run the research workflow
        print("\n🚀 Running research workflow...")
        print("   This will execute all 4 nodes...")
        
        result = await research_graph.ainvoke(initial_state)
        
        print("   ✓ Workflow completed")
        
        # Step 5: Check for errors
        if result.get("errors"):
            print(f"\n⚠️ Errors encountered:")
            for error in result.get("errors", []):
                print(f"   - {error}")
        
        # Step 6: Prepare response
        print("\n📤 Preparing response...")
        
        research_findings = result.get("research_findings")
        thesis_pdf_path = result.get("thesis_pdf_path")
        competitor_analysis = result.get("competitor_analysis")
        
        # Debug: Print what we got from the graph
        print(f"   Debug - research_findings: {'Yes' if research_findings else 'No'}")
        print(f"   Debug - thesis_pdf_path: {thesis_pdf_path}")
        print(f"   Debug - competitor_analysis: {'Yes' if competitor_analysis else 'No'}")
        
        if research_findings:
            # Convert to dict for JSON serialization
            findings_dict = research_findings.model_dump()
            
            # Get AI scorecard data if available
            ai_scorecard_dict = None
            if research_findings.ai_scorecard:
                ai_scorecard_dict = research_findings.ai_scorecard.model_dump()
                print(f"   Debug - AI Scorecard overall score: {research_findings.ai_scorecard.overall_score}")
            
            # Get competitor analysis if available
            competitor_dict = None
            if competitor_analysis:
                competitor_dict = competitor_analysis.model_dump()
                print(f"   Debug - Competitors found: {len(competitor_analysis.competitors)}")
            
            response = {
                "status": "success",
                "startup_name": name,
                "workflow_status": result.get("status"),
                "research_findings": findings_dict,
                "ai_scorecard": ai_scorecard_dict,
                "competitor_analysis": competitor_dict,
                "thesis_pdf_path": thesis_pdf_path,
                "timestamp": datetime.now().isoformat(),
                "errors": result.get("errors", [])
            }
            
            print("   ✓ Response prepared")
            if thesis_pdf_path:
                print(f"   ✓ PDF generated at: {thesis_pdf_path}")
            print("\n" + "="*60)
            print("✅ REQUEST COMPLETED SUCCESSFULLY")
            print("="*60 + "\n")
            
            return JSONResponse(
                status_code=200,
                content=response
            )
        
        else:
            print("   ⚠️ No research findings generated")
            
            response = {
                "status": "error",
                "startup_name": name,
                "workflow_status": result.get("status"),
                "message": "Failed to generate research findings",
                "errors": result.get("errors", []),
                "timestamp": datetime.now().isoformat()
            }
            
            print("\n" + "="*60)
            print("❌ REQUEST FAILED")
            print("="*60 + "\n")
            
            return JSONResponse(
                status_code=500,
                content=response
            )
     
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        
        print("\n" + "="*60)
        print("❌ REQUEST FAILED WITH EXCEPTION")
        print("="*60 + "\n")
        
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "startup_name": name,
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@app.get("/test")
async def test_endpoint():
    """
    Simple test endpoint to verify API is working
    """
    return {
        "status": "working",
        "message": "API is running correctly",
        "next_steps": "POST to /research-startup with startup data"
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "details": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*60)
    print("🚀 STARTING STARTUP RESEARCH AGENT API")
    print("="*60)
    print("\nAPI Documentation: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/health")
    print("Root: http://localhost:8000/")
    print("\nPress Ctrl+C to stop\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )