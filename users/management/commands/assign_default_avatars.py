"""
Commande de gestion Django : attribue la photo de profil par défaut
aux comptes StudentProfile / ProfessorProfile existants qui n'en ont pas.

Emplacement à respecter dans ton projet :
    users/management/commands/assign_default_avatars.py

(crée les dossiers management/ et management/commands/ s'ils n'existent
pas, chacun avec un fichier __init__.py vide)

Usage :
    python manage.py assign_default_avatars            # applique les changements
    python manage.py assign_default_avatars --dry-run   # simulation, n'écrit rien
"""

from django.core.management.base import BaseCommand
from users.models import StudentProfile, ProfessorProfile, DEFAULT_AVATAR_PATH


class Command(BaseCommand):
    help = (
        "Attribue la photo de profil par défaut aux profils étudiants et "
        "professeurs existants qui n'ont pas encore de photo de profil."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Affiche ce qui serait modifié sans enregistrer les changements.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        student_qs = StudentProfile.objects.filter(profil_photo__in=["", None])
        professor_qs = ProfessorProfile.objects.filter(profil_photo__in=["", None])

        student_count = student_qs.count()
        professor_count = professor_qs.count()

        if student_count == 0 and professor_count == 0:
            self.stdout.write(self.style.SUCCESS("Aucun profil sans photo — rien à faire."))
            return

        self.stdout.write(
            f"Profils étudiants sans photo : {student_count}\n"
            f"Profils professeurs sans photo : {professor_count}"
        )

        if dry_run:
            self.stdout.write(self.style.WARNING("Mode --dry-run : aucun enregistrement effectué."))
            return

        updated_students = student_qs.update(profil_photo=DEFAULT_AVATAR_PATH)
        updated_professors = professor_qs.update(profil_photo=DEFAULT_AVATAR_PATH)

        self.stdout.write(
            self.style.SUCCESS(
                f"Terminé : {updated_students} profil(s) étudiant(s) et "
                f"{updated_professors} profil(s) professeur(s) mis à jour."
            )
        )