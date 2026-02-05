#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'teacher_eval_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from evaluation.models import TeacherProfile, Department

User = get_user_model()

# Find all teacher users without profiles
teachers_without_profile = User.objects.filter(user_type='teacher').exclude(teacher_profile__isnull=False)

if teachers_without_profile.exists():
    # Get or create default department
    default_dept, _ = Department.objects.get_or_create(
        name='College of Computer Science',
        defaults={'code': 'CCS', 'description': 'Computer Science Department'}
    )
    
    # Create profiles for teachers without them
    for teacher_user in teachers_without_profile:
        profile, created = TeacherProfile.objects.get_or_create(
            user=teacher_user,
            defaults={
                'employee_id': f'EMP{teacher_user.id:04d}',
                'department': default_dept,
                'qualification': 'Not Specified',
                'experience_years': 0
            }
        )
        status = "Created" if created else "Already exists"
        print(f"✓ {status}: {teacher_user.username} - {profile.employee_id}")
    
    print(f"\n✓ Total teachers processed: {teachers_without_profile.count()}")
else:
    print("✓ All teachers have profiles!")
