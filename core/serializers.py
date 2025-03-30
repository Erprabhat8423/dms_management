from rest_framework import serializers
from .models import CustomUser, Profile, TempUser,TempParent, VehicleType, Parent_Profile, hash_otp,Children, College,CollegeTiming,DriverProfileMapping
from django.utils import timezone
import random
import re 


def generate_otp() -> str:
    """
    Returns a 6-digit numeric OTP code (as a string).
    """
    return str(random.randint(1000, 9999))


class RegistrationSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=200)
    dob = serializers.CharField(max_length=20)
    email = serializers.EmailField()
    phone_number = serializers.CharField(max_length=15)
    licence_no = serializers.CharField(max_length=20)
    licence_exp_date = serializers.DateField()
    vehicle_type = serializers.PrimaryKeyRelatedField(queryset=VehicleType.objects.all())
    vehicle_no = serializers.CharField(max_length=20)
    is_driver = serializers.BooleanField()
    is_student = serializers.BooleanField()
    college_name = serializers.CharField(max_length=100)
    start_shift = serializers.TimeField()
    end_shift = serializers.TimeField()

    def validate_phone_number(self, value):
        """
        Check if a real user already exists with this phone number.
        """
        if CustomUser.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("A user with this phone number already exists.")
        return value

    def create(self, validated_data):
        """
        Create a TempUser and generate OTP.
        """
        phone_number = validated_data['phone_number']
        self.validate_phone_number(phone_number)
        TempUser.objects.filter(phone_number=phone_number).delete()

        # Generate OTP and hash it
        otp_code = generate_otp()
        hashed_otp = hash_otp(otp_code)

        # Create TempUser
        temp_user = TempUser.objects.create(
            **validated_data,
            otp_hash=hashed_otp,
            otp_created_at=timezone.now(),
        )

        return temp_user, otp_code


class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    otp_code = serializers.CharField()

    def validate_otp_code(self, value):
        """
        Validate the OTP format.
        """
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain digits only.")
        return value

#====================== User Serializer =======================

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = '__all__'



class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile details.
    """
    vehicle_type = serializers.PrimaryKeyRelatedField(queryset=VehicleType.objects.all())

    class Meta:
        model = Profile
        fields = [
            'full_name',
            'profile_pic',
            'dob',
            'email',
            'licence_no',
            'licence_exp_date',
            'vehicle_type',
            'vehicle_no',
        ]


#===================Parent Profile serializer=======================
class ParentProfileSerializer(serializers.ModelSerializer):
     class Meta:
        model = Parent_Profile
        fields = '__all__'





class GetCustomUserSerializer(serializers.ModelSerializer):
    """
    Serializer for CustomUser data including profile details.
    """
    profile = ProfileSerializer()
    #parent = ParentProfileSerializer() 

    class Meta:
        model = CustomUser
        fields = [
            'phone_number',
            'is_driver',
            'is_student',
            'is_active',
            'is_staff',
            'date_joined',
            'profile',
        ]

class ParentRegistrationSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=200)
    dob = serializers.CharField(max_length=20)
    email = serializers.EmailField()
    phone_number = serializers.CharField(max_length=15)
   
    is_student = serializers.BooleanField()
    profile_pic = serializers.ImageField(required=False, allow_null=True)  # Add this field

   

    def validate_phone_number(self, value):
        """
        Check if a real Parent already exists with this phone number.
        """
        if not re.fullmatch(r"\d{10}", value): 
            raise serializers.ValidationError("Phone number must be exactly 10 digits.")
        if CustomUser.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("A Parent with this phone number already exists.")
        return value

    def create(self, validated_data):
        """
        Create a TempUser and generate OTP.
        """
        phone_number = validated_data['phone_number']
        self.validate_phone_number(phone_number)
        TempParent.objects.filter(phone_number=phone_number).delete()

        # Generate OTP and hash it
        otp_code = generate_otp()
        hashed_otp = hash_otp(otp_code)

        profile_pic = validated_data.pop('profile_pic', None)

        # Create TempUser
        temp_parent = TempParent.objects.create(
            **validated_data,
            otp_hash=hashed_otp,
            otp_created_at=timezone.now(),
        )

        

        # ✅ Create Parent Profile
        # parent_profile = Parent_Profile.objects.create(
        #     #user=user,
        #     full_name=validated_data["full_name"],
        #     dob=validated_data.get("dob", ""),
        #     email=validated_data.get("email", ""),
        #     profile_pic=profile_pic
        # )
        
        return temp_parent, otp_code





#===========================Create children serializer======================
class CollegeSerializer(serializers.ModelSerializer):
    class Meta:
        model = College
        fields = '__all__'

class CollegeTimingSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollegeTiming
        fields = '__all__'



class ChildrenSerializer(serializers.ModelSerializer):
    

    class Meta:
        model = Children
        fields = '__all__'

    def validate_contact_person_number(self, value):
        """Ensure contact_person_number is exactly 10 digits"""
        if not re.fullmatch(r"\d{10}", value):
            raise serializers.ValidationError("Contact person number must be exactly 10 digits.")
        return value

    def validate_alternate_number(self, value):
        """Ensure alternate_number is exactly 10 digits"""
        if not re.fullmatch(r"\d{10}", value):
            raise serializers.ValidationError("Alternate number must be exactly 10 digits.")
        return value
    

class ChildrenListSerializer(serializers.ModelSerializer):
    college = CollegeSerializer()  # Include College details
    collegetiming = CollegeTimingSerializer()  # Include CollegeTiming details
    parent = CustomUserSerializer() 
    parent_profile = ParentProfileSerializer(source='parent.parent_profile', read_only=True)  # Fix here

    class Meta:
        model = Children
        fields = '__all__'

#========================= Driver Profile Serializer=====================

# class ProfileListSerializer(serializers.ModelSerializer):
#     college = CollegeSerializer()  # Include College details
#     collegetiming = CollegeTimingSerializer()  # Include CollegeTiming details
#     driver = CustomUserSerializer() 

#     class Meta:
#         model = Profile
#         fields = '__all__'

class ProfileListSerializer(serializers.ModelSerializer):
    college = serializers.SerializerMethodField()
    collegetiming = serializers.SerializerMethodField()
    user = CustomUserSerializer()  # Change 'driver' to 'user'

    class Meta:
        model = Profile
        fields = '__all__'

    def get_college(self, obj):
        try:
            mapping = DriverProfileMapping.objects.get(driver=obj)
            return CollegeSerializer(mapping.college).data
        except DriverProfileMapping.DoesNotExist:
            return None

    def get_collegetiming(self, obj):
        try:
            mapping = DriverProfileMapping.objects.get(driver=obj)
            return CollegeTimingSerializer(mapping.timing).data
        except DriverProfileMapping.DoesNotExist:
            return None

class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['full_name', 'profile_pic', 'dob', 'email', 'licence_no', 'licence_exp_date', 'vehicle_type', 'vehicle_no']


# ====================Serializer for DriverProfileMapping ============================
class DriverProfileMappingSerializer(serializers.ModelSerializer):
    college_name = serializers.CharField(source='college.college_name', read_only=True)
    start_shift = serializers.TimeField(source='timing.start_shift', read_only=True)
    end_shift = serializers.TimeField(source='timing.end_shift', read_only=True)

    class Meta:
        model = DriverProfileMapping
        fields = ['id', 'college', 'college_name', 'timing', 'start_shift', 'end_shift']
