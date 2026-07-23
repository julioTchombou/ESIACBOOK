from django.apps import AppConfig


class UsersConfig(AppConfig):
 default_auto_field = 'django.db.models.BigAutoField'
 name = 'users'

 def ready(self):
        # Importez les signaux ici pour qu'ils soient enregistrés
        import users.signals