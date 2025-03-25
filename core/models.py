from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
import hashlib
from django.core.validators import RegexValidator
alphanumeric = RegexValidator(r'^[0-9a-zA-Z]*$', 'Only alphanumeric characters are allowed.')


# Utility function to hash OTP
def hash_otp(otp):
    return hashlib.sha256(otp.encode()).hexdigest()

# Custom User Manager
class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, **extra_fields):
        if not phone_number:
            raise ValueError("The phone number must be set")
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(extra_fields.get('password', None))
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if not extra_fields.get('is_staff') or not extra_fields.get('is_superuser'):
            raise ValueError("Superuser must have is_staff=True and is_superuser=True.")
        return self.create_user(phone_number, **extra_fields)

# Vehicle Type Model
class VehicleType(models.Model):

    vehicle_name = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.vehicle_name

    class Meta:
        ordering = ['vehicle_name']
        verbose_name = 'Vehicle Type'
        verbose_name_plural = 'Vehicle Types'

# Temporary User Model
class TempUser(models.Model):

    full_name = models.CharField(max_length=200)
    dob = models.CharField(max_length=20)
    email = models.CharField(max_length=254)
    phone_number = models.CharField(max_length=15, unique=True)
    licence_no = models.CharField(max_length=20)
    licence_exp_date = models.DateField()
    vehicle_type = models.ForeignKey(VehicleType, on_delete=models.CASCADE)
    vehicle_no = models.CharField(max_length=20)
    is_driver = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)
    otp_hash = models.CharField(max_length=64, null=True, blank=True)
    otp_created_at = models.DateTimeField(default=timezone.now,null=True, blank=True)
    is_active = models.BooleanField(default=True)
    college_name = models.CharField(max_length=100)
    start_shift = models.TimeField()
    end_shift = models.TimeField()
    max_attempts = models.PositiveIntegerField(default=5)
    attempt_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} ({self.phone_number})"

# Custom User Model
class CustomUser(AbstractBaseUser, PermissionsMixin):
    phone_number = models.CharField(max_length=15, unique=True, db_index=True)
    otp_hash = models.CharField(max_length=64, null=True, blank=True)
    otp_created_at = models.DateTimeField(default=timezone.now,null=True, blank=True)
    is_driver = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    objects = CustomUserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    def __str__(self):
        return str(self.phone_number)

    class Meta:
        ordering = ['-date_joined']
        verbose_name = 'Custom User'
        verbose_name_plural = 'Custom Users'

# ================================Driver Profile Model
class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=200)
    profile_pic = models.ImageField(null=True, blank=True)
    dob = models.CharField(max_length=20)
    email = models.CharField(max_length=254, null=True, blank=True)
    licence_no = models.CharField(max_length=20, null=True, blank=True)
    licence_exp_date = models.DateField(null=True, blank=True)
    vehicle_type = models.ForeignKey(VehicleType, on_delete=models.CASCADE, null=True, blank=True)
    vehicle_no = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return f"Profile of {self.user.phone_number}"

# College Model
class College(models.Model):
    college_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.college_name

    class Meta:
        ordering = ['college_name']
        verbose_name = 'College'
        verbose_name_plural = 'Colleges'

# =========================== College Timing Model ======================
class CollegeTiming(models.Model):
    start_shift = models.TimeField()
    end_shift = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Timing: {self.start_shift} - {self.end_shift}"

# ===============================  Driver Profile Mapping Model =======================
class DriverProfileMapping(models.Model):
    driver = models.OneToOneField(Profile, on_delete=models.CASCADE)
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    timing = models.ForeignKey(CollegeTiming, on_delete=models.CASCADE)

    def __str__(self):
        return f"Driver {self.driver.full_name} at {self.college.college_name}"

#========================  Parent Profile Model ============================
class Parent_Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='parent_profile')
    full_name = models.CharField(max_length=200)
    profile_pic = models.ImageField(null=True, blank=True)
    dob = models.CharField(max_length=20, null=True, blank=True)
    email = models.CharField(max_length=254, null=True, blank=True)
   
    def __str__(self):
        return f"parent of student:  {self.full_name}"

# =========================== Temporary Parent Model =============================
class TempParent(models.Model):

    full_name = models.CharField(max_length=200)
    dob = models.CharField(max_length=20)
    email = models.CharField(max_length=254)
    phone_number = models.CharField(max_length=15, unique=True)
    
    is_student = models.BooleanField(default=False)
    otp_hash = models.CharField(max_length=64, null=True, blank=True)
    otp_created_at = models.DateTimeField(default=timezone.now,null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    max_attempts = models.PositiveIntegerField(default=5)
    attempt_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} ({self.phone_number})"


# ======================= Chidren Profile Model ============================
class Children(models.Model):
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name='child')
    collegetiming = models.ForeignKey(CollegeTiming, on_delete=models.CASCADE, related_name='child_timing')
    parent = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='children')
    

    full_name = models.CharField(max_length=200)
    dob = models.DateField()  # Changed from CharField to DateField
    age = models.IntegerField()
    children_class = models.CharField(max_length=50, blank=True, null=True, validators=[alphanumeric])

    contact_person_name = models.CharField(max_length=200)
    contact_person_number = models.CharField(max_length=15)
    alternate_number = models.CharField(max_length=15, blank=True, null=True)  # Made optional

    def __str__(self):
        return f"Children of {self.parent}"
