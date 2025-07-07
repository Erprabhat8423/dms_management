# users/urls.py

from django.urls import path

from core.views.driver import (
    RegisterView,
    RegisterVerifyView,
    SendOTPView,
    LoginView,
    DriverProfileDetailView,
    DriverProfileUpdateView,
    CollegeMappingCreateView,
    DriverProfileMappingUpdateDeleteView,
    CollegeListAPIView,
    VehicleTypeListAPIView
)

from core.views.parent import (
    ParentRegisterView,
    ParentRegisterVerifyView,
    ParentSendOTPView,
    ParentLoginView,
    ParentProfileUpdateView,
    
)

from core.views.children import (
    ChildrenCreateView,
    ChildrenUpdateView,
    ChildrenDeleteView,
    ChildrenListByParentView,
)

urlpatterns = [
    path('register', RegisterView.as_view(), name='register'),
    path('verify-otp', RegisterVerifyView.as_view(), name='verify-otp'),
    path('send-otp', SendOTPView.as_view(), name='send-otp'),
    path('login', LoginView.as_view(), name='login'),
    #=========================== Driver Details========================

    path('driver-profile/<int:driver_id>', DriverProfileDetailView.as_view(), name='driver-profile-detail'),
    path('driver-profile-update/<int:driver_id>', DriverProfileUpdateView.as_view(), name='driver-profile-update'),
    path('driver-mapping-create/', CollegeMappingCreateView.as_view(), name='driver-mapping-create'),
    path('driver-mapping-update-delete/<int:pk>', DriverProfileMappingUpdateDeleteView.as_view(), name='driver-mapping-update-delete'),

    
    #===========================Parent Details==========================
    path('parent-register', ParentRegisterView.as_view(), name='parent-register'),
    path('parent-verify-otp', ParentRegisterVerifyView.as_view(), name='parent-verify-otp'),
    path('parent-send-otp', ParentSendOTPView.as_view(), name='parent-send-otp'),
    path('parent-login', ParentLoginView.as_view(), name='parent-login'),
    #===========================Parent Profile Details==========================
    path('parent-profile-update/<int:pk>/', ParentProfileUpdateView.as_view(), name='parent-profile-update'),
    #===========================Children Details==========================
    path('children/add/', ChildrenCreateView.as_view(), name='add-child'),
    path('children/edit/<int:pk>/', ChildrenUpdateView.as_view(), name='edit-child'),
    path('children/delete/<int:pk>/', ChildrenDeleteView.as_view(), name='delete-child'),
    path('children/list/<int:parent_id>/', ChildrenListByParentView.as_view(), name='list-children-by-parent'),
    #============================Master data==========================
    path('colleges/', CollegeListAPIView.as_view(), name='college-list'),
    path('vehicle-types/', VehicleTypeListAPIView.as_view(), name='vehicle-type-list'),
    
]
