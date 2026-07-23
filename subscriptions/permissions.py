# subscriptions/permissions.py
from rest_framework import permissions

class IsStudentOnly(permissions.BasePermission):
    """
    Permission personnalisée pour n'autoriser que les étudiants authentifiés.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'student'

class IsProfessorOnly(permissions.BasePermission):
    """
    Permission personnalisée pour n'autoriser que les professeurs authentifiés.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'professor'

class IsSubscriptionOwnerOrAdmin(permissions.BasePermission):
    """
    Permet au propriétaire de l'abonnement (l'étudiant) ou à un admin de le supprimer.
    """
    def has_object_permission(self, request, view, obj):
        # L'administrateur a toujours la permission
        if request.user and (request.user.is_superuser or request.user.role == 'admin'):
            return True

        # L'abonnement ne peut être supprimé que par l'étudiant qui l'a créé
        return request.user and request.user.is_authenticated and obj.student == request.user