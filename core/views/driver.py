import random
import hashlib
import logging
from django.utils import timezone
from rest_framework import status, generics,mixins
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from core.models import (
    TempUser,
    CustomUser,
    Profile,
    hash_otp,
    College,
    CollegeTiming,
    DriverProfileMapping,
    VehicleType
)
from core.serializers import (
    RegistrationSerializer,
    VerifyOTPSerializer,
    GetCustomUserSerializer,
    ProfileListSerializer,
    ProfileUpdateSerializer,
    DriverProfileMappingSerializer,
    CollegeSerializer,
    VehicleTypeSerializer
)
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
from core.utils import save_driver_profile_mapping
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import NotFound

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
                {"detail": "No pending registration found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check max attempts
        if temp_user.attempt_count >= temp_user.max_attempts:
            temp_user.delete()
            return Response(
                {"detail": "Maximum OTP attempts exceeded."},
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
        4. If the user is a driver, fetch driver mapping details, college, shift, and vehicle type.
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

        # Fetch driver mapping details if the user is a driver
        driver_data = None
        if user.is_driver:
            try:
                profile = user.profile
                driver_mappings = DriverProfileMapping.objects.filter(driver=profile)
                
                # Prepare mappings data
                mappings_data = []
                for mapping in driver_mappings:
                    mappings_data.append({
                        "id": mapping.id,
                        "college": mapping.college.college_name,
                        "shift": {
                            "start": mapping.timing.start_shift,
                            "end": mapping.timing.end_shift
                        }
                    })
                
                driver_data = {
                    "id": user.id,
                    "phone_number": user.phone_number,
                    "full_name": profile.full_name,
                    "profile_pic": profile.profile_pic.url if profile.profile_pic else None,
                    "dob": profile.dob,
                    "email": profile.email,
                    "licence_no": profile.licence_no,
                    "licence_exp_date": profile.licence_exp_date,
                    "vehicle_type": profile.vehicle_type.vehicle_name if profile.vehicle_type else None,
                    "vehicle_no": profile.vehicle_no,
                    "mappings": mappings_data  # List of all college-shift mappings
                }
            except Profile.DoesNotExist:
                driver_data = None

        # Clean up OTP fields after successful login (optional, for security reasons)
        user.otp_hash = None
        user.otp_created_at = None
        user.save()

        # Return JWT tokens and user data
        return Response({
            "user": user_data,
            "driver_info": driver_data,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "message": "Login successful"
        }, status=status.HTTP_200_OK)


# ======================== API View for  getting  Driver Profile
class DriverProfileDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileListSerializer

    def get_object(self):
        driver_id = self.kwargs['driver_id']
        try:
            return Profile.objects.get(user_id=driver_id)
        except Profile.DoesNotExist:
            raise NotFound({"message": "No profile found for the given driver ID."})


class DriverProfileUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileUpdateSerializer
    parser_classes = [MultiPartParser, FormParser]
    queryset = Profile.objects.all()

    def get_object(self):
        """
        Retrieve the Profile object based on driver_id from URL parameters.
        Ensure the authenticated user can only update their own profile.
        """
        driver_id = self.kwargs.get('driver_id')
        try:
            # Get the CustomUser by ID
            driver_user = get_object_or_404(CustomUser, id=driver_id)
            
            # Check if the authenticated user is the same as the driver being updated
            if self.request.user != driver_user:
                return Response(
                    {"detail": "You can only update your own profile."}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get the profile associated with the driver
            profile = get_object_or_404(Profile, user=driver_user)
            return profile
            
        except CustomUser.DoesNotExist:
            return Response(
                {"detail": "Driver not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Profile.DoesNotExist:
            return Response(
                {"detail": "Driver profile not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if isinstance(instance, Response):
            return instance

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#=======================edit college===========================


# API for updating or deleting a driver's college and shift mapping
class DriverProfileMappingUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """
    API for updating or deleting a driver's college and shift mapping.
    """
    serializer_class = DriverProfileMappingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Ensure that the logged-in user is a driver and retrieve their mapping.
        """
        return DriverProfileMapping.objects.filter(driver__user=self.request.user)

    def update(self, request, *args, **kwargs):
        """
        Update the college and shift timing for a driver.
        """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({"message": "Driver mapping updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)
        except DriverProfileMapping.DoesNotExist:
            return Response({"detail": "Mapping not found."}, status=status.HTTP_404_NOT_FOUND)

    def destroy(self, request, *args, **kwargs):
        """
        Delete the driver's college and shift mapping.
        """
        try:
            instance = self.get_object()
            instance.delete()
            return Response({"message": "Driver mapping deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except DriverProfileMapping.DoesNotExist:
            return Response({"detail": "Mapping not found."}, status=status.HTTP_404_NOT_FOUND)


# ======================== API for College List

class CollegeListAPIView(generics.ListAPIView):
    serializer_class = CollegeSerializer

    def get_queryset(self):
        queryset = College.objects.all()
        college_name = self.request.query_params.get('college_name')
        is_active = self.request.query_params.get('is_active')

        if college_name:
            queryset = queryset.filter(college_name__icontains=college_name)

        if is_active is not None:
            is_active = is_active.lower() in ['true', '1']
            queryset = queryset.filter(is_active=is_active)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "message": "College list fetched successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class VehicleTypeListAPIView(generics.ListAPIView):
    serializer_class = VehicleTypeSerializer

    def get_queryset(self):
        queryset = VehicleType.objects.all()
        vehicle_name = self.request.query_params.get('vehicle_name')
        is_active = self.request.query_params.get('is_active')

        if vehicle_name:
            queryset = queryset.filter(vehicle_name__icontains=vehicle_name)

        if is_active is not None:
            is_active = is_active.lower() in ['true', '1']
            queryset = queryset.filter(is_active=is_active)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "message": "Vehicle type list fetched successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

#=======================Create College Time Mapping===========================

class CollegeMappingCreateView(generics.CreateAPIView):
    """
    API for creating a new driver's college and shift mapping.
    Similar to RegisterVerifyView but for adding new mappings to existing drivers.
    """
    serializer_class = DriverProfileMappingSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        """
        Create a new college and shift mapping for the authenticated driver.
        Expects: college_name, start_shift, end_shift
        """
        # Ensure the user is a driver
        if not request.user.is_driver:
            return Response(
                {"detail": "Only drivers can create college mappings."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get required fields from request
        college_name = request.data.get('college_name')
        start_shift = request.data.get('start_shift')
        end_shift = request.data.get('end_shift')
        
        # Validate required fields
        if not all([college_name, start_shift, end_shift]):
            return Response(
                {"detail": "college_name, start_shift, and end_shift are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get the driver's profile
            profile = request.user.profile
            
            # Check if this exact mapping already exists
            college, college_created = College.objects.get_or_create(college_name=college_name, defaults={'is_active': True})
            timing, timing_created = CollegeTiming.objects.get_or_create(start_shift=start_shift, end_shift=end_shift)
            
            # Check if mapping already exists
            existing_mapping = DriverProfileMapping.objects.filter(
                driver=profile,
                college=college,
                timing=timing
            ).first()
            
            if existing_mapping:
                # Return existing mapping
                serializer = self.get_serializer(existing_mapping)
                return Response({
                    "message": "Driver profile mapping already exists.",
                    "data": serializer.data
                }, status=status.HTTP_200_OK)
            
            # Create new mapping
            with transaction.atomic():
                driver_mapping = DriverProfileMapping.objects.create(
                    driver=profile,
                    college=college,
                    timing=timing
                )
                
                # Serialize the mapping
                serializer = self.get_serializer(driver_mapping)
                
                return Response({
                    "message": f"Mapping Created Successfully .",
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)
                
        except Profile.DoesNotExist:
            return Response(
                {"detail": "Driver profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            # Handle specific database constraint errors
            if "UNIQUE constraint failed" in str(e):
                return Response(
                    {"detail": "A mapping with this combination already exists for this driver."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                {"detail": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
