from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    email = models.EmailField(
        verbose_name='Adresse e-mail',
        max_length=255,
        help_text='Addresse e-mail de l\'utilisateur',
        unique=True
    )
    phone_number = models.CharField(
        verbose_name='Numéro de téléphone',
        max_length=15,
        help_text='Numéro de téléphone de l\'utilisateur',
        blank=True,
        null=True
    )
    ROLE_CHOICES = (
        ('student', 'Étudiant'),
        ('professor', 'Professeur'),
        ('admin', 'Administrateur'),
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='student',
        verbose_name='Rôle de l\'utilisateur',
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'role']

    class Meta:
        verbose_name = 'Utilisateur ESIACBOOK'
        verbose_name_plural = 'Utilisateurs ESIACBOOK'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_role_display()})"

    def is_student(self):
        return self.role == 'student'

    def is_professor(self):
        return self.role == 'professor'


class StudentProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='student_profile', verbose_name='Utilisateur Etudiant')
    student_id = models.CharField(max_length=50, unique=True, verbose_name= 'Numero matricule',null=True, blank=True,help_text=' matricule unique de l\'étudiant')
    major = models.CharField(max_length=100, verbose_name='Filiere / Spécialité', help_text='Genie Logiel, Reseaux et Telecoms', null=True, blank=True)
    level = models.CharField(max_length=50, verbose_name='Niveau d\'étude',help_text='Ex: Licence 1, Master 2, etc.', null=True, blank=True)
    profil_photo = models.ImageField( upload_to='profile_photos/students/',
        verbose_name='Photo de profil',
        null=True,
        blank=True,
      
        help_text='Photo de profil de l\'étudiant')
    class Meta:
        verbose_name = 'Profil Étudiant'
        verbose_name_plural = 'Profils Étudiants'
        ordering = ['user__last_name']
    def __str__(self):
        return f"Profil Etudiant de {self.user.get_full_name()} )"
    
class ProfessorProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='professor_profile', verbose_name='Utilisateur Professeur')
    employee_id = models.CharField(max_length=50, unique=True, verbose_name='Numero Employé', null=True, blank=True, help_text='Identifiant unique du professeur')
    department = models.CharField(max_length=100, verbose_name='Département', help_text='Département d\'enseignement du professeur', null=True, blank=True)
    specialization = models.CharField(max_length=100, verbose_name='Spécialisation', help_text='Spécialisation du professeur', null=True, blank=True)
    profil_photo = models.ImageField(upload_to='profile_photos/professors/',
        verbose_name='Photo de profil',
        null=True,
        blank=True,
       
        help_text='Photo de profil du professeur')
    class Meta:
        verbose_name = 'Profil Professeur'
        verbose_name_plural = 'Profils Professeurs'
        ordering = ['user__last_name']
        
    def __str__(self):
        return f"Profil Professeur de {self.user.get_full_name()}"