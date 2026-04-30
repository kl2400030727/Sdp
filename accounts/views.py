from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import PermissionDenied
import json
import requests
from django.utils import timezone
from django.db.models import Sum
from .models import Profile, UserActivityLog, Course, Quiz, Challenge, QuizQuestion, QuizAttempt, Enrollment, EcoImpact, Module, EcoTip, ModuleCompletion
from .decorators import admin_required


# ==================== LANDING & AUTHENTICATION ====================

def landing(request):
    return render(request, 'accounts/landing.html')


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            profile, created = Profile.objects.get_or_create(user=user)
            profile.update_streak()
            profile.add_points(5)

            UserActivityLog.objects.create(
                user=user,
                activity_type='login',
                description=f'User logged in successfully',
                points_earned=5
            )

            messages.success(request, f'Welcome back, {user.first_name or user.username}!')

            # Redirect based on user role
            if user.is_staff:
                return redirect("admin_dashboard")
            else:
                return redirect("home")
        else:
            return render(request, 'accounts/login.html', {'error': 'Invalid username or password'})

    return render(request, 'accounts/login.html')


def register(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        phone = request.POST.get("phone")
        city = request.POST.get("city")

        if password != confirm_password:
            return render(request, 'accounts/register.html', {'error': 'Passwords do not match'})

        if User.objects.filter(username=username).exists():
            return render(request, 'accounts/register.html', {'error': 'Username already exists'})

        if User.objects.filter(email=email).exists():
            return render(request, 'accounts/register.html', {'error': 'Email already registered'})

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            profile = Profile.objects.create(
                user=user,
                phone_number=phone,
                city=city
            )

            profile.add_points(100)

            messages.success(request, 'Registration successful! Please login.')
            return redirect("login")

        except Exception as e:
            return render(request, 'accounts/register.html', {'error': f'Registration failed: {str(e)}'})

    return render(request, 'accounts/register.html')


# ==================== USER DASHBOARD VIEWS ====================

@login_required(login_url='login')
def home(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    # Calculate stats
    courses_completed = QuizAttempt.objects.filter(user=request.user, passed=True).values('quiz').distinct().count()
    challenges_won = UserActivityLog.objects.filter(user=request.user, activity_type='challenge_complete').count()
    
    # Get active content
    featured_courses = Course.objects.filter(is_active=True)[:3]
    enrollments = Enrollment.objects.filter(user=request.user)
    enrolled_courses = enrollments.values_list('course_id', flat=True)
    enrollment_progress = {e.course_id: e.progress_percent for e in enrollments}
    
    daily_challenge = Challenge.objects.filter(is_active=True).first()
    impact, _ = EcoImpact.objects.get_or_create(user=request.user)
    
    # Get a featured video from enrolled courses or a random active module
    featured_video = Module.objects.filter(course_id__in=enrolled_courses, video_url__isnull=False).first()
    if not featured_video:
        featured_video = Module.objects.filter(video_url__isnull=False).first()
    
    # Community Impact
    community_impact = EcoImpact.objects.aggregate(
        total_co2=Sum('co2_saved'),
        total_water=Sum('water_saved')
    )
    
    # Daily Eco Tip
    daily_tip = EcoTip.objects.filter(is_active=True).order_by('?').first()
    
    context = {
        'profile': profile,
        'courses_completed': courses_completed,
        'challenges_won': challenges_won,
        'featured_courses': featured_courses,
        'enrolled_courses': enrolled_courses,
        'enrollment_progress': enrollment_progress,
        'daily_challenge': daily_challenge,
        'impact': impact,
        'featured_video': featured_video,
        'recent_activity': UserActivityLog.objects.filter(user=request.user).order_by('-created_at')[:5],
        'community_impact': community_impact,
        'daily_tip': daily_tip
    }
    return render(request, 'accounts/home.html', context)


@login_required(login_url='login')
def eco_calculator(request):
    if request.method == "POST":
        try:
            electricity = float(request.POST.get('electricity', 0) or 0)
            transport = request.POST.get('transport', 'car')
            km = float(request.POST.get('km', 0) or 0)
            
            co2 = electricity * 0.5
            if transport == 'car': co2 += km * 0.2
            elif transport == 'bus': co2 += km * 0.1
            elif transport == 'metro': co2 += km * 0.05
            
            profile = request.user.profile
            profile.eco_score = max(0, 100 - int(co2 / 10))
            profile.save()
            
            # Update EcoImpact
            impact, _ = EcoImpact.objects.get_or_create(user=request.user)
            impact.co2_saved = max(0, 500 - co2) # Demo logic: baseline 500kg
            impact.save()
            
            messages.success(request, f"Calculation complete! Your monthly footprint is approx {co2:.2f} kg CO2.")
            return redirect('impact_dashboard')
        except ValueError:
            messages.error(request, "Please enter valid numerical values.")
            
    return render(request, 'accounts/eco_calculator.html')


@login_required(login_url='login')
def impact_dashboard(request):
    impact, _ = EcoImpact.objects.get_or_create(user=request.user)
    profile = request.user.profile
    
    context = {
        'impact': impact,
        'profile': profile,
    }
    return render(request, 'accounts/impact_dashboard.html', context)


@login_required(login_url='login')
def courses(request):
    courses = Course.objects.filter(is_active=True)
    enrolled_courses = Enrollment.objects.filter(user=request.user).values_list('course_id', flat=True)
    completed_enrollments = Enrollment.objects.filter(user=request.user, is_completed=True)
    completed_dict = {e.course_id: e.id for e in completed_enrollments}
    
    return render(request, 'accounts/courses.html', {
        'courses': courses,
        'enrolled_courses': enrolled_courses,
        'completed_enrollments': completed_dict
    })


@login_required(login_url='login')
def course_detail(request, course_id):
    course = Course.objects.get(id=course_id)
    modules = course.modules.all()
    enrollment = Enrollment.objects.filter(user=request.user, course=course).first()
    
    completed_modules = []
    if enrollment:
        completed_modules = ModuleCompletion.objects.filter(user=request.user, module__course=course).values_list('module_id', flat=True)

    context = {
        'course': course,
        'modules': modules,
        'enrollment': enrollment,
        'completed_modules': completed_modules,
    }
    return render(request, 'accounts/course_detail.html', context)


@login_required(login_url='login')
def enroll_course(request, course_id):
    course = Course.objects.get(id=course_id)
    enrollment, created = Enrollment.objects.get_or_create(user=request.user, course=course)
    
    if created:
        UserActivityLog.objects.create(
            user=request.user,
            activity_type='course_start',
            description=f"Enrolled in course: {course.title}"
        )
        messages.success(request, f"Successfully enrolled in {course.title}!")
    else:
        messages.info(request, f"You are already enrolled in {course.title}.")
        
    return redirect('course_detail', course_id=course.id)


@login_required(login_url='login')
def challenges(request):
    quizzes = Quiz.objects.filter(is_active=True)
    challenges = Challenge.objects.filter(is_active=True)
    return render(request, 'accounts/challenges.html', {'quizzes': quizzes, 'challenges': challenges})


def fetch_quiz_questions_from_api(amount=10):
    """Fetch questions from Open Trivia DB API"""
    url = f"https://opentdb.com/api.php?amount={amount}&type=multiple"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if data['response_code'] == 0:
            questions = []
            for item in data['results']:
                import html
                import random

                question = {
                    'question_text': html.unescape(item['question']),
                    'correct_answer': html.unescape(item['correct_answer']),
                    'incorrect_answers': [html.unescape(ans) for ans in item['incorrect_answers']],
                }

                # Create options list
                options = [question['correct_answer']] + question['incorrect_answers']
                random.shuffle(options)

                # Find correct option letter
                correct_index = options.index(question['correct_answer'])
                correct_letter = ['A', 'B', 'C', 'D'][correct_index]

                questions.append({
                    'question_text': question['question_text'],
                    'option_a': options[0],
                    'option_b': options[1],
                    'option_c': options[2],
                    'option_d': options[3],
                    'correct_answer': correct_letter,
                })
            return questions
        else:
            return None
    except Exception as e:
        print(f"API Error: {e}")
        return None


@login_required(login_url='login')
def quiz(request, quiz_id):
    quiz_obj = Quiz.objects.get(id=quiz_id)

    # Check if user already attempted this quiz
    existing_attempt = QuizAttempt.objects.filter(user=request.user, quiz=quiz_obj).first()
    if existing_attempt:
        return render(request, 'accounts/quiz_result.html', {'attempt': existing_attempt, 'quiz': quiz_obj})

    # Get or create questions for this quiz
    questions = QuizQuestion.objects.filter(quiz=quiz_obj)

    if not questions.exists():
        # Fetch from API
        api_questions = fetch_quiz_questions_from_api(amount=quiz_obj.question_count)
        if api_questions:
            for q in api_questions:
                QuizQuestion.objects.create(
                    quiz=quiz_obj,
                    question_text=q['question_text'],
                    option_a=q['option_a'],
                    option_b=q['option_b'],
                    option_c=q['option_c'],
                    option_d=q['option_d'],
                    correct_answer=q['correct_answer']
                )
            questions = QuizQuestion.objects.filter(quiz=quiz_obj)

    if request.method == "POST":
        # Calculate score
        score = 0
        total = questions.count()
        user_answers = {}

        for question in questions:
            user_answer = request.POST.get(f'q_{question.id}')
            user_answers[str(question.id)] = user_answer
            if user_answer and user_answer.upper() == question.correct_answer:
                score += 1

        percentage = (score / total) * 100 if total > 0 else 0
        passed = percentage >= 50
        points_earned = int(quiz_obj.points * (score / total)) if passed else 0

        # Save attempt
        attempt = QuizAttempt.objects.create(
            user=request.user,
            quiz=quiz_obj,
            score=score,
            total_questions=total,
            percentage=percentage,
            passed=passed,
            points_earned=points_earned,
            answers_json=json.dumps(user_answers)
        )

        # Add points to user profile and mark course as completed
        if passed:
            profile, _ = Profile.objects.get_or_create(user=request.user)
            profile.add_points(points_earned)
            
            # If this quiz is linked to a course, mark the enrollment as completed
            if quiz_obj.course:
                enrollment = Enrollment.objects.filter(user=request.user, course=quiz_obj.course).first()
                if enrollment:
                    enrollment.is_completed = True
                    enrollment.save()
                    messages.success(request, f"Congratulations! You've completed {quiz_obj.course.title} and earned a certificate!")

        return render(request, 'accounts/quiz_result.html', {'attempt': attempt, 'quiz': quiz_obj})

    context = {
        'quiz': quiz_obj,
        'questions': questions,
        'total_questions': questions.count(),
    }
    return render(request, 'accounts/quiz.html', context)


@login_required(login_url='login')
def complete_challenge(request, challenge_id):
    if request.method == "POST":
        challenge = Challenge.objects.get(id=challenge_id)
        profile, _ = Profile.objects.get_or_create(user=request.user)
        
        # Check if already completed today (simple version)
        already_done = UserActivityLog.objects.filter(
            user=request.user, 
            activity_type='challenge_complete',
            description__contains=challenge.title,
            created_at__date=timezone.now().date()
        ).exists()
        
        if not already_done:
            profile.add_points(challenge.points)
            UserActivityLog.objects.create(
                user=request.user,
                activity_type='challenge_complete',
                description=f"Completed challenge: {challenge.title}",
                points_earned=challenge.points
            )
            messages.success(request, f"Challenge completed! You earned {challenge.points} points.")
        else:
            messages.info(request, "You have already completed this challenge today.")
            
    return redirect('challenges')


@login_required(login_url='login')
def progress(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    activities = UserActivityLog.objects.filter(user=request.user).order_by('-created_at')[:20]
    quiz_attempts = QuizAttempt.objects.filter(user=request.user).order_by('-attempted_at')
    
    context = {
        'profile': profile,
        'activities': activities,
        'quiz_attempts': quiz_attempts,
    }
    return render(request, 'accounts/progress.html', context)


@login_required(login_url='login')
def leaderboard(request):
    top_profiles = Profile.objects.all().order_by('-total_points')[:10]
    context = {
        'top_profiles': top_profiles,
    }
    return render(request, 'accounts/leaderboard.html', context)


@login_required(login_url='login')
def achievements(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    completed_enrollments = Enrollment.objects.filter(user=request.user, is_completed=True).select_related('course')
    
    context = {
        'profile': profile,
        'completed_enrollments': completed_enrollments,
    }
    return render(request, 'accounts/achievements.html', context)


@login_required(login_url='login')
def profile_settings(request):
    user = request.user
    profile, created = Profile.objects.get_or_create(user=user)

    if request.method == "POST":
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()

        profile.phone_number = request.POST.get('phone_number', profile.phone_number)
        profile.city = request.POST.get('city', profile.city)
        profile.bio = request.POST.get('bio', profile.bio)

        if request.FILES.get('profile_picture'):
            profile.profile_picture = request.FILES['profile_picture']

        profile.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('profile_settings')

    context = {
        'user': user,
        'profile': profile,
    }
    return render(request, 'accounts/profile_settings.html', context)


@login_required(login_url='login')
def settings(request):
    user = request.user

    if request.method == "POST":
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        messages.success(request, 'Settings updated successfully!')
        return redirect('settings')

    return render(request, 'accounts/settings.html', {'user': user})


# ==================== ADMIN DASHBOARD VIEWS ====================

@admin_required
def admin_dashboard(request):
    """Admin dashboard for managing platform"""
    return render(request, 'accounts/admin_dashboard.html')


@admin_required
def manage_users(request):
    """Admin can view and manage users"""
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'accounts/manage_users.html', {'users': users})


@admin_required
def toggle_admin_status(request, user_id):
    """Admin can make another user admin"""
    if request.method == "POST":
        target_user = User.objects.get(id=user_id)
        if not target_user.is_superuser:
            target_user.is_staff = not target_user.is_staff
            target_user.save()
            messages.success(request, f"Updated {target_user.username}'s admin status")
    return redirect('manage_users')


@admin_required
def quiz_results(request):
    """Admin can view all quiz attempts"""
    attempts = QuizAttempt.objects.all().order_by('-attempted_at')

    # Calculate passed and failed counts
    passed_count = attempts.filter(passed=True).count()
    failed_count = attempts.filter(passed=False).count()

    context = {
        'attempts': attempts,
        'passed_count': passed_count,
        'failed_count': failed_count,
    }
    return render(request, 'accounts/quiz_results.html', context)


# ==================== COURSE MANAGEMENT ====================

@admin_required
def manage_courses(request):
    """Admin page for managing courses"""
    courses = Course.objects.all()
    return render(request, 'accounts/manage_courses.html', {'courses': courses})


def get_youtube_embed_url(url):
    """Helper to convert any YouTube URL to an embed URL"""
    if not url:
        return None
    url = url.strip()
    if 'embed/' in url:
        return url
    
    video_id = None
    if 'watch?v=' in url:
        video_id = url.split('v=')[1].split('&')[0]
    elif 'youtu.be/' in url:
        video_id = url.split('youtu.be/')[1].split('?')[0]
    elif 'youtube.com/shorts/' in url:
        video_id = url.split('shorts/')[1].split('?')[0]
        
    if video_id:
        return f'https://www.youtube.com/embed/{video_id}'
    return url if url.startswith('http') else None

@admin_required
def add_course(request):
    """Add a new course with modules"""
    if request.method == "POST":
        course = Course.objects.create(
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            category=request.POST.get('category', 'WASTE'),
            level=request.POST.get('level'),
            duration_hours=int(request.POST.get('duration_hours', 2)),
            points=int(request.POST.get('points', 100)),
            icon=request.POST.get('icon', 'fas fa-leaf'),
        )
        
        module_titles = request.POST.getlist('module_title')
        module_descs = request.POST.getlist('module_description')
        module_videos = request.POST.getlist('module_video')
        
        for idx, title in enumerate(module_titles):
            if title.strip():
                raw_video = module_videos[idx] if idx < len(module_videos) else ''
                embed_url = get_youtube_embed_url(raw_video)
                
                Module.objects.create(
                    course=course,
                    title=title.strip(),
                    description=module_descs[idx].strip() if idx < len(module_descs) else '',
                    video_url=embed_url,
                    order=idx + 1,
                )
        
        messages.success(request, f'Course "{course.title}" added successfully!')
        return redirect('manage_courses')
    return redirect('manage_courses')

@admin_required
def edit_course(request, course_id):
    """Edit an existing course and its modules"""
    if request.method == "POST":
        course = Course.objects.get(id=course_id)
        course.title = request.POST.get('title')
        course.description = request.POST.get('description')
        course.category = request.POST.get('category', course.category)
        course.level = request.POST.get('level')
        course.duration_hours = int(request.POST.get('duration_hours', 2))
        course.points = int(request.POST.get('points', 100))
        course.icon = request.POST.get('icon', course.icon)
        course.save()
        
        course.modules.all().delete()
        module_titles = request.POST.getlist('module_title')
        module_descs = request.POST.getlist('module_description')
        module_videos = request.POST.getlist('module_video')
        
        for idx, title in enumerate(module_titles):
            if title.strip():
                raw_video = module_videos[idx] if idx < len(module_videos) else ''
                embed_url = get_youtube_embed_url(raw_video)
                
                Module.objects.create(
                    course=course,
                    title=title.strip(),
                    description=module_descs[idx].strip() if idx < len(module_descs) else '',
                    video_url=embed_url,
                    order=idx + 1,
                )
        
        messages.success(request, f'Course "{course.title}" updated successfully!')
        return redirect('manage_courses')
    return redirect('manage_courses')



@admin_required
def delete_course(request, course_id):
    """Delete a course"""
    if request.method == "POST":
        course = Course.objects.get(id=course_id)
        title = course.title
        course.delete()
        messages.success(request, f'Course "{title}" deleted successfully!')
        return redirect('manage_courses')
    return redirect('manage_courses')


# ==================== QUIZ MANAGEMENT ====================

@admin_required
def manage_quizzes(request):
    """Admin page for managing quizzes"""
    quizzes = Quiz.objects.all()
    return render(request, 'accounts/manage_quizzes.html', {'quizzes': quizzes})


@admin_required
def add_quiz(request):
    """Add a new quiz"""
    if request.method == "POST":
        quiz = Quiz.objects.create(
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            difficulty=request.POST.get('difficulty'),
            points=int(request.POST.get('points', 100)),
            question_count=int(request.POST.get('question_count', 10))
        )
        messages.success(request, f'Quiz "{quiz.title}" added successfully!')
        return redirect('manage_quizzes')
    return redirect('manage_quizzes')


@admin_required
def edit_quiz(request, quiz_id):
    """Edit an existing quiz"""
    if request.method == "POST":
        quiz = Quiz.objects.get(id=quiz_id)
        quiz.title = request.POST.get('title')
        quiz.description = request.POST.get('description')
        quiz.difficulty = request.POST.get('difficulty')
        quiz.points = int(request.POST.get('points', 100))
        quiz.question_count = int(request.POST.get('question_count', 10))
        
        course_id = request.POST.get('course')
        if course_id:
            quiz.course = Course.objects.filter(id=course_id).first()
        else:
            quiz.course = None
            
        quiz.save()
        messages.success(request, f'Quiz "{quiz.title}" updated successfully!')
        return redirect('manage_quizzes')
    return redirect('manage_quizzes')


@admin_required
def delete_quiz(request, quiz_id):
    """Delete a quiz"""
    if request.method == "POST":
        quiz = Quiz.objects.get(id=quiz_id)
        title = quiz.title
        quiz.delete()
        messages.success(request, f'Quiz "{title}" deleted successfully!')
        return redirect('manage_quizzes')
    return redirect('manage_quizzes')


# ==================== CHALLENGE MANAGEMENT ====================

@admin_required
def manage_challenges(request):
    """Admin page for managing challenges"""
    challenges = Challenge.objects.all()
    return render(request, 'accounts/manage_challenges.html', {'challenges': challenges})


@admin_required
def add_challenge(request):
    """Add a new challenge"""
    if request.method == "POST":
        difficulty = request.POST.get('difficulty')
        points_map = {'easy': 30, 'medium': 50, 'hard': 100}
        
        challenge = Challenge.objects.create(
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            difficulty=difficulty,
            points=points_map.get(difficulty, 30)
        )
        messages.success(request, f'Challenge "{challenge.title}" added successfully!')
        return redirect('manage_challenges')
    return redirect('manage_challenges')


@admin_required
def delete_challenge(request, challenge_id):
    """Delete a challenge"""
    if request.method == "POST":
        challenge = Challenge.objects.get(id=challenge_id)
        title = challenge.title
        challenge.delete()
        messages.success(request, f'Challenge "{title}" deleted successfully!')
        return redirect('manage_challenges')
    return redirect('manage_challenges')


# ==================== API VIEWS ====================

@admin_required
def api_stats(request):
    """Return statistics for admin dashboard"""
    stats = {
        'courses': Course.objects.count(),
        'quizzes': Quiz.objects.count(),
        'users': User.objects.count(),
        'challenges': Challenge.objects.count(),
    }
    return JsonResponse(stats)


@admin_required
def api_courses(request):
    """Return list of courses for admin dashboard"""
    courses_data = []
    for course in Course.objects.all():
        courses_data.append({
            'id': course.id,
            'title': course.title,
            'level': course.level,
            'duration_hours': course.duration_hours,
        })
    return JsonResponse(courses_data, safe=False)


@admin_required
def api_quizzes(request):
    """Return list of quizzes for admin dashboard"""
    quizzes_data = []
    for quiz in Quiz.objects.all():
        quizzes_data.append({
            'id': quiz.id,
            'title': quiz.title,
            'questions': quiz.question_count,
            'points': quiz.points,
        })
    return JsonResponse(quizzes_data, safe=False)


@admin_required
def api_users(request):
    """Return list of users for admin dashboard"""
    users_data = []
    for user in User.objects.all().order_by('-date_joined')[:20]:
        users_data.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_staff': user.is_staff,
            'date_joined': user.date_joined.strftime('%Y-%m-%d'),
        })
    return JsonResponse(users_data, safe=False)


@admin_required
def api_challenges(request):
    """Return list of challenges for admin dashboard"""
    challenges_data = []
    for challenge in Challenge.objects.all():
        challenges_data.append({
            'id': challenge.id,
            'title': challenge.title,
            'difficulty': challenge.difficulty,
            'points': challenge.points,
        })
    return JsonResponse(challenges_data, safe=False)


@admin_required
def api_quiz_results(request):
    """Return quiz results for admin dashboard API"""
    attempts = QuizAttempt.objects.all().order_by('-attempted_at')[:10]
    results_data = []
    for attempt in attempts:
        results_data.append({
            'id': attempt.id,
            'username': attempt.user.username,
            'quiz_title': attempt.quiz.title,
            'score': attempt.score,
            'total': attempt.total_questions,
            'percentage': round(attempt.percentage, 1),
            'passed': attempt.passed,
            'points_earned': attempt.points_earned,
            'date': attempt.attempted_at.strftime('%Y-%m-%d %H:%M'),
        })
    return JsonResponse(results_data, safe=False)
@login_required(login_url='login')
def generate_certificate(request, enrollment_id):
    enrollment = get_object_or_404(Enrollment, id=enrollment_id, user=request.user)
    
    if not enrollment.is_completed:
        messages.error(request, 'You must complete the course before downloading the certificate.')
        return redirect('course_detail', course_id=enrollment.course.id)
    
    return render(request, 'accounts/certificate.html', {'enrollment': enrollment})


@login_required(login_url='login')
def mark_module_completed(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    enrollment = Enrollment.objects.filter(user=request.user, course=module.course).first()
    
    if not enrollment:
        messages.error(request, "You must be enrolled in this course.")
        return redirect('courses')
    
    # Create completion record
    ModuleCompletion.objects.get_or_create(user=request.user, module=module)
    
    # Update progress percentage
    total_modules = module.course.modules.count()
    completed_modules = ModuleCompletion.objects.filter(user=request.user, module__course=module.course).count()
    
    if total_modules > 0:
        enrollment.progress_percent = int((completed_modules / total_modules) * 100)
        # Check if this was the last module and there's no quiz
        if enrollment.progress_percent >= 100:
            # We still wait for quiz in most cases, but marking as progress 100 is key
            pass
        enrollment.save()
    
    messages.success(request, f"Module '{module.title}' marked as completed!")
    return redirect('course_detail', course_id=module.course.id)
