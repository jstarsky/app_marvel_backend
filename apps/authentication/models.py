from django.db import models
from django.contrib.auth.models import User  # Import Django's default User

# Comment out the entire custom User class to avoid conflicts
# class User(AbstractUser):
#     """
#     Custom User model extending AbstractUser
#     """
#     email = models.EmailField(blank=True, null=True)
#     username = models.CharField(max_length=150, unique=True)
#     is_active = models.BooleanField(default=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
# 
#     USERNAME_FIELD = 'username'
#     REQUIRED_FIELDS = []
# 
#     class Meta:
#         verbose_name = 'User'
#         verbose_name_plural = 'Users'
# 
#     def __str__(self):
#         return self.email or self.username
# 
#     def get_full_name(self):
#         return f"{self.first_name} {self.last_name}".strip()

class UserProfile(models.Model):
    """
    Extended user profile information
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.URLField(blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    birth_date = models.DateField(blank=True, null=True)
    
    class Meta:
        db_table = 'user_profile'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.username}'s profile"