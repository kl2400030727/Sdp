# In accounts/admin.py
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Profile, Course, Quiz, Challenge, QuizQuestion, QuizAttempt, Module, Enrollment, EcoImpact, EcoTip

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False

class CustomUserAdmin(UserAdmin):
    inlines = [ProfileInline]

# Unregister default User admin and register new one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Register other models
admin.site.register(Course)
admin.site.register(Quiz)
admin.site.register(Challenge)
admin.site.register(QuizQuestion)
admin.site.register(QuizAttempt)
admin.site.register(Module)
admin.site.register(Enrollment)
admin.site.register(EcoImpact)
admin.site.register(EcoTip)
