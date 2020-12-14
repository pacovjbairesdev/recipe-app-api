from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')


def create_user(**params):
    """Function for typing less"""
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test the Users API (public)"""

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_sucess(self):
        """Test creating user with valid payload is successful"""
        payload = {
            'email': 'test@test.com',
            'password': '123456',
            'name': 'Test Name'
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_user_exist(self):
        """Test trying to duplicate a user"""
        payload = {
            'email': 'test@test.com',
            'password': '123456',
            'name': 'Test Name'
        }
        create_user(**payload)

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_restriction(self):
        """Test password too short (less than 6 characters)"""
        payload = {
            'email': 'test@test.com',
            'password': '1234',
            'name': 'Test Name'
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exist = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exist)

    def test_create_token_for_user(self):
        """"Test that a token is created for the user"""
        payload = {
            'email': 'test@test.com',
            'password': '123456',
            'name': 'Test Name'
        }
        create_user(**payload)
        res = self.client.post(TOKEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('token', res.data)

    def test_create_token_invalid_creation(self):
        """Test that token is not created if invalid creation are given"""
        payload1 = {
            'email': 'test@test.com',
            'password': '123456',
            'name': 'Test Name'
        }
        payload2 = {
            'email': 'test@test.com',
            'password': 'wrong password',
            'name': 'Test Name'
        }
        create_user(**payload1)
        res = self.client.post(TOKEN_URL, payload2)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        """Test that token is not created if user doesn't exist"""
        payload1 = {
            'email': 'test@test.com',
            'password': '123456',
            'name': 'Test Name'
        }
        payload2 = {
            'email': 'user2@test.com',
            'password': 'other password',
            'name': 'Test Name'
        }
        create_user(**payload1)
        res = self.client.post(TOKEN_URL, payload2)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        """Check that email and pass are required"""
        payload1 = {
            'email': 'test@test.com',
            'password': '',
            'name': 'Test Name'
        }
        payload2 = {
            'email': '',
            'password': 'other password',
            'name': 'Test Name'
        }
        res = self.client.post(TOKEN_URL, payload1)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        res = self.client.post(TOKEN_URL, payload2)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
