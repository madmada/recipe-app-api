"""Test for ingredients API."""

from decimal import Decimal


from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe

from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse("recipe:ingredient-list")


def detail_url(ingredient_id):
    """Create and return an ingredient detail URL."""
    return reverse("recipe:ingredient-detail", args=[ingredient_id])


def create_user(email="user@example.com", password="testpass123"):
    """Create and return a new user."""
    return get_user_model().objects.create_user(email, password)


class PublicIngredientsApiTests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving ingredients."""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        """Test retrieving a list of ingredients."""
        Ingredient.objects.create(user=self.user, name="Salt")
        Ingredient.objects.create(user=self.user, name="Pepper")

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by("-name")
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """Test list of ingredients is limited to authenticated user."""
        user2 = create_user(email="user2@example.com")
        Ingredient.objects.create(user=user2, name="Vinegar")
        ingredient = Ingredient.objects.create(user=self.user, name="Sugar")

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], ingredient.name)
        self.assertEqual(res.data[0]["id"], ingredient.id)

    def test_update_ingredient(self):
        """Test updating an ingredient."""
        ingredient = Ingredient.objects.create(user=self.user, name="Cilantro")

        payload = {"name": "Coriander"}
        url = detail_url(ingredient.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload["name"])

    def test_delete_ingredient(self):
        """Test deleting an ingredient."""
        ingredient = Ingredient.objects.create(user=self.user, name="Lettuce")
        url = detail_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertFalse(ingredients.exists())

    def test_filter_ingredients_assigned_to_recipes(self):
        """Test listing ingredients by those assigned to recipes."""
        ingredient_apple = Ingredient.objects.create(user=self.user, name="Apples")
        ingredient_turkey = Ingredient.objects.create(
            user=self.user, name="Turkey"
        )
        recipe = Recipe.objects.create(
            title="Apple crumble",
            time_minutes=5,
            price=Decimal("10.00"),
            user=self.user,
        )
        recipe.ingredients.add(ingredient_apple)

        res = self.client.get(INGREDIENTS_URL, {"assigned_only": 1})

        serializer_apple = IngredientSerializer(ingredient_apple)
        serializer_turkey = IngredientSerializer(ingredient_turkey)

        self.assertIn(serializer_apple.data, res.data)
        # assert that turkey is not in the response, because it's not assigned to any recipe
        self.assertNotIn(serializer_turkey.data, res.data)

    def test_filtered_ingredients_unique(self):
        """Test filtered ingredients returns a unique list."""
        ingredient_eggs = Ingredient.objects.create(user=self.user, name="Eggs")
        Ingredient.objects.create(user=self.user, name="Lentils")
        recipe_eggs_benedict = Recipe.objects.create(
            title="Eggs Benedict",
            time_minutes=60,
            price=Decimal("7.00"),
            user=self.user,
        )
        recipe_hard_boiled_eggs = Recipe.objects.create(
            title="Hard boiled eggs",
            time_minutes=2,
            price=Decimal("3.00"),
            user=self.user,
        )

        recipe_eggs_benedict.ingredients.add(ingredient_eggs)
        recipe_hard_boiled_eggs.ingredients.add(ingredient_eggs)

        res = self.client.get(INGREDIENTS_URL, {"assigned_only": 1})

        self.assertEqual(len(res.data), 1)
