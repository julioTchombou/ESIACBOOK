# resources/permissions.py
from rest_framework import permissions

class IsProfessorOrReadOnly(permissions.BasePermission):
    """
    Permission personnalisée pour n'autoriser que les professeurs VÉRIFIÉS
    à créer, modifier ou supprimer des ressources.
    La lecture est autorisée pour tous les utilisateurs authentifiés.
    """
    def has_permission(self, request, view):
        # Les requêtes GET, HEAD, OPTIONS sont toujours autorisées pour les utilisateurs authentifiés.
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        # Les requêtes POST, PUT, PATCH, DELETE ne sont autorisées que si l'utilisateur est un
        # professeur VÉRIFIÉ par un admin (voir CustomUser.is_verified). Un compte professeur
        # fraîchement inscrit et non encore validé n'a donc pas ce privilège.
        # Un admin (superutilisateur ou role='admin') peut toujours effectuer ces actions.
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.is_superuser or user.role == 'admin':
            return True
        return user.role == 'professor' and user.is_verified


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission personnalisée pour n'autoriser que le propriétaire de la ressource
    à la modifier ou la supprimer.
    Un administrateur peut également modifier ou supprimer n'importe quelle ressource.
    La lecture est autorisée pour tout le monde (ou via IsProfessorOrReadOnly).
    """
    def has_object_permission(self, request, view, obj):
        # Les requêtes GET, HEAD, OPTIONS sont toujours autorisées.
        if request.method in permissions.SAFE_METHODS:
            return True # Permet la lecture pour tous (car IsProfessorOrReadOnly gère déjà l'authentification pour les vues de liste)

        # Si l'utilisateur est un administrateur, il a toutes les permissions.
        if request.user and (request.user.is_superuser or request.user.role == 'admin'):
            return True

        # Les requêtes d'écriture (PUT, PATCH, DELETE) ne sont autorisées qu'au propriétaire de la ressource.
        return obj.uploaded_by == request.user
 