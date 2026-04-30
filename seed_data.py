import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ps23_project.settings')
django.setup()

import requests
from django.contrib.auth.models import User
from accounts.models import Course, Quiz, Challenge, QuizQuestion, Profile, Module, EcoImpact

YOUTUBE_API_KEY = 'AIzaSyDOeUStZ64BTlAXhiwPzZJHXRQ7cXxOy4g'


def fetch_youtube_videos(query, max_results=3):
    """Fetch real YouTube video IDs using the YouTube Data API v3."""
    url = 'https://www.googleapis.com/youtube/v3/search'
    params = {
        'part': 'snippet',
        'q': query,
        'type': 'video',
        'maxResults': max_results,
        'key': YOUTUBE_API_KEY,
        'videoEmbeddable': 'true',
        'relevanceLanguage': 'en',
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()
        results = []
        for item in data.get('items', []):
            vid = item['id']['videoId']
            title = item['snippet']['title']
            desc = item['snippet']['description'][:200]
            results.append({
                'video_id': vid,
                'title': title,
                'description': desc,
                'embed_url': f'https://www.youtube.com/embed/{vid}',
            })
        return results
    except Exception as e:
        print(f"  [WARN] YouTube API error: {e}")
        return []


def seed_data():
    print("=" * 60)
    print("  Sustainable Living Platform – Full Data Seeder")
    print("=" * 60)

    # ──────────────────────────────────────────────────────────
    # 1. COURSES + MODULES (with YouTube videos)
    # ──────────────────────────────────────────────────────────
    courses_config = [
        {
            'title': 'Solar Energy Basics',
            'category': 'ENERGY',
            'description': 'Learn how solar panels work and how to implement solar energy in your home. Covers photovoltaics, inverters, and net metering.',
            'level': 'beginner',
            'duration_hours': 4,
            'points': 150,
            'icon': 'fas fa-solar-panel',
            'module_queries': [
                'solar energy basics for beginners',
                'how solar panels work explained',
                'home solar panel installation guide',
            ],
        },
        {
            'title': 'Zero Waste Living',
            'category': 'WASTE',
            'description': 'Master the 5 Rs: Refuse, Reduce, Reuse, Repurpose, Recycle. Practical daily steps to a zero-waste lifestyle.',
            'level': 'beginner',
            'duration_hours': 3,
            'points': 100,
            'icon': 'fas fa-recycle',
            'module_queries': [
                'zero waste lifestyle tips beginners',
                'kitchen composting tutorial',
                'reduce plastic waste at home',
            ],
        },
        {
            'title': 'Water Conservation',
            'category': 'WATER',
            'description': 'Strategies for reducing water waste in gardening, cooking, and daily hygiene. Learn about rainwater harvesting and greywater systems.',
            'level': 'intermediate',
            'duration_hours': 2,
            'points': 120,
            'icon': 'fas fa-water',
            'module_queries': [
                'water conservation methods at home',
                'rainwater harvesting system DIY',
                'greywater recycling explained',
            ],
        },
        {
            'title': 'Sustainable Food & Diet',
            'category': 'FOOD',
            'description': 'Understand the environmental impact of food choices. Explore plant-based eating, local sourcing, and reducing food waste.',
            'level': 'beginner',
            'duration_hours': 3,
            'points': 150,
            'icon': 'fas fa-apple-alt',
            'module_queries': [
                'sustainable food choices environment',
                'plant based diet benefits environment',
                'how to reduce food waste at home',
            ],
        },
    ]

    for cdata in courses_config:
        queries = cdata.pop('module_queries')
        course, created = Course.objects.get_or_create(
            title=cdata['title'],
            defaults=cdata,
        )
        status = "CREATED" if created else "EXISTS"
        print(f"\n📚 Course: {course.title} [{status}]")

        # Fetch YouTube videos for each module query
        for idx, query in enumerate(queries, start=1):
            # Check if module already exists
            existing = Module.objects.filter(course=course, order=idx).first()
            if existing and existing.video_url:
                print(f"   ✅ Module {idx}: {existing.title} (already has video)")
                continue

            print(f"   🔍 Searching YouTube: '{query}' ...")
            videos = fetch_youtube_videos(query, max_results=1)

            if videos:
                v = videos[0]
                mod, m_created = Module.objects.update_or_create(
                    course=course,
                    order=idx,
                    defaults={
                        'title': v['title'][:200],
                        'description': v['description'],
                        'video_url': v['embed_url'],
                    }
                )
                act = "CREATED" if m_created else "UPDATED"
                print(f"   🎬 Module {idx} [{act}]: {v['title'][:60]}...")
            else:
                # Fallback: create module without video
                Module.objects.get_or_create(
                    course=course,
                    order=idx,
                    defaults={
                        'title': query.replace('_', ' ').title(),
                        'description': f'Learn about {query}',
                    }
                )
                print(f"   ⚠️  Module {idx}: Created without video (API unavailable)")

    # ──────────────────────────────────────────────────────────
    # 2. QUIZZES + QUESTIONS
    # ──────────────────────────────────────────────────────────
    print("\n" + "─" * 60)
    print("📝 Seeding Quizzes...")

    quizzes_config = [
        {
            'title': 'Sustainability Basics',
            'description': 'Test your knowledge on general environmental sustainability.',
            'difficulty': 'easy',
            'points': 50,
            'question_count': 5,
            'questions': [
                {'question_text': 'Which of these is a renewable energy source?', 'option_a': 'Coal', 'option_b': 'Natural Gas', 'option_c': 'Solar', 'option_d': 'Nuclear', 'correct_answer': 'C'},
                {'question_text': 'What percentage of Earth\'s water is freshwater?', 'option_a': '97%', 'option_b': '50%', 'option_c': '3%', 'option_d': '25%', 'correct_answer': 'C'},
                {'question_text': 'Which gas is the main contributor to global warming?', 'option_a': 'Oxygen', 'option_b': 'Carbon Dioxide', 'option_c': 'Nitrogen', 'option_d': 'Hydrogen', 'correct_answer': 'B'},
                {'question_text': 'What does the term "carbon footprint" refer to?', 'option_a': 'A type of shoe', 'option_b': 'Total greenhouse gas emissions', 'option_c': 'A hiking trail', 'option_d': 'Carbon dating', 'correct_answer': 'B'},
                {'question_text': 'Which of the 5 Rs comes first?', 'option_a': 'Recycle', 'option_b': 'Reduce', 'option_c': 'Refuse', 'option_d': 'Reuse', 'correct_answer': 'C'},
            ]
        },
        {
            'title': 'Energy Efficiency',
            'description': 'How well do you know home energy saving techniques?',
            'difficulty': 'medium',
            'points': 100,
            'question_count': 5,
            'questions': [
                {'question_text': 'LED bulbs use how much less energy than incandescent?', 'option_a': '25%', 'option_b': '50%', 'option_c': '75%', 'option_d': '90%', 'correct_answer': 'C'},
                {'question_text': 'Which appliance uses the most electricity at home?', 'option_a': 'Refrigerator', 'option_b': 'Air Conditioner', 'option_c': 'Television', 'option_d': 'Washing Machine', 'correct_answer': 'B'},
                {'question_text': 'What is a "phantom load"?', 'option_a': 'A ghost story', 'option_b': 'Energy used by devices on standby', 'option_c': 'A power outage', 'option_d': 'Solar panel output', 'correct_answer': 'B'},
                {'question_text': 'Double-glazed windows help save energy by...', 'option_a': 'Blocking sunlight', 'option_b': 'Reducing noise', 'option_c': 'Insulating against heat loss', 'option_d': 'Generating power', 'correct_answer': 'C'},
                {'question_text': 'What is the ideal thermostat setting to save energy?', 'option_a': '15°C', 'option_b': '20°C', 'option_c': '25°C', 'option_d': '30°C', 'correct_answer': 'B'},
            ]
        },
        {
            'title': 'Water Conservation Quiz',
            'description': 'Test your knowledge about saving water resources.',
            'difficulty': 'easy',
            'points': 75,
            'question_count': 5,
            'questions': [
                {'question_text': 'A leaking tap can waste how many liters per day?', 'option_a': '5', 'option_b': '20', 'option_c': '75', 'option_d': '200', 'correct_answer': 'C'},
                {'question_text': 'Which uses less water: shower or bath?', 'option_a': 'Shower', 'option_b': 'Bath', 'option_c': 'Same', 'option_d': 'Depends on duration', 'correct_answer': 'D'},
                {'question_text': 'What is greywater?', 'option_a': 'Polluted river water', 'option_b': 'Wastewater from sinks and showers', 'option_c': 'Rainwater', 'option_d': 'Distilled water', 'correct_answer': 'B'},
                {'question_text': 'Drip irrigation saves water compared to flood irrigation by...', 'option_a': '10%', 'option_b': '30%', 'option_c': '60%', 'option_d': '90%', 'correct_answer': 'C'},
                {'question_text': 'Which crop requires the most water to produce 1 kg?', 'option_a': 'Rice', 'option_b': 'Wheat', 'option_c': 'Beef', 'option_d': 'Potatoes', 'correct_answer': 'C'},
            ]
        },
    ]

    for qdata in quizzes_config:
        questions = qdata.pop('questions')
        quiz, created = Quiz.objects.get_or_create(title=qdata['title'], defaults=qdata)
        print(f"   {'✅ Created' if created else '📌 Exists'}: {quiz.title}")
        if created:
            for q in questions:
                QuizQuestion.objects.create(quiz=quiz, **q)
            print(f"      + Added {len(questions)} questions")

    # ──────────────────────────────────────────────────────────
    # 3. CHALLENGES
    # ──────────────────────────────────────────────────────────
    print("\n" + "─" * 60)
    print("🏆 Seeding Challenges...")

    challenges_data = [
        {'title': 'No Plastic Day', 'description': 'Avoid all single-use plastics for 24 hours. Carry your own bag and bottle!', 'difficulty': 'easy', 'points': 30},
        {'title': 'Meat-Free Monday', 'description': 'Eat only plant-based meals for a full day to reduce your carbon footprint.', 'difficulty': 'medium', 'points': 50},
        {'title': 'Use Public Transport', 'description': 'Take the bus, metro, or train instead of a private vehicle today.', 'difficulty': 'easy', 'points': 25},
        {'title': 'Plant a Sapling', 'description': 'Plant a tree or sapling in your garden or community space.', 'difficulty': 'medium', 'points': 75},
        {'title': 'Zero Waste Week', 'description': 'Produce no landfill waste for 7 consecutive days.', 'difficulty': 'hard', 'points': 100},
        {'title': '5-Minute Shower', 'description': 'Reduce your shower time to 5 minutes or less to conserve water.', 'difficulty': 'easy', 'points': 20},
    ]

    for data in challenges_data:
        ch, created = Challenge.objects.get_or_create(title=data['title'], defaults=data)
        print(f"   {'✅ Created' if created else '📌 Exists'}: {ch.title}")

    # ──────────────────────────────────────────────────────────
    # 4. ENSURE PROFILES & ECO-IMPACT EXIST
    # ──────────────────────────────────────────────────────────
    print("\n" + "─" * 60)
    print("👤 Ensuring profiles exist...")
    for user in User.objects.all():
        Profile.objects.get_or_create(user=user)
        EcoImpact.objects.get_or_create(user=user)
        print(f"   ✅ {user.username}")

    print("\n" + "=" * 60)
    print("  ✅ ALL SEEDING COMPLETED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    seed_data()
