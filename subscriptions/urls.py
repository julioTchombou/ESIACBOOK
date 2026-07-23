# subscriptions/urls.py
from django.urls import path
from .views import SubscriptionListCreateView, SubscriptionDestroyView, ProfessorSubscribersView

urlpatterns = [
    # Créer un abonnement (POST), Lister les abonnements de l'utilisateur (GET)
    path('', SubscriptionListCreateView.as_view(), name='subscription-list-create'),

    # Supprimer un abonnement (Désabonnement) par l'ID du professeur
    path('delete/<int:professor_id>/', SubscriptionDestroyView.as_view(), name='subscription-delete'),

    # Lister les abonnés d'un professeur spécifique
    #path('my-subscribers/', ProfessorSubscribersView.as_view(), name='my-subscribers'),
   path('my-subscribers/', ProfessorSubscribersView.as_view(), name='my-subscribers'),
]