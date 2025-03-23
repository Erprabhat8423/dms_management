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