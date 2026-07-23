from rest_framework import serializers
from .models import Resource
from users.serializers import CustomUserSerializer # Pour afficher les infos de l'uploader

class ResourceSerializer(serializers.ModelSerializer):
    uploaded_by = CustomUserSerializer(read_only=True)
    uploaded_by_username = serializers.SerializerMethodField()  # Ajouté
    file_url = serializers.SerializerMethodField()
    upload_date= serializers.SerializerMethodField()

    class Meta:
        model = Resource
        fields = [
            'id', 'title', 'description', 'file', 'file_url',
            'resource_type', 'uploaded_by', 'uploaded_by_username',  # Ajouté ici
            'subject', 'level', 'uploaded_at', 'updated_at','upload_date'
        ]
        read_only_fields = ['uploaded_by', 'uploaded_at', 'updated_at']

    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
        return None

    def get_uploaded_by_username(self, obj):
        # Retourne le nom d'utilisateur ou None
        return obj.uploaded_by.username if obj.uploaded_by else None
     
    def get_upload_date(self,obj):
        return obj.uploaded_at.isoformat() if obj.uploaded_at else None
class ResourceCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = [
            'title', 'description', 'file',
            'resource_type', 'subject', 'level'
        ]