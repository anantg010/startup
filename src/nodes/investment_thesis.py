from ..state import GraphState
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image, Flowable
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Circle, String, Group
from reportlab.graphics.charts.barcharts import HorizontalBarChart
from reportlab.graphics import renderPDF
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os
import json

# Register Fonts (Arial for Rupee Support)
try:
    pdfmetrics.registerFont(TTFont('Arial', 'C:\\Windows\\Fonts\\arial.ttf'))
    pdfmetrics.registerFont(TTFont('Arial-Bold', 'C:\\Windows\\Fonts\\arialbd.ttf'))
except Exception as e:
    print(f"⚠️ Could not register standard Arial font: {e}")
    # Fallback to Helvetica is automatic if assignment fails, but we'll try to stick to Arial names
    pass

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
    return colors.black


def format_currency(value):
    """Format number as currency string. Returns None for 0 or empty."""
    if value is None:
        return None
    
    # Check for "Not disclosed" or various forms of zero
    str_val = str(value).strip().lower()
    if str_val in ["not disclosed", "none", "n/a", "", "0", "$0", "$0.00", "0.0"]:
        return None
        
    try:
        # If string contains currency symbol, try to parse
        clean_val = str_val.replace('$', '').replace(',', '')
        val_float = float(clean_val)
        if val_float == 0:
            return None
            
        if value == 0:
            return None
            
        # Indian Numbering System Logic
        # 1 Crore = 10,000,000
        # 1 Lakh = 100,000
        
        if value >= 10000000: # 1 Crore
            return f"₹{value/10000000:.2f} Cr"
        elif value >= 100000: # 1 Lakh
            return f"₹{value/100000:.2f} L"
        else:
            return f"₹{value:,.0f}"
    except (TypeError, ValueError):
        # If it's a string like "Undisclosed", return None as per new requirement 
        # "All the information that is not present... must not be printed"
        return None


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


class ConditionalPageBreak(Flowable):
    """
    A flowable that only triggers a page break if the current page 
    is more than 50% full.
    """
    def __init__(self, page_height=letter[1], top_margin=0.6*inch, bottom_margin=0.6*inch):
        super().__init__()
        self.total_page_height = page_height
        self.content_height = page_height - top_margin - bottom_margin
        
    def wrap(self, availWidth, availHeight):
        # Calculate how much space is used
        # availHeight is what is LEFT on the page
        threshold = self.content_height * 0.5
        
        # If available height is less than threshold (meaning used > 50%), force break
        if availHeight <= threshold:
            # Force page break by consuming all available height
            return (availWidth, availHeight)
        else:
            # No break, take 0 space
            return (0, 0)
            
    def draw(self):
        pass



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
        print("\\n" + "="*60)
        print("📄 NODE 6: GENERATE ENHANCED INVESTMENT THESIS PDF")
        print("="*60)
        
        # Step 1: Check if research findings exist
        if not state.research_findings:
            print("⚠️ No research findings available")
            print("Status: Cannot generate PDF without research data\\n")
            
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
        print("\\n📊 DEBUG - Data Available:")
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
            fontName='Arial-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#000000'),
            spaceAfter=16,
            spaceBefore=12,
            fontName='Arial-Bold',
            alignment=TA_LEFT
        )
        
        graph_heading_style = ParagraphStyle(
            'GraphHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#000000'),
            spaceAfter=6,
            spaceBefore=12,
            fontName='Arial-Bold',
            alignment=TA_LEFT
        )

        table_cell_style = ParagraphStyle(
            'TableCell',
            parent=styles['Normal'],
            fontSize=9,
            alignment=TA_LEFT,
            spaceAfter=0,
            fontName='Arial'
        )
        
        subheading_style = ParagraphStyle(
            'SubHeading',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=10,
            spaceBefore=8,
            fontName='Arial-Bold'
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
            fontName='Arial'
        )
        
        bullet_style = ParagraphStyle(
            'BulletPoint',
            parent=styles['Normal'],
            fontSize=10,
            leftIndent=15,
            firstLineIndent=-10,
            spaceAfter=8,
            alignment=TA_LEFT,
            fontName='Arial'
        )
        
        label_style = ParagraphStyle(
            'Label',
            parent=styles['Normal'],
            fontSize=10,
            fontName='Arial-Bold',
            textColor=colors.HexColor('#2e5c8a'),
            spaceAfter=10,
            spaceBefore=6
        )
        
        score_style = ParagraphStyle(
            'Score',
            parent=styles['Normal'],
            fontSize=18,
            fontName='Arial-Bold',
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
            spaceAfter=20,
            fontName='Arial-Bold'
        )))
        
        # AI Recommendation Badge and Overall Score removed per user request
        
        elements.append(Spacer(1, 0.3*inch))
        
        # ==================== KEY DETAILS SECTION (Commented Out) ====================
        '''
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
        
        key_details_list = [
            ("Startup Name", research_findings.name or startup_data.name),
            ("Legal Name", research_findings.legal_name or startup_data.legal_name or startup_data.name),
            ("Industry", research_findings.industry or startup_data.industry),
            ("Thesis Category", research_findings.thesis_name),
            ("Stage", stage_value),
            ("Location", location_value),
            ("Founded", str(founded_year) if founded_year else None),
        ]
        
        # Filter out empty values
        valid_details = []
        for label, value in key_details_list:
            if value and str(value).lower() not in ["not disclosed", "none", "n/a", ""]:
                valid_details.append((label, value))
        
        for label, value in valid_details:
            row_data = [[
                Paragraph(f"<b>{label}:</b>", label_style),
                Paragraph(str(value), normal_style)
            ]]
            table = Table(row_data, colWidths=[1.8*inch, 4.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f0f7')),
                ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#f5f5f5')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, -1), 'Arial'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 0.05*inch))
        
        elements.append(Spacer(1, 0.2*inch))
        '''
        
        # ==================== EXECUTIVE SUMMARY ====================
        elements.append(Paragraph("Executive Summary", heading_style))
        overview_text = research_findings.description or "No description available"
        elements.extend(create_bullet_points(overview_text, bullet_style))
        
        elements.append(Spacer(1, 0.2*inch))
        
        # ==================== AI INVESTMENT ANALYSIS SECTION ====================
        if ai_scorecard:
            elements.append(ConditionalPageBreak())
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
            
            # Score Details - Simplified and Black Color
            for name, score_detail, _ in score_rows:
                if score_detail:
                    elements.append(Paragraph(f"<b>{name} ({score_detail.score:.1f}/10):</b>", subheading_style))
                    
                    # Combine strengths and weaknesses into a single brief bullet list
                    points = []
                    if score_detail.strengths:
                        points.extend(score_detail.strengths[:2]) # Keep brief
                    if score_detail.weaknesses:
                         points.extend(score_detail.weaknesses[:2]) # Keep brief
                    
                    if points:
                        combined_text = ", ".join(points)
                        elements.append(Paragraph(f"• {combined_text}", ParagraphStyle('AnalysisPoint', fontSize=10, leftIndent=15, textColor=colors.black)))

                    elements.append(Spacer(1, 0.05*inch))
            
            elements.append(Spacer(1, 0.2*inch))

        # ==================== RISKS & OPPORTUNITIES (Was Investment Analysis) ====================
        elements.append(ConditionalPageBreak())
        elements.append(Paragraph("Risks & Opportunities", heading_style))
        
        # Risk Factors - Red text changed to Black
        if research_findings.risk_factors:
            elements.append(Paragraph("<b>Risk Factors:</b>", subheading_style))
            for i, risk in enumerate(research_findings.risk_factors[:7], 1):
                elements.append(Paragraph(f"⚠ {risk}", ParagraphStyle('Risk', fontSize=10, leftIndent=15, textColor=colors.black, spaceAfter=3)))
            elements.append(Spacer(1, 0.15*inch))
        
        # Key Opportunities (from scorecard)
        if ai_scorecard and ai_scorecard.key_opportunities:
            elements.append(Paragraph("<b>Key Opportunities:</b>", subheading_style))
            for opp in ai_scorecard.key_opportunities[:5]:
                elements.append(Paragraph(f"→ {opp}", ParagraphStyle('Opportunity', fontSize=10, leftIndent=15, textColor=colors.HexColor('#000000'), spaceAfter=3)))
            elements.append(Spacer(1, 0.15*inch))
        
        # ==================== FOUNDERS & TEAM SECTION ====================
        elements.append(ConditionalPageBreak())
        elements.append(Paragraph("Founders & Team", heading_style))

        # Founder Profiles
        if research_findings.founders and len(research_findings.founders) > 0:
            # Define table data structure
            # Columns: Founder Name, Role, Education, Experience & Background, Expertise
            table_data = [[
                Paragraph("<b>Founder</b>", label_style),
                Paragraph("<b>Role</b>", label_style),
                Paragraph("<b>Education</b>", label_style),
                Paragraph("<b>Experience & Background</b>", label_style),
                Paragraph("<b>Expertise</b>", label_style)
            ]]
            
            for founder in research_findings.founders[:5]:
                # Helper to format lists
                def fmt_list(l): return ", ".join(l[:3]) if l else ""
                
                # Column 1: Name (Black Highlight)
                name_cell = Paragraph(f"<b><font color='black'>{founder.name}</font></b>", table_cell_style)
                
                # Column 2: Role
                role_cell = Paragraph(founder.role or "", table_cell_style)
                
                # Column 3: Education
                edu_cell = Paragraph(fmt_list(founder.education), table_cell_style)
                
                # Column 4: Experience & Background
                bg_parts = []
                if founder.years_experience:
                    bg_parts.append(f"Exp: {founder.years_experience} yrs")
                if founder.previous_companies:
                    bg_parts.append(f"Prev: {fmt_list(founder.previous_companies)}")
                if founder.previous_exits:
                    bg_parts.append(f"Exits: {fmt_list(founder.previous_exits)}")
                bg_cell = Paragraph("<br/>".join(bg_parts), table_cell_style)
                
                # Column 5: Expertise / Achievements
                exp_parts = []
                if founder.domain_expertise:
                    exp_parts.append(founder.domain_expertise)
                if founder.notable_achievements:
                    exp_parts.append(f"<i>{fmt_list(founder.notable_achievements)}</i>")
                expertise_cell = Paragraph("<br/><br/>".join(exp_parts), table_cell_style)
                
                row = [name_cell, role_cell, edu_cell, bg_cell, expertise_cell]
                table_data.append(row)
            
            # Create Table
            # Total width approx 7.3 inch
            # Col widths: 1.3, 1.0, 1.5, 2.0, 1.5
            col_widths = [1.3*inch, 1.0*inch, 1.5*inch, 2.0*inch, 1.5*inch]
            founder_table = Table(table_data, colWidths=col_widths, repeatRows=1)
            
            founder_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8f0f7')), # Header bg
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ]))
            
            elements.append(founder_table)
            elements.append(Spacer(1, 0.1*inch))
            
        else:
            elements.append(Paragraph("<i>Detailed founder profiles not available from provided sources.</i>", normal_style))
        
        # Team Insights
        team_text = clean_text_field(research_findings.team_insights) if research_findings.team_insights else ""
        # Filter out generic "not found" messages to ensure section is truly dynamic as requested
        if team_text and team_text.lower().strip() not in ["none", "null", "unknown", "not specified", "not disclosed", "n/a", ""]:
            elements.append(Paragraph("<b>Team Analysis:</b>", label_style))
            elements.extend(create_bullet_points(team_text, bullet_style))
        
        elements.append(Spacer(1, 0.2*inch))
        
        # ==================== PRODUCT & BUSINESS SECTION ====================
        elements.append(ConditionalPageBreak())
        elements.append(Paragraph("Product & Business Model", heading_style))
        
        has_product_content = False
        
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
            
        # MOVED CUSTOMER BASE HERE per user request
        if research_findings.customer_base:
            elements.append(Paragraph("<b>Customer Base:</b>", label_style))
            elements.extend(create_bullet_points(clean_text_field(research_findings.customer_base) or "Not disclosed", bullet_style))
            has_product_content = True
        
        # Fallback if no product content
        if not has_product_content:
            elements.append(Paragraph("<i>Detailed product information not available from provided sources.</i>", normal_style))
        
        elements.append(Spacer(1, 0.2*inch))
        
        # ==================== FINANCIAL DETAILS SECTION (Commented Out) ====================
        '''
        # Prepare financial data first
        financial_list = [
            ("Funding Raised", format_currency(research_findings.funding_raised)),
            ("Funding Ask", format_currency(research_findings.funding_ask_amount)),
            ("Monthly Recurring Revenue (MRR)", format_currency(research_findings.current_mrr)),
            ("Annual Recurring Revenue (ARR)", format_currency(research_findings.current_arr)),
        ]
        
        # Filter valid financial data
        financial_data = []
        for label, val in financial_list:
            if val: # format_currency returns None if invalid
                financial_data.append([label, val])
        
        # Only render section if we have data
        if financial_data:
            elements.append(ConditionalPageBreak())
            elements.append(Paragraph("Financial Details", heading_style))
            
            financial_table = Table(financial_data, colWidths=[2.5*inch, 3.8*inch])
            financial_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f0f7')),
                ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#f5f5f5')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Arial-Bold'),
                ('FONTNAME', (0, 0), (-1, -1), 'Arial'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elements.append(financial_table)
            elements.append(Spacer(1, 0.2*inch))
        '''
        
        # ==================== MARKET ANALYSIS SECTION (Commented Out) ====================
        '''
        elements.append(ConditionalPageBreak())
        elements.append(Paragraph("Market Analysis", heading_style))
        
        # Market Size Table (Validated Data)
        tam_val = None
        sam_val = None
        som_val = None
        market_explanation = []

        if competitor_analysis:
            tam_val = competitor_analysis.tam
            sam_val = competitor_analysis.sam
            som_val = competitor_analysis.som
            market_explanation = competitor_analysis.market_data_explanation
        
        # Fallback to research_findings if validation data missing
        if not tam_val and research_findings.tam:
             tam_val = research_findings.tam
             sam_val = research_findings.sam
             som_val = research_findings.som

        if tam_val or sam_val or som_val:
            # Draw Concentric Circles for Market Analysis
            # Radii settings
            r_tam = 150
            r_sam = 100
            r_som = 50
            
            # Center of the drawing
            cx = 250
            cy = 160
            
            drawing = Drawing(500, 320)
            
            # Colors
            c_tam = colors.HexColor('#e0f2fe') # Lightest Blue
            c_sam = colors.HexColor('#bae6fd') # Medium Blue
            c_som = colors.HexColor('#7dd3fc') # Darker Blue/Cyan
            
            # Text Color
            c_text = colors.HexColor('#0c4a6e')
            
            # Formatting values
            def fmt(v): return format_currency(v) if v else "N/A"
            
            lbl_tam = f"TAM: {fmt(tam_val)}"
            lbl_sam = f"SAM: {fmt(sam_val)}"
            lbl_som = f"SOM: {fmt(som_val)}"
            
            # Draw Circles (Largest first)
            # TAM Circle
            drawing.add(Circle(cx, cy, r_tam, fillColor=c_tam, strokeColor=colors.white, strokeWidth=2))
            # SAM Circle
            drawing.add(Circle(cx, cy, r_sam, fillColor=c_sam, strokeColor=colors.white, strokeWidth=2))
            # SOM Circle
            drawing.add(Circle(cx, cy, r_som, fillColor=c_som, strokeColor=colors.white, strokeWidth=2))
            
            # Draw Labels
            # SOM Label (Center)
            drawing.add(String(cx, cy, "SOM", textAnchor='middle', fontSize=12, fontName='Helvetica-Bold', fillColor=c_text))
            drawing.add(String(cx, cy - 15, fmt(som_val), textAnchor='middle', fontSize=10, fontName='Helvetica', fillColor=c_text))
            
            # SAM Label (Top of SAM area)
            # Position: Center X, roughly Y = cy + r_som + (r_sam - r_som)/2
            y_sam = cy + r_som + 25 
            drawing.add(String(cx, y_sam, "SAM", textAnchor='middle', fontSize=12, fontName='Helvetica-Bold', fillColor=c_text))
            drawing.add(String(cx, y_sam - 15, fmt(sam_val), textAnchor='middle', fontSize=10, fontName='Helvetica', fillColor=c_text))
            
            # TAM Label (Top of TAM area)
            y_tam = cy + r_sam + 25
            drawing.add(String(cx, y_tam, "TAM", textAnchor='middle', fontSize=12, fontName='Helvetica-Bold', fillColor=c_text))
            drawing.add(String(cx, y_tam - 15, fmt(tam_val), textAnchor='middle', fontSize=10, fontName='Helvetica', fillColor=c_text))
            
            elements.append(drawing)
            elements.append(Spacer(1, 0.15*inch))
        else:
            elements.append(Paragraph("Market size data not available.", normal_style))
        
        # Validated Market Explanation
        if market_explanation:
            elements.append(Paragraph("<b>Source of Evaluation:</b>", label_style))
            for item in market_explanation:
                elements.append(Paragraph(f"• {item}", bullet_style))
        elif research_findings.market_analysis:
             # Fallback if no specific validation explanation but we have old analysis
             # But user asked to remove "Market Opportunity", so maybe we just show nothing if no validation?
             # User said "explain it" implying the new explanation. 
             # I will skip the old market_analysis to strictly follow "Remove ... Market Opportunity".
             pass
        
        elements.append(Spacer(1, 0.2*inch))
        '''

        # ==================== COMPETITOR ANALYSIS SECTION (Commented Out) ====================
        '''
        if competitor_analysis and competitor_analysis.competitors:
            elements.append(ConditionalPageBreak())
            elements.append(Paragraph("Competitor Analysis", heading_style))
            elements.append(Spacer(1, 0.1*inch))
            
            # Define table data structure
            # Columns: Competitor, Financials, Business Model & Market, Traction, Notes
            table_data = [[
                Paragraph("<b>Competitor</b>", label_style),
                Paragraph("<b>Financials</b>", label_style),
                Paragraph("<b>Model & Market</b>", label_style),
                Paragraph("<b>Traction</b>", label_style),
                Paragraph("<b>Notes</b>", label_style)
            ]]
            
            for comp in competitor_analysis.competitors[:5]:
                # Helper to format None as N/A but strictly for filtering
                def get_val(v): return str(v) if v else None
                
                # Column 1: Competitor Info - Remove HQ, shift Founded
                comp_name = get_val(comp.name) or "Unknown"
                founded_yr = get_val(comp.founded_year)
                
                # Highlight name in BLACK explicitly
                comp_info_parts = [f"<b><font color='black'>{comp_name}</font></b>"]
                if founded_yr:
                    comp_info_parts.append(f"<br/><br/>Founded: {founded_yr}")
                comp_info = "".join(comp_info_parts)
                
                # Column 2: Financials - Filter $0/None
                fin_parts = []
                fund_val = format_currency(comp.funding_raised)
                if fund_val: fin_parts.append(f"Funding: {fund_val}")
                
                eval_val = format_currency(comp.current_valuation)
                if eval_val: fin_parts.append(f"Val: {eval_val}")
                
                rev_val = format_currency(comp.revenue)
                if rev_val: fin_parts.append(f"Rev: {rev_val}")
                
                fin_info = "<br/>".join(fin_parts)
                
                # Column 3: Model & Market
                model_parts = []
                model_val = get_val(comp.business_model)
                if model_val: model_parts.append(f"<b>Model:</b> {model_val}")
                
                market_val = get_val(comp.focus_market)
                if market_val: model_parts.append(f"<b>Market:</b> {market_val}")
                
                # Join with double spacing for distinction
                model_info = "<br/><br/>".join(model_parts)
                
                # Column 4: Traction
                traction_info = get_val(comp.traction) or ""
                
                # Column 5: Notes
                notes_info = get_val(comp.similarities) or ""

                row = [
                    Paragraph(comp_info, table_cell_style),
                    Paragraph(fin_info, table_cell_style),
                    Paragraph(model_info, table_cell_style),
                    Paragraph(traction_info, table_cell_style),
                    Paragraph(notes_info, table_cell_style)
                ]
                table_data.append(row)
            
            # Create Table
            # Total width approx 7.3 inch
            # Col widths: 1.0, 1.4, 2.0, 1.5, 1.4
            col_widths = [1.0*inch, 1.5*inch, 2.0*inch, 1.4*inch, 1.4*inch]
            comp_table = Table(table_data, colWidths=col_widths, repeatRows=1)
            
            comp_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8f0f7')), # Header bg
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ]))
            
            elements.append(comp_table)
            
            elements.append(Spacer(1, 0.2*inch))
        '''
        
        # ==================== L1 CALL RECOMMENDATION ====================
        if ai_scorecard and ai_scorecard.investment_recommendation:
             elements.append(Spacer(1, 0.15*inch))
             elements.append(Paragraph("<b>L1 Call Recommendation:</b>", subheading_style))
             
             rec_text = ai_scorecard.investment_recommendation.replace("_", " ")
             elements.append(Paragraph(rec_text, ParagraphStyle('L1Rec', fontSize=12, leftIndent=15, textColor=colors.black, fontName='Helvetica-Bold')))
        
        
        # Step 7: Build PDF
        doc.build(elements)
        
        print(f"  ✓ PDF created: {pdf_filename}")
        
        # Step 8: Log summary
        print("\\n📊 PDF GENERATION SUMMARY:")
        print(f"   - Startup: {research_findings.name}")
        print(f"   - PDF File: {pdf_filename}")
        print(f"   - AI Scorecard: {'Included' if ai_scorecard else 'Not available'}")
        if ai_scorecard:
            print(f"   - Overall Score: {ai_scorecard.overall_score}/10")
            print(f"   - Recommendation: {ai_scorecard.investment_recommendation}")
        print(f"   - Founders Included: {len(research_findings.founders)}")
        print(f"   - Competitors Included: {len(competitor_analysis.competitors) if competitor_analysis else 0}")
        print(f"   - File Size: {os.path.getsize(pdf_filename) / 1024:.2f} KB")
        
        print("\\n✅ Node 6 Complete: Enhanced investment thesis PDF generated successfully")
        print("="*60 + "\\n")
        
        # Step 9: Return updated state
        return {
            "status": "thesis_pdf_generated",
            "thesis_pdf_path": pdf_filename
        }
    
    except Exception as e:
        print(f"\\n❌ ERROR in Node 6: {str(e)}")
        import traceback
        traceback.print_exc()
        print("="*60 + "\\n")
        
        return {
            "status": "error",
            "errors": [f"PDF generation error: {str(e)}"]
        }