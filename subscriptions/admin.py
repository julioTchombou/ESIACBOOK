
from django.contrib import admin
from .models import Subscription

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('student', 'professor', 'subscribed_at')
    list_filter = ('subscribed_at', 'student', 'professor')
    search_fields = ('student__username', 'professor__username', 'student__email', 'professor__email')
    raw_id_fields = ('student', 'professor') # Pour faciliter la sélectio
# Register your models here.
