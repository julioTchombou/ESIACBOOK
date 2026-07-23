# esiacbook_backend/users/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, StudentProfile, ProfessorProfile

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