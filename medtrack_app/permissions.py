from rest_framework.permissions import BasePermission

class IsDoctor(BasePermission):
    # Allows access only to users in the 'Doctor' group.
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Doctor')

class IsAdmin(BasePermission):
    # Allows access only to users in the 'Admin' group.    
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Admin')

class IsFrontDesk(BasePermission):
    # Allows access only to users in the 'Front_Desk' group.
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Front_Desk')
