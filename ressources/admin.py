

# Register your models here.
# resources/admin.py
from django.contrib import admin
from .models import Resource

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'resource_type', 'subject', 'level', 'uploaded_by', 'uploaded_at')
    list_filter = ('resource_type', 'subject', 'level', 'uploaded_by')
    search_fields = ('title', 'description', 'subject', 'level')
    raw_id_fields = ('uploaded_by',) # Pour faciliter la sélection de l'uploader si beaucoup d'utilisateurs
