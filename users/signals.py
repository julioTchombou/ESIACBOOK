# esiacbook_backend/users/signals.py
# esiacbook_backend/users/signals.py
import logging

import requests
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import CustomUser, StudentProfile, ProfessorProfile, Notification

logger = logging.getLogger(__name__)


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.role == 'student':
            StudentProfile.objects.create(user=instance)
        elif instance.role == 'professor':
            ProfessorProfile.objects.create(user=instance)
        # Pas besoin de créer un profil pour 'admin' si ce n'est pas nécessaire,
        # ou ajoutez un modèle AdminProfile si vous en avez un.


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    # Cette fonction est vide pour l'instant, mais peut être utilisée pour
    # sauvegarder les changements dans le profil si l'utilisateur est modifié.
    # Par exemple, si vous permettez de changer le rôle après la création.
    pass


@receiver(post_save, sender=CustomUser)
def create_user_welcome_notification(sender, instance, created, **kwargs):
    if not created:
        return

    Notification.objects.create(
        user=instance,
        title='Bienvenue sur ESIACBOOK',
        message='Votre compte a bien été créé. Complétez votre profil pour profiter pleinement de la plateforme.',
    )


@receiver(post_save, sender=CustomUser)
def notify_n8n_new_user(sender, instance, created, **kwargs):
    """
    Déclenche le workflow n8n d'email de bienvenue à la création d'un compte.

    N8N_WEBHOOK_URL doit être défini dans les variables d'environnement (.env) :
        N8N_WEBHOOK_URL=https://<ton-instance-n8n>/webhook/esiacbook-welcome-email

    En développement, utilise l'URL de test n8n (bouton "Listen for test event")
    puis remplace par l'URL de production une fois le workflow activé.

    Le try/except est volontaire : si n8n est indisponible ou mal configuré,
    l'inscription de l'utilisateur ne doit JAMAIS échouer à cause de ça.
    """
    if not created:
        return

    webhook_url = getattr(settings, 'N8N_WEBHOOK_URL', '')
    if not webhook_url:
        return

    payload = {
        'email': instance.email,
        'first_name': instance.first_name,
        'username': instance.username,
        'role': instance.role,
    }

    try:
        requests.post(webhook_url, json=payload, timeout=3)
    except requests.RequestException:
        # On log l'échec mais on ne remonte jamais l'erreur à l'utilisateur qui s'inscrit
        logger.warning("Échec de l'appel au webhook n8n pour %s", instance.email, exc_info=True)
