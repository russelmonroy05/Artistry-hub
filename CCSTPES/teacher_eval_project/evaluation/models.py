from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Count, Q
from django.core.validators import FileExtensionValidator
from datetime import datetime



class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('admin', 'Admin'),
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    phone = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    is_pending = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"


class Department(models.Model):
    """Department model for organizing teachers and students"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    head_of_department = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_teacher_count(self):
        """Get number of teachers in this department"""
        return self.teachers.count()
    
    def get_student_count(self):
        """Get number of students in this department"""
        return self.students.count()
    
    class Meta:
        ordering = ['name']



class Subject(models.Model):

    YEAR_LEVEL_CHOICES = (
        (1, '1st Year'),
        (2, '2nd Year'),
        (3, '3rd Year'),
        (4, '4th Year'),
    )

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)

    start_time = models.TimeField(
        help_text="Start time of the subject",
        default="09:00"
    )
    end_time = models.TimeField(
        help_text="End time of the subject",
        default="10:00"
    )

    days = models.CharField(
        max_length=50,
        help_text="Days of the week (e.g. MON,WED,FRI)",
        blank=True
    )

    description = models.TextField(blank=True)

    year_level = models.IntegerField(
        choices=YEAR_LEVEL_CHOICES,
        help_text="Year level this subject is offered to"
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='subjects',
        help_text="Department offering this subject"
    )

    created_by = models.ForeignKey(
        'TeacherProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_subjects',
        help_text="Teacher who created this subject"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"

    def get_time_range(self):
        return f"{self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')}"

    def get_schedule(self):
        days = self.days.replace(',', ', ') if self.days else 'TBA'
        return f"{days} · {self.get_time_range()}"

    def get_duration(self):
        start = datetime.combine(datetime.min, self.start_time)
        end = datetime.combine(datetime.min, self.end_time)
        return round((end - start).total_seconds() / 3600, 2)

    def get_creator_name(self):
        return self.created_by.user.get_full_name() if self.created_by else "System"



class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    employee_id = models.CharField(max_length=50, unique=True)
    profile_picture = models.ImageField(upload_to='teacher_profiles/', blank=True, null=True)
    
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='teachers',
        help_text="Department this teacher belongs to"
    )
    
    subjects = models.ManyToManyField(
        Subject, 
        related_name='teachers',
        blank=True,
        help_text="Subjects taught by this teacher"
    )
    
    qualification = models.CharField(max_length=200)
    experience_years = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Teacher: {self.user.username} ({self.department.code})"
    
    def get_average_rating(self):
        """Calculate average rating from all evaluations"""
        evaluations = self.evaluations.all()
        if evaluations.exists():
            total_avg = 0
            for evaluation in evaluations:
                total_avg += evaluation.get_average_rating()  # Use Evaluation's get_average_rating() method
            return round(total_avg / evaluations.count(), 2)
        return 0
    
    def get_subjects_list(self):
        """Get comma-separated list of subject codes"""
        return ", ".join([subject.code for subject in self.subjects.all()])
    
    def get_teaching_schedule(self):
        """Get all teaching schedules for this teacher"""
        schedules = []
        for subject in self.subjects.all():
            schedules.append({
                'subject': subject,
                'schedule': subject.get_schedule(),
                'duration': subject.get_duration()
            })
        return schedules
    
    def get_created_subjects_count(self):
        """Get count of subjects created by this teacher"""
        return self.created_subjects.count()
    
    def get_evaluation_progress(self):
        """Get evaluation progress percentage for this teacher
        Returns a dict with total_possible, completed, and percentage"""
        # Get all students in the same department
        total_students = StudentProfile.objects.filter(
            department=self.department
        ).count()
        
        # Get completed evaluations for this teacher
        completed_evaluations = self.evaluations.count()
        
        if total_students == 0:
            return {
                'total_possible': 0,
                'completed': 0,
                'percentage': 0
            }
        
        percentage = round((completed_evaluations / total_students) * 100, 2)
        
        return {
            'total_possible': total_students,
            'completed': completed_evaluations,
            'percentage': percentage
        }
    
    class Meta:
        ordering = ['user__username']


class StudentProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )

    student_id_number = models.CharField(max_length=50, unique=True)

    profile_picture = models.ImageField(
        upload_to='student_profiles/',
        blank=True, 
        null=True
    )

    year_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(4)]
    )

    course = models.CharField(max_length=100)
    section = models.CharField(max_length=50, default="A")

    # Certificate of Registration (COR)
    certificate_of_registration = models.FileField(
        upload_to='student_cor/%Y/%m/',
        validators=[FileExtensionValidator(
            allowed_extensions=['pdf', 'jpg', 'jpeg', 'png']
        )],
        blank=True,
        null=True
    )

    cor_uploaded_at = models.DateTimeField(
        null=True,
        blank=True
    )

    # Student belongs to ONE department
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='students'
    )

    class Meta:
        ordering = ['user__username']

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.student_id_number})"

    # ---------------------------
    # HELPERS - FIXED FOR YOUR SETUP
    # ---------------------------

    def has_cor(self):
        """Check if student has uploaded COR"""
        return bool(self.certificate_of_registration)

    def get_assigned_subjects(self):
        """
        Returns StudentSubject objects assigned by admin based on COR.
        These are manually entered subjects from the student's COR.
        """
        return self.assigned_subjects.select_related('teacher', 'teacher__user').all()

    def get_assigned_teachers(self):
        """
        Get teachers from assigned StudentSubject entries.
        These are the teachers the student should evaluate based on COR.
        """
        teacher_ids = self.assigned_subjects.filter(
            teacher__isnull=False
        ).values_list('teacher_id', flat=True).distinct()
        
        return TeacherProfile.objects.filter(id__in=teacher_ids).distinct()

    def has_assigned_subjects(self):
        """Check if student has subjects assigned by admin based on COR"""
        return self.assigned_subjects.exists()

    def get_year_level_display(self):
        """Get formatted year level text"""
        return {
            1: '1st Year',
            2: '2nd Year',
            3: '3rd Year',
            4: '4th Year'
        }.get(self.year_level, 'Unknown')

    def get_available_subjects(self):
        """
        Get subjects this student should see.
        
        Returns:
        - StudentSubject queryset if admin assigned subjects via COR
        - Subject queryset if no COR assignments yet
        
        NOTE: These are different models! Handle accordingly in views.
        """
        # If admin has assigned subjects via COR, return those
        if self.has_assigned_subjects():
            # Return StudentSubject queryset (has: subject_name, subject_code, teacher)
            return self.assigned_subjects.select_related('teacher', 'teacher__user').all()
        
        # Otherwise, return Subject queryset for this year level
        # (has: name, code, teachers ManyToMany, department)
        return Subject.objects.filter(
            year_level=self.year_level
        ).prefetch_related('teachers', 'teachers__user').distinct()

    def get_available_teachers(self):
        """
        Get teachers this student should evaluate.
        
        Logic:
        - If COR subjects assigned: only evaluate those specific teachers
        - If no COR assignments: evaluate all teachers for year level subjects
        """
        # If student has COR-assigned subjects, only evaluate those teachers
        if self.has_assigned_subjects():
            return self.get_assigned_teachers()
        
        # Otherwise, get all teachers teaching subjects for this year level
        # Since Subject.teachers is ManyToMany, we need to collect all teachers
        subjects_for_year = Subject.objects.filter(year_level=self.year_level)
        
        teacher_ids = set()
        for subject in subjects_for_year.prefetch_related('teachers'):
            teacher_ids.update(subject.teachers.values_list('id', flat=True))
        
        if teacher_ids:
            return TeacherProfile.objects.filter(id__in=teacher_ids).distinct()
        
        return TeacherProfile.objects.none()

    def get_evaluation_progress(self):
        """
        Get evaluation progress percentage for this student.
        
        Returns:
            dict with total_available, completed, and percentage
        """
        # Get all teachers this student should evaluate
        total_available = self.get_available_teachers().count()
        
        # Get completed evaluations by this student
        completed_evaluations = self.my_evaluations.count()
        
        if total_available == 0:
            return {
                'total_available': 0,
                'completed': 0,
                'percentage': 0
            }
        
        percentage = round((completed_evaluations / total_available) * 100, 2)
        
        return {
            'total_available': total_available,
            'completed': completed_evaluations,
            'percentage': percentage
        }
    

    
class StudentSubject(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='assigned_subjects')
    
    # Add this field to link to actual Subject
    subject = models.ForeignKey(
        'Subject', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text="Link to the actual Subject in the system"
    )
    
    # Keep these for backward compatibility
    subject_name = models.CharField(max_length=100)
    subject_code = models.CharField(max_length=20)
    
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.subject:
            return f"{self.subject.code} - {self.subject.name}"
        return f"{self.subject_code} - {self.subject_name}"
    
    def get_subject_code(self):
        return self.subject.code if self.subject else self.subject_code
    
    def get_subject_name(self):
        return self.subject.name if self.subject else self.subject_name
    

class AcademicYear(models.Model):
    name = models.CharField(max_length=20, unique=True)
    start_Year = models.IntegerField()
    end_Year = models.IntegerField()
    is_active = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-start_Year']
    def __str__(self):
        return f"{self.name} ({self.start_Year}-{self.end_Year})"



class Semester(models.Model):
    name = models.CharField(max_length=20, unique=True)
    start_Month = models.DateField()
    end_Month = models.DateField()
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='semesters'
    )
    class Meta:
        ordering = ['-start_Month']
    def __str__(self):
        return f"{self.name} ({self.academic_year.start_Year}-{self.academic_year.end_Year})"

class EvaluationSettings(models.Model):
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='evaluation_settings'
    )
    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE,
        related_name='evaluation_settings'
    )
    is_open = models.BooleanField(default=False)
    open_date = models.DateTimeField(null=True, blank=True)
    close_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['academic_year', 'semester']
        ordering = ['-academic_year__start_Year', '-semester__start_Month']
    
    def __str__(self):
        status = "Open" if self.is_open else "Closed"
        return f"Evaluation Settings for {self.academic_year.name} - {self.semester.name} ({status})"
    


class Evaluation(models.Model):
    student = models.ForeignKey(
        StudentProfile, 
        on_delete=models.CASCADE, 
        related_name='my_evaluations'
    )
    teacher = models.ForeignKey(
        TeacherProfile, 
        on_delete=models.CASCADE, 
        related_name='evaluations'
    )
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    
    # PART I: PRESENTATION OF LESSON (1-5)
    presentation_objectives = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Communicates clearly the objectives of the lesson"
    )
    presentation_motivation = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Uses motivational techniques that elicit student interest"
    )
    presentation_relation = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Relates previous lesson to the present"
    )
    presentation_assignments = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Checks assignments (if any)"
    )
    
    # PART II: DEVELOPMENT OF THE LESSON - Expected Teacher Behavior (1-5)
    dev_anticipates = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Anticipates difficulties of the students"
    )
    dev_mastery = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Demonstrates mastery of the lesson"
    )
    dev_logical = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Develops the lesson logically"
    )
    dev_expression = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Provides opportunities for free expression of class"
    )
    dev_participation = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Provides opportunities for students' participation in decision making"
    )
    dev_questions = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Asks questions of various levels"
    )
    dev_values = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Integrates values in the lesson"
    )
    dev_reinforcement = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Provides appropriate reinforcement to student behavior"
    )
    dev_involvement = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Keeps majority of students involved in learning tasks"
    )
    dev_voice = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Speaks in well-modulated voice"
    )
    dev_grammar = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Observes correct grammar in speaking and writing"
    )
    dev_monitoring = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Monitors student progress through assessment tools"
    )
    dev_time = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Utilizes instructional time productively"
    )
    
    # PART III: EXPECTED STUDENT BEHAVIOR (1-5)
    student_answers = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Students answer in own words at designed cognitive level"
    )
    student_questions = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Students ask questions relevant to the lesson"
    )
    student_engagement = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Students are actively engaged in learning tasks"
    )
    student_timeframe = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Students work within time frame allotted"
    )
    student_majority = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Students abide by the decision of the majority"
    )
    
    # PART IV: WRAP-UP (1-5)
    wrapup_demonstrate = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Teacher provides opportunities to demonstrate learnings"
    )
    wrapup_synthesize = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Students synthesize learning through integration activities"
    )
    
    # PART V: PROBLEMS MET (1-3: 3=Very Serious, 2=Serious, 1=Not Serious)
    problem_late = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        help_text="Late in coming to class"
    )
    problem_absent = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        help_text="Absenteeism"
    )
    problem_video = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        help_text="Very long video presentation (>30 minutes)"
    )
    
    # PART VI: SUGGESTIONS
    suggestions = models.TextField(
        help_text="Suggested measures to solve the problems"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'teacher', 'subject', 'semester', 'academic_year']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.user.username} evaluated {self.teacher.user.username} - {self.subject.code}"
    
    def get_average_rating(self):
        """Calculate overall average rating from all criteria"""
        # Part I: Presentation (4 items)
        part1 = (
            self.presentation_objectives + self.presentation_motivation + 
            self.presentation_relation + self.presentation_assignments
        )
        
        # Part II: Development (13 items)
        part2 = (
            self.dev_anticipates + self.dev_mastery + self.dev_logical + 
            self.dev_expression + self.dev_participation + self.dev_questions + 
            self.dev_values + self.dev_reinforcement + self.dev_involvement + 
            self.dev_voice + self.dev_grammar + self.dev_monitoring + self.dev_time
        )
        
        # Part III: Student Behavior (5 items)
        part3 = (
            self.student_answers + self.student_questions + 
            self.student_engagement + self.student_timeframe + self.student_majority
        )
        
        # Part IV: Wrap-up (2 items)
        part4 = self.wrapup_demonstrate + self.wrapup_synthesize
        
        # Total: 24 items, all rated 1-5
        total_score = part1 + part2 + part3 + part4
        average = total_score / 24
        
        return round(average, 2)
    
    def get_presentation_average(self):
        """Average for Part I: Presentation of Lesson"""
        total = (
            self.presentation_objectives + self.presentation_motivation + 
            self.presentation_relation + self.presentation_assignments
        )
        return round(total / 4, 2)
    
    def get_development_average(self):
        """Average for Part II: Development of Lesson"""
        total = (
            self.dev_anticipates + self.dev_mastery + self.dev_logical + 
            self.dev_expression + self.dev_participation + self.dev_questions + 
            self.dev_values + self.dev_reinforcement + self.dev_involvement + 
            self.dev_voice + self.dev_grammar + self.dev_monitoring + self.dev_time
        )
        return round(total / 13, 2)
    
    def get_student_behavior_average(self):
        """Average for Part III: Expected Student Behavior"""
        total = (
            self.student_answers + self.student_questions + 
            self.student_engagement + self.student_timeframe + self.student_majority
        )
        return round(total / 5, 2)
    
    def get_wrapup_average(self):
        """Average for Part IV: Wrap-up"""
        total = self.wrapup_demonstrate + self.wrapup_synthesize
        return round(total / 2, 2)
    
    def get_problems_severity(self):
        """Get total problems severity (3 = most serious)"""
        return {
            'late': self.problem_late,
            'absent': self.problem_absent,
            'video': self.problem_video,
            'total': self.problem_late + self.problem_absent + self.problem_video
        }