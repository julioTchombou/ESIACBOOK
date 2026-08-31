# subscriptions/serializers.py
from rest_framework import serializers
from .models import Subscription
from users.models import create_notification
from users.serializers import CustomUserSerializer # Pour afficher les détails de l'étudiant/professeur

class SubscriptionSerializer(serializers.ModelSerializer):
    # Utilise CustomUserSerializer pour afficher les détails complets de l'étudiant et du professeur
    student = CustomUserSerializer(read_only=True)
    professor = CustomUserSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = ['id', 'student', 'professor', 'subscribed_at']
        read_only_fields = ['subscribed_at']

class CreateSubscriptionSerializer(serializers.ModelSerializer):
    # Pour la création, nous avons seulement besoin de l'ID du professeur
    professor_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Subscription
        fields = ['professor_id']

    def validate_professor_id(self, value):
        # Vérifie que l'ID correspond à un professeur existant
        from users.models import CustomUser # Importation locale pour éviter les dépendances circulaires
        try:
            professor = CustomUser.objects.get(id=value)
            if not professor.role == 'professor':
                raise serializers.ValidationError("L'utilisateur avec cet ID n'est pas un professeur.")
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("Le professeur n'existe pas.")
        return value

    def create(self, validated_data):
        professor_id = validated_data.pop('professor_id')
        student = self.context['request'].user # L'étudiant qui fait la requête

        from users.models import CustomUser
        professor = CustomUser.objects.get(id=professor_id)

        # Vérifie que l'utilisateur est bien un étudiant
        if not student.role == 'student':
            raise serializers.ValidationError("Seuls les étudiants peuvent s'abonner à des professeurs.")

        # Vérifie que l'étudiant n'est pas déjà abonné à ce professeur
        if Subscription.objects.filter(student=student, professor=professor).exists():
            raise serializers.ValidationError("Vous êtes déjà abonné à ce professeur.")

        subscription = Subscription.objects.create(student=student, professor=professor, **validated_data)

        create_notification(
            professor,
            'Nouvel abonnement',
            f'{student.get_full_name() or student.username} s\'est abonné à votre profil.',
        )
        create_notification(
            student,
            'Abonnement enregistré',
            f'Vous êtes maintenant abonné à {professor.get_full_name() or professor.username}.',
        )

        return subscription