from rest_framework.permissions import BasePermission

from .models import User

class IsLibrarian(BasePermission):
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'Librarian'

class IsBorrowerOrlibrarian(BasePermission):
    
    def has_permission(self, request,view   ):
        if request.user.is_superuser:
            return True
       
        if view.action in ['list','retrieve']:
            return True
        
        
        return False
     
