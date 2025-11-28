"""
Export utilities for PDF and Excel generation
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import pandas as pd
from datetime import datetime
import io


def export_to_pdf(session_info, results, top_n=None):
    """
    Export screening results to PDF
    
    Args:
        session_info: Dictionary with session information
        results: List of result dictionaries
        top_n: If specified, export only top N candidates
        
    Returns:
        BytesIO object containing PDF data
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, 
                           topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    # Container for PDF elements
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#4f46e5'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=12
    )
    
    # Title
    title_text = "Resume Screening Report"
    elements.append(Paragraph(title_text, title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Session Information
    session_data = [
        ['Job Title:', session_info.get('job_title', 'N/A')],
        ['Company:', session_info.get('company', 'N/A')],
        ['Date:', datetime.fromisoformat(session_info['timestamp']).strftime('%Y-%m-%d %H:%M')],
        ['Total Candidates:', str(session_info.get('total_candidates', len(results)))]
    ]
    
    if top_n:
        session_data.append(['Showing:', f'Top {top_n} candidates'])
    
    session_table = Table(session_data, colWidths=[2*inch, 4*inch])
    session_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    
    elements.append(session_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Results Summary
    if top_n:
        results = results[:top_n]
    
    # Add summary statistics
    if results:
        avg_score = sum(r.get('overall_score', 0) for r in results) / len(results)
        top_candidate = max(results, key=lambda x: x.get('overall_score', 0))
        
        summary_data = [
            ['Average Score:', f"{avg_score:.1f}/100"],
            ['Top Candidate:', top_candidate.get('candidate_name', 'N/A')],
            ['Top Score:', f"{top_candidate.get('overall_score', 0):.1f}/100"]
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 4*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        
        elements.append(Paragraph("Summary Statistics", heading_style))
        elements.append(summary_table)
        elements.append(Spacer(1, 0.3*inch))
    
    # Results
    for idx, result in enumerate(results, 1):
        # Rank badge
        rank_color = colors.HexColor('#fbbf24') if idx == 1 else \
                     colors.HexColor('#9ca3af') if idx == 2 else \
                     colors.HexColor('#cd7f32') if idx == 3 else \
                     colors.HexColor('#e5e7eb')
        
        # Candidate header with medal
        medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"#{idx}"
        rank_text = f"{medal} {result.get('candidate_name', 'N/A')}"
        elements.append(Paragraph(rank_text, heading_style))
        
        # Score bars visualization
        elements.append(Spacer(1, 0.1*inch))
        
        # Overall Score Bar
        overall_score = result.get('overall_score', 0)
        score_bar_elements = []
        score_bar_elements.append(Paragraph(f"Overall Score: {overall_score:.1f}/100", styles['Normal']))
        
        # Create visual bar
        bar_width = 4*inch * (overall_score / 100)
        bar_height = 0.3*inch
        
        # Score bar container
        d = Drawing(4*inch, bar_height)
        d.add(Rect(0, 0, 4*inch, bar_height, fillColor=colors.HexColor('#e5e7eb'), strokeColor=None))
        
        # Score bar fill
        if overall_score > 0:
            d.add(Rect(0, 0, bar_width, bar_height, fillColor=colors.HexColor('#6366f1'), strokeColor=None))
        
        score_bar_elements.append(d)
        elements.extend(score_bar_elements)
        elements.append(Spacer(1, 0.1*inch))
        
        # Detailed Scores
        score_data = [
            ['Skills Match', f"{result.get('skills_match_score', 0):.1f}/100"],
            ['Experience', f"{result.get('experience_score', 0):.1f}/100"],
            ['Education', f"{result.get('education_score', 0):.1f}/100"]
        ]
        
        score_table = Table(score_data, colWidths=[2*inch, 2*inch])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f9fafb')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        
        elements.append(score_table)
        elements.append(Spacer(1, 0.1*inch))
        
        # Recommendation
        recommendation = result.get('recommendation', 'N/A')
        elements.append(Paragraph(f"<b>Recommendation:</b> {recommendation}", styles['Normal']))
        elements.append(Spacer(1, 0.1*inch))
        
        # Reasoning
        reasoning_text = f"<b>Analysis:</b> {result.get('reasoning', 'N/A')}"
        elements.append(Paragraph(reasoning_text, styles['Normal']))
        elements.append(Spacer(1, 0.1*inch))
        
        # Strengths
        strengths = result.get('strengths', [])
        if strengths:
            elements.append(Paragraph("<b>Strengths:</b>", styles['Normal']))
            for strength in strengths:
                elements.append(Paragraph(f"• {strength}", styles['Normal']))
            elements.append(Spacer(1, 0.1*inch))
        
        # Weaknesses
        weaknesses = result.get('weaknesses', [])
        if weaknesses:
            elements.append(Paragraph("<b>Areas for Improvement:</b>", styles['Normal']))
            for weakness in weaknesses:
                elements.append(Paragraph(f"• {weakness}", styles['Normal']))
        
        if idx < len(results):
            elements.append(Spacer(1, 0.3*inch))
            elements.append(PageBreak())
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


def export_to_excel(session_info, results, top_n=None):
    """
    Export screening results to Excel
    
    Args:
        session_info: Dictionary with session information
        results: List of result dictionaries
        top_n: If specified, export only top N candidates
        
    Returns:
        BytesIO object containing Excel data
    """
    buffer = io.BytesIO()
    
    if top_n:
        results = results[:top_n]
    
    # Prepare data for Excel
    data = []
    for idx, result in enumerate(results, 1):
        row = {
            'Rank': idx,
            'Candidate Name': result.get('candidate_name', 'N/A'),
            'Overall Score': round(result.get('overall_score', 0), 1),
            'Skills Match': round(result.get('skills_match_score', 0), 1),
            'Experience Score': round(result.get('experience_score', 0), 1),
            'Education Score': round(result.get('education_score', 0), 1),
            'Recommendation': result.get('recommendation', 'N/A'),
            'Reasoning': result.get('reasoning', 'N/A'),
            'Strengths': ', '.join(result.get('strengths', [])),
            'Weaknesses': ', '.join(result.get('weaknesses', []))
        }
        data.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Create Excel writer
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # Write session info
        session_df = pd.DataFrame([
            ['Job Title', session_info.get('job_title', 'N/A')],
            ['Company', session_info.get('company', 'N/A')],
            ['Date', datetime.fromisoformat(session_info['timestamp']).strftime('%Y-%m-%d %H:%M')],
            ['Total Candidates', session_info.get('total_candidates', len(results))]
        ], columns=['Field', 'Value'])
        
        session_df.to_excel(writer, sheet_name='Session Info', index=False)
        
        # Write results
        df.to_excel(writer, sheet_name='Results', index=False)
        
        # Auto-adjust column widths
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
    
    buffer.seek(0)
    return buffer
