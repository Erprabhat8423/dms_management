from django.contrib import admin
from .models import (
    CustomUser,
    Profile,
    VehicleType,
    TempUser,
    TempParent,
    College,
    CollegeTiming,
    DriverProfileMapping,
    Parent_Profile,
    Children
)


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id','phone_number', 'is_staff', 'is_driver', 'is_student', 'is_active', 'date_joined','password')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('phone_number',)
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined',)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id','user', 'full_name', 'email', 'licence_no', 'vehicle_no', 'vehicle_type', 'profile_pic')
    search_fields = ('user__phone_number', 'full_name', 'email')
    list_filter = ('vehicle_type', 'user__is_active')
    readonly_fields = ('licence_no',)


@admin.register(VehicleType)
class VehicleTypeAdmin(admin.ModelAdmin):
    list_display = ('vehicle_name', 'is_active', 'created_at')
    search_fields = ('vehicle_name',)
    list_filter = ('is_active',)
    ordering = ('vehicle_name',)
    readonly_fields = ('created_at',)


@admin.register(TempUser)
class TempUserAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone_number', 'is_driver', 'is_student', 'created_at')
    search_fields = ('phone_number', 'full_name')
    list_filter = ('is_driver', 'is_student', 'is_active')
    ordering = ('-created_at',)

@admin.register(TempParent)
class TempParentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone_number', 'profile_pic', 'is_student', 'created_at')
    search_fields = ('phone_number', 'full_name')
    list_filter = ( 'is_student', 'is_active')
    ordering = ('-created_at',)



@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = ('id','college_name', 'is_active', 'created_at')
    search_fields = ('college_name',)
    list_filter = ('is_active',)
    ordering = ('college_name',)
    readonly_fields = ('created_at',)


@admin.register(CollegeTiming)
class CollegeTimingAdmin(admin.ModelAdmin):
    list_display = ('id','start_shift', 'end_shift', 'created_at')
    list_filter = ('start_shift', 'end_shift')
    ordering = ('start_shift',)
    readonly_fields = ('created_at',)


@admin.register(DriverProfileMapping)
class DriverProfileMappingAdmin(admin.ModelAdmin):
    list_display = ('driver', 'college', 'timing')
    search_fields = ('driver__full_name', 'driver__phone_number', 'college__college_name')
    list_filter = ('college',)
    ordering = ('college',)


@admin.register(Parent_Profile)
class Parent_ProfileAdmin(admin.ModelAdmin):
    list_display = ('id','user', 'full_name', 'email', 'dob',  'profile_pic')
    search_fields = ('user__phone_number', 'full_name', 'email')

@admin.register(Children)
class ChildrenAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'college', 'collegetiming',  'parent')
    
    