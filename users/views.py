from django.shortcuts import render
from rest_framework import generics, permissions, status,viewsets
from rest_framework.decorators import action

from rest_framework.response import Response
from .models import CustomUser, StudentProfile, ProfessorProfile # Assurez-vous d'importer les modèles de profil
from .serializers import CustomUserSerializer, RegisterSerializer, StudentProfileSerializer, ProfessorProfileSerializer,MyTokenObtainPairSerializer # Importez tous les sérialiseurs nécessaires
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.contrib.auth.password_validation import validate_password
# Vue pour l'inscription des utilisateurs
class RegisterUserView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class ProfessorListView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        professors = CustomUser.objects.filter(role='professor')
        serializer = CustomUserSerializer(professors, many=True)
        return Response(serializer.data)

    # La méthode post est déjà bonne grâce au sérialiseur RegisterSerializer mis à jour

# Vue pour obtenir/mettre à jour les détails de l'utilisateur connecté (profil)
class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = CustomUserSerializer # Utilise le sérialiseur qui inclut les profils
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        # Récupérer l'instance de CustomUser
        user = self.get_object()

        # Si le rôle est présent dans la requête, rejeter la modification
        if 'role' in request.data:
            return Response({"detail": "Le rôle de l'utilisateur ne peut pas être modifié via cette API."},
                            status=status.HTTP_403_FORBIDDEN)

        # Mettre à jour les champs du CustomUser
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer) # Appelle la méthode perform_update ci-dessous

        # Logique pour mettre à jour les profils spécifiques imbriqués (si vous voulez la supporter)
        # C'est un peu plus complexe car il faut gérer les données imbriquées séparément
        # si vous ne voulez pas recréer une instance de profil complète.
        # Pour l'instant, je recommande de gérer les mises à jour des profils via des endpoints séparés
        # pour simplifier ou de faire une mise à jour manuelle des profils ici.

        # Exemple simple pour les photos de profil (si vous avez un endpoint séparé pour l'upload de photo)
        # Si vous avez des champs de profil qui peuvent être mis à jour ici via le CustomUserSerializer :
        # Les champs du CustomUserSerializer (first_name, last_name, email, phone_number) sont mis à jour
        # automatiquement par perform_update(serializer)

        return Response(serializer.data)

# Vue pour lister tous les utilisateurs (peut être restreinte aux admins)
class UserListView(generics.ListAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAdminUser]

# Create your views here.
class ChangePasswordView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def update(self,request,*args,**kwargs):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not user.check_password(old_password):
            return Response({"old_password": "Ancien mot de passe incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(new_password, user)
        except Exception as e:
            return Response({"new_password": e.messages}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({"detail": "Mot de passe changé avec succès."})

class AdminUserUpdateView(generics.RetrieveUpdateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAdminUser]   


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAdminUser]

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class UserMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data)
class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated] # Protégez ce ViewSet

    @action(detail=False, methods=['get', 'put', 'patch'], url_path='me')
    def me(self, request):
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        elif request.method in ['PUT', 'PATCH']:
            serializer = self.get_serializer(request.user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class StudentProfileViewSet(viewsets.ModelViewSet):
    queryset = StudentProfile.objects.all()
    serializer_class = StudentProfileSerializer
    permission_classes = [IsAuthenticated] # Assurez-vous que seuls les authentifiés peuvent modifier

    def get_queryset(self):
        # Les étudiants ne peuvent voir/modifier que leur propre profil
        if self.request.user.is_authenticated and self.request.user.is_student():
            return StudentProfile.objects.filter(user=self.request.user)
        return StudentProfile.objects.none() # Ne pas exposer d'autres profils

    @action(detail=False, methods=['get', 'put', 'patch'], url_path='my-profile')
    def my_profile(self, request):
        try:
            profile = StudentProfile.objects.get(user=request.user)
        except StudentProfile.DoesNotExist:
            return Response({'detail': 'Student profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        elif request.method in ['PUT', 'PATCH']:
            serializer = self.get_serializer(profile, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class ProfessorProfileViewSet(viewsets.ModelViewSet):
    queryset = ProfessorProfile.objects.all()
    serializer_class = ProfessorProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Les professeurs ne peuvent voir/modifier que leur propre profil
        if self.request.user.is_authenticated and self.request.user.is_professor():
            return ProfessorProfile.objects.filter(user=self.request.user)
        return ProfessorProfile.objects.none()

    @action(detail=False, methods=['get', 'put', 'patch'], url_path='my-profile')
    def my_profile(self, request):
        try:
            profile = ProfessorProfile.objects.get(user=request.user)
        except ProfessorProfile.DoesNotExist:
            return Response({'detail': 'Professor profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        elif request.method in ['PUT', 'PATCH']:
            serializer = self.get_serializer(profile, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)