from rest_framework.permissions import BasePermission

class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.roles == 'super_admin'

class IsNormalAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.roles == 'normal_admin'

class IsUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.roles in ['user', 'normal_admin', 'super_admin']
