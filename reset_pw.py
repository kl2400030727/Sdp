import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ps23_project.settings')
django.setup()

from django.contrib.auth.models import User

def reset_password(username, new_password):
    try:
        user = User.objects.get(username=username)
        user.set_password(new_password)
        user.save()
        print(f"Password reset for {username} to {new_password}")
    except User.DoesNotExist:
        print(f"User {username} does not exist")

if __name__ == "__main__":
    reset_password('2400033253', '12345678')
