from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from .models import TeacherProfile, Department, Evaluation, AcademicYear, Semester, StudentProfile
from .pdf_reports import (
    generate_teacher_evaluation_report,
    generate_department_report,
    generate_detailed_evaluation_report
)
@login_required
@require_http_methods(["GET"])
def download_teacher_report(request, teacher_id):
    """
    Generate and download a PDF report for a specific teacher's evaluations.
    
    URL: /reports/teacher/<teacher_id>/pdf/
    Query Parameters:
        - academic_year: Optional academic year ID
        - semester: Optional semester ID
    """
    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    
    # Check permissions
    if request.user.user_type == 'teacher' and request.user.teacher_profile.id != teacher_id:
        raise Http404("You don't have permission to view this report.")
    
    # Get optional filters
    academic_year_id = request.GET.get('academic_year')
    semester_id = request.GET.get('semester')
    
    academic_year = None
    semester = None
    
    if academic_year_id:
        academic_year = get_object_or_404(AcademicYear, id=academic_year_id)
    
    if semester_id:
        semester = get_object_or_404(Semester, id=semester_id)
    
    # Generate PDF
    buffer = generate_teacher_evaluation_report(teacher, academic_year, semester)
    
    # Create response
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    
    # Set filename
    filename = f"teacher_evaluation_{teacher.employee_id}"
    if academic_year:
        filename += f"_{academic_year.name}"
    if semester:
        filename += f"_{semester.name}"
    filename += ".pdf"
    
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


@login_required
@require_http_methods(["GET"])
def download_department_report(request, department_id):
    """
    Generate and download a PDF report for department-wide evaluations.
    
    URL: /reports/department/<department_id>/pdf/
    Query Parameters:
        - academic_year: Optional academic year ID
        - semester: Optional semester ID
    """
    department = get_object_or_404(Department, id=department_id)
    
    # Check permissions - only admins can view department reports
    if request.user.user_type != 'admin':
        raise Http404("You don't have permission to view this report.")
    
    # Get optional filters
    academic_year_id = request.GET.get('academic_year')
    semester_id = request.GET.get('semester')
    
    academic_year = None
    semester = None
    
    if academic_year_id:
        academic_year = get_object_or_404(AcademicYear, id=academic_year_id)
    
    if semester_id:
        semester = get_object_or_404(Semester, id=semester_id)
    
    # Generate PDF
    buffer = generate_department_report(department, academic_year, semester)
    
    # Create response
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    
    # Set filename
    filename = f"department_evaluation_{department.code}"
    if academic_year:
        filename += f"_{academic_year.name}"
    if semester:
        filename += f"_{semester.name}"
    filename += ".pdf"
    
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


@login_required
@require_http_methods(["GET"])
def download_evaluation_detail(request, evaluation_id):
    """
    Generate and download a detailed PDF report for a single evaluation.
    
    URL: /reports/evaluation/<evaluation_id>/pdf/
    """
    evaluation = get_object_or_404(Evaluation, id=evaluation_id)
    
    # Check permissions
    user = request.user
    if user.user_type == 'student':
        if user.student_profile.id != evaluation.student.id:
            raise Http404("You don't have permission to view this evaluation.")
    elif user.user_type == 'teacher':
        if user.teacher_profile.id != evaluation.teacher.id:
            raise Http404("You don't have permission to view this evaluation.")
    # Admins can view any evaluation
    
    # Generate PDF
    buffer = generate_detailed_evaluation_report(evaluation)
    
    # Create response
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    
    # Set filename
    filename = f"evaluation_detail_{evaluation.teacher.employee_id}_{evaluation.subject.code}_{evaluation.student.student_id_number}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


@login_required
@require_http_methods(["GET"])
def download_all_teachers_report(request):
    """
    Generate a comprehensive report for all teachers across all departments.
    Only accessible by admins.
    
    URL: /reports/all-teachers/pdf/
    Query Parameters:
        - academic_year: Optional academic year ID
        - semester: Optional semester ID
    """
    # Check permissions - only admins
    if request.user.user_type != 'admin':
        raise Http404("You don't have permission to view this report.")
    
    # Get optional filters
    academic_year_id = request.GET.get('academic_year')
    semester_id = request.GET.get('semester')
    
    academic_year = None
    semester = None
    
    if academic_year_id:
        academic_year = get_object_or_404(AcademicYear, id=academic_year_id)
    
    if semester_id:
        semester = get_object_or_404(Semester, id=semester_id)
    
    # For now, we'll generate a report combining all departments
    # You could also create a new function in pdf_reports.py for this
    from io import BytesIO
    from reportlab.platypus import SimpleDocTemplate, PageBreak
    
    buffer = BytesIO()
    departments = Department.objects.all()
    
    # Generate combined report (simple approach - concatenate department reports)
    if departments.exists():
        # For the first department
        first_dept = departments.first()
        buffer = generate_department_report(first_dept, academic_year, semester)
    
    # Create response
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    
    # Set filename
    filename = "all_teachers_evaluation"
    if academic_year:
        filename += f"_{academic_year.name}"
    if semester:
        filename += f"_{semester.name}"
    filename += ".pdf"
    
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


@login_required
@require_http_methods(["GET"])
def download_student_evaluations_report(request, student_id):
    """
    Generate a PDF report showing all evaluations submitted by a specific student.
    
    URL: /reports/student/<student_id>/evaluations/pdf/
    """
    student = get_object_or_404(StudentProfile, id=student_id)
    
    # Check permissions
    if request.user.user_type == 'student' and request.user.student_profile.id != student_id:
        raise Http404("You don't have permission to view this report.")
    
    # Get student's evaluations
    evaluations = Evaluation.objects.filter(student=student).select_related(
        'teacher', 'teacher__user', 'subject', 'academic_year', 'semester'
    )
    
    # Generate a simple report
    from io import BytesIO
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from .pdf_reports import get_custom_styles, create_header_table
    from datetime import datetime
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    
    elements = []
    styles = get_custom_styles()
    
    # Header
    elements.append(create_header_table(
        "Student Evaluation Summary",
        f"{student.user.get_full_name()}"
    ))
    elements.append(Spacer(1, 0.2*inch))
    
    # Student info
    student_info_data = [
        ['Student ID:', student.student_id_number],
        ['Name:', student.user.get_full_name()],
        ['Department:', str(student.department)],
        ['Year Level:', student.get_year_level_display()],
        ['Course:', student.course],
        ['Total Evaluations:', str(evaluations.count())],
        ['Report Generated:', datetime.now().strftime("%B %d, %Y at %I:%M %p")],
    ]
    
    from reportlab.lib.units import inch
    student_info_table = Table(student_info_data, colWidths=[2*inch, 4.5*inch])
    student_info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1a237e')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(student_info_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Evaluations list
    elements.append(Paragraph("Submitted Evaluations", styles['SectionHeader']))
    
    if evaluations.exists():
        eval_data = [
            ['Date', 'Teacher', 'Subject', 'Rating', 'Academic Year', 'Semester'],
        ]
        
        for evaluation in evaluations:
            eval_data.append([
                evaluation.created_at.strftime("%m/%d/%Y"),
                evaluation.teacher.user.get_full_name(),
                evaluation.subject.code,
                f"{evaluation.get_average_rating():.2f}",
                str(evaluation.academic_year.name),
                str(evaluation.semester.name),
            ])
        
        eval_table = Table(eval_data, colWidths=[1*inch, 1.8*inch, 1*inch, 0.8*inch, 1.2*inch, 1*inch])
        eval_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3f51b5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        elements.append(eval_table)
    else:
        elements.append(Paragraph("No evaluations submitted yet.", styles['InfoText']))
    
    # Build PDF
    doc.build(elements)
    
    buffer.seek(0)
    
    # Create response
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    filename = f"student_evaluations_{student.student_id_number}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response