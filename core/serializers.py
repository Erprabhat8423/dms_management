from rest_framework import serializers
from .models import CustomUser, Profile, TempUser, VehicleType, hash_otp
from django.utils import timezone
import random


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


class GetCustomUserSerializer(serializers.ModelSerializer):
    """
    Serializer for CustomUser data including profile details.
    """
    profile = ProfileSerializer()

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
