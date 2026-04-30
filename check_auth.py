import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ps23_project.settings')
django.setup()

from django.contrib.auth import authenticate
from django.contrib.auth.models import User

def check_login(username, password):
    print(f"Checking credentials for: {username}")
    user = authenticate(username=username, password=password)
    if user:
        print(f"SUCCESS: Authenticated as {user.username}")
    else:
        print(f"FAILURE: Could not authenticate {username}")
        # Check if user exists
        try:
            u = User.objects.get(username=username)
            print(f"User exists: {u.username}")
            print(f"Is active: {u.is_active}")
            print(f"Is staff: {u.is_staff}")
            print(f"Is superuser: {u.is_superuser}")
        except User.DoesNotExist:
            print(f"User {username} DOES NOT EXIST in database.")

if __name__ == "__main__":
    check_login('superadmin', 'admin123')
    print("-" * 20)
    check_login('2400033253', '12345678')
