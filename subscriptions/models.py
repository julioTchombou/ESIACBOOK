
# subscriptions/models.py
from django.db import models
from django.conf import settings # Pour référencer CustomUser

class Subscription(models.Model):
    """
    Modèle représentant l'abonnement d'un étudiant à un professeur.
    """
    # L'étudiant qui s'abonne
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_subscriptions',
        limit_choices_to={'role': 'student'}, # S'assure que seul un utilisateur avec le rôle 'student' peut être ici
        verbose_name="Étudiant"
    )

    # Le professeur auquel l'étudiant s'abonne
    professor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='professor_subscribers',
        limit_choices_to={'role': 'professor'}, # S'assure que seul un utilisateur avec le rôle 'professor' peut être ici
        verbose_name="Professeur"
    )

    # Date de l'abonnement
    subscribed_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'abonnement")

    class Meta:
        verbose_name = "Abonnement"
        verbose_name_plural = "Abonnements"
        # Assure qu'un étudiant ne peut s'abonner qu'une seule fois à un même professeur
        unique_together = ('student', 'professor')
        ordering = ['-subscribed_at']

    def __str__(self):
        return f"{self.student.username} abonné à {self.professor.username}"
