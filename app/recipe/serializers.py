"""Serializers for recipe API."""

from rest_framework import serializers

from core.models import Recipe


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipes."""

    class Meta:
        model = Recipe
        fields = ["id", "title", "time_minutes", "price", "link"]
        read_only_fields = ["id"]

    # def create(self, validated_data):
    #     """Create and return a recipe."""
    #     return Recipe.objects.create(**validated_data)

    # def update(self, instance, validated_data):
    #     """Update and return a recipe."""
    #     return super().update(instance, validated_data)
