import random
import hashlib
import logging
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from core.models import TempUser, CustomUser, Profile, hash_otp,College,CollegeTiming,DriverProfileMapping
from core.serializers import RegistrationSerializer, VerifyOTPSerializer, GetCustomUserSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
from core.utils import save_driver_profile_mapping

# Set up logging
logger = logging.getLogger(__name__)

class RegisterView(generics.GenericAPIView):
    """
    Step 1: 
      - Accept registration data (phone_number, full_name, etc.).
      - Create TempUser with hashed OTP.
      - (Production: send OTP to phone).
    """
    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Handle registration step 1, where the OTP is generated and sent to the user's phone.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create TempUser using validated data and OTP
        temp_user, otp_code = serializer.save()

        # Simulate sending OTP via SMS (e.g., Twilio)
        logger.info(f"OTP for {temp_user.phone_number} is {otp_code}")  # Log for debugging (don't return OTP in production)
        
        return Response(
            {
                "message": "Registration step 1 complete. OTP sent (demo).",
                "phone_number": str(temp_user.phone_number),
                "otp_code": otp_code  # DO NOT return this in production
            },
            status=status.HTTP_200_OK
        )



class RegisterVerifyView(generics.GenericAPIView):
    """
    Step 2:
      - Verify phone_number & otp_code.
      - If correct and not expired, create real user & profile, delete TempUser.
      - Map the driver to a college and timing.
    """
    serializer_class = VerifyOTPSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data['phone_number']
        otp_code = serializer.validated_data['otp_code']
        hashed_input_otp = hash_otp(otp_code)

        try:
            temp_user = TempUser.objects.get(phone_number=phone_number)
        except TempUser.DoesNotExist:
            return Response(
                {"detail": "No pending registration found for this phone number."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check max attempts
        if temp_user.attempt_count >= temp_user.max_attempts:
            temp_user.delete()
            return Response(
                {"detail": "Maximum OTP attempts exceeded. Please register again."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if OTP is expired
        if (timezone.now() - temp_user.otp_created_at).total_seconds() > 300:  # 5 minutes
            temp_user.delete()
            return Response(
                {"detail": "OTP expired. Please register again."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Compare hashed OTP
        if temp_user.otp_hash != hashed_input_otp:
            temp_user.attempt_count += 1
            temp_user.save()
            return Response(
                {"detail": f"Invalid OTP. Attempts left: {temp_user.max_attempts - temp_user.attempt_count}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # OTP is correct -> Create real user
        user = CustomUser.objects.create_user(
            phone_number=temp_user.phone_number,
            is_driver=temp_user.is_driver,
            is_student=temp_user.is_student,
        )
        profile = Profile.objects.create(
            user=user,
            full_name=temp_user.full_name,
            dob=temp_user.dob,
            email=temp_user.email,
            licence_no=temp_user.licence_no,
            licence_exp_date=temp_user.licence_exp_date,
            vehicle_type=temp_user.vehicle_type,
            vehicle_no=temp_user.vehicle_no,
        )

        # Map the driver to the college and shift
        if temp_user.is_driver:
            mapping_result = save_driver_profile_mapping(
                profile,
                temp_user.college_name,
                temp_user.start_shift,
                temp_user.end_shift
            )
            if 'error' in mapping_result:
                return Response(
                    {"detail": mapping_result['error']},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        # Clean up the TempUser
        temp_user.delete()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        user_data = GetCustomUserSerializer(user).data

        return Response({
            "user": user_data,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "message": "Registration successful"
        }, status=status.HTTP_201_CREATED)



class SendOTPView(generics.GenericAPIView):
    """
    Generate and send OTP via phone number for login.
    """
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        phone_number = request.data.get("phone_number")
        
        # Validate phone number
        if not phone_number:
            return Response({"detail": "Phone number is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if the user exists
        try:
            user = CustomUser.objects.get(phone_number=phone_number)
        except CustomUser.DoesNotExist:
            return Response({"detail": "User not found with this phone number."}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user is active and the correct type
        if not user.is_active:
            return Response({"detail": "User is not active."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not user.is_driver or user.is_student:
            return Response({"detail": "Invalid user type."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate OTP
        otp_code = str(random.randint(1000, 9999))
        hashed_otp = hashlib.sha256(otp_code.encode()).hexdigest()
        
        # Save OTP hash temporarily (you can store it in a user-specific field if needed)
        user.otp_hash = hashed_otp
        user.otp_created_at = timezone.now()
        user.save()
        
        # Log OTP (In production, DO NOT log OTP, this is for debugging only)
        logger.info(f"OTP for {phone_number} is {otp_code}")  # Log for debugging (don't return OTP in production)
        
        return Response(
            {
                "message": "OTP sent successfully.",
                "phone_number": phone_number,
                "otp_code": otp_code
            },
            status=status.HTTP_200_OK
        )


class LoginView(generics.GenericAPIView):
    """
    Login using phone number and OTP.
    """
    serializer_class = VerifyOTPSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """
        1. Accept phone number and OTP.
        2. Verify OTP for the user.
        3. If correct, return access and refresh tokens for the user.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data['phone_number']
        otp_code = serializer.validated_data['otp_code']
        hashed_input_otp = hashlib.sha256(otp_code.encode()).hexdigest()

        # Check if the user exists
        try:
            user = CustomUser.objects.get(phone_number=phone_number)
        except CustomUser.DoesNotExist:
            return Response(
                {"detail": "User not found with this phone number."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if the user is active
        if not user.is_active:
            return Response({"detail": "User is not active."}, status=status.HTTP_400_BAD_REQUEST)

        # Compare OTP hash
        if user.otp_hash != hashed_input_otp:
            return Response(
                {"detail": "Invalid OTP."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if OTP is expired (e.g., 5 minutes)
        if (timezone.now() - user.otp_created_at).total_seconds() > 300:  # 5 minutes
            return Response(
                {"detail": "OTP expired. Please request a new OTP."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # OTP is correct, generate JWT tokens for the user
        refresh = RefreshToken.for_user(user)
        user_data = GetCustomUserSerializer(user).data

        # Clean up OTP fields after successful login (optional, for security reasons)
        user.otp_hash = None
        user.otp_created_at = None
        user.save()

        # Return JWT tokens and user data
        return Response({
            "user": user_data,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "message": "Login successful"
        }, status=status.HTTP_200_OK)
