from django.core.management.base import BaseCommand
from django.db.models import Count
from evaluation.models import User, StudentProfile, TeacherProfile, Evaluation


class Command(BaseCommand):
    help = 'Find and optionally deduplicate users that share the same email address.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Apply changes (merge and delete duplicates)')

    def handle(self, *args, **options):
        duplicates = (
            User.objects
            .values('email')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
            .order_by('-count')
        )

        if not duplicates:
            self.stdout.write(self.style.SUCCESS('No duplicate emails found.'))
            return

        self.stdout.write('Duplicate emails:')
        for item in duplicates:
            email = item['email']
            count = item['count']
            self.stdout.write(f'  {email!r}: {count} users')

        if not options['apply']:
            self.stdout.write('\nRun this command with --apply to merge duplicates (non-reversible).')
            return

        self.stdout.write('\nApplying deduplication...')

        for item in duplicates:
            email = item['email']
            users = list(User.objects.filter(email__iexact=email).order_by('date_joined'))
            if len(users) <= 1:
                continue

            keep = users[0]
            others = users[1:]

            self.stdout.write(f"Merging {len(others)} users into {keep.username} (id={keep.id}) for email {email}")

            # Reassign profiles where possible
            for other in others:
                # StudentProfile
                try:
                    other_student = other.student_profile
                except StudentProfile.DoesNotExist:
                    other_student = None

                try:
                    keep_student = keep.student_profile
                except StudentProfile.DoesNotExist:
                    keep_student = None

                if other_student and not keep_student:
                    self.stdout.write(f'  Reassigning student profile {other_student.id} -> user {keep.username}')
                    other_student.user = keep
                    other_student.save()
                elif other_student and keep_student:
                    # Move evaluations from other_student to keep_student
                    self.stdout.write(f'  Moving evaluations from student {other_student.id} to {keep_student.id}')
                    Evaluation.objects.filter(student=other_student).update(student=keep_student)
                    # Delete the empty other_student profile
                    try:
                        other_student.delete()
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'    Failed to delete student profile: {e}'))

                # TeacherProfile
                try:
                    other_teacher = other.teacher_profile
                except TeacherProfile.DoesNotExist:
                    other_teacher = None

                try:
                    keep_teacher = keep.teacher_profile
                except TeacherProfile.DoesNotExist:
                    keep_teacher = None

                if other_teacher and not keep_teacher:
                    self.stdout.write(f'  Reassigning teacher profile {other_teacher.id} -> user {keep.username}')
                    other_teacher.user = keep
                    other_teacher.save()
                elif other_teacher and keep_teacher:
                    # Move evaluations for teacher
                    self.stdout.write(f'  Moving evaluations from teacher {other_teacher.id} to {keep_teacher.id}')
                    Evaluation.objects.filter(teacher=other_teacher).update(teacher=keep_teacher)
                    try:
                        other_teacher.delete()
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'    Failed to delete teacher profile: {e}'))

                # Finally delete the duplicate user
                try:
                    other.delete()
                    self.stdout.write(self.style.SUCCESS(f'  Deleted duplicate user id={other.id}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  Failed to delete user id={other.id}: {e}'))

        self.stdout.write(self.style.SUCCESS('Deduplication complete.'))
