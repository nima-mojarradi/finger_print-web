from django.urls import path
from .views import (
    LoginView,
    LogoutView,
    UserCreateView,
    UserListView,
    UserEditView,
    UserDetailView,
    UserDeleteView,
    ProfileView,
    EnrollFingerprintView,
    AddFingerprintAPI,
    FingerprintAttendanceView,
    ChangePasswordView,
    CompanyListView,
    CompanyCreateView,
    CompanyEditView,
    CompanyDeleteView,
    ShowTempPasswordView
)

urlpatterns = [
    path('', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/create/', UserCreateView.as_view(), name='user-create'),
    path('users/<str:nationality_number>/edit/', UserEditView.as_view(), name='user-edit'),
    path('users/<str:nationality_number>/', UserDetailView.as_view(), name='user-detail'),
    path('users/<str:nationality_number>/delete/', UserDeleteView.as_view(),
         name='user-delete'),
    path('show-temp-password/<str:nationality_number>/', 
     ShowTempPasswordView.as_view(), name='show_temp_password'),
    path('enroll-fingerprint/<str:nationality_number>/<str:finger_name>/',
    EnrollFingerprintView.as_view(), name='enroll_fingerprint'),
    path('api/users/<str:nationality_number>/fingerprint/add/', AddFingerprintAPI.as_view(), name='add_fingerprint'),

    path('api/attendance/fingerprint/', FingerprintAttendanceView.as_view(), name='fingerprint_attendance'),
    path("companies/", CompanyListView.as_view(), name="company-list"),
    path("companies/create/", CompanyCreateView.as_view(), name="company-create"),
    path("companies/<int:company_id>/edit/", CompanyEditView.as_view(), name="company-edit"),
    path("companies/<int:company_id>/delete/", CompanyDeleteView.as_view(), name="company-delete"),

]
