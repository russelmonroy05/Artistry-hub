

from io import BytesIO
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import numpy as np
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, 
    PageBreak, Image, KeepTogether, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics import renderPDF
from django.db.models import Avg, Count, Q
from datetime import datetime



def create_rating_gauge_chart(rating, max_rating=5, title=""):
    """
    Create a beautiful gauge/speedometer chart for rating visualization
    """
    fig, ax = plt.subplots(figsize=(6, 3), subplot_kw={'projection': 'polar'})
    

    theta = np.linspace(0, np.pi, 100)
    rating_angle = (rating / max_rating) * np.pi
    

    if rating >= 4.5:
        color = '#4CAF50'  # Green
    elif rating >= 4.0:
        color = '#8BC34A'  # Light Green
    elif rating >= 3.5:
        color = '#FFC107'  # Amber
    elif rating >= 3.0:
        color = '#FF9800'  # Orange
    else:
        color = '#F44336'  # Red
    
    # Draw gauge background
    ax.plot(theta, np.ones_like(theta), color='#E0E0E0', linewidth=20)
    
    # Draw rating arc
    rating_theta = np.linspace(0, rating_angle, 100)
    ax.plot(rating_theta, np.ones_like(rating_theta), color=color, linewidth=20)
    
    # Add rating text
    ax.text(np.pi/2, 0.5, f'{rating:.2f}', 
            ha='center', va='center', fontsize=32, fontweight='bold', color=color)
    ax.text(np.pi/2, 0.2, f'out of {max_rating}', 
            ha='center', va='center', fontsize=12, color='gray')
    
    # Styling
    ax.set_ylim(0, 1.2)
    ax.set_yticks([])
    ax.set_xticks([0, np.pi/4, np.pi/2, 3*np.pi/4, np.pi])
    ax.set_xticklabels(['1', '2', '3', '4', '5'])
    ax.spines['polar'].set_visible(False)
    ax.grid(False)
    
    if title:
        plt.title(title, fontsize=14, fontweight='bold', pad=20)
    
    # Save to buffer
    buffer = BytesIO()
    plt.tight_layout()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', transparent=True)
    plt.close()
    buffer.seek(0)
    
    return buffer


def create_category_bar_chart(categories_data, title="Performance by Category"):
    """
    Create a professional horizontal bar chart for category comparison
    
    Args:
        categories_data: dict like {'Presentation': 4.5, 'Development': 4.3, ...}
    """
    fig, ax = plt.subplots(figsize=(8, 5))
    
    categories = list(categories_data.keys())
    values = list(categories_data.values())
    
    # Color gradient
    colors_list = ['#8B0000', '#A52A2A', '#B22222', '#DC143C']
    
    # Create horizontal bars
    bars = ax.barh(categories, values, color=colors_list[:len(categories)])
    
    # Add value labels on bars
    for i, (bar, value) in enumerate(zip(bars, values)):
        ax.text(value + 0.05, i, f'{value:.2f}', 
                va='center', fontsize=11, fontweight='bold')
    
    # Styling
    ax.set_xlim(0, 5.5)
    ax.set_xlabel('Average Rating', fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    
    # Reference line at 4.0 (good performance)
    ax.axvline(x=4.0, color='green', linestyle='--', alpha=0.5, linewidth=1.5, label='Good (4.0)')
    ax.legend(loc='lower right')
    
    plt.tight_layout()
    
    # Save to buffer
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    plt.close()
    buffer.seek(0)
    
    return buffer


def create_radar_chart(categories_data, title="Performance Overview"):
    """
    Create a radar/spider chart for multi-dimensional performance view
    
    Args:
        categories_data: dict like {'Presentation': 4.5, 'Development': 4.3, ...}
    """
    categories = list(categories_data.keys())
    values = list(categories_data.values())
    
    # Number of variables
    N = len(categories)
    
    # Compute angle for each axis
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    values += values[:1]  # Complete the circle
    angles += angles[:1]
    
    # Initialize figure
    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(projection='polar'))
    
    # Draw the plot
    ax.plot(angles, values, 'o-', linewidth=2, color='maroon', label='Rating')
    ax.fill(angles, values, alpha=0.25, color='maroon')
    
    # Fix axis to go from 0 to 5
    ax.set_ylim(0, 5)
    
    # Set category labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=10)
    
    # Set y-axis labels
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_yticklabels(['1', '2', '3', '4', '5'], fontsize=9, color='gray')
    
    # Add gridlines
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Title
    plt.title(title, size=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    
    # Save to buffer
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    buffer.seek(0)
    
    return buffer


def create_trend_line_chart(weekly_data, title="Rating Trend Over Time"):
    """
    Create a line chart showing rating trends over time
    
    Args:
        weekly_data: dict like {'Week 1': 4.2, 'Week 2': 4.3, ...}
    """
    fig, ax = plt.subplots(figsize=(8, 4))
    
    weeks = list(weekly_data.keys())
    ratings = list(weekly_data.values())
    
    # Create line plot
    ax.plot(weeks, ratings, marker='o', linewidth=2.5, markersize=8, 
            color='maroon', markerfacecolor='white', markeredgewidth=2,
            markeredgecolor='maroon')
    
    # Fill area under curve
    ax.fill_between(range(len(weeks)), ratings, alpha=0.2, color='maroon')
    
    # Add value labels on points
    for i, (week, rating) in enumerate(zip(weeks, ratings)):
        ax.text(i, rating + 0.1, f'{rating:.2f}', 
                ha='center', fontsize=10, fontweight='bold')
    
    # Styling
    ax.set_ylim(0, 5.5)
    ax.set_ylabel('Average Rating', fontsize=11, fontweight='bold')
    ax.set_title(title, fontsize=13, fontweight='bold', pad=15)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Reference lines
    ax.axhline(y=4.0, color='green', linestyle='--', alpha=0.5, linewidth=1.5)
    ax.axhline(y=3.0, color='orange', linestyle='--', alpha=0.5, linewidth=1.5)
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    # Save to buffer
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    plt.close()
    buffer.seek(0)
    
    return buffer


def create_pie_chart(data_dict, title="Distribution"):
    """
    Create a professional pie chart
    
    Args:
        data_dict: dict like {'Excellent': 10, 'Good': 20, ...}
    """
    fig, ax = plt.subplots(figsize=(7, 5))
    
    labels = list(data_dict.keys())
    sizes = list(data_dict.values())
    
    # Colors
    colors_list = ['#8B0000', '#A52A2A', '#CD5C5C', '#F08080', '#FFA07A']
    
    # Create pie chart
    wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                        colors=colors_list[:len(labels)],
                                        startangle=90,
                                        textprops={'fontsize': 11, 'fontweight': 'bold'})
    
    # Enhance autotext
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    
    # Save to buffer
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    plt.close()
    buffer.seek(0)
    
    return buffer


def create_problems_heatmap(problems_data):
    """
    Create a heatmap showing problem severity distribution
    
    Args:
        problems_data: dict with problem counts
    """
    fig, ax = plt.subplots(figsize=(8, 4))
    
    # Problem categories
    problems = ['Late to Class', 'Absenteeism', 'Long Videos']
    severity = ['Not Serious', 'Serious', 'Very Serious']
    
    # Data matrix
    data = np.array([
        [problems_data.get('late_not_serious', 0), 
         problems_data.get('late_serious', 0), 
         problems_data.get('late_very_serious', 0)],
        [problems_data.get('absent_not_serious', 0), 
         problems_data.get('absent_serious', 0), 
         problems_data.get('absent_very_serious', 0)],
        [problems_data.get('video_not_serious', 0), 
         problems_data.get('video_serious', 0), 
         problems_data.get('video_very_serious', 0)]
    ])
    
    # Create heatmap
    im = ax.imshow(data, cmap='RdYlGn_r', aspect='auto')
    
    # Set ticks
    ax.set_xticks(np.arange(len(severity)))
    ax.set_yticks(np.arange(len(problems)))
    ax.set_xticklabels(severity)
    ax.set_yticklabels(problems)
    
    # Rotate x labels
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    
    # Add text annotations
    for i in range(len(problems)):
        for j in range(len(severity)):
            text = ax.text(j, i, int(data[i, j]),
                          ha="center", va="center", color="black", fontweight='bold')
    
    ax.set_title("Problem Severity Distribution", fontsize=14, fontweight='bold', pad=15)
    
    # Colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Number of Reports', rotation=270, labelpad=15)
    
    plt.tight_layout()
    
    # Save to buffer
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    plt.close()
    buffer.seek(0)
    
    return buffer


def create_star_rating_visual(rating, max_stars=5):
    """
    Create a visual star rating image
    """
    fig, ax = plt.subplots(figsize=(6, 1))
    
    full_stars = int(rating)
    partial_star = rating - full_stars
    
    for i in range(max_stars):
        if i < full_stars:
            # Full star
            ax.text(i, 0, '★', fontsize=60, color='#FFD700', ha='center', va='center')
        elif i == full_stars and partial_star > 0:
            # Partial star (use gradient or different color)
            ax.text(i, 0, '★', fontsize=60, color='#FFD700', alpha=partial_star, ha='center', va='center')
            ax.text(i, 0, '☆', fontsize=60, color='#C0C0C0', alpha=1-partial_star, ha='center', va='center')
        else:
            # Empty star
            ax.text(i, 0, '☆', fontsize=60, color='#C0C0C0', ha='center', va='center')
    
    ax.set_xlim(-0.5, max_stars - 0.5)
    ax.set_ylim(-0.5, 0.5)
    ax.axis('off')
    
    plt.tight_layout()
    
    # Save to buffer
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', transparent=True)
    plt.close()
    buffer.seek(0)
    
    return buffer


# ============================================================================
# CUSTOM STYLES
# ============================================================================

def get_custom_styles():
    """Create enhanced custom paragraph styles for reports"""
    styles = getSampleStyleSheet()
    
    # Modern Title
    styles.add(ParagraphStyle(
        name='ModernTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#8B0000'),  # Maroon
        spaceAfter=20,
        spaceBefore=10,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    ))
    
    # Subtitle
    styles.add(ParagraphStyle(
        name='ModernSubtitle',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.HexColor('#A52A2A'),  # Brown
        spaceAfter=15,
        spaceBefore=10,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    ))
    
    # Section Header
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=colors.HexColor('#8B0000'),
        spaceAfter=10,
        spaceBefore=15,
        fontName='Helvetica-Bold',
        borderPadding=5,
        leftIndent=0,
    ))
    
    # Info Text
    styles.add(ParagraphStyle(
        name='InfoText',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.black,
        spaceAfter=6,
        leading=14,
    ))
    
    # Highlight Box
    styles.add(ParagraphStyle(
        name='HighlightBox',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#1a237e'),
        backColor=colors.HexColor('#E3F2FD'),
        borderPadding=10,
        spaceAfter=10,
        fontName='Helvetica-Bold'
    ))
    
    return styles


def get_rating_descriptor(rating):
    """Get descriptive text for rating"""
    if rating >= 4.5:
        return "Outstanding"
    elif rating >= 4.0:
        return "Excellent"
    elif rating >= 3.5:
        return "Very Good"
    elif rating >= 3.0:
        return "Good"
    elif rating >= 2.5:
        return "Satisfactory"
    elif rating >= 2.0:
        return "Fair"
    else:
        return "Needs Improvement"


def create_header_table(title, subtitle=""):
    """Create a professional header table"""
    header_data = [[title]]
    if subtitle:
        header_data.append([subtitle])
    
    header_table = Table(header_data, colWidths=[6.5*inch])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 20),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#8B0000')),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFF5F5')),
        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#8B0000')),
    ]))
    
    if subtitle:
        header_table.setStyle(TableStyle([
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, 1), 14),
            ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor('#A52A2A')),
        ]))
    
    return header_table


# ============================================================================
# MAIN REPORT GENERATION FUNCTIONS
# ============================================================================

def generate_teacher_evaluation_report(teacher, academic_year=None, semester=None):
    """
    Generate comprehensive PDF report for a teacher with charts and visualizations
    
    Args:
        teacher: TeacherProfile instance
        academic_year: Optional AcademicYear filter
        semester: Optional Semester filter
    
    Returns:
        BytesIO buffer containing the PDF
    """
    from .models import Evaluation
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    elements = []
    styles = get_custom_styles()
    
    # ========== HEADER ==========
    elements.append(create_header_table(
        "Teacher Evaluation Report",
        f"Academic Performance Analysis"
    ))
    elements.append(Spacer(1, 0.3*inch))
    
    # ========== TEACHER INFORMATION ==========
    teacher_info_data = [
        ['Teacher Name:', teacher.user.get_full_name()],
        ['Employee ID:', teacher.employee_id],
        ['Department:', str(teacher.department)],
        ['Qualification:', teacher.qualification],
        ['Experience:', f'{teacher.experience_years} years'],
    ]
    
    if academic_year:
        teacher_info_data.append(['Academic Year:', str(academic_year.name)])
    if semester:
        teacher_info_data.append(['Semester:', str(semester.name)])
    
    teacher_info_data.append(['Report Generated:', datetime.now().strftime("%B %d, %Y at %I:%M %p")])
    
    info_table = Table(teacher_info_data, colWidths=[2*inch, 4.5*inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#8B0000')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.lightgrey),
    ]))
    
    elements.append(info_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # ========== GET EVALUATION DATA ==========
    evaluations = Evaluation.objects.filter(teacher=teacher).select_related(
        'student', 'student__user', 'subject', 'academic_year', 'semester'
    )
    
    if academic_year:
        evaluations = evaluations.filter(academic_year=academic_year)
    if semester:
        evaluations = evaluations.filter(semester=semester)
    
    total_evaluations = evaluations.count()
    
    if total_evaluations == 0:
        elements.append(Paragraph(
            "No evaluations available for the selected period.",
            styles['InfoText']
        ))
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    # Calculate statistics
    average_rating = sum([e.get_average_rating() for e in evaluations]) / total_evaluations
    presentation_avg = sum([e.get_presentation_average() for e in evaluations]) / total_evaluations
    development_avg = sum([e.get_development_average() for e in evaluations]) / total_evaluations
    student_behavior_avg = sum([e.get_student_behavior_average() for e in evaluations]) / total_evaluations
    wrapup_avg = sum([e.get_wrapup_average() for e in evaluations]) / total_evaluations
    
    # ========== OVERALL RATING WITH GAUGE CHART ==========
    elements.append(Paragraph("Overall Performance", styles['SectionHeader']))
    
    # Create gauge chart
    gauge_buffer = create_rating_gauge_chart(average_rating, title="Overall Average Rating")
    gauge_img = Image(gauge_buffer, width=5*inch, height=2.5*inch)
    elements.append(gauge_img)
    elements.append(Spacer(1, 0.2*inch))
    
    # Rating summary box
    rating_desc = get_rating_descriptor(average_rating)
    summary_data = [[
        f"Rating: {average_rating:.2f}/5.00",
        f"Descriptor: {rating_desc}",
        f"Total Evaluations: {total_evaluations}"
    ]]
    
    summary_table = Table(summary_data, colWidths=[2.2*inch, 2.2*inch, 2.1*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFF5F5')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#8B0000')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#8B0000')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # ========== CATEGORY BREAKDOWN WITH BAR CHART ==========
    elements.append(PageBreak())
    elements.append(Paragraph("Performance by Category", styles['SectionHeader']))
    
    categories_data = {
        'Presentation': presentation_avg,
        'Development': development_avg,
        'Student Behavior': student_behavior_avg,
        'Wrap-up': wrapup_avg
    }
    
    # Bar chart
    bar_buffer = create_category_bar_chart(categories_data)
    bar_img = Image(bar_buffer, width=6.5*inch, height=4*inch)
    elements.append(bar_img)
    elements.append(Spacer(1, 0.2*inch))
    
    # Category details table
    category_table_data = [
        ['Category', 'Average Score', 'Descriptor'],
        ['Presentation', f'{presentation_avg:.2f}', get_rating_descriptor(presentation_avg)],
        ['Development', f'{development_avg:.2f}', get_rating_descriptor(development_avg)],
        ['Student Behavior', f'{student_behavior_avg:.2f}', get_rating_descriptor(student_behavior_avg)],
        ['Wrap-up', f'{wrapup_avg:.2f}', get_rating_descriptor(wrapup_avg)],
    ]
    
    category_table = Table(category_table_data, colWidths=[2.5*inch, 2*inch, 2*inch])
    category_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8B0000')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FFF5F5')]),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    elements.append(category_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # ========== RADAR CHART ==========
    elements.append(PageBreak())
    elements.append(Paragraph("Multi-Dimensional Performance View", styles['SectionHeader']))
    
    radar_buffer = create_radar_chart(categories_data)
    radar_img = Image(radar_buffer, width=5.5*inch, height=5.5*inch)
    elements.append(radar_img)
    elements.append(Spacer(1, 0.3*inch))
    
    # ========== PERFORMANCE BY SUBJECT ==========
    elements.append(PageBreak())
    elements.append(Paragraph("Performance by Subject", styles['SectionHeader']))
    
    # Group by subject
    subjects_dict = {}
    for eval in evaluations:
        subject_code = eval.subject.code
        if subject_code not in subjects_dict:
            subjects_dict[subject_code] = {
                'name': eval.subject.name,
                'evaluations': []
            }
        subjects_dict[subject_code]['evaluations'].append(eval)
    
    subject_table_data = [['Subject Code', 'Subject Name', 'Evaluations', 'Average Rating', 'Performance']]
    
    for code, data in sorted(subjects_dict.items()):
        evals = data['evaluations']
        avg = sum([e.get_average_rating() for e in evals]) / len(evals)
        subject_table_data.append([
            code,
            data['name'],
            str(len(evals)),
            f'{avg:.2f}',
            get_rating_descriptor(avg)
        ])
    
    subject_table = Table(subject_table_data, colWidths=[1.3*inch, 2.2*inch, 1.2*inch, 1.3*inch, 1.5*inch])
    subject_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8B0000')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FFF5F5')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(subject_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # ========== PROBLEMS ANALYSIS ==========
    elements.append(PageBreak())
    elements.append(Paragraph("Problems Identified", styles['SectionHeader']))
    
    # Collect problem data
    late_issues = [e.problem_late for e in evaluations]
    absent_issues = [e.problem_absent for e in evaluations]
    video_issues = [e.problem_video for e in evaluations]
    
    problems_data = {
        'late_not_serious': late_issues.count(1),
        'late_serious': late_issues.count(2),
        'late_very_serious': late_issues.count(3),
        'absent_not_serious': absent_issues.count(1),
        'absent_serious': absent_issues.count(2),
        'absent_very_serious': absent_issues.count(3),
        'video_not_serious': video_issues.count(1),
        'video_serious': video_issues.count(2),
        'video_very_serious': video_issues.count(3),
    }
    
    # Heatmap
    heatmap_buffer = create_problems_heatmap(problems_data)
    heatmap_img = Image(heatmap_buffer, width=6.5*inch, height=3.5*inch)
    elements.append(heatmap_img)
    elements.append(Spacer(1, 0.3*inch))
    
    # Problem summary
    problem_summary_data = [
        ['Problem Type', 'Not Serious', 'Serious', 'Very Serious', 'Total'],
        ['Late to Class', 
         str(problems_data['late_not_serious']),
         str(problems_data['late_serious']),
         str(problems_data['late_very_serious']),
         str(sum([problems_data['late_not_serious'], problems_data['late_serious'], problems_data['late_very_serious']]))],
        ['Absenteeism',
         str(problems_data['absent_not_serious']),
         str(problems_data['absent_serious']),
         str(problems_data['absent_very_serious']),
         str(sum([problems_data['absent_not_serious'], problems_data['absent_serious'], problems_data['absent_very_serious']]))],
        ['Long Videos (>30min)',
         str(problems_data['video_not_serious']),
         str(problems_data['video_serious']),
         str(problems_data['video_very_serious']),
         str(sum([problems_data['video_not_serious'], problems_data['video_serious'], problems_data['video_very_serious']]))],
    ]
    
    problem_table = Table(problem_summary_data, colWidths=[2*inch, 1.3*inch, 1.3*inch, 1.3*inch, 1.3*inch])
    problem_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8B0000')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FFF5F5')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(problem_table)
    
    # ========== FOOTER ==========
    elements.append(Spacer(1, 0.5*inch))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#8B0000')))
    elements.append(Spacer(1, 0.1*inch))
    
    footer_text = f"<para align='center'><font size=9 color='grey'>Osmeña Colleges - Teacher Evaluation System | " \
                   f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} | " \
                   f"Confidential Document</font></para>"
    elements.append(Paragraph(footer_text, styles['InfoText']))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    return buffer


# Continue with generate_department_report and generate_detailed_evaluation_report...
# (Due to length, I'll create them in the next response)

"""
Enhanced PDF Reports - Part 2
==============================
Department and Evaluation Detail Reports with visualizations
"""

# NOTE: This is a continuation of pdf_reports_enhanced.py
# Add these functions to the main file

def generate_department_report(department, academic_year=None, semester=None):
    """
    Generate comprehensive department report with comparative charts
    
    Args:
        department: Department instance
        academic_year: Optional AcademicYear filter
        semester: Optional Semester filter
    
    Returns:
        BytesIO buffer containing the PDF
    """
    from .models import TeacherProfile, Evaluation
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    elements = []
    styles = get_custom_styles()
    
    # ========== HEADER ==========
    elements.append(create_header_table(
        "Department Evaluation Report",
        f"{department.name} ({department.code})"
    ))
    elements.append(Spacer(1, 0.3*inch))
    
    # ========== DEPARTMENT INFO ==========
    teachers = TeacherProfile.objects.filter(department=department)
    total_teachers = teachers.count()
    
    dept_info_data = [
        ['Department:', department.name],
        ['Department Code:', department.code],
        ['Head of Department:', department.head_of_department or 'Not Assigned'],
        ['Total Teachers:', str(total_teachers)],
    ]
    
    if academic_year:
        dept_info_data.append(['Academic Year:', str(academic_year.name)])
    if semester:
        dept_info_data.append(['Semester:', str(semester.name)])
    
    dept_info_data.append(['Report Generated:', datetime.now().strftime("%B %d, %Y at %I:%M %p")])
    
    info_table = Table(dept_info_data, colWidths=[2.5*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#8B0000')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.lightgrey),
    ]))
    
    elements.append(info_table)
    elements.append(Spacer(1, 0.3*inch))
    
    if total_teachers == 0:
        elements.append(Paragraph("No teachers found in this department.", styles['InfoText']))
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    # ========== DEPARTMENT STATISTICS ==========
    teacher_stats = []
    
    for teacher in teachers:
        evaluations = Evaluation.objects.filter(teacher=teacher)
        
        if academic_year:
            evaluations = evaluations.filter(academic_year=academic_year)
        if semester:
            evaluations = evaluations.filter(semester=semester)
        
        eval_count = evaluations.count()
        if eval_count > 0:
            avg_rating = sum([e.get_average_rating() for e in evaluations]) / eval_count
            teacher_stats.append({
                'teacher': teacher,
                'avg_rating': avg_rating,
                'eval_count': eval_count
            })
    
    if not teacher_stats:
        elements.append(Paragraph("No evaluation data available for this period.", styles['InfoText']))
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    # Sort by rating
    teacher_stats.sort(key=lambda x: x['avg_rating'], reverse=True)
    
    # Calculate department average
    dept_avg = sum([t['avg_rating'] for t in teacher_stats]) / len(teacher_stats)
    
    # ========== DEPARTMENT OVERVIEW GAUGE ==========
    elements.append(Paragraph("Department Overall Performance", styles['SectionHeader']))
    
    gauge_buffer = create_rating_gauge_chart(dept_avg, title="Department Average Rating")
    gauge_img = Image(gauge_buffer, width=5*inch, height=2.5*inch)
    elements.append(gauge_img)
    elements.append(Spacer(1, 0.2*inch))
    
    # Summary box
    summary_data = [[
        f"Department Avg: {dept_avg:.2f}/5.00",
        f"Descriptor: {get_rating_descriptor(dept_avg)}",
        f"Teachers Evaluated: {len(teacher_stats)}/{total_teachers}"
    ]]
    
    summary_table = Table(summary_data, colWidths=[2.2*inch, 2.2*inch, 2.1*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFF5F5')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#8B0000')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#8B0000')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 0.4*inch))
    
    # ========== TEACHER RANKINGS BAR CHART ==========
    elements.append(PageBreak())
    elements.append(Paragraph("Teacher Performance Rankings", styles['SectionHeader']))
    
    # Create bar chart for top 10 teachers
    top_teachers = teacher_stats[:min(10, len(teacher_stats))]
    teacher_names = {t['teacher'].user.last_name[:15]: t['avg_rating'] for t in top_teachers}
    
    bar_buffer = create_category_bar_chart(teacher_names, title="Top Teacher Ratings")
    bar_img = Image(bar_buffer, width=6.5*inch, height=4.5*inch)
    elements.append(bar_img)
    elements.append(Spacer(1, 0.3*inch))
    
    # ========== TEACHER RANKINGS TABLE ==========
    elements.append(Paragraph("Complete Teacher Rankings", styles['SectionHeader']))
    
    ranking_data = [['Rank', 'Teacher Name', 'Employee ID', 'Evaluations', 'Avg Rating', 'Performance']]
    
    for idx, stat in enumerate(teacher_stats, 1):
        teacher = stat['teacher']
        ranking_data.append([
            str(idx),
            teacher.user.get_full_name(),
            teacher.employee_id,
            str(stat['eval_count']),
            f"{stat['avg_rating']:.2f}",
            get_rating_descriptor(stat['avg_rating'])
        ])
    
    ranking_table = Table(ranking_data, colWidths=[0.6*inch, 2*inch, 1.2*inch, 1*inch, 1*inch, 1.5*inch])
    ranking_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8B0000')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FFF5F5')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        # Highlight top 3
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#FFD700')),  # Gold
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#C0C0C0')),  # Silver
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#CD7F32')),  # Bronze
    ]))
    
    elements.append(ranking_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # ========== RATING DISTRIBUTION PIE CHART ==========
    elements.append(PageBreak())
    elements.append(Paragraph("Rating Distribution Analysis", styles['SectionHeader']))
    
    # Categorize ratings
    excellent = sum(1 for t in teacher_stats if t['avg_rating'] >= 4.5)
    very_good = sum(1 for t in teacher_stats if 4.0 <= t['avg_rating'] < 4.5)
    good = sum(1 for t in teacher_stats if 3.5 <= t['avg_rating'] < 4.0)
    satisfactory = sum(1 for t in teacher_stats if 3.0 <= t['avg_rating'] < 3.5)
    needs_improvement = sum(1 for t in teacher_stats if t['avg_rating'] < 3.0)
    
    distribution_data = {}
    if excellent > 0:
        distribution_data['Excellent (4.5+)'] = excellent
    if very_good > 0:
        distribution_data['Very Good (4.0-4.5)'] = very_good
    if good > 0:
        distribution_data['Good (3.5-4.0)'] = good
    if satisfactory > 0:
        distribution_data['Satisfactory (3.0-3.5)'] = satisfactory
    if needs_improvement > 0:
        distribution_data['Needs Improvement (<3.0)'] = needs_improvement
    
    if distribution_data:
        pie_buffer = create_pie_chart(distribution_data, title="Teacher Rating Distribution")
        pie_img = Image(pie_buffer, width=6*inch, height=4.5*inch)
        elements.append(pie_img)
    
    # ========== FOOTER ==========
    elements.append(Spacer(1, 0.5*inch))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#8B0000')))
    elements.append(Spacer(1, 0.1*inch))
    
    footer_text = f"<para align='center'><font size=9 color='grey'>Osmeña Colleges - Department Report | " \
                   f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} | " \
                   f"Confidential Document</font></para>"
    elements.append(Paragraph(footer_text, styles['InfoText']))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    return buffer


def generate_detailed_evaluation_report(evaluation):
    """
    Generate detailed PDF report for a single evaluation with all criteria
    
    Args:
        evaluation: Evaluation instance
    
    Returns:
        BytesIO buffer containing the PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    elements = []
    styles = get_custom_styles()
    
    # ========== HEADER ==========
    elements.append(create_header_table(
        "Detailed Evaluation Report",
        "Complete Assessment Breakdown"
    ))
    elements.append(Spacer(1, 0.2*inch))
    
    # ========== EVALUATION INFO ==========
    eval_info_data = [
        ['Teacher:', evaluation.teacher.user.get_full_name()],
        ['Employee ID:', evaluation.teacher.employee_id],
        ['Subject:', f"{evaluation.subject.code} - {evaluation.subject.name}"],
        ['Department:', str(evaluation.teacher.department)],
        ['Student ID:', evaluation.student.student_id_number],
        ['Academic Year:', str(evaluation.academic_year.name)],
        ['Semester:', str(evaluation.semester.name)],
        ['Evaluation Date:', evaluation.created_at.strftime("%B %d, %Y at %I:%M %p")],
        ['Report Generated:', datetime.now().strftime("%B %d, %Y at %I:%M %p")],
    ]
    
    info_table = Table(eval_info_data, colWidths=[2*inch, 4.5*inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#8B0000')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.lightgrey),
    ]))
    
    elements.append(info_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # ========== OVERALL RATING ==========
    overall_avg = evaluation.get_average_rating()
    
    elements.append(Paragraph("Overall Rating", styles['SectionHeader']))
    
    # Star rating visual
    star_buffer = create_star_rating_visual(overall_avg)
    star_img = Image(star_buffer, width=5*inch, height=0.8*inch)
    elements.append(star_img)
    elements.append(Spacer(1, 0.1*inch))
    
    # Overall summary
    overall_data = [[
        f"Overall Score: {overall_avg:.2f}/5.00",
        f"Performance: {get_rating_descriptor(overall_avg)}"
    ]]
    
    overall_table = Table(overall_data, colWidths=[3.25*inch, 3.25*inch])
    overall_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFF5F5')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#8B0000')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#8B0000')),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    
    elements.append(overall_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # ========== CATEGORY AVERAGES WITH RADAR CHART ==========
    categories_data = {
        'Presentation': evaluation.get_presentation_average(),
        'Development': evaluation.get_development_average(),
        'Student Behavior': evaluation.get_student_behavior_average(),
        'Wrap-up': evaluation.get_wrapup_average()
    }
    
    elements.append(Paragraph("Category Performance Overview", styles['SectionHeader']))
    
    radar_buffer = create_radar_chart(categories_data, title="Performance Radar")
    radar_img = Image(radar_buffer, width=5*inch, height=5*inch)
    elements.append(radar_img)
    elements.append(Spacer(1, 0.2*inch))
    
    # Category table
    category_data = [
        ['Category', 'Score', 'Rating'],
        ['Presentation', f"{categories_data['Presentation']:.2f}", get_rating_descriptor(categories_data['Presentation'])],
        ['Development', f"{categories_data['Development']:.2f}", get_rating_descriptor(categories_data['Development'])],
        ['Student Behavior', f"{categories_data['Student Behavior']:.2f}", get_rating_descriptor(categories_data['Student Behavior'])],
        ['Wrap-up', f"{categories_data['Wrap-up']:.2f}", get_rating_descriptor(categories_data['Wrap-up'])],
    ]
    
    category_table = Table(category_data, colWidths=[2.5*inch, 2*inch, 2*inch])
    category_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8B0000')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FFF5F5')]),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    elements.append(category_table)
    
    # ========== DETAILED CRITERIA (New Page) ==========
    elements.append(PageBreak())
    elements.append(Paragraph("Part I: Presentation of Lesson", styles['SectionHeader']))
    
    part1_data = [
        ['Criterion', 'Score'],
        ['Communicates clearly the objectives', str(evaluation.presentation_objectives)],
        ['Uses motivational techniques', str(evaluation.presentation_motivation)],
        ['Relates previous lesson to present', str(evaluation.presentation_relation)],
        ['Checks assignments', str(evaluation.presentation_assignments)],
        ['Average', f"{evaluation.get_presentation_average():.2f}"],
    ]
    
    part1_table = Table(part1_data, colWidths=[4.5*inch, 2*inch])
    part1_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3f51b5')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E3F2FD')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#1a237e')),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(part1_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Part II: Development (showing first 7 items as example)
    elements.append(Paragraph("Part II: Development of Lesson", styles['SectionHeader']))
    
    part2_data = [
        ['Criterion', 'Score'],
        ['Anticipates difficulties of students', str(evaluation.dev_anticipates)],
        ['Demonstrates mastery of lesson', str(evaluation.dev_mastery)],
        ['Develops lesson logically', str(evaluation.dev_logical)],
        ['Provides opportunities for free expression', str(evaluation.dev_expression)],
        ['Student participation in decision making', str(evaluation.dev_participation)],
        ['Asks questions of various levels', str(evaluation.dev_questions)],
        ['Integrates values in lesson', str(evaluation.dev_values)],
        ['Provides appropriate reinforcement', str(evaluation.dev_reinforcement)],
        ['Keeps majority of students involved', str(evaluation.dev_involvement)],
        ['Speaks in well-modulated voice', str(evaluation.dev_voice)],
        ['Observes correct grammar', str(evaluation.dev_grammar)],
        ['Monitors student progress', str(evaluation.dev_monitoring)],
        ['Utilizes time productively', str(evaluation.dev_time)],
        ['Average', f"{evaluation.get_development_average():.2f}"],
    ]
    
    part2_table = Table(part2_data, colWidths=[4.5*inch, 2*inch])
    part2_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E8F5E9')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#1B5E20')),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    elements.append(part2_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Part III: Student Behavior
    elements.append(Paragraph("Part III: Expected Student Behavior", styles['SectionHeader']))
    
    part3_data = [
        ['Criterion', 'Score'],
        ['Students answer at designed cognitive level', str(evaluation.student_answers)],
        ['Students ask relevant questions', str(evaluation.student_questions)],
        ['Students actively engaged in learning', str(evaluation.student_engagement)],
        ['Students work within time frame', str(evaluation.student_timeframe)],
        ['Students abide by majority decision', str(evaluation.student_majority)],
        ['Average', f"{evaluation.get_student_behavior_average():.2f}"],
    ]
    
    part3_table = Table(part3_data, colWidths=[4.5*inch, 2*inch])
    part3_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF9800')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#FFF3E0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#E65100')),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(part3_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Part IV: Wrap-up
    elements.append(Paragraph("Part IV: Wrap-up", styles['SectionHeader']))
    
    part4_data = [
        ['Criterion', 'Score'],
        ['Provides opportunities to demonstrate learnings', str(evaluation.wrapup_demonstrate)],
        ['Students synthesize learning through integration', str(evaluation.wrapup_synthesize)],
        ['Average', f"{evaluation.get_wrapup_average():.2f}"],
    ]
    
    part4_table = Table(part4_data, colWidths=[4.5*inch, 2*inch])
    part4_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00BCD4')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E0F7FA')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#006064')),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(part4_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # ========== PROBLEMS MET ==========
    elements.append(PageBreak())
    elements.append(Paragraph("Part V: Problems Identified", styles['SectionHeader']))
    
    problem_severity = {
        1: ('Not Serious', colors.HexColor('#4CAF50')),
        2: ('Serious', colors.HexColor('#FF9800')),
        3: ('Very Serious', colors.HexColor('#F44336'))
    }
    
    problems_data = [
        ['Problem', 'Severity Level', 'Rating'],
        ['Late in coming to class', problem_severity[evaluation.problem_late][0], str(evaluation.problem_late)],
        ['Absenteeism', problem_severity[evaluation.problem_absent][0], str(evaluation.problem_absent)],
        ['Very long video presentation (>30min)', problem_severity[evaluation.problem_video][0], str(evaluation.problem_video)],
    ]
    
    problems_table = Table(problems_data, colWidths=[3*inch, 2*inch, 1.5*inch])
    problems_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8B0000')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        # Color code severity
        ('BACKGROUND', (1, 1), (1, 1), problem_severity[evaluation.problem_late][1]),
        ('BACKGROUND', (1, 2), (1, 2), problem_severity[evaluation.problem_absent][1]),
        ('BACKGROUND', (1, 3), (1, 3), problem_severity[evaluation.problem_video][1]),
    ]))
    
    elements.append(problems_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # ========== SUGGESTIONS ==========
    if evaluation.suggestions:
        elements.append(Paragraph("Part VI: Suggestions for Improvement", styles['SectionHeader']))
        
        suggestions_box = Table([[evaluation.suggestions]], colWidths=[6.5*inch])
        suggestions_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#E7F3FF')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#0066CC')),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ]))
        
        elements.append(suggestions_box)
    
    # ========== FOOTER ==========
    elements.append(Spacer(1, 0.5*inch))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#8B0000')))
    elements.append(Spacer(1, 0.1*inch))
    
    footer_text = f"<para align='center'><font size=9 color='grey'>Osmeña Colleges - Detailed Evaluation Report | " \
                   f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} | " \
                   f"Confidential Document</font></para>"
    elements.append(Paragraph(footer_text, styles['InfoText']))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    return buffer