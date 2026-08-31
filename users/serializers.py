from rest_framework import serializers
from .models import CustomUser, StudentProfile, ProfessorProfile, Notification
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'read', 'created_at']
        read_only_fields = ['id', 'created_at']

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
            'role', 'is_verified', 'student_profile', 'professor_profile'
        ]
       # read_only_fields = ['role'] # Le rôle n'est pas modifiable via cette API directement par l'utilisateur
        # is_verified n'est pas marqué read_only ici car AdminUserUpdateView utilise
        # ce même sérialiseur pour permettre à un admin de valider un professeur.
        # La protection contre l'auto-modification par un utilisateur normal se fait
        # dans UserProfileView.update() (voir views.py), pas ici.
    
    def get_student_profile(self, obj):
        if obj.role == 'student' and hasattr(obj, 'student_profile'):
            return StudentProfileSerializer(obj.student_profile).data
        return None


class AdminCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cette adresse e-mail est déjà utilisée.")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        return CustomUser.objects.create_user(
            password=password,
            role='admin',
            is_verified=True,
            **validated_data,
        )

    def get_professor_profile(self, obj):
        if obj.role == 'professor' and hasattr(obj, 'professor_profile'):
            return ProfessorProfileSerializer(obj.professor_profile).data
        return None


# Sérialiseur pour l'enregistrement (inscription)
#
# IMPORTANT : les champs de profil (student_id, major, level, employee_id,
# department, specialization) et profil_photo sont déclarés À PLAT ici,
# et non imbriqués sous student_profile / professor_profile comme avant.
# Raison : le front envoie maintenant du multipart/form-data (FormData) pour
# pouvoir joindre le fichier de la photo, et DRF ne sait pas reconstruire des
# objets imbriqués (student_profile.major, etc.) depuis du multipart — seuls
# des champs à plat fonctionnent de façon fiable dans ce cas.
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    # Photo de profil optionnelle choisie à l'inscription (sinon la valeur
    # par défaut du modèle StudentProfile/ProfessorProfile s'applique)
    profil_photo = serializers.ImageField(write_only=True, required=False, allow_null=True)

    # Champs optionnels du profil étudiant
    student_id = serializers.CharField(write_only=True, required=False, allow_blank=True)
    major = serializers.CharField(write_only=True, required=False, allow_blank=True)
    level = serializers.CharField(write_only=True, required=False, allow_blank=True)

    # Champs optionnels du profil professeur
    employee_id = serializers.CharField(write_only=True, required=False, allow_blank=True)
    department = serializers.CharField(write_only=True, required=False, allow_blank=True)
    specialization = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'password', 'phone_number',
            'first_name', 'role', 'profil_photo',
            'student_id', 'major', 'level',
            'employee_id', 'department', 'specialization',
        ]
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        profil_photo = validated_data.pop('profil_photo', None)

        student_fields = {
            'student_id': validated_data.pop('student_id', ''),
            'major': validated_data.pop('major', ''),
            'level': validated_data.pop('level', ''),
        }
        professor_fields = {
            'employee_id': validated_data.pop('employee_id', ''),
            'department': validated_data.pop('department', ''),
            'specialization': validated_data.pop('specialization', ''),
        }

        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            phone_number=validated_data.get('phone_number'),
            first_name=validated_data.get('first_name', ''),
            role=validated_data.get('role', 'student'),
            # Un compte professeur démarre non vérifié : il n'a pas les privilèges
            # professeur tant qu'un admin ne l'a pas validé (voir DashboardAdmin).
            # Un étudiant reste vérifié par défaut — moins de risque, pas de gain
            # de privilège sensible associé au rôle 'student'.
            is_verified=(validated_data.get('role', 'student') != 'professor'),
        )

        # Le signal post_save crée déjà un profil vide : on le met à jour au lieu d'en créer un second
        if user.role == 'student':
            profile, _ = StudentProfile.objects.get_or_create(user=user)
            for attr, value in student_fields.items():
                if value:
                    setattr(profile, attr, value)
            if profil_photo:
                profile.profil_photo = profil_photo
            profile.save()
        elif user.role == 'professor':
            profile, _ = ProfessorProfile.objects.get_or_create(user=user)
            for attr, value in professor_fields.items():
                if value:
                    setattr(profile, attr, value)
            if profil_photo:
                profile.profil_photo = profil_photo
            profile.save()

        return user

    def validate(self, data):
        # Valide l'unicité de l'email
        if CustomUser.objects.filter(email=data.get('email')).exists():
            raise serializers.ValidationError({"email": "Cette adresse e-mail est déjà utilisée."})
        if data.get('role') == 'admin':
            raise serializers.ValidationError({"role": "La création d'un administrateur est réservée aux administrateurs existants."})
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
