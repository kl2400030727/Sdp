from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, MinValueValidator
from django.utils import timezone


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in format: '+1234567890'. Up to 15 digits allowed."
            )
        ]
    )
    city = models.CharField(max_length=100)
    bio = models.TextField(max_length=500, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    total_points = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    eco_score = models.IntegerField(default=50, validators=[MinValueValidator(0)])
    level = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    current_streak = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    longest_streak = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    last_activity = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user'], name='idx_profile_user'),
            models.Index(fields=['total_points'], name='idx_profile_points'),
            models.Index(fields=['-last_activity'], name='idx_profile_activity'),
        ]

    def __str__(self):
        return f"{self.user.username}'s profile"

    def add_points(self, points):
        self.total_points += points
        self.level = (self.total_points // 500) + 1
        self.save()

    def update_streak(self):
        today = timezone.now().date()
        last = self.last_activity.date()

        if (today - last).days == 1:
            self.current_streak += 1
            if self.current_streak > self.longest_streak:
                self.longest_streak = self.current_streak
        elif (today - last).days > 1:
            self.current_streak = 1

        self.last_activity = timezone.now()
        self.save()

    def add_points(self, points):
        if points > 0:
            self.total_points += points
            self.save()


class UserActivityLog(models.Model):
    ACTIVITY_TYPES = [
        ('login', 'Login'),
        ('course_start', 'Course Started'),
        ('module_complete', 'Module Completed'),
        ('quiz_pass', 'Quiz Passed'),
        ('quiz_fail', 'Quiz Failed'),
        ('challenge_complete', 'Challenge Completed'),
        ('badge_earned', 'Badge Earned'),
        ('points_earned', 'Points Earned'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    description = models.CharField(max_length=255)
    points_earned = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', '-created_at'], name='idx_activity_user_date'),
            models.Index(fields=['activity_type'], name='idx_activity_type'),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.activity_type}"


# Add these models to your existing models.py file

class Course(models.Model):
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    CATEGORIES = [
        ('WASTE', 'Waste Management'),
        ('WATER', 'Water Conservation'),
        ('ENERGY', 'Energy Saving'),
        ('FOOD', 'Sustainable Food'),
    ]

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORIES, default='WASTE')

    description = models.TextField()
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    duration_hours = models.IntegerField(default=2)
    points = models.IntegerField(default=100)
    icon = models.CharField(max_length=50, default='fas fa-leaf')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Quiz(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    title = models.CharField(max_length=200)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quizzes', null=True, blank=True)
    description = models.TextField(blank=True)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='easy')
    points = models.IntegerField(default=100)
    question_count = models.IntegerField(default=10)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Challenge(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy - 30 points'),
        ('medium', 'Medium - 50 points'),
        ('hard', 'Hard - 100 points'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    points = models.IntegerField(default=30)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        points_map = {'easy': 30, 'medium': 50, 'hard': 100}
        if not self.points and self.difficulty:
            self.points = points_map.get(self.difficulty, 30)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class QuizQuestion(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    option_a = models.CharField(max_length=500)
    option_b = models.CharField(max_length=500)
    option_c = models.CharField(max_length=500)
    option_d = models.CharField(max_length=500)
    correct_answer = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])
    explanation = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quiz.title} - Q{self.id}"


class EcoImpact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='impacts')
    co2_saved = models.FloatField(default=0)  # in kg
    water_saved = models.FloatField(default=0)  # in liters
    plastic_reduced = models.FloatField(default=0)  # in items/kg
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Eco Impact"


class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField()
    video_url = models.URLField(blank=True, null=True)
    order = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Enrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrolled_users')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    progress_percent = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'course')

    def __str__(self):
        return f"{self.user.username} enrolled in {self.course.title}"


class ModuleCompletion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'module')

    def __str__(self):
        return f"{self.user.username} completed {self.module.title}"



class QuizAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    score = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    percentage = models.FloatField(default=0)
    passed = models.BooleanField(default=False)
    points_earned = models.IntegerField(default=0)
    answers_json = models.TextField(blank=True, null=True)  # Store answers as JSON
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-attempted_at']

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} - {self.score}/{self.total_questions}"


class EcoTip(models.Model):
    content = models.TextField()
    category = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.content[:50] + "..."