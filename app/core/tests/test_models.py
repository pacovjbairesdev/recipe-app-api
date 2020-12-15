from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


def sample_user(email='test@test.com', password='testpass'):
    """Create a sample user"""
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):

    def test_create_user_with_email_successful(self):
        """Test creating a new user with email is successful"""
        email = 'test@test.com'
        password = '12345'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test the email for a new user is normalized"""
        email = 'test@PRUEBA.COM'
        user = get_user_model().objects.create_user(
            email=email,
            password='xxx'
        )

        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        """Check if the email of the new user is valid"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, '1234')

    def test_create_new_superuser(self):
        """Test creating a new super user"""
        user = get_user_model().objects.create_superuser(
            'test@prueba.com',
            '1234'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_tag_str(self):
        """Test the tag string representations"""
        tag = models.Tag.objects.create(
            user=sample_user(),
            name='Vegan'
        )

        self.assertEqual(str(tag), tag.name)

    def test_ingredient_str(self):
        """Test the ingredient string representations"""
        tag = models.Ingredient.objects.create(
            user=sample_user(),
            name='Salt'
        )

        self.assertEqual(str(tag), tag.name)
