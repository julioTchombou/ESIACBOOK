from django.shortcuts import render
from rest_framework import generics, permissions, status,viewsets
from rest_framework.decorators import action

from rest_framework.response import Response
from .models import CustomUser, StudentProfile, ProfessorProfile, Notification, create_notification # Assurez-vous d'importer les modèles de profil
from .serializers import CustomUserSerializer, RegisterSerializer, AdminCreateSerializer, StudentProfileSerializer, ProfessorProfileSerializer,MyTokenObtainPairSerializer, NotificationSerializer # Importez tous les sérialiseurs nécessaires
from .ai_agent import ask_ai
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

# Champs qu'un utilisateur ne peut JAMAIS modifier lui-même via UserProfileView,
# même en connaissant leur nom — seul un admin peut les changer (AdminUserUpdateView).
SELF_UPDATE_LOCKED_FIELDS = ('role', 'is_verified')


class IsApplicationAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.is_superuser or user.is_staff or user.role == 'admin')
        )


# Vue pour obtenir/mettre à jour les détails de l'utilisateur connecté (profil)
class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = CustomUserSerializer # Utilise le sérialiseur qui inclut les profils
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        # Récupérer l'instance de CustomUser
        user = self.get_object()

        # Un utilisateur ne peut modifier ni son rôle ni son statut de vérification
        locked_fields_present = [f for f in SELF_UPDATE_LOCKED_FIELDS if f in request.data]
        if locked_fields_present:
            return Response(
                {"detail": f"Les champs {locked_fields_present} ne peuvent pas être modifiés via cette API."},
                status=status.HTTP_403_FORBIDDEN,
            )

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
    permission_classes = [IsApplicationAdmin]


class AdminCreateView(generics.CreateAPIView):
    serializer_class = AdminCreateSerializer
    permission_classes = [IsApplicationAdmin]

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
    # Vue réservée aux admins : c'est ICI (et uniquement ici) qu'on peut
    # écrire role et is_verified — ex. PATCH /api/users/update/<pk>/
    # avec { "is_verified": true } pour valider un professeur.
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsApplicationAdmin]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if instance.role == 'professor' and request.data.get('is_verified') is True and not instance.is_verified:
            create_notification(
                instance,
                'Compte validé',
                'Votre compte professeur a été validé par un administrateur. Vous pouvez maintenant publier des cours et gérer vos abonnés.',
            )

        return Response(serializer.data)


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsApplicationAdmin]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance == request.user:
            return Response(
                {'detail': 'Vous ne pouvez pas supprimer votre propre compte administrateur.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class UserMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        return self._update(request)

    def put(self, request):
        return self._update(request)

    def _update(self, request):
        user = request.user

        locked_fields_present = [f for f in SELF_UPDATE_LOCKED_FIELDS if f in request.data]
        if locked_fields_present:
            return Response(
                {"detail": f"Les champs {locked_fields_present} ne peuvent pas être modifiés via cette API."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CustomUserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class NotificationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)

    def patch(self, request):
        Notification.objects.filter(user=request.user, read=False).update(read=True)
        return Response({"detail": "Notifications marquées comme lues."})

    def delete(self, request):
        Notification.objects.filter(user=request.user).delete()
        return Response({"detail": "Notifications supprimées."}, status=status.HTTP_200_OK)


class SendUserNotificationView(APIView):
    permission_classes = [IsApplicationAdmin]

    def post(self, request):
        user_id = request.data.get('user_id')
        title = (request.data.get('title') or '').strip()
        message = (request.data.get('message') or '').strip()

        if not user_id or not title or not message:
            return Response({"detail": "user_id, title et message sont requis."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            target_user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({"detail": "Utilisateur introuvable."}, status=status.HTTP_404_NOT_FOUND)

        create_notification(target_user, title, message)
        return Response({"detail": "Notification envoyée avec succès."}, status=status.HTTP_201_CREATED)


class AIAssistantView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        question = (request.data.get('question') or '').strip()
        if not question:
            return Response({"detail": "La question est obligatoire."}, status=status.HTTP_400_BAD_REQUEST)
        if len(question) > 4000:
            return Response({"detail": "La question ne peut pas dépasser 4000 caractères."}, status=status.HTTP_400_BAD_REQUEST)

        history = request.data.get('history', [])
        if not isinstance(history, list):
            return Response({"detail": "L’historique doit être une liste."}, status=status.HTTP_400_BAD_REQUEST)

        answer = ask_ai(question, request.user, history)
        return Response({"answer": answer}, status=status.HTTP_200_OK)


class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsApplicationAdmin]

    def get_permissions(self):
        if self.action == 'me':
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(detail=False, methods=['get', 'put', 'patch'], url_path='me')
    def me(self, request):
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        elif request.method in ['PUT', 'PATCH']:
            # Même protection que UserProfileView : pas d'auto-modification de role/is_verified
            locked_fields_present = [f for f in SELF_UPDATE_LOCKED_FIELDS if f in request.data]
            if locked_fields_present:
                return Response(
                    {"detail": f"Les champs {locked_fields_present} ne peuvent pas être modifiés via cette API."},
                    status=status.HTTP_403_FORBIDDEN,
                )
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
