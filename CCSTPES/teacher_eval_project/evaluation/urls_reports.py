"""
URL Configuration for PDF Reports
==================================

Add these URL patterns to your main urls.py or create a separate reports app.

Usage:
    In your main urls.py:
    
    from django.urls import path, include
    
    urlpatterns = [
        # ... other patterns
        path('reports/', include('your_app.urls_reports')),
    ]
"""

from django.urls import path
from . import views_reports

app_name = 'reports'

urlpatterns = [
    # Teacher evaluation reports
    path(
        'teacher/<int:teacher_id>/pdf/',
        views_reports.download_teacher_report,
        name='teacher_report_pdf'
    ),
    
    # Department reports
    path(
        'department/<int:department_id>/pdf/',
        views_reports.download_department_report,
        name='department_report_pdf'
    ),
    
    # Detailed evaluation report
    path(
        'evaluation/<int:evaluation_id>/pdf/',
        views_reports.download_evaluation_detail,
        name='evaluation_detail_pdf'
    ),
    
    # All teachers comprehensive report
    path(
        'all-teachers/pdf/',
        views_reports.download_all_teachers_report,
        name='all_teachers_report_pdf'
    ),
    
    # Student evaluations report
    path(
        'student/<int:student_id>/evaluations/pdf/',
        views_reports.download_student_evaluations_report,
        name='student_evaluations_pdf'
    ),
]

# Example usage in templates:
"""
<!-- Download teacher report -->
<a href="{% url 'reports:teacher_report_pdf' teacher.id %}?academic_year=1&semester=2" 
   class="btn btn-primary">
    Download Teacher Report
</a>

<!-- Download department report -->
<a href="{% url 'reports:department_report_pdf' department.id %}" 
   class="btn btn-success">
    Download Department Report
</a>

<!-- Download evaluation detail -->
<a href="{% url 'reports:evaluation_detail_pdf' evaluation.id %}" 
   class="btn btn-info">
    Download Evaluation Details
</a>

<!-- Download student evaluations -->
<a href="{% url 'reports:student_evaluations_pdf' student.id %}" 
   class="btn btn-warning">
    Download My Evaluations
</a>
"""