from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from .models import CustomUser, Notification


class UserMeViewTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='alice',
            email='alice@esiac.cm',
            password='StrongPass123!',
            first_name='Alice',
            role='student',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_patch_me_updates_user_profile(self):
        response = self.client.patch(
            reverse('user-me'),
            {
                'first_name': 'Alicia',
                'username': 'alicia',
                'email': 'alicia@esiac.cm',
                'phone_number': '690000000',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Alicia')
        self.assertEqual(self.user.username, 'alicia')
        self.assertEqual(self.user.phone_number, '690000000')

    def test_patch_me_rejects_locked_fields(self):
        response = self.client.patch(
            reverse('user-me'),
            {'role': 'admin'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_can_list_and_mark_notifications_as_read(self):
        notification = Notification.objects.create(
            user=self.user,
            title='Nouveau cours',
            message='Un nouveau cours vient d\'être publié.',
        )

        list_response = self.client.get(reverse('notifications'))
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)
        self.assertFalse(list_response.data[0]['read'])

        patch_response = self.client.patch(reverse('notifications'))
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)

        notification.refresh_from_db()
        self.assertTrue(notification.read)


class AdminUserDeletionTests(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            username='admin', email='admin@esiac.cm', password='StrongPass123!',
            first_name='Admin', role='admin',
        )
        self.other_admin = CustomUser.objects.create_user(
            username='other-admin', email='other-admin@esiac.cm', password='StrongPass123!',
            first_name='Other Admin', role='admin',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_admin_can_delete_another_admin(self):
        response = self.client.delete(
            reverse('user-detail', kwargs={'pk': self.other_admin.pk}),
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CustomUser.objects.filter(pk=self.other_admin.pk).exists())

    def test_admin_cannot_delete_own_account(self):
        response = self.client.delete(
            reverse('user-detail', kwargs={'pk': self.admin.pk}),
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(CustomUser.objects.filter(pk=self.admin.pk).exists())


class UserSecurityTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='student', email='student@esiac.cm', password='StrongPass123!',
            role='student',
        )
        self.client = APIClient()

    def test_public_registration_cannot_create_admin(self):
        response = self.client.post(
            reverse('register'),
            {
                'username': 'attacker',
                'email': 'attacker@esiac.cm',
                'password': 'StrongPass123!',
                'first_name': 'Attacker',
                'role': 'admin',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(CustomUser.objects.filter(email='attacker@esiac.cm').exists())

    def test_authenticated_user_cannot_use_user_viewset_crud(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            f'/api/users/{self.user.pk}/',
            {'role': 'admin'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, 'student')
