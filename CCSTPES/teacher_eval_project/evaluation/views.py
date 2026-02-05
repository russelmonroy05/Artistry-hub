from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Count, Q, Prefetch
from django.db import models
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.core.exceptions import MultipleObjectsReturned
from django.urls import reverse
import secrets
from .forms import StudentRegistrationForm, TeacherRegistrationForm, EvaluationForm
from .models import User, TeacherProfile, StudentProfile, Evaluation, Subject, Department, StudentSubject, Semester, AcademicYear, EvaluationSettings
from django.http import JsonResponse
import random
import json
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from django.db import IntegrityError
from django.views.decorators.http import require_http_methods
from django.db import connection



def home(request):
    """Home page"""
    return render(request, 'home.html')


def register_choice(request):
    """Choose registration type"""
    return render(request, 'register_choice.html')


def send_admin_notification_email(request, user, user_type='student'):
    """Send notification email to admins about a new pending registration"""
    try:
        admin_users = User.objects.filter(user_type='admin', email__isnull=False).exclude(email='')
        
        if not admin_users.exists():
            return
        
        admin_emails = [admin.email for admin in admin_users]
        
        approval_url = request.build_absolute_uri(f'/admin-dashboard/students/')
        
        subject = f'New {user_type.title()} Registration Pending Approval'
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: white; padding: 30px; border: 1px solid #ddd; }}
                .user-info {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 10px 20px; 
                          text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; color: #999; font-size: 12px; padding: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎓 New Registration Pending</h1>
                </div>
                <div class="content">
                    <h2>A new {user_type} has registered and is awaiting approval.</h2>
                    
                    <div class="user-info">
                        <p><strong>Name:</strong> {user.first_name} {user.last_name}</p>
                        <p><strong>Username:</strong> {user.username}</p>
                        <p><strong>Email:</strong> {user.email}</p>
                        <p><strong>Account Type:</strong> {user_type.title()}</p>
                        <p><strong>Registration Date:</strong> {user.date_joined.strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                    
                    <p>Please review and approve or reject this registration in the admin dashboard:</p>
                    <div style="text-align: center;">
                        <a href="{approval_url}" class="button">View Pending Registrations</a>
                    </div>
                    
                    <p style="color: #999; font-size: 14px;">
                        <strong>Note:</strong> This is an automated notification. Please do not reply to this email.
                    </p>
                </div>
                <div class="footer">
                    <p>© 2024 Teacher Evaluation System. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        plain_message = f"A new {user_type} has registered and is awaiting your approval.\n\nName: {user.first_name} {user.last_name}\nUsername: {user.username}\nEmail: {user.email}\n\nView pending registrations at: {approval_url}"
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            admin_emails,
            html_message=html_message,
            fail_silently=True,
        )
    except Exception as e:
        print(f"Error sending admin notification: {e}")


def student_register(request):
    """Student registration with email verification, profile picture, and COR upload"""
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            course = form.cleaned_data.get('course')
            student_id_number = form.cleaned_data.get('student_id_number')
            
            # Check if email was verified via the button (in cache)
            verify_status_key = f'verify_status_{email}'
            is_verified_via_button = cache.get(verify_status_key) == 'verified'
            
            if not is_verified_via_button:
                messages.error(request, 'Please verify your email using the Verify button before submitting the form.')
                return render(request, 'student_register.html', {'form': form})
            
            # Prevent duplicate emails (case-insensitive)
            if User.objects.filter(email__iexact=email).exists():
                messages.error(request, 'An account with that email already exists. Please use a different email or login.')
                return render(request, 'student_register.html', {'form': form})
            
            # Check for duplicate student_id_number
            if StudentProfile.objects.filter(student_id_number=student_id_number).exists():
                messages.error(request, 'This Student ID is already registered. Please use a different Student ID.')
                return render(request, 'student_register.html', {'form': form})

            user = form.save(commit=False)
            user.is_active = False
            user.is_pending = True
            user.is_email_verified = True
            user.email_verification_token = ''
            user.save()
            
            # Map course to department
            department_mapping = {
                'Computer Science': 'CS',
                'College of Computer Science': 'CS',
                'Information Technology': 'CS',
                'Mathematics': 'MATH',
                'Engineering': 'ENG',
                'Civil Engineering': 'ENG',
                'Mechanical Engineering': 'ENG',
                'Electrical Engineering': 'ENG',
            }
            
            dept_code = department_mapping.get(course, 'CS')
            try:
                department = Department.objects.get(code=dept_code)
            except Department.DoesNotExist:
                department = Department.objects.first()
                if not department:
                    messages.error(request, 'No departments available. Please contact administrator.')
                    return render(request, 'student_register.html', {'form': form})
            
            # Create student profile with profile picture and COR
            try:
                profile_picture = form.cleaned_data.get('profile_picture')
                cor_file = form.cleaned_data.get('certificate_of_registration')
                
                StudentProfile.objects.create(
                    user=user,
                    student_id_number=student_id_number,
                    year_level=form.cleaned_data['year_level'],
                    course=course,
                    department=department,
                    profile_picture=profile_picture,
                    certificate_of_registration=cor_file,
                    cor_uploaded_at=timezone.now() if cor_file else None
                )
            except IntegrityError:
                user.delete()
                messages.error(request, 'This Student ID is already registered. Please use a different Student ID.')
                return render(request, 'student_register.html', {'form': form})
            
            print(f"✓ Created user: {user.username}")
            print(f"✓ Email: {user.email}")
            print(f"✓ Course: {course}")
            print(f"✓ Department: {department.name}")
            print(f"✓ Profile Picture: {bool(profile_picture)}")
            print(f"✓ COR uploaded: {bool(cor_file)}")
            print(f"✓ is_email_verified: {user.is_email_verified}")
            
            # Clear the verification status from cache
            cache.delete(verify_status_key)
            
            # Send admin notification email
            send_admin_notification_email(request, user, user_type='student')
            
            messages.success(request, 'Registration successful! Your account is pending admin approval. You will be able to login once approved.')
            return redirect('login')

    else:
        form = StudentRegistrationForm()
    return render(request, 'student_register.html', {'form': form})


def teacher_register(request):
    """Teacher registration with email verification"""
    if request.method == 'POST':
        form = TeacherRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            employee_id = form.cleaned_data.get('employee_id')
            
            # Check if email was verified via the button (in cache)
            verify_status_key = f'verify_status_{email}'
            is_verified_via_button = cache.get(verify_status_key) == 'verified'
            
            if not is_verified_via_button:
                messages.error(request, 'Please verify your email using the Verify button before submitting the form.')
                return render(request, 'teacher_register.html', {'form': form})
            
            # Prevent duplicate emails (case-insensitive)
            if User.objects.filter(email__iexact=email).exists():
                messages.error(request, 'An account with that email already exists. Please use a different email or login.')
                return render(request, 'teacher_register.html', {'form': form})
            
            # Check for duplicate employee_id
            if TeacherProfile.objects.filter(employee_id=employee_id).exists():
                messages.error(request, 'This Employee ID is already registered. Please use a different Employee ID.')
                return render(request, 'teacher_register.html', {'form': form})

            user = form.save(commit=False)
            user.is_active = False
            user.is_email_verified = True
            user.email_verification_token = ''
            user.save()
            
            print(f"✓ Created teacher: {user.username}")
            print(f"✓ Email: {user.email}")
            print(f"✓ is_email_verified: {user.is_email_verified}")
            
            # Get department and profile picture from form
            department = Department.objects.get(name="College of Computer Science")
            profile_picture = form.cleaned_data.get('profile_picture')
            
            # Create teacher profile with profile picture
            try:
                TeacherProfile.objects.create(
                    user=user,
                    employee_id=employee_id,
                    department=department,
                    qualification=form.cleaned_data['qualification'],
                    experience_years=form.cleaned_data['experience_years'],
                    profile_picture=profile_picture
                )
            except IntegrityError:
                user.delete()
                messages.error(request, 'This Employee ID is already registered. Please use a different Employee ID.')
                return render(request, 'teacher_register.html', {'form': form})
            
            print(f"✓ Department: {department.name}")
            print(f"✓ Profile Picture: {bool(profile_picture)}")
            
            # Clear the verification status from cache
            cache.delete(verify_status_key)
            
            # Activate teacher immediately
            user.is_active = True
            user.save()
            
            messages.success(request, 'Registration successful! You can now login with your credentials.')
            return redirect('login')

    else:
        form = TeacherRegistrationForm()
    return render(request, 'teacher_register.html', {'form': form})


def verify_email(request, token):
    """Verify email using token from link"""
    print("=" * 50)
    print(f"VERIFY_EMAIL FUNCTION CALLED!")
    print(f"Token received: {token}")
    print(f"Token length: {len(token)}")
    print("=" * 50)
    
    import logging
    logger = logging.getLogger(__name__)
    
    # Validate token
    if not token:
        messages.error(request, 'Invalid or expired verification link.')
        return redirect('login')

    # FIRST check if this is a cache token (from verify button BEFORE registration)
    cache_key = f'temp_email_token_{token}'
    email = cache.get(cache_key)
    
    print(f"Checking cache with key: {cache_key}")
    print(f"Email from cache: {email}")

    if email:
        print(f"✓ Found email in cache: {email}")
        # This is a pre-registration verification
        cache.set(f'verify_status_{email}', 'verified', 3600)
        cache.delete(cache_key)
        
        print(f"✓ Set verification status for: {email}")
        messages.success(request, 'Email verified successfully! You can now complete your registration.')
        redirect_url = reverse('student_register')
        return render(request, 'verification_success.html', {'redirect_url': redirect_url})

    # If not a cache token, try to find a registered user with this token
    user = None
    try:
        user = User.objects.select_for_update().get(email_verification_token=token)
        logger.info(f"Found user with token: {user.username} (ID: {user.id})")
    except MultipleObjectsReturned:
        user = User.objects.select_for_update().filter(email_verification_token=token).first()
        logger.warning(f"Multiple users found with same token, using first: {user.username}")
    except User.DoesNotExist:
        logger.error(f"No user found with token: {token}")
        print(f"✗ No user found in database with token")
        user = None

    if user:
        logger.info(f"Before update - User: {user.username}, is_email_verified: {user.is_email_verified}")
        
        # Update using QuerySet update()
        updated_count = User.objects.filter(id=user.id).update(
            is_email_verified=True,
            email_verification_token=''
        )
        
        logger.info(f"Updated {updated_count} user(s)")
        
        # Refresh from database
        user.refresh_from_db()
        logger.info(f"After update - User: {user.username}, is_email_verified: {user.is_email_verified}")
        
        if user.is_email_verified:
            if user.is_pending:
                messages.success(request, 'Email verified successfully! Your account is pending admin approval. You will be able to login once an administrator approves your account.')
            else:
                messages.success(request, 'Email verified successfully! You can now login.')
            redirect_url = reverse('login')
            return render(request, 'verification_success.html', {'redirect_url': redirect_url})
        else:
            logger.error(f"Failed to verify email for user: {user.username}")
            messages.error(request, 'Email verification failed. Please contact support.')
            return redirect('login')

    print("✗ Token not found in cache or database")
    messages.error(request, 'Invalid or expired verification link.')
    return redirect('login')


def check_verification_status(request):
    """Check if email has been verified"""
    email = request.GET.get('email')
    
    if not email:
        return JsonResponse({'verified': False, 'message': 'Email required'})
    
    # Check if verified in cache
    status_key = f'verify_status_{email}'
    status = cache.get(status_key)
    if status == 'verified':
        return JsonResponse({
            'verified': True,
            'message': 'Email verified successfully!'
        })
    
    # Check if registered user has verified their email
    try:
        user = User.objects.get(email=email)
        if user.is_email_verified:
            return JsonResponse({
                'verified': True,
                'message': 'Email verified successfully!'
            })
    except User.DoesNotExist:
        pass
    
    return JsonResponse({
        'verified': False,
        'message': 'Email not verified yet'
    })


@csrf_exempt
def send_verification_code(request):
    """Send verification email with link"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            
            if not email:
                return JsonResponse({'success': False, 'message': 'Email required'})
            
            # Check if user with this email already exists
            try:
                user = User.objects.get(email=email)
                return JsonResponse({
                    'success': False,
                    'message': 'This email is already registered'
                })
            except User.DoesNotExist:
                pass
            
            # Generate a temporary token
            token = secrets.token_urlsafe(32)
            
            # Store email in cache with token as key
            cache_key = f'temp_email_token_{token}'
            cache.set(cache_key, email, 3600)
            
            # Build verification link
            verification_url = request.build_absolute_uri(f'/verify-email/{token}/')
            
            # Send email with link
            subject = 'Verify Your Email - Teacher Evaluation System'
            html_message = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                              color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: white; padding: 30px; border: 1px solid #ddd; }}
                    .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ text-align: center; color: #999; font-size: 12px; padding: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎓 Email Verification</h1>
                    </div>
                    <div class="content">
                        <h2>Welcome!</h2>
                        <p>Thank you for registering with the Teacher Evaluation System!</p>
                        <p>Please click the button below to verify your email address:</p>
                        <div style="text-align: center;">
                            <a href="{verification_url}" class="button">Verify Email</a>
                        </div>
                        <p style="color: #666; font-size: 14px;">
                            Or copy and paste this link in your browser:<br>
                            <code style="background: #f5f5f5; padding: 5px; word-break: break-all;">{verification_url}</code>
                        </p>
                        <p style="color: #999; font-size: 12px;">
                            This link will expire in 1 hour. If you didn't create this account, please ignore this email.
                        </p>
                    </div>
                    <div class="footer">
                        <p>© 2024 Teacher Evaluation System. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            plain_message = f"Click this link to verify your email:\n{verification_url}\n\nThis link will expire in 1 hour."
            
            try:
                send_mail(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    html_message=html_message,
                    fail_silently=False,
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Verification email sent successfully'
                })
            except Exception as e:
                print(f"Email send error: {e}")
                return JsonResponse({
                    'success': False,
                    'message': 'Failed to send email. Please try again.'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


def resend_verification(request):
    """Resend verification email"""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email, is_active=False)
            
            # Generate new token
            token = secrets.token_urlsafe(32)
            user.email_verification_token = token
            user.save()
            
            messages.success(request, 'Verification email resent! Please check your inbox.')
        except User.DoesNotExist:
            messages.error(request, 'No unverified account found with this email.')
    
    return render(request, 'resend_verification.html')


def user_login(request):
    """Login view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Try to find the user by username
        try:
            user_obj = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, 'Invalid username or password')
            return render(request, 'login.html')
        
        # Check password
        if not user_obj.check_password(password):
            messages.error(request, 'Invalid username or password')
            return render(request, 'login.html')
        
        # Check if account is pending
        if getattr(user_obj, 'is_pending', False):
            messages.error(request, 'Your account is pending approval by an administrator. You will be able to login once approved.')
            return render(request, 'login.html')

        # Check email verification
        if not getattr(user_obj, 'is_email_verified', False):
            messages.error(request, 'Please verify your email before logging in. Check your inbox for the verification link.')
            return render(request, 'login.html')
        
        # All checks passed
        user_obj.is_active = True
        user_obj.save()
        login(request, user_obj)
        
        # Handle "Remember Me"
        if request.POST.get('remember'):
            request.session.set_expiry(30 * 24 * 3600)
        else:
            request.session.set_expiry(0)
        
        if user_obj.user_type == 'admin':
            return redirect('admin_dashboard')
        elif user_obj.user_type == 'student':
            return redirect('student_dashboard')
        elif user_obj.user_type == 'teacher':
            return redirect('teacher_dashboard')
    
    return render(request, 'login.html')


def user_logout(request):
    """Logout view"""
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('login')


@login_required
def student_dashboard(request):
    """Student dashboard"""
    if request.user.user_type != 'student':
        messages.error(request, 'Access denied!')
        return redirect('home')
    
    student_profile = request.user.student_profile
    
    # CHECK IF EVALUATION IS OPEN
    current_evaluation_settings = EvaluationSettings.objects.filter(is_open=True).first()
    evaluation_is_open = current_evaluation_settings is not None
    current_semester = current_evaluation_settings.semester if current_evaluation_settings else None
    current_academic_year = current_evaluation_settings.academic_year if current_evaluation_settings else None
    
    # Filter evaluations by current semester/year if evaluation is open
    if evaluation_is_open and current_semester and current_academic_year:
        my_evaluations = student_profile.my_evaluations.filter(
            semester=current_semester,
            academic_year=current_academic_year
        ).order_by('-created_at')
    else:
        my_evaluations = student_profile.my_evaluations.all().order_by('-created_at')
    
    # Get subjects available for this student's year level
    available_subjects = student_profile.get_available_subjects()
    
    # Sort based on what type was returned
    if student_profile.has_assigned_subjects():
        available_subjects = list(available_subjects.order_by('subject_code'))
    else:
        available_subjects = list(available_subjects.order_by('department__name', 'name'))
    
    # Get all teachers
    available_teachers = student_profile.get_available_teachers().order_by('user__first_name')
    
    # Get list of teacher IDs evaluated this semester/year
    if evaluation_is_open and current_semester and current_academic_year:
        evaluated_teacher_ids = my_evaluations.values_list('teacher_id', flat=True).distinct()
    else:
        evaluated_teacher_ids = []
    
    # Filter unevaluated teachers
    unevaluated_teachers = available_teachers.exclude(id__in=evaluated_teacher_ids)
    
    # Calculate evaluation progress
    total_teachers = available_teachers.count()
    evaluated_teachers_count = len(evaluated_teacher_ids)
    
    if total_teachers > 0:
        progress_percentage = round((evaluated_teachers_count / total_teachers) * 100, 2)
    else:
        progress_percentage = 0
    
    pending_teachers = total_teachers - evaluated_teachers_count
    
    # Get top performing teachers
    top_teachers = sorted(
        [teacher for teacher in available_teachers if teacher.get_average_rating() >= 3.0],
        key=lambda x: x.get_average_rating(),
        reverse=True
    )[:3]
    
    context = {
        'student': student_profile,
        'evaluations': my_evaluations,
        'subjects': available_subjects,
        'teachers': unevaluated_teachers,
        'teachers_count': total_teachers,
        'evaluations_count': my_evaluations.count(),
        'pending_evaluations': pending_teachers,
        'evaluated_teacher_ids': list(evaluated_teacher_ids),
        'progress_percentage': progress_percentage,
        'progress_completed': evaluated_teachers_count,
        'progress_total': total_teachers,
        'top_teachers': top_teachers,
        'student_year_level': student_profile.get_year_level_display(),
        'student_department': student_profile.department.name,
        'has_cor_assignments': student_profile.has_assigned_subjects(),
        'evaluation_is_open': evaluation_is_open,
        'current_semester': current_semester,
        'current_academic_year': current_academic_year,
    }
    return render(request, 'student_dashboard.html', context)


@login_required
def student_dashboard_debug(request):
    """Student dashboard with debug info"""
    if request.user.user_type != 'student':
        messages.error(request, 'Access denied!')
        return redirect('home')
    
    student = request.user.student_profile
    
    print(f"\n=== DEBUG INFO ===")
    print(f"Student: {student}")
    print(f"Department: {student.department}")
    print(f"Year Level: {student.year_level}")
    
    available_subjects = student.get_available_subjects()
    print(f"\nAvailable Subjects: {available_subjects.count()}")
    for s in available_subjects:
        print(f"  - {s.code}: {s.name} (Dept: {s.department})")
        teachers = s.teachers.all()
        print(f"    Teachers: {teachers.count()}")
        for t in teachers:
            print(f"      - {t.user.username} ({t.department})")
    
    available_teachers = student.get_available_teachers()
    print(f"\nAvailable Teachers: {available_teachers.count()}")
    for t in available_teachers:
        print(f"  - {t.user.username} ({t.department})")
        subjects = t.subjects.filter(year_level=student.year_level)
        print(f"    Subjects: {subjects.count()}")
    
    my_evaluations = student.my_evaluations.all()
    evaluated_teacher_ids = my_evaluations.values_list('teacher_id', flat=True).distinct()
    
    print(f"\nEvaluations Completed: {my_evaluations.count()}")
    print(f"Unique Teachers Evaluated: {evaluated_teacher_ids.count()}")
    
    unevaluated_teachers = available_teachers.exclude(id__in=evaluated_teacher_ids)
    print(f"Unevaluated Teachers: {unevaluated_teachers.count()}")
    
    print(f"=== END DEBUG ===\n")
    
    context = {
        'student': student,
        'subjects': available_subjects,
        'teachers': unevaluated_teachers,
        'teachers_count': available_teachers.count(),
        'evaluations_count': my_evaluations.count(),
        'pending_evaluations': unevaluated_teachers.count(),
        'progress_percentage': 0,
        'progress_completed': evaluated_teacher_ids.count(),
        'progress_total': available_teachers.count(),
    }
    return render(request, 'student_dashboard.html', context)

from datetime import datetime, timedelta


@login_required
def teacher_dashboard(request):
    """Teacher dashboard with real chart data"""
    if request.user.user_type != 'teacher':
        messages.error(request, 'Access denied!')
        return redirect('home')
    
    try:
        teacher = TeacherProfile.objects.get(user=request.user)
    except TeacherProfile.DoesNotExist:
        messages.error(request, 'Teacher profile not found. Please contact administrator.')
        return redirect('home')
    
    # Get all evaluations for this teacher
    evaluations = Evaluation.objects.filter(
        teacher=teacher
    ).select_related('student__user', 'subject').order_by('-created_at')
    
    total_evaluations = evaluations.count()
    
    # Calculate average rating
    if total_evaluations > 0:
        total_rating = sum([e.get_average_rating() for e in evaluations])
        average_rating = round(total_rating / total_evaluations, 1)
    else:
        average_rating = 0
    
    # ===== CHART DATA: Rating Trend Over Time =====
    # Get evaluations from the last 5 periods (weeks/months)
    today = datetime.now()
    
    # Calculate weekly averages for the last 5 weeks
    weekly_labels = []
    weekly_ratings = []
    
    for i in range(4, -1, -1):  # Last 5 weeks
        week_start = today - timedelta(weeks=i+1)
        week_end = today - timedelta(weeks=i)
        
        week_evals = evaluations.filter(
            created_at__gte=week_start,
            created_at__lt=week_end
        )
        
        if week_evals.exists():
            avg = sum([e.get_average_rating() for e in week_evals]) / week_evals.count()
            weekly_ratings.append(round(avg, 2))
        else:
            # Use previous week's rating or 0
            weekly_ratings.append(weekly_ratings[-1] if weekly_ratings else 0)
        
        # Label format: "Week 1", "Week 2", etc.
        if i == 0:
            weekly_labels.append('This Week')
        else:
            weekly_labels.append(f'{i+1} Week{"s" if i > 0 else ""} Ago')
    
    # ===== CHART DATA: Performance by Category =====
    # Calculate averages for each evaluation category
    if evaluations.exists():
        category_data = {
            'presentation': round(sum([e.get_presentation_average() for e in evaluations]) / total_evaluations, 2),
            'development': round(sum([e.get_development_average() for e in evaluations]) / total_evaluations, 2),
            'student_behavior': round(sum([e.get_student_behavior_average() for e in evaluations]) / total_evaluations, 2),
            'wrapup': round(sum([e.get_wrapup_average() for e in evaluations]) / total_evaluations, 2)
        }
    else:
        category_data = {
            'presentation': 0,
            'development': 0,
            'student_behavior': 0,
            'wrapup': 0
        }
    
    # ===== CHART DATA: Ratings by Subject =====
    subject_labels = []
    subject_ratings = []
    
    for subject in teacher.subjects.all():
        subject_evals = evaluations.filter(subject=subject)
        if subject_evals.exists():
            avg = sum([e.get_average_rating() for e in subject_evals]) / subject_evals.count()
            subject_labels.append(subject.code)
            subject_ratings.append(round(avg, 2))
    
    # ===== CHART DATA: Monthly Evaluation Count =====
    monthly_labels = []
    monthly_counts = []
    
    for i in range(5, -1, -1):  # Last 6 months
        month_date = today - timedelta(days=30*i)
        month_start = month_date.replace(day=1)
        
        if i == 0:
            month_end = today
        else:
            next_month = month_start.replace(day=28) + timedelta(days=4)
            month_end = next_month.replace(day=1)
        
        month_count = evaluations.filter(
            created_at__gte=month_start,
            created_at__lt=month_end
        ).count()
        
        monthly_labels.append(month_start.strftime('%b'))
        monthly_counts.append(month_count)
    
    context = {
        'teacher': teacher,
        'evaluations': evaluations[:10],  # Recent 10 for table
        'all_evaluations': evaluations,  # All for other calculations
        'total_evaluations': total_evaluations,
        'average_rating': average_rating,
        
        # Chart Data - Weekly Trend
        'weekly_labels': weekly_labels,
        'weekly_ratings': weekly_ratings,
        
        # Chart Data - Category Performance
        'category_data': category_data,
        
        # Chart Data - By Subject
        'subject_labels': subject_labels,
        'subject_ratings': subject_ratings,
        
        # Chart Data - Monthly Counts
        'monthly_labels': monthly_labels,
        'monthly_counts': monthly_counts,
    }
    
    return render(request, 'teacher_dashboard.html', context)


@login_required
def teacher_list(request):
    """List teachers from the same department for evaluation"""
    if request.user.user_type != 'student':
        messages.error(request, 'Only students can access this page!')
        return redirect('home')
    
    student = request.user.student_profile
    
    subjects_qs = Subject.objects.filter(department=student.department)
    teachers = TeacherProfile.objects.filter(department=student.department).prefetch_related(
        Prefetch('subjects', queryset=subjects_qs, to_attr='dept_subjects')
    )

    context = {
        'teachers': teachers,
        'student_department': student.department,
    }
    return render(request, 'teacher_list.html', context)


@login_required
def evaluate_teacher(request, teacher_id):
    """Evaluate a teacher"""
    if request.user.user_type != 'student':
        messages.error(request, 'Only students can evaluate teachers!')
        return redirect('home')
    
    # CHECK IF EVALUATION IS OPEN
    current_evaluation_settings = EvaluationSettings.objects.filter(is_open=True).first()
    
    if not current_evaluation_settings:
        messages.error(
            request, 
            'Evaluation period is currently closed. Please wait for the administrator to open the evaluation period.'
        )
        return redirect('student_dashboard')
    
    current_semester = current_evaluation_settings.semester
    current_academic_year = current_evaluation_settings.academic_year
    
    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    student = request.user.student_profile
    
    # Get subjects this student can evaluate
    if student.has_assigned_subjects():
        assigned_to_student = StudentSubject.objects.filter(
            student=student,
            teacher=teacher
        )
        
        if not assigned_to_student.exists():
            messages.error(request, f'{teacher.user.get_full_name()} does not teach any of your assigned subjects!')
            return redirect('student_dashboard')
        
        subject_codes = assigned_to_student.values_list('subject_code', flat=True)
        common_subjects = Subject.objects.filter(code__in=subject_codes)
        
    else:
        teacher_subject_codes = StudentSubject.objects.filter(
            teacher=teacher
        ).values_list('subject_code', flat=True).distinct()
        
        common_subjects = Subject.objects.filter(
            year_level=student.year_level,
            code__in=teacher_subject_codes
        )
        
        if not common_subjects.exists():
            messages.error(request, f'{teacher.user.get_full_name()} does not teach subjects for your year level!')
            return redirect('student_dashboard')
    
    # Check if already evaluated for this semester/year
    existing_evaluations = Evaluation.objects.filter(
        student=student, 
        teacher=teacher,
        semester=current_semester,
        academic_year=current_academic_year
    )
    
    if request.method == 'POST':
        form = EvaluationForm(request.POST)
        if form.is_valid():
            subject_from_form = form.cleaned_data['subject']
            
            if Evaluation.objects.filter(
                student=student, 
                teacher=teacher, 
                subject=subject_from_form,
                semester=current_semester,
                academic_year=current_academic_year
            ).exists():
                messages.error(request, f'You have already evaluated this teacher for {subject_from_form.name} this semester!')
                return redirect('student_dashboard')
            
            if subject_from_form not in common_subjects:
                messages.error(request, 'You can only evaluate subjects available to you!')
                return redirect('student_dashboard')
            
            # Create evaluation
            evaluation = Evaluation.objects.create(
                student=student,
                teacher=teacher,
                subject=subject_from_form,
                semester=current_semester,
                academic_year=current_academic_year,
                presentation_objectives=form.cleaned_data['presentation_objectives'],
                presentation_motivation=form.cleaned_data['presentation_motivation'],
                presentation_relation=form.cleaned_data['presentation_relation'],
                presentation_assignments=form.cleaned_data['presentation_assignments'],
                dev_anticipates=form.cleaned_data['dev_anticipates'],
                dev_mastery=form.cleaned_data['dev_mastery'],
                dev_logical=form.cleaned_data['dev_logical'],
                dev_expression=form.cleaned_data['dev_expression'],
                dev_participation=form.cleaned_data['dev_participation'],
                dev_questions=form.cleaned_data['dev_questions'],
                dev_values=form.cleaned_data['dev_values'],
                dev_reinforcement=form.cleaned_data['dev_reinforcement'],
                dev_involvement=form.cleaned_data['dev_involvement'],
                dev_voice=form.cleaned_data['dev_voice'],
                dev_grammar=form.cleaned_data['dev_grammar'],
                dev_monitoring=form.cleaned_data['dev_monitoring'],
                dev_time=form.cleaned_data['dev_time'],
                student_answers=form.cleaned_data['student_answers'],
                student_questions=form.cleaned_data['student_questions'],
                student_engagement=form.cleaned_data['student_engagement'],
                student_timeframe=form.cleaned_data['student_timeframe'],
                student_majority=form.cleaned_data['student_majority'],
                wrapup_demonstrate=form.cleaned_data['wrapup_demonstrate'],
                wrapup_synthesize=form.cleaned_data['wrapup_synthesize'],
                problem_late=form.cleaned_data['problem_late'],
                problem_absent=form.cleaned_data['problem_absent'],
                problem_video=form.cleaned_data['problem_video'],
                suggestions=form.cleaned_data['suggestions']
            )
            
            messages.success(
                request, 
                f'Successfully evaluated {teacher.user.get_full_name()} for {subject_from_form.name} '
                f'({current_academic_year.name} - {current_semester.name})!'
            )
            return redirect('student_dashboard')
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        form = EvaluationForm()
        form.fields['subject'].queryset = common_subjects
    
    context = {
        'form': form,
        'teacher': teacher,
        'common_subjects': common_subjects,
        'existing_evaluations': existing_evaluations,
        'current_semester': current_semester,
        'current_academic_year': current_academic_year,
        'evaluation_is_open': True,
    }
    return render(request, 'evaluate_teacher.html', context)


@login_required
def view_evaluation(request, evaluation_id):
    """View evaluation details"""
    evaluation = get_object_or_404(Evaluation, id=evaluation_id)
    
    # Check permissions
    if request.user.user_type == 'student':
        if evaluation.student.user != request.user:
            messages.error(request, 'Access denied!')
            return redirect('student_dashboard')
    elif request.user.user_type == 'teacher':
        if evaluation.teacher.user != request.user:
            messages.error(request, 'Access denied!')
            return redirect('teacher_dashboard')
    
    context = {'evaluation': evaluation}
    return render(request, 'view_evaluation.html', context)


@login_required
def admin_dashboard(request):
    """Admin dashboard"""
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied!')
        return redirect('home')
    
    # Get current active academic year and evaluation settings
    current_academic_year = AcademicYear.objects.filter(is_active=True).first()
    current_evaluation_settings = None
    current_semester = None
    
    if current_academic_year:
        current_evaluation_settings = EvaluationSettings.objects.filter(
            academic_year=current_academic_year,
            is_open=True
        ).select_related('semester', 'academic_year').first()
        
        if current_evaluation_settings:
            current_semester = current_evaluation_settings.semester
    
    all_academic_years = AcademicYear.objects.all()
    all_semesters = Semester.objects.select_related('academic_year').all()
    
    # Filter evaluations by current academic year and semester if set
    evaluations_filter = {}
    if current_academic_year:
        evaluations_filter['academic_year'] = current_academic_year
    if current_semester:
        evaluations_filter['semester'] = current_semester
    
    # Summary stats
    total_students = StudentProfile.objects.count()
    total_teachers = TeacherProfile.objects.count()
    
    if evaluations_filter:
        total_evaluations = Evaluation.objects.filter(**evaluations_filter).count()
    else:
        total_evaluations = Evaluation.objects.count()
    
    total_subjects = Subject.objects.count()

    # Top teachers
    top_teachers = []
    for t in TeacherProfile.objects.select_related('user').all():
        if evaluations_filter:
            teacher_evaluations = t.evaluations.filter(**evaluations_filter)
        else:
            teacher_evaluations = t.evaluations.all()
        
        total = teacher_evaluations.count()
        if total > 0:
            avg = sum([e.get_average_rating() for e in teacher_evaluations]) / total
            top_teachers.append({
                'teacher': t, 
                'rating': round(avg, 2), 
                'total_evals': total
            })
    
    top_teachers = sorted(top_teachers, key=lambda x: x['rating'], reverse=True)[:5]

    # Recent evaluations
    if evaluations_filter:
        recent_evaluations = Evaluation.objects.filter(**evaluations_filter).select_related(
            'student__user',
            'teacher__user',
            'subject'  # ADD THIS
        ).order_by('-created_at')[:5]
    else:
        recent_evaluations = Evaluation.objects.select_related(
            'student__user',
            'teacher__user',
            'subject'  # ADD THIS
        ).order_by('-created_at')[:5]
    
    # Get all students with optimizations
    students = StudentProfile.objects.select_related(
        'user',
        'department'
    ).prefetch_related(
        'assigned_subjects',
        'assigned_subjects__teacher',
        'assigned_subjects__teacher__user',
        'my_evaluations'
    ).annotate(
        evaluations_count=Count('my_evaluations', distinct=True),
        subjects_count=Count('assigned_subjects', distinct=True)
    ).order_by('user__first_name', 'user__last_name')
    
    pending_count = StudentProfile.objects.filter(user__is_pending=True).count()
    approved_count = StudentProfile.objects.filter(user__is_pending=False).count()
    
    departments = Department.objects.all().order_by('name')
    teachers = TeacherProfile.objects.select_related('user', 'department').all()
    
    # ADD THIS LINE:
    subjects = Subject.objects.select_related('department').prefetch_related('teachers').all()

    context = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_evaluations': total_evaluations,
        'total_subjects': total_subjects,
        'top_teachers': top_teachers,
        'recent_evaluations': recent_evaluations,
        'students': students,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'departments': departments,
        'current_academic_year': current_academic_year,
        'current_semester': current_semester,
        'current_evaluation_settings': current_evaluation_settings,
        'all_academic_years': all_academic_years,
        'all_semesters': all_semesters,
        'evaluation_is_open': current_evaluation_settings.is_open if current_evaluation_settings else False,
        'teachers': teachers,
        'subjects': subjects,  # ADD THIS
    }

    return render(request, 'admin_dashboard.html', context)


@login_required
@require_http_methods(["GET"])
def filter_students(request):
    """AJAX endpoint to filter students without page reload"""
    if request.user.user_type != 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    students = StudentProfile.objects.select_related(
        'user',
        'department'
    ).prefetch_related(
        'assigned_subjects',
        'assigned_subjects__teacher',
        'assigned_subjects__teacher__user',
        'my_evaluations'
    ).annotate(
        evaluations_count=Count('my_evaluations', distinct=True),
        subjects_count=Count('assigned_subjects', distinct=True)
    )
    
    # Apply filters
    status_filter = request.GET.get('status', '')
    year_filter = request.GET.get('year_level', '')
    department_filter = request.GET.get('department', '')
    search_query = request.GET.get('search', '')
    
    if status_filter == 'pending':
        students = students.filter(user__is_pending=True)
    elif status_filter == 'approved':
        students = students.filter(user__is_pending=False)
    
    if year_filter:
        students = students.filter(year_level=year_filter)
    
    if department_filter:
        students = students.filter(department_id=department_filter)
    
    if search_query:
        students = students.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(student_id__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(course__icontains=search_query)
        )
    
    students = students.order_by('user__first_name', 'user__last_name')
    
    # Calculate counts
    total_count = students.count()
    pending_count = students.filter(user__is_pending=True).count()
    approved_count = students.filter(user__is_pending=False).count()
    
    # Render table
    html = render_to_string('partials/students_table.html', {
        'students': students
    })
    
    return JsonResponse({
        'html': html,
        'total_count': total_count,
        'pending_count': pending_count,
        'approved_count': approved_count
    })


@login_required
@require_http_methods(["POST"])
def approve_student(request, user_id):
    """Approve a pending student - handles both AJAX and regular POST"""
    print(f"APPROVE_STUDENT called by: {getattr(request.user, 'username', None)}, method={request.method}, X-Requested-With={request.headers.get('X-Requested-With')}, target_user_id={user_id}")
    if not (request.user.user_type == 'admin' or request.user.is_superuser):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Access denied'}, status=403)
        messages.error(request, 'Access denied!')
        return redirect('admin_dashboard')
    
    try:
        user = User.objects.get(id=user_id, user_type='student')
        user.is_pending = False
        user.is_active = True
        user.save()
        
        # If AJAX request, return JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Use StudentProfile (model in this app) for counts
            pending_count = StudentProfile.objects.filter(user__is_pending=True).count()
            approved_count = StudentProfile.objects.filter(user__is_pending=False).count()
            return JsonResponse({
                'success': True,
                'message': f'{user.get_full_name()} approved successfully.',
                'pending_count': pending_count,
                'approved_count': approved_count
            })



        
        # Otherwise, redirect with message
        messages.success(request, f'{user.get_full_name()} has been approved.')
        return redirect('admin_dashboard')
        
    except User.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'User not found'}, status=404)
        messages.error(request, 'User not found.')
        return redirect('admin_dashboard')


@login_required
def set_evaluation_period(request):
    """Admin can set/update evaluation period"""
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied!')
        return redirect('home')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create_year':
            year_name = request.POST.get('year_name')
            year_start = request.POST.get('year_start')
            year_end = request.POST.get('year_end')
            
            try:
                if not year_name or not year_start or not year_end:
                    messages.error(request, 'Please fill in all academic year fields.')
                    return redirect('admin_dashboard')
                
                AcademicYear.objects.create(
                    name=year_name,
                    start_Year=year_start,
                    end_Year=year_end,
                    is_active=False
                )
                
                messages.success(request, f'Academic Year "{year_name}" created successfully!')
                
            except Exception as e:
                messages.error(request, f'Error creating academic year: {str(e)}')
            
            return redirect('admin_dashboard')
        
        elif action == 'create_semester':
            semester_name = request.POST.get('semester_name')
            semester_start = request.POST.get('semester_start')
            semester_end = request.POST.get('semester_end')
            semester_year_id = request.POST.get('semester_year_id')
            
            try:
                if not semester_name or not semester_start or not semester_end or not semester_year_id:
                    messages.error(request, 'Please fill in all semester fields.')
                    return redirect('admin_dashboard')
                
                academic_year = AcademicYear.objects.get(id=semester_year_id)
                
                Semester.objects.create(
                    name=semester_name,
                    start_Month=semester_start,
                    end_Month=semester_end,
                    academic_year=academic_year
                )
                
                messages.success(request, f'Semester "{semester_name}" created successfully!')
                
            except AcademicYear.DoesNotExist:
                messages.error(request, 'Selected academic year not found.')
            except Exception as e:
                messages.error(request, f'Error creating semester: {str(e)}')
            
            return redirect('admin_dashboard')
        
        elif action == 'set_period':
            academic_year_id = request.POST.get('academic_year')
            semester_id = request.POST.get('semester')
            is_open = request.POST.get('is_open') == 'on'
            
            try:
                if not academic_year_id or not semester_id:
                    messages.error(request, 'Please select both academic year and semester.')
                    return redirect('admin_dashboard')
                
                academic_year = AcademicYear.objects.get(id=academic_year_id)
                semester = Semester.objects.get(id=semester_id)
                
                # Close all other evaluation periods
                EvaluationSettings.objects.all().update(is_open=False)
                
                # Get or create evaluation settings
                eval_settings, created = EvaluationSettings.objects.get_or_create(
                    academic_year=academic_year,
                    semester=semester,
                    defaults={
                        'is_open': is_open,
                        'open_date': timezone.now() if is_open else None,
                        'close_date': None
                    }
                )
                
                if not created:
                    eval_settings.is_open = is_open
                    if is_open and not eval_settings.open_date:
                        eval_settings.open_date = timezone.now()
                    if not is_open and eval_settings.is_open:
                        eval_settings.close_date = timezone.now()
                    eval_settings.save()
                
                # Set academic year as active
                AcademicYear.objects.all().update(is_active=False)
                academic_year.is_active = True
                academic_year.save()
                
                status = "opened" if is_open else "closed"
                messages.success(
                    request, 
                    f'Evaluation period for {academic_year.name} - {semester.name} has been {status}!'
                )
                
            except AcademicYear.DoesNotExist:
                messages.error(request, 'Academic year not found!')
            except Semester.DoesNotExist:
                messages.error(request, 'Semester not found!')
            except Exception as e:
                messages.error(request, f'Error updating evaluation period: {str(e)}')
        
        else:
            messages.error(request, 'Invalid action.')
    
    return redirect('admin_dashboard')


@login_required
def manage_students(request):
    """Manage student users"""
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied!')
        return redirect('home')
    
    students = StudentProfile.objects.select_related('user').all()
    context = {'students': students}
    return render(request, 'manage_students.html', context)


@login_required
def manage_pending_students(request):
    """Show students pending approval"""
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied!')
        return redirect('home')

    students = StudentProfile.objects.select_related('user').filter(user__is_pending=True)
    context = {'students': students}
    return render(request, 'manage_students.html', context)


@login_required
def manage_teachers(request):
    """Manage teacher users"""
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied!')
        return redirect('home')
    
    teachers = TeacherProfile.objects.select_related('user').all()
    context = {'teachers': teachers}
    return render(request, 'manage_teachers.html', context)


@login_required
def manage_subjects(request):
    """Manage subjects"""
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied!')
        return redirect('home')
    
    subjects = Subject.objects.all()
    context = {'subjects': subjects}
    return render(request, 'manage_subjects.html', context)


@login_required
def delete_user(request, user_id):
    """Delete a user"""
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied!')
        return redirect('home')
    
    user = get_object_or_404(User, id=user_id)
    user.delete()
    messages.success(request, 'User deleted successfully!')
    return redirect('admin_dashboard')


@login_required
def student_detail(request, student_id):
    """View student details"""
    student = get_object_or_404(StudentProfile, id=student_id)
    context = {'student': student}
    return render(request, 'student_detail.html', context)


@login_required
def edit_student(request, student_id):
    """Edit student details"""
    student = get_object_or_404(StudentProfile, id=student_id)
    
    if request.method == 'POST':
        year_level = request.POST.get('year_level')
        course = request.POST.get('course')
        
        student.year_level = year_level
        student.course = course
        student.save()
        
        messages.success(request, 'Student details updated successfully!')
        return redirect('student_detail', student_id=student.id)
    else:
        context = {'student': student}
        return render(request, 'edit_student.html', context)


@login_required
def debug_user_status(request, user_id):
    """Debug view to check user verification status"""
    if request.user.user_type != 'admin':
        return JsonResponse({'error': 'Access denied'})
    user = get_object_or_404(User, id=user_id)
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT is_email_verified, is_pending, is_active, email_verification_token FROM your_app_user WHERE id = %s",
            [user_id]
        )
        row = cursor.fetchone()
    
    return JsonResponse({
        'username': user.username,
        'email': user.email,
        'is_email_verified_model': user.is_email_verified,
        'is_pending_model': user.is_pending,
        'is_active_model': user.is_active,
        'token_model': user.email_verification_token,
        'is_email_verified_db': row[0] if row else None,
        'is_pending_db': row[1] if row else None,
        'is_active_db': row[2] if row else None,
        'token_db': row[3] if row else None,
    })


@login_required
def view_student_cor(request, student_id):
    """View student COR and assign subjects"""
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied!')
        return redirect('home')

    student = get_object_or_404(StudentProfile, id=student_id)
    
    assigned_subjects = StudentSubject.objects.filter(
        student=student
    ).select_related('teacher', 'teacher__user')
    
    available_subjects = Subject.objects.filter(
        year_level=student.year_level
    ).prefetch_related('teachers')

    if request.method == 'POST':
        assignment_type = request.POST.get('assignment_type')
        teacher_id = request.POST.get('teacher_id')

        if not teacher_id:
            messages.error(request, "Please select a teacher.")
            return redirect('view_student_cor', student_id=student.id)

        try:
            teacher = TeacherProfile.objects.get(id=int(teacher_id))
            
            if assignment_type == 'existing':
                subject_id = request.POST.get('subject_id')
                if not subject_id:
                    messages.error(request, "Please select a subject.")
                    return redirect('view_student_cor', student_id=student.id)
                
                subject = Subject.objects.get(id=int(subject_id))
                
                if StudentSubject.objects.filter(student=student, subject=subject).exists():
                    messages.warning(request, f"Subject {subject.code} is already assigned to this student.")
                    return redirect('view_student_cor', student_id=student.id)
                
                if teacher not in subject.teachers.all():
                    subject.teachers.add(teacher)
                
                StudentSubject.objects.create(
                    student=student,
                    subject=subject,
                    subject_name=subject.name,
                    subject_code=subject.code,
                    teacher=teacher
                )
                
                messages.success(
                    request, 
                    f"Subject {subject.code} - {subject.name} assigned to {student.user.get_full_name()}"
                )
                
            elif assignment_type == 'new':
                subject_name = request.POST.get('subject_name')
                subject_code = request.POST.get('subject_code')
                
                if not subject_name or not subject_code:
                    messages.error(request, "Please fill in subject name and code.")
                    return redirect('view_student_cor', student_id=student.id)
                
                if Subject.objects.filter(code=subject_code).exists():
                    messages.error(request, f"Subject with code {subject_code} already exists.")
                    return redirect('view_student_cor', student_id=student.id)
                
                if StudentSubject.objects.filter(student=student, subject_code=subject_code).exists():
                    messages.warning(request, f"Subject {subject_code} is already assigned to this student.")
                    return redirect('view_student_cor', student_id=student.id)
                
                new_subject = Subject.objects.create(
                    code=subject_code,
                    name=subject_name,
                    year_level=student.year_level,
                    department=student.department,
                    description=f'Subject added from COR for {student.user.get_full_name()}',
                )
                
                new_subject.teachers.add(teacher)
                
                StudentSubject.objects.create(
                    student=student,
                    subject=new_subject,
                    subject_name=subject_name,
                    subject_code=subject_code,
                    teacher=teacher
                )
                
                messages.success(
                    request, 
                    f"New subject {subject_code} - {subject_name} created and assigned"
                )
            
        except TeacherProfile.DoesNotExist:
            messages.error(request, "Selected teacher not found.")
        except Subject.DoesNotExist:
            messages.error(request, "Selected subject not found.")

        return redirect('view_student_cor', student_id=student.id)

    context = {
        'student': student,
        'assigned_subjects': assigned_subjects,
        'available_subjects': available_subjects,
        'teachers': TeacherProfile.objects.all().select_related('user', 'department'),
    }

    return render(request, 'view_student_cor.html', context)


@login_required
def delete_student_subject(request, subject_id):
    """Delete a student's assigned subject"""
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied!')
        return redirect('home')
    
    subject = get_object_or_404(StudentSubject, id=subject_id)
    student_id = subject.student.id
    subject_name = f"{subject.subject_code} - {subject.subject_name}"
    
    subject.delete()
    messages.success(request, f"Subject {subject_name} has been removed.")
    
    return redirect('view_student_cor', student_id=student_id)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from .models import User, TeacherProfile, Department, Subject

@login_required
def add_teacher(request):
    """Add a new teacher"""
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied!')
        return redirect('home')
    
    if request.method == 'POST':
        try:
            # Create User
            user = User.objects.create(
                username=request.POST['username'],
                email=request.POST['email'],
                first_name=request.POST['first_name'],
                last_name=request.POST['last_name'],
                user_type='teacher',
                password=make_password(request.POST['password']),
                phone=request.POST.get('phone', ''),
                bio=request.POST.get('bio', ''),
                is_email_verified=True,  # Auto-verify admin-created accounts
                is_pending=False
            )
            
            # Handle profile picture
            if 'profile_picture' in request.FILES:
                user.profile_picture = request.FILES['profile_picture']
                user.save()
            
            # Create TeacherProfile
            department = get_object_or_404(Department, id=request.POST['department'])
            
            teacher_profile = TeacherProfile.objects.create(
                user=user,
                employee_id=request.POST['employee_id'],
                department=department,
                qualification=request.POST['qualification'],
                experience_years=request.POST.get('experience_years', 0)
            )
            
            messages.success(request, f'Teacher {user.get_full_name()} added successfully!')
            return redirect('admin_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error adding teacher: {str(e)}')
            return redirect('admin_dashboard')
    
    return redirect('admin_dashboard')


@login_required
def edit_teacher(request, teacher_id):
    """Edit existing teacher"""
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied!')
        return redirect('home')
    
    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    
    if request.method == 'POST':
        try:
            # Update User info
            user = teacher.user
            user.first_name = request.POST['first_name']
            user.last_name = request.POST['last_name']
            user.email = request.POST['email']
            user.phone = request.POST.get('phone', '')
            user.bio = request.POST.get('bio', '')
            
            # Handle profile picture
            if 'profile_picture' in request.FILES:
                user.profile_picture = request.FILES['profile_picture']
            
            user.save()
            
            # Update TeacherProfile
            teacher.employee_id = request.POST['employee_id']
            teacher.department = get_object_or_404(Department, id=request.POST['department'])
            teacher.qualification = request.POST['qualification']
            teacher.experience_years = request.POST.get('experience_years', 0)
            teacher.save()
            
            messages.success(request, f'Teacher {user.get_full_name()} updated successfully!')
            
        except Exception as e:
            messages.error(request, f'Error updating teacher: {str(e)}')
    
    return redirect('admin_dashboard')


# @login_required
# def delete_teacher(request, user_id):
#     """Delete a teacher"""
#     if request.user.user_type != 'admin':
#         messages.error(request, 'Access denied!')
#         return redirect('home')
    
#     try:
#         user = get_object_or_404(User, id=user_id, user_type='teacher')
#         teacher_name = user.get_full_name()
        
#         # Delete will cascade to TeacherProfile
#         user.delete()
        
#         messages.success(request, f'Teacher {teacher_name} deleted successfully!')
        
#     except Exception as e:
#         messages.error(request, f'Error deleting teacher: {str(e)}')
    
#     return redirect('admin_dashboard')


@login_required
def assign_subjects(request, teacher_id):
    """Assign subjects to a teacher"""
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied!')
        return redirect('home')
    
    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    
    if request.method == 'POST':
        try:
            # Get selected subject IDs
            subject_ids = request.POST.getlist('subjects')
            
            # Clear existing subjects
            teacher.subjects.clear()
            
            # Add new subjects
            if subject_ids:
                subjects = Subject.objects.filter(id__in=subject_ids)
                teacher.subjects.add(*subjects)
            
            messages.success(request, f'Subjects assigned to {teacher.user.get_full_name()} successfully!')
            
        except Exception as e:
            messages.error(request, f'Error assigning subjects: {str(e)}')
    
    return redirect('admin_dashboard')


# Alternative: If you want a separate teacher list view
@login_required
def teacher_list(request):
    """Display list of all teachers"""
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied!')
        return redirect('home')
    
    teachers = TeacherProfile.objects.select_related(
        'user', 'department'
    ).prefetch_related(
        'subjects', 'evaluations'
    ).all().order_by('user__first_name', 'user__last_name')
    
    departments = Department.objects.all()
    
    context = {
        'teachers': teachers,
        'departments': departments,
    }
    
    return render(request, 'admin/teachers.html', context)


@login_required
def add_subject(request):
    """Add a new subject"""
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied!')
        return redirect('home')
    
    if request.method == 'POST':
        try:
            department = get_object_or_404(Department, id=request.POST['department'])
            
            subject = Subject.objects.create(
                code=request.POST['code'],
                name=request.POST['name'],
                department=department,
                year_level=request.POST['year_level'],
                units=request.POST.get('units', 3),
                description=request.POST.get('description', '')
            )
            
            messages.success(request, f'Subject {subject.code} - {subject.name} added successfully!')
            return redirect('admin_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error adding subject: {str(e)}')
            return redirect('admin_dashboard')
    
    return redirect('admin_dashboard')


@login_required
def edit_subject(request, subject_id):
    """Edit existing subject"""
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied!')
        return redirect('home')
    
    subject = get_object_or_404(Subject, id=subject_id)
    
    if request.method == 'POST':
        try:
            subject.code = request.POST['code']
            subject.name = request.POST['name']
            subject.department = get_object_or_404(Department, id=request.POST['department'])
            subject.year_level = request.POST['year_level']
            subject.units = request.POST.get('units', 3)
            subject.description = request.POST.get('description', '')
            subject.save()
            
            messages.success(request, f'Subject {subject.code} updated successfully!')
            
        except Exception as e:
            messages.error(request, f'Error updating subject: {str(e)}')
    
    return redirect('admin_dashboard')


@login_required
def delete_subject(request, subject_id):
    """Delete a subject"""
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied!')
        return redirect('home')
    
    try:
        subject = get_object_or_404(Subject, id=subject_id)
        subject_name = f"{subject.code} - {subject.name}"
        
        subject.delete()
        
        messages.success(request, f'Subject {subject_name} deleted successfully!')
        
    except Exception as e:
        messages.error(request, f'Error deleting subject: {str(e)}')
    
    return redirect('admin_dashboard')