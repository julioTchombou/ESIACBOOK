from django.db import models

# Create your models here.
from django.conf import settings


class Resource(models.Model):
    RESOURCE_TYPES = [
        ('cours', 'Cours'),
        ('td', 'TD'),
        ('exam', 'Examen'),
        ('other', 'Autre'),
    ]

    title = models.CharField(max_length=255, verbose_name="Titre de la ressource")
    description = models.TextField(blank=True, null=True, verbose_name="Description")

    # Le champ FileField va stocker le chemin du fichier et gérer les uploads
    file = models.FileField(
        upload_to='resources_files/', # Les fichiers seront stockés dans media/resources_files/
        verbose_name="Fichier de la ressource"
    )

    resource_type = models.CharField(
        max_length=10,
        choices=RESOURCE_TYPES,
        default='cours',
        verbose_name="Type de ressource"
    )

    # L'utilisateur qui a uploadé la ressource (doit être un professeur)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Référence à votre CustomUser
        on_delete=models.CASCADE,
        related_name='uploaded_resources',
        verbose_name="Uploader par"
    )

    subject = models.CharField(max_length=100, verbose_name="Matière") # Ex: Mathématiques, Informatique
    level = models.CharField(max_length=50, verbose_name="Niveau d'étude") # Ex: Licence 1, Master 2

    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'upload")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de dernière modification")

    class Meta:
        verbose_name = "Ressource Pédagogique"
        verbose_name_plural = "Ressources Pédagogiques"
        ordering = ['-uploaded_at'] # Triez par défaut par les plus récentes

    def __str__(self):
        return self.title