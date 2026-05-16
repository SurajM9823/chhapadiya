"""
Quick fix script to remove superuser status from staff users
Run this in Django shell: python manage.py shell < fix_user.py
"""

from web.models import CustomerUser

# Fix the finaa user
try:
    user = CustomerUser.objects.get(username='finaa')
    print(f"Found user: {user.username}")
    print(f"  Current - is_superuser: {user.is_superuser}, is_staff: {user.is_staff}, role: {user.role}")
    
    # Keep staff but remove superuser
    user.is_superuser = False
    user.is_staff = True
    user.save()
    
    print(f"  Updated - is_superuser: {user.is_superuser}, is_staff: {user.is_staff}, role: {user.role}")
    print("✓ User fixed successfully!")
except CustomerUser.DoesNotExist:
    print("User 'finaa' not found")
except Exception as e:
    print(f"Error: {e}")
