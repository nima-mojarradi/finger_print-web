from django.urls import path
from .views import (
    LoginView,
    LogoutView,
    UserCreateView,
    UserListView,
    UserDetailView,
    UserEditView,
    # CompanyListCreateView,
    # CompanyDetailView,
    # ChangePasswordView,
    # AddFingerprintView,
    ProfileView,
)

urlpatterns = [
    path("", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/", ProfileView.as_view(), name="profile"),
    
    path("users/", UserListView.as_view(), name="user-list"),
    path("users/create/", UserCreateView.as_view(), name="user-create"),
    # path("users/change_password/", ChangePasswordView.as_view(), name="change_password"),
    path("users/<str:nationality_number>/", UserDetailView.as_view(), name="user-detail"),
    path("users/<str:nationality_number>/edit/", UserEditView.as_view(), name="edit_user"),

    # path("users/<str:nationality_number>/add_fingerprint/", AddFingerprintView.as_view(), name="add_fingerprint"),


    # path("companies/", CompanyListCreateView.as_view(), name="company-list-create"),
    # path("companies/<int:pk>/", CompanyDetailView.as_view(), name="company-detail"),
]
