# -*- coding: utf-8 -*-

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, permissions, status
from .models import Subscription
from .serializers import SubscriptionSerializer, CreateSubscriptionSerializer
from .permissions import IsStudentOnly, IsProfessorOnly, IsSubscriptionOwnerOrAdmin
from users.models import CustomUser

class SubscriptionListCreateView(generics.ListCreateAPIView):
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        if self.request.user.role == 'student':
            return Subscription.objects.filter(student=self.request.user)
        elif self.request.user.role == 'professor':
            return Subscription.objects.filter(professor=self.request.user)
        elif self.request.user.is_superuser or self.request.user.role == 'admin':
            return Subscription.objects.all()
        return Subscription.objects.none()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateSubscriptionSerializer
        return SubscriptionSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            self.permission_classes = [IsStudentOnly]
        else:
            self.permission_classes = [permissions.IsAuthenticated]
        return super().get_permissions()

class SubscriptionDestroyView(generics.DestroyAPIView):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsSubscriptionOwnerOrAdmin]

    def get_object(self):
        professor_id = self.kwargs.get('professor_id')
        if not professor_id:
            raise generics.ValidationError({"detail": "L'ID du professeur est requis pour la désinscription."})

        try:
            professor = CustomUser.objects.get(id=professor_id, role='professor')
        except CustomUser.DoesNotExist:
            raise generics.ValidationError({"detail": "Professeur introuvable."})

        try:
            obj = Subscription.objects.get(student=self.request.user, professor=professor)
        except Subscription.DoesNotExist:
            raise generics.ValidationError({"detail": "Abonnement introuvable pour cet étudiant et ce professeur."})

        self.check_object_permissions(self.request, obj)
        return obj

class ProfessorSubscribersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            
            if not hasattr(user, 'role') or user.role != 'professor':
                return Response(
                    {'detail': 'Accès réservé aux professeurs.'}, 
                    status=status.HTTP_403_FORBIDDEN
                )

            # Un professeur non encore validé par un admin n'a pas accès à la liste
            # de ses abonnés (données personnelles d'étudiants).
            if not user.is_verified:
                return Response(
                    {'detail': "Votre compte professeur est en attente de validation par un administrateur."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            subscriptions = Subscription.objects.filter(professor=user)
            
            subscribers_data = []
            for sub in subscriptions:
                student = sub.student
                
                # Données de base
                subscriber_data = {
                    'id': student.id,
                    'username': student.username,
                    'email': student.email,
                    'first_name': getattr(student, 'first_name', '') or '',
                    'last_name': getattr(student, 'last_name', '') or '',
                }
                
                # Gestion du profil étudiant avec chemin correct
                if hasattr(student, 'student_profile') and student.student_profile:
                    profile = student.student_profile
                    
                    if hasattr(profile, 'profil_photo') and profile.profil_photo:
                        photo_path = str(profile.profil_photo)
                        if photo_path and photo_path != 'None':
                            # Ajoute le préfixe /media/ si il n'est pas déjà présent
                            if not photo_path.startswith('/media/'):
                                photo_path = '/media/' + photo_path
                            
                            subscriber_data['student_profile'] = {
                                'profil_photo': photo_path
                            }
                
                subscribers_data.append(subscriber_data)
            
            return Response(subscribers_data)
            
        except Exception as e:
            print(f"Erreur: {e}")
            return Response(
                {'detail': 'Erreur interne du serveur.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
