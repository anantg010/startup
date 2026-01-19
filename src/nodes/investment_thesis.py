from ..state import GraphState
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import HorizontalBarChart
from reportlab.graphics import renderPDF
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import datetime
import os
import json
def get_score_color(score):
    """Return color based on score value"""
    if score >= 8.0:
        return colors.HexColor('#22c55e')  # Green
    elif score >= 6.5:
        return colors.HexColor('#3b82f6')  # Blue
    elif score >= 5.0:
        return colors.HexColor('#f59e0b')  # Amber
    else:
        return colors.HexColor('#ef4444')  # Red


def get_recommendation_color(recommendation):
    """Return color based on recommendation"""
    color_map = {
        "STRONG_BUY": colors.HexColor('#22c55e'),
        "BUY": colors.HexColor('#3b82f6'),
        "HOLD": colors.HexColor('#f59e0b'),
        "PASS": colors.HexColor('#ef4444')
    }
    return color_map.get(recommendation, colors.grey)


def format_currency(value):
    """Format number as currency string"""
    if value is None:
        return "Not disclosed"
    try:
        value = float(value)
        if value >= 1e9:
            return f"${value/1e9:.2f}B"
        elif value >= 1e6:
            return f"${value/1e6:.2f}M"
        elif value >= 1e3:
            return f"${value/1e3:.1f}K"
        else:
            return f"${value:,.0f}"
    except (TypeError, ValueError):
        return "Not disclosed"


def clean_text_field(value) -> str:
    """
    Clean a text field that might contain JSON or be empty.
    Returns clean plain text suitable for PDF display.
    """
    if value is None:
        return ""
    
    if not isinstance(value, str):
        if isinstance(value, dict):
            # Extract text from dict values
            text_parts = []
            for k, v in value.items():
                if isinstance(v, str) and v and k not in ['tam', 'sam', 'som', 'market_growth_rate']:
                    text_parts.append(str(v))
            return " ".join(text_parts)
        elif isinstance(value, list):
            return ", ".join(str(item) for item in value if item)
        return str(value) if value else ""
    
    # If it starts with { it might be JSON
    text = value.strip()
    if text.startswith('{'):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                text_parts = []
                for k, v in parsed.items():
                    if isinstance(v, str) and v and k not in ['tam', 'sam', 'som', 'market_growth_rate']:
                        text_parts.append(str(v))
                return " ".join(text_parts) if text_parts else ""
        except json.JSONDecodeError:
            pass
    
    return text


def create_bullet_points(text, style):
    """Convert text string into a list of bullet point Paragraphs"""
    if not text:
        return []
    
    # If text is very short/simple and looks like a single item, return as one bullet
    if len(text) < 100 and '.' not in text and '\n' not in text:
        return [Paragraph(f"• {text}", style)]
        
    # Split by clear delimiters first
    if '\n' in text:
        items = [t.strip() for t in text.split('\n') if t.strip()]
    elif '•' in text:
        items = [t.strip() for t in text.split('•') if t.strip()]
    elif '-' in text and text.count('- ') > 1:
         items = [t.strip() for t in text.split('- ') if t.strip()]
    else:
        # Fallback: split by sentences for long text
        # We assume sentences end with ". "
        items = [t.strip() + "." for t in text.split('. ') if t.strip()]
        # Remove double periods if we added one to a string that already had it
        items = [t[:-1] if t.endswith('..') else t for t in items]
        
    bullets = []
    for item in items:
        # Remove existing bullet markers if any
        clean_item = item.lstrip('•- ').strip()
        if clean_item:
            bullets.append(Paragraph(f"• {clean_item}", style))
    return bullets


async def generate_investment_thesis_node(state: GraphState) -> dict:
    """
    Node 6: Generate Enhanced Investment Thesis PDF with AI Scorecard
    
    This node:
    1. Reads research_findings (with AI Scorecard) and competitor_analysis from state
    2. Extracts all detailed data including scores
    3. Creates a professional PDF document with:
       - Executive Summary
       - AI Scorecard visualization
       - Detailed founder profiles
       - Market analysis
       - Product deep dive
       - Traction metrics
       - Financial details
       - Competitor analysis
       - Investment recommendation
    4. Saves it to outputs folder
    5. Returns path to the generated PDF
    
    Args:
        state: Current GraphState with research_findings and competitor_analysis
        
    Returns:
        dict: Updated state with pdf_path
        
    Example:
        result = await generate_investment_thesis_node(state)
        print(result["status"])  # "thesis_pdf_generated"
    """
    
    try:
        print("\n" + "="*60)
        print("📄 NODE 6: GENERATE ENHANCED INVESTMENT THESIS PDF")
        print("="*60)
        
        # Step 1: Check if research findings exist
        if not state.research_findings:
            print("⚠️ No research findings available")
            print("Status: Cannot generate PDF without research data\n")
            
            return {
                "status": "no_research_findings",
                "thesis_pdf_path": None
            }
        
        research_findings = state.research_findings
        competitor_analysis = state.competitor_analysis
        ai_scorecard = research_findings.ai_scorecard
        startup_data = state.startup_data  # Access API input for fallback values
        
        print(f"✓ Generating enhanced PDF for: {research_findings.name}")
        
        # Debug: Print what data we have
        print("\n📊 DEBUG - Data Available:")
        print(f"   - Name: {research_findings.name}")
        print(f"   - Description: {len(research_findings.description) if research_findings.description else 0} chars")
        print(f"   - Industry: {research_findings.industry}")
        print(f"   - Stage: {research_findings.startup_stage}")
        print(f"   - Location: {research_findings.location}")
        print(f"   - Employee Count: {research_findings.employee_count}")
        print(f"   - CEO Name: {research_findings.ceo_name}")
        print(f"   - Founders: {len(research_findings.founders) if research_findings.founders else 0}")
        print(f"   - Product Description: {len(research_findings.product_description) if research_findings.product_description else 0} chars")
        print(f"   - Market Analysis: {len(research_findings.market_analysis) if research_findings.market_analysis else 0} chars")
        print(f"   - Team Insights: {len(research_findings.team_insights) if research_findings.team_insights else 0} chars")
        print(f"   - Funding Raised: {research_findings.funding_raised}")
        print(f"   - Current MRR: {research_findings.current_mrr}")
        print(f"   - TAM: {research_findings.tam}")
        
        if ai_scorecard:
            print(f"   - AI Scorecard: Yes (score: {ai_scorecard.overall_score})")
        else:
            print(f"   - AI Scorecard: No")
            
        if competitor_analysis:
            print(f"   - Competitors: {len(competitor_analysis.competitors)}")
        else:
            print(f"   - Competitors: No")
        
        # Step 2: Create output directory if it doesn't exist
        output_dir = "outputs"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"  ✓ Created output directory: {output_dir}")
        
        # Step 3: Create PDF filename
        startup_name_clean = research_findings.name.replace(" ", "_").replace("/", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"{output_dir}/Investment_Thesis_{startup_name_clean}_{timestamp}.pdf"
        
        print(f"  ✓ PDF path: {pdf_filename}")
        
        # Step 4: Create PDF document
        print("  Creating enhanced PDF document...")
        
        doc = SimpleDocTemplate(
            pdf_filename,
            pagesize=letter,
            rightMargin=0.6*inch,
            leftMargin=0.6*inch,
            topMargin=0.6*inch,
            bottomMargin=0.6*inch
        )
        
        # Step 5: Define styles
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#000000'),
            spaceAfter=16,
            spaceBefore=12,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER
        )
        
        graph_heading_style = ParagraphStyle(
            'GraphHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#000000'),
            spaceAfter=6,
            spaceBefore=12,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER
        )
        
        subheading_style = ParagraphStyle(
            'SubHeading',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=10,
            spaceBefore=8,
            fontName='Helvetica-Bold'
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_JUSTIFY,
            spaceAfter=6
        )
        
        bullet_style = ParagraphStyle(
            'BulletPoint',
            parent=styles['Normal'],
            fontSize=10,
            leftIndent=15,
            firstLineIndent=-10,
            spaceAfter=8,
            alignment=TA_LEFT
        )
        
        label_style = ParagraphStyle(
            'Label',
            parent=styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#2e5c8a'),
            spaceAfter=10,
            spaceBefore=6
        )
        
        score_style = ParagraphStyle(
            'Score',
            parent=styles['Normal'],
            fontSize=18,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER
        )
        
        # Step 6: Build document elements
        elements = []
        
        # ==================== TITLE PAGE ====================
        elements.append(Paragraph(f"Investment Thesis", title_style))
        elements.append(Paragraph(f"<b>{research_findings.name}</b>", ParagraphStyle(
            'CompanyName',
            parent=styles['Heading1'],
            fontSize=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#000000'),
            spaceAfter=20
        )))
        
        # AI Recommendation Badge and Overall Score removed per user request
        
        elements.append(Spacer(1, 0.3*inch))
        
        # ==================== KEY DETAILS SECTION ====================
        elements.append(Paragraph("Key Details", heading_style))
        
        # Get founded year with fallback chain
        founded_year = None
        if isinstance(research_findings.company_info, dict):
            founded_year = research_findings.company_info.get("founded_year")
        if not founded_year and startup_data.founded_year:
            founded_year = startup_data.founded_year
        
        # Get values with fallback to startup_data
        stage_value = research_findings.startup_stage or startup_data.stage or "Not specified"
        location_value = research_findings.location or startup_data.location or "Not specified"
        team_size_value = research_findings.employee_count or startup_data.team_size
        
        key_details = [
            ("Startup Name", research_findings.name or startup_data.name),
            ("Legal Name", research_findings.legal_name or startup_data.legal_name or startup_data.name),
            ("Industry", research_findings.industry or startup_data.industry),
            ("Thesis Category", research_findings.thesis_name),
            ("Stage", stage_value),
            ("Location", location_value),
            ("Founded", str(founded_year) if founded_year else "Not specified"),
        ]
        
        for label, value in key_details:
            row_data = [[
                Paragraph(f"<b>{label}:</b>", label_style),
                Paragraph(str(value) if value else "Not specified", normal_style)
            ]]
            table = Table(row_data, colWidths=[1.8*inch, 4.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f0f7')),
                ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#f5f5f5')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 0.05*inch))
        
        elements.append(Spacer(1, 0.2*inch))
        
        # ==================== EXECUTIVE SUMMARY ====================
        elements.append(Paragraph("Executive Summary", heading_style))
        overview_text = research_findings.description or "No description available"
        elements.extend(create_bullet_points(overview_text, bullet_style))
        
        elements.append(Spacer(1, 0.2*inch))
        
        
        # ==================== FOUNDERS & TEAM SECTION ====================
        elements.append(PageBreak())
        elements.append(Paragraph("Founders & Team", heading_style))

        # Founder Profiles
        if research_findings.founders and len(research_findings.founders) > 0:
            for idx, founder in enumerate(research_findings.founders[:5], 1):
                elements.append(Paragraph(f"<b>Founder {idx}: {founder.name}</b>", subheading_style))
                
                founder_info = []
                if founder.role:
                    founder_info.append(f"<b>Role:</b> {founder.role}")
                if founder.education:
                    founder_info.append(f"<b>Education:</b> {', '.join(founder.education[:3])}")
                if founder.previous_companies:
                    founder_info.append(f"<b>Previous Companies:</b> {', '.join(founder.previous_companies[:3])}")
                if founder.previous_exits:
                    founder_info.append(f"<b>Previous Exits:</b> {', '.join(founder.previous_exits[:3])}")
                if founder.years_experience:
                    founder_info.append(f"<b>Experience:</b> {founder.years_experience} years")
                if founder.domain_expertise:
                    founder_info.append(f"<b>Domain Expertise:</b> {founder.domain_expertise}")
                if founder.notable_achievements:
                    founder_info.append(f"<b>Achievements:</b> {', '.join(founder.notable_achievements[:3])}")
                
                for info in founder_info:
                    elements.append(Paragraph(info, ParagraphStyle('FounderInfo', fontSize=9, leftIndent=10, spaceAfter=2)))
                elements.append(Spacer(1, 0.1*inch))
        else:
            elements.append(Paragraph("<i>Detailed founder profiles not available from provided sources.</i>", normal_style))
        
        # Team Insights
        team_text = clean_text_field(research_findings.team_insights) if research_findings.team_insights else ""
        if team_text:
            elements.append(Paragraph("<b>Team Analysis:</b>", label_style))
            elements.extend(create_bullet_points(team_text, bullet_style))
        
        elements.append(Spacer(1, 0.2*inch))
        
        # ==================== PRODUCT & BUSINESS SECTION ====================
        elements.append(PageBreak())
        elements.append(Paragraph("Product & Business Model", heading_style))
        
        has_product_content = False
        
        product_desc = clean_text_field(research_findings.product_description) if research_findings.product_description else ""
        if product_desc:

            elements.append(Paragraph("<b>Product Description:</b>", label_style))
            elements.extend(create_bullet_points(product_desc, bullet_style))
            has_product_content = True
        
        uvp = clean_text_field(research_findings.unique_value_proposition) if research_findings.unique_value_proposition else ""
        if uvp:
            elements.append(Paragraph("<b>Unique Value Proposition:</b>", label_style))
            elements.extend(create_bullet_points(uvp, bullet_style))
            has_product_content = True
        
        tech_moat = clean_text_field(research_findings.technology_moat) if research_findings.technology_moat else ""
        if tech_moat:
            elements.append(Paragraph("<b>Technology Moat:</b>", label_style))
            elements.extend(create_bullet_points(tech_moat, bullet_style))
            has_product_content = True
        
        biz_model = clean_text_field(research_findings.business_model_details) if research_findings.business_model_details else ""
        if biz_model:
            elements.append(Paragraph("<b>Business Model:</b>", label_style))
            elements.extend(create_bullet_points(biz_model, bullet_style))
            has_product_content = True
        
        rev_model = clean_text_field(research_findings.revenue_model) if research_findings.revenue_model else ""
        if rev_model:
            elements.append(Paragraph("<b>Revenue Model:</b>", label_style))
            elements.extend(create_bullet_points(rev_model, bullet_style))
            has_product_content = True
        
        tech_stack = clean_text_field(research_findings.technology_stack) if research_findings.technology_stack else ""
        if tech_stack:
            elements.append(Paragraph("<b>Technology Stack:</b>", label_style))
            elements.extend(create_bullet_points(tech_stack, bullet_style))
            has_product_content = True
        
        # Fallback if no product content
        if not has_product_content:
            elements.append(Paragraph("<i>Detailed product information not available from provided sources.</i>", normal_style))
        
        elements.append(Spacer(1, 0.2*inch))
        
        # ==================== FINANCIAL DETAILS SECTION ====================
        elements.append(PageBreak())
        elements.append(Paragraph("Financial Details", heading_style))
        
        financial_data = [
            ["Funding Raised", format_currency(research_findings.funding_raised)],
            ["Funding Ask", format_currency(research_findings.funding_ask_amount)],
            ["Monthly Recurring Revenue (MRR)", format_currency(research_findings.current_mrr)],
            ["Annual Recurring Revenue (ARR)", format_currency(research_findings.current_arr)],
        ]
        
        financial_table = Table(financial_data, colWidths=[2.5*inch, 3.8*inch])
        financial_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f0f7')),
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#f5f5f5')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(financial_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # ==================== TRACTION & METRICS SECTION - REMOVED ====================
        # Traction & Metrics table removed per user request
        # Keeping only customer base text if available
        if research_findings.customer_base:
            elements.append(Paragraph("<b>Customer Base:</b>", label_style))
            elements.extend(create_bullet_points(clean_text_field(research_findings.customer_base) or "Not disclosed", bullet_style))
            elements.append(Spacer(1, 0.2*inch))
        
        # ==================== MARKET ANALYSIS SECTION ====================
        elements.append(PageBreak())
        elements.append(Paragraph("Market Analysis", heading_style))
        
        # Market Size Table
        market_data = [
            ["Total Addressable Market (TAM)", format_currency(research_findings.tam)],
            ["Serviceable Addressable Market (SAM)", format_currency(research_findings.sam)],
            ["Serviceable Obtainable Market (SOM)", format_currency(research_findings.som)],
            ["Market Growth Rate", f"{research_findings.market_growth_rate:.1f}%" if research_findings.market_growth_rate else "Not disclosed"],
        ]
        
        market_table = Table(market_data, colWidths=[3*inch, 3.3*inch])
        market_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f0f7')),
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#f5f5f5')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(market_table)
        elements.append(Spacer(1, 0.15*inch))
        
        if research_findings.market_analysis:
            market_text = clean_text_field(research_findings.market_analysis)
            if market_text:
                elements.append(Paragraph("<b>Market Opportunity:</b>", label_style))
                elements.extend(create_bullet_points(market_text, bullet_style))
        
        elements.append(Spacer(1, 0.2*inch))
        
        # ==================== COMPETITIVE LANDSCAPE SECTION ====================
        elements.append(Paragraph("Competitive Landscape", heading_style))
        
        if research_findings.competitive_landscape:
            comp_text = clean_text_field(research_findings.competitive_landscape)
            if comp_text:
                elements.extend(create_bullet_points(comp_text, bullet_style))
            else:
                elements.append(Paragraph("Competitive landscape analysis not available.", normal_style))
        else:
            elements.append(Paragraph("Competitive landscape analysis not available.", normal_style))
        
        elements.append(Spacer(1, 0.2*inch))
        
        # ==================== COMPETITOR ANALYSIS SECTION ====================
        if competitor_analysis and competitor_analysis.competitors:
            elements.append(PageBreak())
            elements.append(Paragraph("Competitor Analysis", heading_style))
            elements.append(Spacer(1, 0.1*inch))
            
            for idx, comp in enumerate(competitor_analysis.competitors[:5], 1):
                elements.append(Paragraph(f"<b>{idx}. {comp.name or 'Unknown Competitor'}</b>", subheading_style))
                
                comp_details = [
                    f"<b>Founded:</b> {comp.founded_year or 'N/A'}",
                    f"<b>Headquarters:</b> {comp.headquarters or 'N/A'}",
                    f"<b>Funding:</b> {format_currency(comp.funding_raised)}",
                    f"<b>Valuation:</b> {format_currency(comp.current_valuation)}",
                    f"<b>Revenue:</b> {format_currency(comp.revenue)}",
                    f"<b>Business Model:</b> {comp.business_model or 'N/A'}",
                    f"<b>Target Market:</b> {comp.focus_market or 'N/A'}",
                    f"<b>Traction:</b> {comp.traction or 'N/A'}",
                    f"<b>Similarities:</b> {comp.similarities or 'N/A'}",
                ]
                
                for detail in comp_details:
                    elements.append(Paragraph(detail, ParagraphStyle('CompDetail', fontSize=9, leftIndent=10, spaceAfter=2)))
                elements.append(Spacer(1, 0.1*inch))
            
            if competitor_analysis.market_overview:
                elements.append(Paragraph("<b>Market Overview:</b>", label_style))
                elements.extend(create_bullet_points(competitor_analysis.market_overview, bullet_style))
            
            if competitor_analysis.competitive_advantages:
                elements.append(Paragraph("<b>Competitive Advantages:</b>", label_style))
                elements.extend(create_bullet_points(competitor_analysis.competitive_advantages, bullet_style))
            
            if competitor_analysis.market_threats:
                elements.append(Paragraph("<b>Market Threats:</b>", label_style))
                elements.extend(create_bullet_points(competitor_analysis.market_threats, bullet_style))
        
        # ==================== AI INVESTMENT ANALYSIS SECTION ====================
        if ai_scorecard:
            elements.append(PageBreak())
            elements.append(Paragraph("AI Investment Analysis", graph_heading_style))
            # Spacer removed to move chart up
            
            # Create bar chart for scores
            score_rows = [
                ("Founders", ai_scorecard.founders_score, 0.25),
                ("Market", ai_scorecard.market_score, 0.20),
                ("Product", ai_scorecard.product_score, 0.15),
                ("Traction", ai_scorecard.traction_score, 0.20),
                ("Team", ai_scorecard.team_score, 0.10),
                ("Financials", ai_scorecard.financials_score, 0.10),
            ]
            
            # Prepare chart data
            categories = []
            scores = []
            bar_colors = []
            
            for name, score_detail, weight in score_rows:
                score_val = score_detail.score if score_detail else 0
                categories.append(name)
                scores.append(score_val)
                bar_colors.append(get_score_color(score_val))
            
            # Create horizontal bar chart with individual colors
            drawing = Drawing(500, 225)
            bc = HorizontalBarChart()
            bc.x = 120
            bc.y = 20
            bc.height = 200
            bc.width = 330
            
            # Correct Data Structure: 1 series with all scores
            bc.data = [scores]  
            
            # Categories on Y-axis
            bc.categoryAxis.categoryNames = categories
            bc.categoryAxis.labels.boxAnchor = 'e'
            bc.categoryAxis.labels.dx = -10
            bc.categoryAxis.labels.fontName = 'Helvetica-Bold'
            bc.categoryAxis.labels.fontSize = 11
            
            # Chart styling
            bc.valueAxis.valueMin = 0
            bc.valueAxis.valueMax = 10
            bc.valueAxis.valueStep = 2
            bc.barWidth = 20
            bc.groupSpacing = 15
            
            # Apply individual colors to each bar
            for i, color in enumerate(bar_colors):
                bc.bars[(0, i)].fillColor = color
                bc.bars[(0, i)].strokeColor = color
                bc.bars[(0, i)].strokeWidth = 0.5
            

            
            # Value labels
            bc.valueAxis.labels.fontSize = 9
            bc.valueAxis.labels.fontName = 'Helvetica'
            

            # Add value labels on bars
            bc.barLabelFormat = '%.1f'
            bc.barLabels.nudge = 10
            bc.barLabels.fontSize = 9
            bc.barLabels.fontName = 'Helvetica-Bold'
            
            drawing.add(bc)
            elements.append(drawing)
            
            # Add overall score text
            elements.append(Spacer(1, 0.15*inch))
            overall_color = get_score_color(ai_scorecard.overall_score)
            overall_text = f"<b>Overall Score: {ai_scorecard.overall_score:.1f}/10</b>"
            elements.append(Paragraph(overall_text, ParagraphStyle('OverallScore', 
                                                                    fontSize=14, 
                                                                    alignment=TA_CENTER, 
                                                                    textColor=overall_color,
                                                                    fontName='Helvetica-Bold',
                                                                    spaceAfter=10)))
            elements.append(Spacer(1, 0.1*inch))
            
            # Score Details
            for name, score_detail, _ in score_rows:
                if score_detail:
                    elements.append(Paragraph(f"<b>{name} ({score_detail.score:.1f}/10):</b>", subheading_style))
                    
                    if score_detail.strengths:
                        elements.append(Paragraph("<i>Strengths:</i> " + ", ".join(score_detail.strengths[:3]), 
                                                 ParagraphStyle('Strengths', fontSize=9, textColor=colors.HexColor('#22c55e'))))
                    if score_detail.weaknesses:
                        elements.append(Paragraph("<i>Weaknesses:</i> " + ", ".join(score_detail.weaknesses[:3]), 
                                                 ParagraphStyle('Weaknesses', fontSize=9, textColor=colors.HexColor('#ef4444'))))
                    elements.append(Spacer(1, 0.1*inch))
        
        # ==================== INVESTMENT ANALYSIS ====================
        elements.append(PageBreak())
        elements.append(Paragraph("Investment Analysis", heading_style))
        
        # Investment Highlights
        if research_findings.investment_highlights:
            elements.append(Paragraph("<b>Investment Highlights:</b>", subheading_style))
            for i, highlight in enumerate(research_findings.investment_highlights[:7], 1):
                elements.append(Paragraph(f"✓ {highlight}", ParagraphStyle('Highlight', fontSize=10, leftIndent=15, textColor=colors.HexColor('#000000'), spaceAfter=3)))
            elements.append(Spacer(1, 0.15*inch))
        
        # Risk Factors
        if research_findings.risk_factors:
            elements.append(Paragraph("<b>Risk Factors:</b>", subheading_style))
            for i, risk in enumerate(research_findings.risk_factors[:7], 1):
                elements.append(Paragraph(f"⚠ {risk}", ParagraphStyle('Risk', fontSize=10, leftIndent=15, textColor=colors.HexColor('#ef4444'), spaceAfter=3)))
            elements.append(Spacer(1, 0.15*inch))
        
        # Key Opportunities (from scorecard)
        if ai_scorecard and ai_scorecard.key_opportunities:
            elements.append(Paragraph("<b>Key Opportunities:</b>", subheading_style))
            for opp in ai_scorecard.key_opportunities[:5]:
                elements.append(Paragraph(f"→ {opp}", ParagraphStyle('Opportunity', fontSize=10, leftIndent=15, textColor=colors.HexColor('#000000'), spaceAfter=3)))
            elements.append(Spacer(1, 0.15*inch))
        
        # Key Risks (from scorecard)
        if ai_scorecard and ai_scorecard.key_risks:
            elements.append(Paragraph("<b>Key Risks to Monitor:</b>", subheading_style))
            for risk in ai_scorecard.key_risks[:5]:
                elements.append(Paragraph(f"• {risk}", ParagraphStyle('KeyRisk', fontSize=10, leftIndent=15, spaceAfter=3)))
        
        
        # Step 7: Build PDF
        doc.build(elements)
        
        print(f"  ✓ PDF created: {pdf_filename}")
        
        # Step 8: Log summary
        print("\n📊 PDF GENERATION SUMMARY:")
        print(f"   - Startup: {research_findings.name}")
        print(f"   - PDF File: {pdf_filename}")
        print(f"   - AI Scorecard: {'Included' if ai_scorecard else 'Not available'}")
        if ai_scorecard:
            print(f"   - Overall Score: {ai_scorecard.overall_score}/10")
            print(f"   - Recommendation: {ai_scorecard.investment_recommendation}")
        print(f"   - Founders Included: {len(research_findings.founders)}")
        print(f"   - Competitors Included: {len(competitor_analysis.competitors) if competitor_analysis else 0}")
        print(f"   - File Size: {os.path.getsize(pdf_filename) / 1024:.2f} KB")
        
        print("\n✅ Node 6 Complete: Enhanced investment thesis PDF generated successfully")
        print("="*60 + "\n")
        
        # Step 9: Return updated state
        return {
            "status": "thesis_pdf_generated",
            "thesis_pdf_path": pdf_filename
        }
    
    except Exception as e:
        print(f"\n❌ ERROR in Node 6: {str(e)}")
        import traceback
        traceback.print_exc()
        print("="*60 + "\n")
        
        return {
            "status": "error",
            "errors": [f"PDF generation error: {str(e)}"]
        }