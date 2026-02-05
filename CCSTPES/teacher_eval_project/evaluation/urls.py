from django.urls import path
from . import views 

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_choice, name='register_choice'),
    path('register/student/', views.student_register, name='student_register'),
    path('register/teacher/', views.teacher_register, name='teacher_register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    path('send-verification-code/', views.send_verification_code, name='send_verification_code'),
    path('check-verification-status/', views.check_verification_status, name='check_verification_status'),
    # path('verify-email-code/', views.verify_email_code, name='verify_email_code'),
    path('debug-user/<int:user_id>/', views.debug_user_status, name='debug_user_status'),
    # Admin URLs
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/approve-student/<int:user_id>/', views.approve_student, name='approve_student'),
    path('admin-dashboard/pending-students/', views.manage_pending_students, name='manage_pending_students'),
    # path('ajax/check-verification/', views.check_verification, name='check_verification'),
    path('admin-dashboard/student/<int:student_id>/', views.student_detail, name='student_detail'),
    path('admin-dashboard/student/<int:student_id>/edit/', views.edit_student, name='edit_student'),
    path('admin-dashboard/teachers/', views.manage_teachers, name='manage_teachers'),
    path('admin-dashboard/subjects/', views.manage_subjects, name='manage_subjects'),
    path('admin-dashboard/delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('admin-dashboard/view-cor/<int:student_id>/', views.view_student_cor, name='view_student_cor'),
    path('admin-dashboard/delete-subject/<int:subject_id>/', views.delete_student_subject, name='delete_student_subject'),
    # AJAX endpoints for student filtering (FIXED PATHS)
    path('admin-dashboard/filter-students/', views.filter_students, name='filter_students'),
    path('admin-dashboard/approve-student/<int:user_id>/', views.approve_student, name='approve_student'),
    # Evaluation Period Settings
    path('set-evaluation-period/', views.set_evaluation_period, name='set_evaluation_period'),
    # Student & Teacher URLs
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teachers/', views.teacher_list, name='teacher_list'),
    path('evaluate/<int:teacher_id>/', views.evaluate_teacher, name='evaluate_teacher'),
    path('evaluation/<int:evaluation_id>/', views.view_evaluation, name='view_evaluation'),
    path('student/dashboard-debug/', views.student_dashboard_debug, name='student_dashboard_debug'),

    path('admin/add-teacher/', views.add_teacher, name='add_teacher'),
    path('edit-teacher/<int:teacher_id>/', views.edit_teacher, name='edit_teacher'),
    # path('delete-teacher/<int:user_id>/', views.delete_teacher, name='delete_teacher'),
    path('assign-subjects/<int:teacher_id>/', views.assign_subjects, name='assign_subjects'),

    path('add-subject/', views.add_subject, name='add_subject'),
    path('edit-subject/<int:subject_id>/', views.edit_subject, name='edit_subject'),
    path('delete-subject/<int:subject_id>/', views.delete_subject, name='delete_subject'),
    
]