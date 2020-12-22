from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe

from recipe.serializers import TagSerializer


TAGS_URL = reverse('recipe:tag-list')


class PublicTagsApiTests(TestCase):
    """Test the publicly available tags API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving tags"""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    """Test the authorized user Tags API"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
                        'test@hola.com',
                        'password'
                        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving tags"""
        Tag.objects.create(name='Vegan', user=self.user)
        Tag.objects.create(name='Dessert', user=self.user)

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_my_tags(self):
        """Test that tags returned are for the authenticated user"""
        user2 = get_user_model().objects.create_user(
                    'test2@hola.com',
                    'password2'
                    )
        Tag.objects.create(name='Fruity', user=user2)
        tag2 = Tag.objects.create(name='Dessert', user=self.user)

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag2.name)

    def test_create_tags_successful(self):
        """Test creating a new tag"""
        payload = {'name': 'test'}
        self.client.post(TAGS_URL, payload)

        exists = Tag.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()
        self.assertTrue(exists)

    def test_create_invalid_tag(self):
        """Test create an invalid tag"""
        payload = {'name': ''}
        res = self.client.post(TAGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_tags_assign_to_recipe(self):
        """Test retrieving tags assigned to a recipe"""
        tag1 = Tag.objects.create(user=self.user, name='Tag 1')
        tag2 = Tag.objects.create(user=self.user, name='Tag 2')
        defaults = {
            'title': 'Sample recipe',
            'time_minutes': 10,
            'price': 5.00
        }
        recipe = Recipe.objects.create(user=self.user, **defaults)
        recipe.tags.add(tag1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_tags_assigned_unique(self):
        """Test that API returns unique items"""
        tag1 = Tag.objects.create(user=self.user, name='Tag 1')
        Tag.objects.create(user=self.user, name='Tag 2')
        defaults1 = {
            'title': 'Sample recipe',
            'time_minutes': 10,
            'price': 5.00
        }
        recipe1 = Recipe.objects.create(user=self.user, **defaults1)
        recipe1.tags.add(tag1)
        defaults2 = {
            'title': 'Sample recipe 2',
            'time_minutes': 10,
            'price': 5.00
        }
        recipe2 = Recipe.objects.create(user=self.user, **defaults2)
        recipe2.tags.add(tag1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
