# users/urls.py

from django.urls import path

from core.views.driver import (
    RegisterView,
    RegisterVerifyView,
    SendOTPView,
    LoginView,
    DriverProfileDetailView,
    DriverProfileUpdateView,
    DriverProfileMappingUpdateDeleteView
)

from core.views.parent import (
    ParentRegisterView,
    ParentRegisterVerifyView,
    ParentSendOTPView,
    ParentLoginView
    
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

    path('driver-profile/<int:driver_id>/', DriverProfileDetailView.as_view(), name='driver-profile-detail'),
    path('driver-profile-update/<int:driver_id>/', DriverProfileUpdateView.as_view(), name='driver-profile-update'),
    path('driver-mapping-update-delete/<int:pk>/', DriverProfileMappingUpdateDeleteView.as_view(), name='driver-mapping-update-delete'),
    
    #===========================Parent Details==========================
    path('parent-register', ParentRegisterView.as_view(), name='parent-register'),
    path('parent-verify-otp', ParentRegisterVerifyView.as_view(), name='parent-verify-otp'),
    path('parent-send-otp', ParentSendOTPView.as_view(), name='parent-send-otp'),
    path('parent-login', ParentLoginView.as_view(), name='parent-login'),

    #===========================Children Details==========================
    path('children/add/', ChildrenCreateView.as_view(), name='add-child'),
    path('children/edit/<int:pk>/', ChildrenUpdateView.as_view(), name='edit-child'),
    path('children/delete/<int:pk>/', ChildrenDeleteView.as_view(), name='delete-child'),
    path('children/list/<int:parent_id>/', ChildrenListByParentView.as_view(), name='list-children-by-parent'),
    
]
