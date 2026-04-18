from rest_framework import serializers
from .models import Reflection


class ReflectionIngestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reflection
        fields = ["ayah_key", "reflection_text"]

    def validate_ayah_key(self, value):
        if ":" not in value:
            raise serializers.ValidationError(
                "ayah_key must be in the format 'Surah:Ayah' (e.g., '2:255')."
            )
        return value


class ReflectionQueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reflection
        fields = [
            "id",
            "ayah_key",
            "reflection_text",
            "interval",
            "repetitions",
            "created_at",
            "next_review_date",
        ]
