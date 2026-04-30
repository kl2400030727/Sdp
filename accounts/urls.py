from django.urls import path
from . import views

urlpatterns = [
    # Authentication URLs
    path('', views.landing, name='landing'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('home/', views.home, name='home'),

    # User URLs
    path('courses/', views.courses, name='courses'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('challenges/', views.challenges, name='challenges'),
    path('challenge/complete/<int:challenge_id>/', views.complete_challenge, name='complete_challenge'),
    path('quiz/<int:quiz_id>/', views.quiz, name='quiz'),
    path('progress/', views.progress, name='progress'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('achievements/', views.achievements, name='achievements'),
    path('enroll/<int:course_id>/', views.enroll_course, name='enroll_course'),
    path('mark-module-completed/<int:module_id>/', views.mark_module_completed, name='mark_module_completed'),
    path('eco-calculator/', views.eco_calculator, name='eco_calculator'),
    path('impact/', views.impact_dashboard, name='impact_dashboard'),
    path('profile/', views.profile_settings, name='profile_settings'),
    path('settings/', views.settings, name='settings'),
    path('certificate/<int:enrollment_id>/', views.generate_certificate, name='generate_certificate'),

    # Admin URLs
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('manage-users/', views.manage_users, name='manage_users'),
    path('manage-courses/', views.manage_courses, name='manage_courses'),
    path('manage-quizzes/', views.manage_quizzes, name='manage_quizzes'),
    path('manage-challenges/', views.manage_challenges, name='manage_challenges'),
    path('quiz-results/', views.quiz_results, name='quiz_results'),
    path('toggle-admin/<int:user_id>/', views.toggle_admin_status, name='toggle_admin'),

    # Course CRUD URLs
    path('add-course/', views.add_course, name='add_course'),
    path('edit-course/<int:course_id>/', views.edit_course, name='edit_course'),
    path('delete-course/<int:course_id>/', views.delete_course, name='delete_course'),

    # Quiz CRUD URLs
    path('add-quiz/', views.add_quiz, name='add_quiz'),
    path('edit-quiz/<int:quiz_id>/', views.edit_quiz, name='edit_quiz'),
    path('delete-quiz/<int:quiz_id>/', views.delete_quiz, name='delete_quiz'),

    # Challenge CRUD URLs
    path('add-challenge/', views.add_challenge, name='add_challenge'),
    path('delete-challenge/<int:challenge_id>/', views.delete_challenge, name='delete_challenge'),

    # API URLs
    path('api/stats/', views.api_stats, name='api_stats'),
    path('api/courses/', views.api_courses, name='api_courses'),
    path('api/quizzes/', views.api_quizzes, name='api_quizzes'),
    path('api/users/', views.api_users, name='api_users'),
    path('api/challenges/', views.api_challenges, name='api_challenges'),
    path('api/quiz-results/', views.api_quiz_results, name='api_quiz_results'),
]