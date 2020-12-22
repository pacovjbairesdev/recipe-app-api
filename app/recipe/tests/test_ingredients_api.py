from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe
from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse('recipe:ingredient-list')


class PublicIngredientApiTests(TestCase):
    """Test the publicly available ingredients API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Check that login is required to access the endpoint"""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTests(TestCase):
    """Test the authorized user Ingredients API"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'test@hola.com',
            'password'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredient_list(self):
        """Test retrieving a list of ingredients"""
        Ingredient.objects.create(user=self.user, name='Salt')
        Ingredient.objects.create(user=self.user, name='Sugar')

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredient_limited_to_user(self):
        """Check that ingredients for the authenticated user are returned"""
        user2 = get_user_model().objects.create_user(
            'test2@hola.com',
            'password2'
        )
        i1 = Ingredient.objects.create(user=self.user, name='Salt')
        Ingredient.objects.create(user=user2, name='Sugar')
        Ingredient.objects.create(user=user2, name='Pepper')

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], i1.name)

    def test_create_ingredient_successful(self):
        """Check that ingredients are created"""
        payload = {'name': 'Pepper'}
        self.client.post(INGREDIENTS_URL, payload)

        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name'],
        ).exists()

        self.assertTrue(exists)

    def test_create_ingredient_invalid(self):
        """Test creating invalid ingredient fails"""
        payload = {'name': ''}
        res = self.client.post(INGREDIENTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_ingredients_assign_to_recipe(self):
        """Test retrieving ingredients assigned to a recipe"""
        ingredient1 = Ingredient.objects.create(
                        user=self.user, name='Ingredient 1'
                        )
        ingredient2 = Ingredient.objects.create(
                        user=self.user, name='Ingredient 2'
                        )
        defaults = {
            'title': 'Sample recipe',
            'time_minutes': 10,
            'price': 5.00
        }
        recipe = Recipe.objects.create(user=self.user, **defaults)
        recipe.ingredients.add(ingredient1)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        serializer1 = IngredientSerializer(ingredient1)
        serializer2 = IngredientSerializer(ingredient2)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_ingredients_assigned_unique(self):
        """Test that API returns unique items"""
        ingredient1 = Ingredient.objects.create(
                        user=self.user, name='Ingredient 1'
                        )
        Ingredient.objects.create(user=self.user, name='Ingredient 2')
        defaults1 = {
            'title': 'Sample recipe',
            'time_minutes': 10,
            'price': 5.00
        }
        recipe1 = Recipe.objects.create(user=self.user, **defaults1)
        recipe1.ingredients.add(ingredient1)
        defaults2 = {
            'title': 'Sample recipe 2',
            'time_minutes': 10,
            'price': 5.00
        }
        recipe2 = Recipe.objects.create(user=self.user, **defaults2)
        recipe2.ingredients.add(ingredient1)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
