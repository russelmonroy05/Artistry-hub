from django import forms
import uuid

from django.contrib.auth.forms import UserCreationForm
from .models import User, StudentProfile, TeacherProfile, Evaluation, Subject, Department

class StudentRegistrationForm(UserCreationForm):
    
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    student_id_number = forms.CharField(required=True)
    year_level = forms.IntegerField(min_value=1, max_value=4, required=True)
    course = forms.CharField(required=True, initial="College of Computer Science")
    phone = forms.CharField(required=False)
    
    profile_picture = forms.ImageField(
        required=False,
        help_text="Upload your profile picture (Optional)",
        widget=forms.FileInput(attrs={
            'accept': 'image/*',
            'class': 'form-control',
            'id': 'profilePictureInput'
        })
    )
    
    # Add COR field
    certificate_of_registration = forms.FileField(
        required=True,
        help_text="Upload your Certificate of Registration (PDF, JPG, or PNG)",
        widget=forms.FileInput(attrs={
            'accept': '.pdf,.jpg,.jpeg,.png',
            'class': 'form-control',
            'id': 'corInput'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['course'].initial = "College of Computer Science"

    def clean_student_id_number(self):
        student_id_number = self.cleaned_data.get('student_id_number')
        # Skip validation if field is empty (let required=True handle it)
        if not student_id_number:
            return student_id_number
        
        if StudentProfile.objects.filter(student_id_number=student_id_number).exists():
            raise forms.ValidationError("This Student ID is already registered. Please use a different Student ID.")
        return student_id_number

    def clean_course(self):
        return "College of Computer Science"
    
    def clean_profile_picture(self):
        profile_pic = self.cleaned_data.get('profile_picture')
        if profile_pic:
            if profile_pic.size > 2 * 1024 * 1024:
                raise forms.ValidationError("Image file size must be under 2MB")
            try:
                from PIL import Image
                image = Image.open(profile_pic)
                image.verify()
            except Exception:
                raise forms.ValidationError("Invalid image file")
        return profile_pic
    
    def clean_certificate_of_registration(self):
        cor_file = self.cleaned_data.get('certificate_of_registration')
        if cor_file:
            # Check file size (limit to 5MB)
            if cor_file.size > 5 * 1024 * 1024:
                raise forms.ValidationError("File size must be under 5MB")
            
            # Check file extension
            ext = cor_file.name.split('.')[-1].lower()
            if ext not in ['pdf', 'jpg', 'jpeg', 'png']:
                raise forms.ValidationError("Only PDF, JPG, and PNG files are allowed")
        return cor_file
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2', 
                  'student_id_number', 'year_level', 'course', 'phone', 'profile_picture', 'certificate_of_registration']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'student'
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data.get('phone')
        user.email_verification_token = uuid.uuid4().hex

        if commit:
            user.save()
        return user

class TeacherRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    employee_id = forms.CharField(max_length=50, required=True)
    # department is fixed, user cannot change it
    department = forms.CharField(initial="Computer Science Department", required=False, disabled=True)
    phone = forms.CharField(max_length=15, required=False)
    qualification = forms.CharField(max_length=200, required=True)
    experience_years = forms.IntegerField(min_value=0, required=True)
    
    # Profile picture field
    profile_picture = forms.ImageField(
        required=False,
        help_text="Upload your profile picture (Optional)",
        widget=forms.FileInput(attrs={
            'accept': 'image/*',
            'class': 'form-control',
            'id': 'profilePictureInput'
        })
    )
    
    
    def clean_employee_id(self):
        """Check if employee_id already exists"""
        employee_id = self.cleaned_data.get('employee_id')
        if TeacherProfile.objects.filter(employee_id=employee_id).exists():
            raise forms.ValidationError(
                "This Employee ID is already registered. Please use a different Employee ID."
            )
        return employee_id
    
    def clean_profile_picture(self):

        profile_pic = self.cleaned_data.get('profile_picture')

        if profile_pic:
        # Check file size (limit to 2MB)
            if profile_pic.size > 2 * 1024 * 1024:
                raise forms.ValidationError("Image file size must be under 2MB")
        
        # Validate it's an actual image
        try:
            from PIL import Image
            image = Image.open(profile_pic)
            image.load()  # Load the image to ensure it's valid
        except Exception:
            raise forms.ValidationError("Invalid image file")
        
        # Reset file pointer so Django can save it
        profile_pic.seek(0)
    
        return profile_pic

    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'teacher'
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data.get('phone')
        
        if commit:
            user.save()
            # Create TeacherProfile with fixed department
            TeacherProfile.objects.create(
                user=user,
                employee_id=self.cleaned_data['employee_id'],
                department="Computer Science Department",
                qualification=self.cleaned_data['qualification'],
                experience_years=self.cleaned_data['experience_years'],
                profile_picture=self.cleaned_data.get('profile_picture'),
            )
        return user
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'teacher'
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data.get('phone')
        
        if commit:
            user.save()
            # Don't create TeacherProfile here anymore
        return user


class EvaluationForm(forms.ModelForm):
    class Meta:
        model = Evaluation
        fields = [
            'subject',
            # Part I: Presentation of Lesson
            'presentation_objectives', 
            'presentation_motivation', 
            'presentation_relation', 
            'presentation_assignments',
            # Part II: Development of Lesson
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
            # Part III: Expected Student Behavior
            'student_answers', 
            'student_questions', 
            'student_engagement',
            'student_timeframe', 
            'student_majority',
            # Part IV: Wrap-up
            'wrapup_demonstrate', 
            'wrapup_synthesize',
            # Part V: Problems Met
            'problem_late', 
            'problem_absent', 
            'problem_video',
            # Part VI: Suggestions
            'suggestions'
        ]
        widgets = {
            'subject': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'suggestions': forms.Textarea(attrs={
                'class': 'suggestions-textarea',
                'rows': 5,
                'placeholder': 'Please provide your suggestions on how to address the problems you identified...'
            }),
        }