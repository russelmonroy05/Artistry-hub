from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User, StudentProfile, TeacherProfile, Subject, Evaluation, Department, StudentSubject, Semester, AcademicYear, EvaluationSettings


class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'user_type', 'first_name', 'last_name', 'is_email_verified', 'is_pending']
    list_filter = ['user_type', 'is_staff', 'is_pending', 'is_email_verified']
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'phone', 'profile_picture', 'bio', 'is_email_verified', 'is_pending', 'email_verification_token')}),
    )


class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'get_teacher_count', 'get_student_count', 'head_of_department']
    search_fields = ['name', 'code']
    fieldsets = (
        ('Department Info', {'fields': ('name', 'code')}),
        ('Details', {'fields': ('description', 'head_of_department')}),
    )


class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'employee_id', 'department', 'get_subjects_count', 'experience_years', 'get_average_rating']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'employee_id']
    list_filter = ['department', 'experience_years']
    filter_horizontal = ['subjects']
    
    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    get_full_name.short_description = 'Name'
    
    def get_subjects_count(self, obj):
        return obj.subjects.count()
    get_subjects_count.short_description = 'Subjects'
    
    def get_average_rating(self, obj):
        rating = obj.get_average_rating()
        return f"★ {rating}/5" if rating > 0 else "No ratings"
    get_average_rating.short_description = 'Rating'
    
    fieldsets = (
        ('User Info', {'fields': ('user', 'employee_id')}),
        ('Department & Subjects', {
            'fields': ('department', 'subjects'),
            'description': 'Teachers can teach subjects from any department'
        }),
        ('Qualifications', {'fields': ('qualification', 'experience_years')}),
    )
    
    def get_average_rating_display(self, obj):
        rating = obj.get_average_rating()
        return f"★ {rating}/5" if rating > 0 else "No ratings"
    get_average_rating_display.short_description = 'Average Rating'
    
    def get_evaluation_progress_display(self, obj):
        progress = obj.get_evaluation_progress()
        return f"{progress['completed']}/{progress['total_possible']} ({progress['percentage']}%)"
    get_evaluation_progress_display.short_description = 'Evaluation Progress'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('user', 'department').prefetch_related('subjects')


class SubjectAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'department', 'year_level', 'get_schedule', 'get_teachers_count', 'created_at']
    search_fields = ['name', 'code', 'description']
    list_filter = ['department', 'year_level', 'created_by', 'created_at']
    readonly_fields = ['created_at', 'updated_at', 'get_creator_name_display']
    
    fieldsets = (
        ('Subject Info', {'fields': ('name', 'code', 'department', 'year_level')}),
        ('Schedule', {'fields': ('start_time', 'end_time', 'days')}),
        ('Details', {'fields': ('description', 'created_by')}),
        ('Meta Info', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    
    def get_schedule(self, obj):
        return obj.get_schedule()
    get_schedule.short_description = 'Schedule'
    
    def get_teachers_count(self, obj):
        """Count unique teachers teaching this subject through StudentSubject"""
        teacher_ids = StudentSubject.objects.filter(
            subject_code=obj.code
        ).values_list('teacher_id', flat=True).distinct()
        return len([t for t in teacher_ids if t is not None])
    get_teachers_count.short_description = 'Teachers'
    
    def get_creator_name_display(self, obj):
        return obj.get_creator_name()
    get_creator_name_display.short_description = 'Created By'
    
    def save_model(self, request, obj, form, change):
        # Auto-assign created_by if it's a new subject and user is a teacher
        if not change and not obj.created_by:
            if hasattr(request.user, 'teacher_profile'):
                obj.created_by = request.user.teacher_profile
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('department', 'created_by__user')


class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'student_id_number', 'department', 'year_level', 'course', 'section', 'has_cor', 'get_assigned_subjects_count']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'student_id_number', 'course']
    list_filter = ['department', 'year_level', 'section']
    
    fieldsets = (
        ('User Info', {'fields': ('user', 'student_id_number')}),
        ('Profile', {'fields': ('profile_picture',)}),
        ('Academic Info', {'fields': ('department', 'year_level', 'course', 'section')}),
        ('Documents', {'fields': ('certificate_of_registration', 'cor_uploaded_at')}),
    )
    readonly_fields = ['cor_uploaded_at']
    
    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    get_full_name.short_description = 'Name'
    get_full_name.admin_order_field = 'user__first_name'
    
    def student_id_number(self, obj):
        return obj.student_id
    student_id_number.short_description = 'Student ID'
    student_id_number.admin_order_field = 'student_id'
    
    def has_cor(self, obj):
        """Return boolean for nice Django admin icon"""
        return bool(obj.certificate_of_registration)
    has_cor.short_description = 'COR'
    has_cor.boolean = True
    
    def get_assigned_subjects_count(self, obj):
        count = obj.assigned_subjects.count()
        return f"{count} subject{'s' if count != 1 else ''}"
    get_assigned_subjects_count.short_description = 'Assigned Subjects'
    get_assigned_subjects_count.admin_order_field = 'assigned_subjects_count'
    
    def get_queryset(self, request):
        """Optimize queryset with prefetch and annotations"""
        qs = super().get_queryset(request)
        from django.db.models import Count
        return qs.select_related('user', 'department').annotate(
            assigned_subjects_count=Count('assigned_subjects')
        )

class StudentSubjectAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject_code', 'subject_name', 'teacher', 'created_at']
    search_fields = ['student__user__username', 'subject_code', 'subject_name']
    list_filter = ['created_at', 'teacher__department']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('student__user', 'teacher__user', 'subject')


class EvaluationAdmin(admin.ModelAdmin):
    list_display = (
        'student',
        'teacher',
        'subject',
        'semester',
        'academic_year',
        'get_average_rating_display',
        'created_at',
    )

    search_fields = (
        'student__user__username',
        'teacher__user__username',
        'subject__code',
        'subject__name',
        'semester__name',
        'academic_year__year',
    )

    list_filter = (
        'teacher__department',
        'semester',
        'academic_year',
        'subject__year_level',
        'created_at',
    )

    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Evaluation Info', {
            'fields': (
                'student',
                'teacher',
                'subject',
                'semester',
                'academic_year',
            )
        }),

        ('PART I: Presentation of Lesson', {
            'fields': (
                'presentation_objectives',
                'presentation_motivation',
                'presentation_relation',
                'presentation_assignments',
            )
        }),

        ('PART II: Development of the Lesson', {
            'fields': (
                'dev_anticipates',
                'dev_mastery',
                'dev_logical',
                'dev_expression',
                'dev_participation',
                'dev_questions',
                'dev_values',
                'dev_reinforcement',
                'dev_involvement',
                'dev_voice',
                'dev_grammar',
                'dev_monitoring',
                'dev_time',
            )
        }),

        ('PART III: Expected Student Behavior', {
            'fields': (
                'student_answers',
                'student_questions',
                'student_engagement',
                'student_timeframe',
                'student_majority',
            )
        }),

        ('PART IV: Wrap-up', {
            'fields': (
                'wrapup_demonstrate',
                'wrapup_synthesize',
            )
        }),

        ('PART V: Problems Met', {
            'fields': (
                'problem_late',
                'problem_absent',
                'problem_video',
            )
        }),

        ('PART VI: Suggestions', {
            'fields': ('suggestions',)
        }),

        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def get_average_rating_display(self, obj):
        return f"{obj.get_average_rating()} / 5"

    get_average_rating_display.short_description = 'Average Rating'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'student__user',
            'teacher__user',
            'subject',
            'semester',
            'academic_year',
        )


# Register all models
admin.site.register(User, CustomUserAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(StudentProfile, StudentProfileAdmin)
admin.site.register(TeacherProfile, TeacherProfileAdmin)
admin.site.register(Subject, SubjectAdmin)
admin.site.register(Evaluation, EvaluationAdmin)
admin.site.register(StudentSubject, StudentSubjectAdmin)
admin.site.register(Semester)
admin.site.register(AcademicYear)
admin.site.register(EvaluationSettings)