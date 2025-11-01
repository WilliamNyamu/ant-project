from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager

# Create your models here.

class CustomUserManager(UserManager):
    """
    Overriding the default usermanager and use email as the primary identifier
    """
    def create_user(self, email, password = None, **extra_fields):
        if not email:
            raise ValueError("Email cannot be empty")
        email = self.normalize_email(email) # standardize the email by lowering the domain name case
        # create a user model. Self.model representes the custom user model that this manager is attached to
        user = self.model(email=email, **extra_fields) # ensure you specify that email=email
        user.set_password(password) # A security check for hashing passwords
        # save the user object in the db
        user.save(using=self.db)
        return user
    

    def create_superuser(self, email, password, **extra_fields):

        # Stamp the authentication codes into the user file
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        # Verification checks
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff set to True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser set to True')
        
        # Employ the DRY Principle and reuse the create_user
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    Creating a customuser that uses the previously defined the CustomUserManager
    """
    email = models.EmailField(unique=True)
    username = models.CharField(unique=True, blank=True, null=True, max_length=150)
    profile_picture = models.ImageField(upload_to='profile_picture', null=True, blank=True)

    objects = CustomUserManager()

    # tells django to use the email field as the primary authentication field by overriding the default username field
    USERNAME_FIELD = 'email'
    
    # Tells the superuser to prompt for the username as well as the email
    REQUIRED_FIELDS = ['username']