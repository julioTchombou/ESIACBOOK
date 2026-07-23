from rest_framework import serializers
from .models import CustomUser, StudentProfile, ProfessorProfile
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

# Sérialiseur pour le profil étudiant
class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        exclude = ['user'] # Le champ 'user' est géré par la relation OneToOne

# Sérialiseur pour le profil professeur
class ProfessorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfessorProfile
        exclude = ['user'] # Le champ 'user' est géré par la relation OneToOne

# Sérialiseur principal pour CustomUser (lecture/affichage)
class CustomUserSerializer(serializers.ModelSerializer):
    student_profile = StudentProfileSerializer(read_only=True)
    professor_profile = ProfessorProfileSerializer(read_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'phone_number', 'first_name',
            'role', 'student_profile', 'professor_profile'
        ]
       # read_only_fields = ['role'] # Le rôle n'est pas modifiable via cette API directement par l'utilisateur
        # Les champs 'is_student' et 'is_professor' ne sont plus nécessaires ici car 'role' les remplace.
    
    def get_student_profile(self, obj):
        if obj.role == 'student' and hasattr(obj, 'student_profile'):
            return StudentProfileSerializer(obj.student_profile).data
        return None

    def get_professor_profile(self, obj):
        if obj.role == 'professor' and hasattr(obj, 'professor_profile'):
            return ProfessorProfileSerializer(obj.professor_profile).data
        return None
# Sérialiseur pour l'enregistrement (inscription)
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    # Ces profils sont optionnels lors de l'inscription
    student_profile = StudentProfileSerializer(required=False)
    professor_profile = ProfessorProfileSerializer(required=False)

    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'password', 'phone_number',
            'first_name', 'role',
            'student_profile', 'professor_profile'
        ]
        extra_kwargs = {'password': {'write_only': True}} # Le mot de passe n'est que pour l'écriture

    def create(self, validated_data):
        student_profile_data = validated_data.pop('student_profile', None)
        professor_profile_data = validated_data.pop('professor_profile', None)

        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            phone_number=validated_data.get('phone_number'),
            first_name=validated_data.get('first_name', ''),
            role=validated_data.get('role', 'student')
        )

        # Le signal post_save crée déjà un profil vide : on le met à jour au lieu d'en créer un second
        if user.role == 'student':
            profile, _ = StudentProfile.objects.get_or_create(user=user)
            if student_profile_data:
                for attr, value in student_profile_data.items():
                    setattr(profile, attr, value)
                profile.save()
        elif user.role == 'professor':
            profile, _ = ProfessorProfile.objects.get_or_create(user=user)
            if professor_profile_data:
                for attr, value in professor_profile_data.items():
                    setattr(profile, attr, value)
                profile.save()

        return user

    def validate(self, data):
        # Valide l'unicité de l'email
        if CustomUser.objects.filter(email=data.get('email')).exists():
            raise serializers.ValidationError({"email": "Cette adresse e-mail est déjà utilisée."})

        # Valide le rôle et la présence des données de profil associées
        role = data.get('role')
        student_profile_data = data.get('student_profile')
        professor_profile_data = data.get('professor_profile')

        if role == 'student' and professor_profile_data:
            raise serializers.ValidationError({"role": "Un étudiant ne peut pas avoir de profil professeur."})
        if role == 'professor' and student_profile_data:
            raise serializers.ValidationError({"role": "Un professeur ne peut pas avoir de profil étudiant."})
        if role == 'admin' and (student_profile_data or professor_profile_data):
            raise serializers.ValidationError({"role": "Un administrateur ne peut pas avoir de profil étudiant ou professeur."})

        return data
    
class StudentProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True) # Affiche les détails de l'utilisateur lié

    class Meta:
        model = StudentProfile
        fields = '__all__' # Inclut user, student_id, major, level, profil_photo

class ProfessorProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True) # Affiche les détails de l'utilisateur lié

    class Meta:
        model = ProfessorProfile
        fields = '__all__' # Inclut user, employee_id, department, specialization, profil_photo

    
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token=super().get_token(user)
        token['email'] = user.email
        token['role']=user.role
        token['first_name'] = user.first_name
       # token['last_name'] = user.last_name
        # Ajoutez l'URL de la photo de profil au token si elle existe
        if user.role == 'student' and hasattr(user, 'student_profile') and user.student_profile.profil_photo:
            token['profile_photo_url'] = user.student_profile.profil_photo.url
        elif user.role == 'professor' and hasattr(user, 'professor_profile') and user.professor_profile.profil_photo:
            token['profile_photo_url'] = user.professor_profile.profil_photo.url
        return token
        
    
